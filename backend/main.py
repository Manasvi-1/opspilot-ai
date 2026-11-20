from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
import json
from datetime import datetime
from models import get_db, Order, Customer, RefundRequest, AuditEvent, init_db, SessionLocal

app = FastAPI(title="OpsPilot AI", description="Autonomous Business Operations Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic models ---
class CustomerRequest(BaseModel):
    customer_email: str
    message: str
    order_number: Optional[str] = None

class RefundDecision(BaseModel):
    refund_id: int
    decision: str  # approve / reject
    notes: Optional[str] = None

class AgentResponse(BaseModel):
    intent: str
    order_number: Optional[str]
    recommendation: str
    evidence: Dict[str, Any]
    requires_human: bool
    response_text: str

# --- Simple deterministic agent (LangGraph-style state) ---
def run_operations_agent(db: Session, request: CustomerRequest) -> AgentResponse:
    # 1. Intent classification (rule-based for MVP; replace with LLM structured output)
    msg = request.message.lower()
    if any(w in msg for w in ["refund", "return", "money back"]):
        intent = "refund_request"
    elif any(w in msg for w in ["where is", "delayed", "not arrived", "shipping", "delivery", "received", "arrive", "haven't"]):
        intent = "order_status"
    else:
        intent = "general_inquiry"

    # 2. Order lookup
    order = None
    if request.order_number:
        order = db.query(Order).filter(Order.order_number == request.order_number).first()
    if not order and request.customer_email:
        customer = db.query(Customer).filter(Customer.email == request.customer_email).first()
        if customer and customer.orders:
            order = customer.orders[0]  # demo: most recent

    evidence = {}
    requires_human = False
    recommendation = ""
    response_text = ""

    if not order:
        response_text = "I couldn't find an order matching the details provided. Please check the order number or email."
        return AgentResponse(
            intent=intent,
            order_number=None,
            recommendation="request_more_info",
            evidence={"customer_email": request.customer_email},
            requires_human=False,
            response_text=response_text
        )

    evidence = {
        "order_number": order.order_number,
        "status": order.status,
        "shipping_status": order.shipping_status,
        "expected_delivery": order.expected_delivery,
        "amount": order.amount,
        "product": order.product.name if order.product else "Unknown"
    }

    if intent == "order_status":
        if order.status == "delayed":
            recommendation = "inform_delay"
            response_text = f"Your order {order.order_number} is currently delayed. Expected delivery was {order.expected_delivery}. Shipping status: {order.shipping_status}. We are investigating with the carrier."
            requires_human = False
        else:
            recommendation = "status_update"
            response_text = f"Your order {order.order_number} is {order.status}. Shipping: {order.shipping_status}."
            requires_human = False

    elif intent == "refund_request":
        # Deterministic eligibility
        eligible = order.status in ["delivered", "delayed"] and order.amount <= 100
        if not eligible:
            recommendation = "deny_refund"
            response_text = f"Order {order.order_number} is not eligible for refund under current policy (status: {order.status}, amount: £{order.amount})."
            requires_human = False
        else:
            recommendation = "recommend_approval"
            response_text = f"Order {order.order_number} appears eligible for refund of £{order.amount}. Policy check passed. Awaiting human approval."
            requires_human = True
            # Create refund request
            rr = RefundRequest(
                order_id=order.id,
                reason=request.message,
                amount=order.amount,
                eligibility="eligible",
                ai_recommendation=response_text,
                evidence=json.dumps(evidence),
                status="pending_approval",
                audit_log=json.dumps([{"event": "ai_recommended", "time": datetime.utcnow().isoformat()}])
            )
            db.add(rr)
            db.commit()
            evidence["refund_request_id"] = rr.id

    # Audit
    audit = AuditEvent(
        event_type="agent_run",
        entity_type="order",
        entity_id=order.order_number,
        details=json.dumps({"intent": intent, "recommendation": recommendation})
    )
    db.add(audit)
    db.commit()

    return AgentResponse(
        intent=intent,
        order_number=order.order_number,
        recommendation=recommendation,
        evidence=evidence,
        requires_human=requires_human,
        response_text=response_text
    )

# --- Endpoints ---
@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
def root():
    return {"message": "OpsPilot AI is running", "docs": "/docs", "dashboard": "/dashboard"}

@app.post("/agent/process", response_model=AgentResponse)
def process_request(req: CustomerRequest, db: Session = Depends(get_db)):
    return run_operations_agent(db, req)

@app.get("/orders")
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(Order).all()
    return [
        {
            "order_number": o.order_number,
            "status": o.status,
            "amount": o.amount,
            "customer": o.customer.email if o.customer else None,
            "shipping": o.shipping_status
        } for o in orders
    ]

@app.get("/refunds/pending")
def pending_refunds(db: Session = Depends(get_db)):
    refunds = db.query(RefundRequest).filter(RefundRequest.status == "pending_approval").all()
    return [
        {
            "id": r.id,
            "order_id": r.order_id,
            "amount": r.amount,
            "ai_recommendation": r.ai_recommendation,
            "evidence": json.loads(r.evidence) if r.evidence else {}
        } for r in refunds
    ]

@app.post("/refunds/decide")
def decide_refund(decision: RefundDecision, db: Session = Depends(get_db)):
    rr = db.query(RefundRequest).filter(RefundRequest.id == decision.refund_id).first()
    if not rr:
        raise HTTPException(404, "Refund request not found")
    rr.status = "approved" if decision.decision == "approve" else "rejected"
    rr.human_decision = decision.decision
    # Update audit
    log = json.loads(rr.audit_log) if rr.audit_log else []
    log.append({"event": f"human_{decision.decision}", "notes": decision.notes, "time": datetime.utcnow().isoformat()})
    rr.audit_log = json.dumps(log)
    db.commit()
    return {"status": rr.status, "refund_id": rr.id}

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
      <title>OpsPilot AI – Control Centre</title>
      <style>
        body { font-family: system-ui; margin: 2rem; background: #0f172a; color: #e2e8f0; }
        .card { background: #1e293b; padding: 1.5rem; border-radius: 12px; margin: 1rem 0; }
        button { background: #3b82f6; color: white; border: none; padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; }
        input, textarea { width: 100%; padding: 0.5rem; margin: 0.5rem 0; background: #334155; color: white; border: 1px solid #475569; border-radius: 6px; }
        pre { background: #0f172a; padding: 1rem; border-radius: 8px; overflow-x: auto; }
      </style>
    </head>
    <body>
      <h1>OpsPilot AI – Human-in-the-loop Control Centre</h1>
      <div class="card">
        <h2>Process Customer Request</h2>
        <input id="email" placeholder="Customer email (alice@example.com)" value="alice@example.com">
        <textarea id="msg" rows="3" placeholder="Message">My order was supposed to arrive yesterday. I still haven't received it.</textarea>
        <input id="ord" placeholder="Order number (optional)" value="ORD-1001">
        <button onclick="process()">Run Agent</button>
        <pre id="result"></pre>
      </div>
      <div class="card">
        <h2>Pending Approvals</h2>
        <button onclick="loadPending()">Refresh</button>
        <div id="pending"></div>
      </div>
      <script>
        async function process() {
          const res = await fetch('/agent/process', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
              customer_email: document.getElementById('email').value,
              message: document.getElementById('msg').value,
              order_number: document.getElementById('ord').value || null
            })
          });
          const data = await res.json();
          document.getElementById('result').textContent = JSON.stringify(data, null, 2);
        }
        async function loadPending() {
          const res = await fetch('/refunds/pending');
          const data = await res.json();
          document.getElementById('pending').innerHTML = data.map(r => `
            <div style="border-bottom:1px solid #475569; padding:0.5rem 0">
              Refund #${r.id} – £${r.amount}<br>
              ${r.ai_recommendation}<br>
              <button onclick="decide(${r.id}, 'approve')">Approve</button>
              <button onclick="decide(${r.id}, 'reject')">Reject</button>
            </div>
          `).join('') || 'No pending approvals';
        }
        async function decide(id, decision) {
          await fetch('/refunds/decide', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({refund_id: id, decision})
          });
          loadPending();
        }
        loadPending();
      </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
