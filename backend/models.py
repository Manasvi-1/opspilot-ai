import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import json

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////tmp/opspilot.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    orders = relationship("Order", back_populates="customer")

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    sku = Column(String, unique=True)
    name = Column(String)
    price = Column(Float)
    stock = Column(Integer)

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    order_number = Column(String, unique=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    status = Column(String)  # pending, processing, shipped, delivered, delayed, cancelled
    amount = Column(Float)
    shipping_status = Column(String)
    expected_delivery = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    customer = relationship("Customer", back_populates="orders")
    product = relationship("Product")

class RefundRequest(Base):
    __tablename__ = "refund_requests"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    reason = Column(Text)
    amount = Column(Float)
    eligibility = Column(String)  # eligible, ineligible, needs_review
    ai_recommendation = Column(Text)
    evidence = Column(Text)  # JSON
    status = Column(String)  # pending_approval, approved, rejected, executed
    human_decision = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    audit_log = Column(Text)  # JSON array of events

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id = Column(Integer, primary_key=True)
    event_type = Column(String)
    entity_type = Column(String)
    entity_id = Column(String)
    details = Column(Text)  # JSON
    timestamp = Column(DateTime, default=datetime.utcnow)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Sample data
    if db.query(Customer).count() == 0:
        c1 = Customer(email="alice@example.com", name="Alice Johnson")
        c2 = Customer(email="bob@example.com", name="Bob Smith")
        db.add_all([c1, c2])
        db.commit()

        p1 = Product(sku="SKU001", name="Wireless Headphones", price=75.0, stock=50)
        p2 = Product(sku="SKU002", name="Running Shoes", price=120.0, stock=20)
        db.add_all([p1, p2])
        db.commit()

        o1 = Order(order_number="ORD-1001", customer_id=1, product_id=1, status="delayed", amount=75.0,
                   shipping_status="in_transit", expected_delivery="2026-11-18")
        o2 = Order(order_number="ORD-1002", customer_id=2, product_id=2, status="delivered", amount=120.0,
                   shipping_status="delivered", expected_delivery="2026-11-15")
        o3 = Order(order_number="ORD-1003", customer_id=1, product_id=1, status="processing", amount=75.0,
                   shipping_status="pending", expected_delivery="2026-11-22")
        db.add_all([o1, o2, o3])
        db.commit()
    db.close()
    print("Database initialized with sample data.")

if __name__ == "__main__":
    init_db()
