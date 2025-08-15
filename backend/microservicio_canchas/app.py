from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime # Importar datetime para updated_at
from functools import wraps

from .config import Config # Importa la clase de configuración
from .db.models import db, Court # Importa la instancia db y el modelo Court
from .core.security import token_required, admin_required, permission_required # Importa los decoradores de seguridad

app = Flask(__name__)
app.config.from_object(Config) # Carga la configuración

# Inicializa SQLAlchemy con la aplicación Flask
db.init_app(app)

# =========================================================================
# RUTAS DE LA API DE GESTIÓN DE CANCHAS
# =========================================================================

@app.route('/courts', methods=['POST'])
@admin_required # Solo administradores pueden crear canchas
# O: @permission_required('canchas:create') si quieres usar permisos granulares con el API Gateway haciendo la validación
def create_court():
    """
    Crea una nueva cancha de fútbol.
    Requiere: name, location, capacity, price_per_hour en el cuerpo de la solicitud (JSON).
    """
    data = request.get_json()
    name = data.get('name')
    location = data.get('location')
    capacity = data.get('capacity')
    price_per_hour = data.get('price_per_hour')

    if not all([name, location, capacity, price_per_hour]):
        return jsonify({'message': 'Faltan campos obligatorios (name, location, capacity, price_per_hour)'}), 400

    if Court.query.filter_by(name=name).first():
        return jsonify({'message': 'Ya existe una cancha con ese nombre'}), 409

    try:
        new_court = Court(name=name, location=location, capacity=capacity, price_per_hour=price_per_hour)
        db.session.add(new_court)
        db.session.commit()
        return jsonify({'message': 'Cancha creada exitosamente', 'court': new_court.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al crear cancha: {str(e)}'}), 500

@app.route('/courts', methods=['GET'])
@token_required # Cualquier usuario autenticado puede ver las canchas
def get_courts(user_id_from_token, user_role_from_token): # Los argumentos se pasan por el decorador
    """
    Obtiene todas las canchas de fútbol.
    """
    courts = Court.query.all()
    output = []
    for court in courts:
        output.append(court.to_dict())
    return jsonify(output), 200

@app.route('/courts/<int:court_id>', methods=['GET'])
@token_required # Cualquier usuario autenticado puede ver una cancha específica
def get_court_by_id(court_id, user_id_from_token, user_role_from_token):
    """
    Obtiene una cancha de fútbol por su ID.
    """
    court = Court.query.get(court_id)
    if not court:
        return jsonify({'message': 'Cancha no encontrada'}), 404
    return jsonify(court.to_dict()), 200

@app.route('/courts/<int:court_id>', methods=['PUT'])
@admin_required # Solo administradores pueden actualizar canchas
# O: @permission_required('canchas:update')
def update_court(court_id):
    """
    Actualiza la información de una cancha existente por su ID.
    Permite actualizar: name, location, capacity, price_per_hour, is_active.
    """
    court = Court.query.get(court_id)
    if not court:
        return jsonify({'message': 'Cancha no encontrada'}), 404

    data = request.get_json()
    new_name = data.get('name')
    new_location = data.get('location')
    new_capacity = data.get('capacity')
    new_price_per_hour = data.get('price_per_hour')
    new_is_active = data.get('is_active')

    try:
        if new_name is not None:
            if new_name != court.name and Court.query.filter_by(name=new_name).first():
                return jsonify({'message': 'Ya existe otra cancha con ese nombre'}), 409
            court.name = new_name
        
        if new_location is not None:
            court.location = new_location
        if new_capacity is not None:
            court.capacity = new_capacity
        if new_price_per_hour is not None:
            court.price_per_hour = new_price_per_hour
        if new_is_active is not None:
            court.is_active = new_is_active
        
        # Actualiza el timestamp 'updated_at'
        court.updated_at = datetime.utcnow()

        db.session.commit()
        return jsonify({'message': 'Cancha actualizada exitosamente', 'court': court.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al actualizar cancha: {str(e)}'}), 500

@app.route('/courts/<int:court_id>', methods=['DELETE'])
@admin_required # Solo administradores pueden eliminar canchas
# O: @permission_required('canchas:delete')
def delete_court(court_id):
    """
    Elimina una cancha de fútbol por su ID.
    """
    court = Court.query.get(court_id)
    if not court:
        return jsonify({'message': 'Cancha no encontrada'}), 404

    try:
        db.session.delete(court)
        db.session.commit()
        return jsonify({'message': 'Cancha eliminada exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al eliminar cancha: {str(e)}'}), 500

# Punto de entrada principal para la aplicación Flask
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Crea las tablas si no existen
    app.run(host='0.0.0.0', port=5002, debug=True) # Este servicio usará el puerto 5002