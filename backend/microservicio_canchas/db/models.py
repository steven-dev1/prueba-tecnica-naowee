from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# db se pasará desde app.py, no se inicializa aquí directamente
db = SQLAlchemy()

# =========================================================================
# MODELOS DE LA BASE DE DATOS
# =========================================================================

class Court(db.Model):
    """
    Modelo para la tabla 'courts'.
    Representa una cancha de fútbol disponible para reserva.
    """
    __tablename__ = 'courts'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    capacity = db.Column(db.Integer, nullable=False) # Ej. 5, 7, 11 jugadores
    price_per_hour = db.Column(db.Numeric(10, 2), nullable=False) # Precio de reserva por hora
    is_active = db.Column(db.Boolean, default=True, nullable=False) # Indica si la cancha está disponible
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        """Representación en cadena del objeto Court."""
        return f'<Court {self.name}>'

    def to_dict(self):
        """Convierte el objeto Court a un diccionario para respuestas JSON."""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'capacity': self.capacity,
            'price_per_hour': float(self.price_per_hour), # Convertir Decimal a float para JSON
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
