from datetime import datetime
from database import db

class Instrument(db.Model):
    __tablename__ = "instruments"

    id = db.Column(db.Integer, primary_key=True)
    manufacturer = db.Column(db.String(150), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    serial_number = db.Column(db.String(100), unique=True, nullable=False)
    max_capacity = db.Column(db.Float)
    min_capacity = db.Column(db.Float)
    scale_interval = db.Column(db.Float)
    accuracy_class = db.Column(db.String(20))

class Inspection(db.Model):
    __tablename__ = "inspections"

    id = db.Column(db.Integer, primary_key=True)
    shop_name = db.Column(db.String(150), nullable=False)
    standard_weight = db.Column(db.Float, nullable=False)
    reading_weight = db.Column(db.Float, nullable=False)
    error = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)