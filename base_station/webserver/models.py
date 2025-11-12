from datetime import datetime
from config import db

class Protocol(db.Model):
    __tablename__ = 'protocols'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f"<Protocol {self.name}>"

class Device(db.Model):
    __tablename__ = 'devices'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    ip = db.Column(db.String(45), unique=True, nullable=False)
    port = db.Column(db.Integer, default=80)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    protocol_id = db.Column(db.Integer, db.ForeignKey('protocols.id'))
    protocol = db.relationship('Protocol')

    type = db.Column(db.String(50))
    __mapper_args__ = {'polymorphic_on': type, 'polymorphic_identity': 'device'}

class Drone(Device):
    __tablename__ = 'drones'
    id = db.Column(db.Integer, db.ForeignKey('devices.id'), primary_key=True)
    model = db.Column(db.String(100))
    status = db.Column(db.String(50), default='idle')

    __mapper_args__ = {'polymorphic_identity': 'drone'}

class Camera(Device):
    __tablename__ = 'cameras'
    id = db.Column(db.Integer, db.ForeignKey('devices.id'), primary_key=True)
    resolution = db.Column(db.String(50))
    fps = db.Column(db.Integer)

    __mapper_args__ = {'polymorphic_identity': 'camera'}
