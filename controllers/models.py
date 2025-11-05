from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ==================== MODELS ======================================================================#
#ORM 
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True)
    name = db.Column(db.String(100))
    profile_pic = db.Column(db.String(100))
    role = db.Column(db.String(50), nullable=False, default='user')
    passhash = db.Column(db.String(500), nullable=False)
    is_admin=db.Column(db.Boolean, nullable=False ,default=False)
    #relationship 
    reservations = db.relationship('Reservation', backref='user', lazy=True)
    
    @property
    def password(self):
        raise AttributeError('password is not readable')
    @password.setter
    def password(self,password):
        self.passhash=generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.passhash, password)

    

class ParkingLot(db.Model):
    __tablename__ = 'parking_lots'
    lot_id = db.Column(db.Integer, primary_key=True)
    lot_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(300), nullable=False)
    postal_code = db.Column(db.String(100), nullable=False)
    billing_rate = db.Column(db.Float, nullable=False)
    maximum_spots = db.Column(db.Integer, nullable=False)
    #relationship
    spots= db.relationship('ParkingSpot', backref='parking_lot', lazy=True , cascade="all, delete-orphan", passive_deletes=False)
    @property
    def available_spots(self):
        return len([spot for spot in self.spots if spot.availability == 'A'])

class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lots.lot_id' ,ondelete='CASCADE') , nullable=False)
    availability = db.Column(db.String(1), nullable=False, default='A')   # A for available, U for unavailable
    spot_number = db.Column(db.String(10), nullable=True)
    #relationship
    reservations = db.relationship('Reservation', backref='parking_spot', lazy=True , cascade="all, delete-orphan", passive_deletes=False) 
    
class Reservation(db.Model):
    __tablename__ = 'reservations'
    reservation_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spots.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    grand_total = db.Column(db.Float, nullable=True)
    #relationship
    spot = db.relationship('ParkingSpot', foreign_keys=[spot_id] , overlaps="parking_spot,reservations")
    total_duration = db.Column(db.Float, nullable=True)  
