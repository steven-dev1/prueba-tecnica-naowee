from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Booking(db.Model):

    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    court_id = db.Column(db.Integer, nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    status = db.Column(db.String(50), default='Confirmada', nullable=False) # Ej. 'Confirmada', 'Cancelada', 'Completada'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        """Representación en cadena del objeto Booking."""
        return f'<Booking {self.id} User:{self.user_id} Court:{self.court_id} Date:{self.booking_date} {self.start_time}-{self.end_time}>'

    def to_dict(self):
        """Convierte el objeto Booking a un diccionario para respuestas JSON."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'court_id': self.court_id,
            'booking_date': self.booking_date.isoformat(),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }