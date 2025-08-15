from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date, time, timedelta # Importar datetime, date, time y timedelta
from functools import wraps
import requests # Necesario para hacer llamadas a otros microservicios

from .config import Config # Importa la clase de configuración
from .db.models import db, Booking # Importa la instancia db y el modelo Booking
from .core.security import token_required, admin_required, permission_required # Importa los decoradores de seguridad

app = Flask(__name__)
app.config.from_object(Config) # Carga la configuración

# Inicializa SQLAlchemy con la aplicación Flask
db.init_app(app)

# =========================================================================
# FUNCIONES AUXILIARES INTER-SERVICIO
# =========================================================================

def get_court_info(court_id, auth_token):
    """
    Obtiene la información de una cancha desde el Microservicio de Canchas.
    """
    try:
        url = f"{app.config['CANCHAS_SERVICE_URL']}/courts/{court_id}"
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Lanza excepción si la respuesta no es 2xx
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener info de cancha {court_id} desde el servicio de canchas: {e}")
        return None

def get_user_info(user_id, auth_token):
    """
    Obtiene la información de un usuario desde el Microservicio de Autenticación.
    """
    try:
        url = f"{app.config['AUTH_SERVICE_URL']}/profile" # Asume que /profile puede tomar un user_id si es admin, o solo el propio
        # Para obtener info de CUALQUIER usuario, el servicio de auth necesitaría un endpoint como /users/<user_id>
        # Por ahora, solo usaremos el user_id que ya viene en el token.
        return {'id': user_id} # Simula que tenemos la info básica
    except Exception as e:
        print(f"Error al obtener info de usuario {user_id} desde el servicio de autenticación: {e}")
        return None

# =========================================================================
# RUTAS DE LA API DE GESTIÓN DE RESERVAS
# =========================================================================

@app.route('/bookings', methods=['POST'])
@token_required # Cualquier usuario autenticado puede crear una reserva
def create_booking(user_id_from_token, user_role_from_token):
    """
    Crea una nueva reserva de cancha.
    Requiere: court_id, booking_date, start_time, end_time en el cuerpo (JSON).
    El user_id se toma del token JWT.
    """
    data = request.get_json()
    court_id = data.get('court_id')
    booking_date_str = data.get('booking_date') # Formato 'YYYY-MM-DD'
    start_time_str = data.get('start_time')     # Formato 'HH:MM'
    end_time_str = data.get('end_time')         # Formato 'HH:MM'

    if not all([court_id, booking_date_str, start_time_str, end_time_str]):
        return jsonify({'message': 'Faltan campos obligatorios (court_id, booking_date, start_time, end_time)'}), 400

    try:
        booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
        start_time = datetime.strptime(start_time_str, '%H:%M').time()
        end_time = datetime.strptime(end_time_str, '%H:%M').time()
    except ValueError:
        return jsonify({'message': 'Formato de fecha u hora inválido. Usa YYYY-MM-DD y HH:MM'}), 400

    if booking_date < date.today():
        return jsonify({'message': 'No se pueden hacer reservas en el pasado'}), 400
    if start_time >= end_time:
        return jsonify({'message': 'La hora de inicio debe ser anterior a la hora de fin'}), 400

    # Verificar que la cancha exista y esté activa (llamada al servicio de canchas)
    auth_token = request.headers.get('Authorization', '').split(" ")[1]
    court_info = get_court_info(court_id, auth_token)
    if not court_info or not court_info.get('is_active'):
        return jsonify({'message': 'Cancha no encontrada o no activa'}), 404

    # Verificar disponibilidad de la cancha para la fecha y hora solicitada
    # Consulta si hay alguna reserva existente que se superponga
    # El status 'Confirmada' asegura que solo se consideren reservas activas
    conflicting_bookings = Booking.query.filter(
        Booking.court_id == court_id,
        Booking.booking_date == booking_date,
        Booking.status == 'Confirmada',
        (
            (Booking.start_time < end_time) & (Booking.end_time > start_time)
        )
    ).first()

    if conflicting_bookings:
        return jsonify({'message': 'La cancha no está disponible en esa franja horaria'}), 409 # Conflict

    try:
        new_booking = Booking(
            user_id=user_id_from_token, # Tomamos el user_id del token JWT
            court_id=court_id,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            status='Confirmada'
        )
        db.session.add(new_booking)
        db.session.commit()
        return jsonify({'message': 'Reserva creada exitosamente', 'booking': new_booking.to_dict()}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al crear reserva: {str(e)}'}), 500

@app.route('/bookings', methods=['GET'])
@token_required
def get_bookings(user_id_from_token, user_role_from_token):
    """
    Obtiene todas las reservas.
    Administradores pueden ver todas las reservas. Usuarios normales solo sus propias reservas.
    """
    if user_role_from_token == 'Administrador':
        bookings = Booking.query.all()
    else:
        bookings = Booking.query.filter_by(user_id=user_id_from_token).all()
        
    output = []
    for booking in bookings:
        output.append(booking.to_dict())
    return jsonify(output), 200

@app.route('/bookings/<int:booking_id>', methods=['GET'])
@token_required
def get_booking_by_id(booking_id, user_id_from_token, user_role_from_token):
    """
    Obtiene una reserva por su ID.
    Administradores pueden ver cualquier reserva. Usuarios normales solo sus propias reservas.
    """
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'message': 'Reserva no encontrada'}), 404
    
    if user_role_from_token != 'Administrador' and booking.user_id != user_id_from_token:
        return jsonify({'message': 'Acceso denegado: No autorizado para ver esta reserva'}), 403

    return jsonify(booking.to_dict()), 200

@app.route('/bookings/<int:booking_id>', methods=['PUT'])
@token_required
def update_booking(booking_id, user_id_from_token, user_role_from_token):
    """
    Actualiza el estado o detalles de una reserva.
    Administradores pueden actualizar cualquier reserva. Usuarios normales solo las suyas.
    """
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'message': 'Reserva no encontrada'}), 404
    
    if user_role_from_token != 'Administrador' and booking.user_id != user_id_from_token:
        return jsonify({'message': 'Acceso denegado: No autorizado para actualizar esta reserva'}), 403

    data = request.get_json()
    new_status = data.get('status')
    new_date_str = data.get('booking_date')
    new_start_time_str = data.get('start_time')
    new_end_time_str = data.get('end_time')
    new_court_id = data.get('court_id')

    try:
        # Validar y actualizar campos
        if new_status:
            valid_statuses = ['Confirmada', 'Cancelada', 'Completada']
            if new_status not in valid_statuses:
                return jsonify({'message': 'Estado de reserva inválido'}), 400
            booking.status = new_status

        if new_date_str:
            new_booking_date = datetime.strptime(new_date_str, '%Y-%m-%d').date()
            if new_booking_date < date.today() and user_role_from_token != 'Administrador':
                return jsonify({'message': 'No se pueden mover reservas a una fecha pasada sin ser Administrador'}), 400
            booking.booking_date = new_booking_date
        
        if new_start_time_str:
            new_start_time = datetime.strptime(new_start_time_str, '%H:%M').time()
            booking.start_time = new_start_time
        
        if new_end_time_str:
            new_end_time = datetime.strptime(new_end_time_str, '%H:%M').time()
            booking.end_time = new_end_time
        
        if new_court_id:
            # Verificar si la nueva cancha existe y está activa
            auth_token = request.headers.get('Authorization', '').split(" ")[1]
            court_info = get_court_info(new_court_id, auth_token)
            if not court_info or not court_info.get('is_active'):
                return jsonify({'message': 'Nueva cancha no encontrada o no activa'}), 404
            booking.court_id = new_court_id

        # Si se modificaron fecha, hora o cancha, volver a verificar disponibilidad
        if new_date_str or new_start_time_str or new_end_time_str or new_court_id:
            if booking.start_time >= booking.end_time:
                return jsonify({'message': 'La hora de inicio debe ser anterior a la hora de fin'}), 400

            # Consulta si hay alguna reserva existente que se superponga (excluyendo la reserva actual)
            conflicting_bookings = Booking.query.filter(
                Booking.court_id == booking.court_id,
                Booking.booking_date == booking.booking_date,
                Booking.status == 'Confirmada',
                Booking.id != booking_id, # Excluir la propia reserva que se está actualizando
                (
                    (Booking.start_time < booking.end_time) & (Booking.end_time > booking.start_time)
                )
            ).first()

            if conflicting_bookings:
                return jsonify({'message': 'La nueva franja horaria de la cancha no está disponible'}), 409 # Conflict

        booking.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Reserva actualizada exitosamente', 'booking': booking.to_dict()}), 200
    except ValueError:
        db.session.rollback()
        return jsonify({'message': 'Formato de fecha u hora inválido. Usa YYYY-MM-DD y HH:MM'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al actualizar reserva: {str(e)}'}), 500

@app.route('/bookings/<int:booking_id>', methods=['DELETE'])
@token_required # Cualquier usuario puede intentar cancelar su reserva, el admin cualquier reserva
def delete_booking(booking_id, user_id_from_token, user_role_from_token):
    """
    Elimina (cancela) una reserva por su ID.
    Administradores pueden cancelar cualquier reserva. Usuarios normales solo las suyas.
    """
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'message': 'Reserva no encontrada'}), 404
    
    if user_role_from_token != 'Administrador' and booking.user_id != user_id_from_token:
        return jsonify({'message': 'Acceso denegado: No autorizado para cancelar esta reserva'}), 403

    try:
        # En lugar de eliminar, se recomienda cambiar el estado a 'Cancelada'
        booking.status = 'Cancelada'
        booking.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Reserva cancelada exitosamente', 'booking': booking.to_dict()}), 200
        # Si realmente quieres eliminar el registro de la DB:
        # db.session.delete(booking)
        # db.session.commit()
        # return jsonify({'message': 'Reserva eliminada exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al cancelar reserva: {str(e)}'}), 500

@app.route('/courts/<int:court_id>/availability', methods=['GET'])
@token_required # Cualquier usuario autenticado puede consultar disponibilidad
def get_court_availability(court_id, user_id_from_token, user_role_from_token):
    """
    Consulta la disponibilidad de una cancha para un rango de fechas.
    Requiere: date_start (YYYY-MM-DD), date_end (YYYY-MM-DD) como query parameters.
    Devuelve un diccionario con las franjas horarias disponibles/ocupadas por día.
    """
    date_start_str = request.args.get('date_start')
    date_end_str = request.args.get('date_end')

    if not all([date_start_str, date_end_str]):
        return jsonify({'message': 'Se requieren los parámetros date_start y date_end (YYYY-MM-DD)'}), 400

    try:
        start_date = datetime.strptime(date_start_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(date_end_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'message': 'Formato de fecha inválido. Usa YYYY-MM-DD'}), 400
    
    if start_date > end_date:
        return jsonify({'message': 'La fecha de inicio no puede ser posterior a la fecha de fin'}), 400

    # Verificar que la cancha exista y esté activa
    auth_token = request.headers.get('Authorization', '').split(" ")[1]
    court_info = get_court_info(court_id, auth_token)
    if not court_info or not court_info.get('is_active'):
        return jsonify({'message': 'Cancha no encontrada o no activa'}), 404
    
    availability = {}
    current_date = start_date
    
    # Rango de horas a considerar para la cancha (ej. 8 AM a 10 PM)
    # Esto debería ser configurable por cancha o por sistema
    operating_start_hour = time(8, 0)
    operating_end_hour = time(22, 0) # Hasta las 10 PM

    while current_date <= end_date:
        # Obtener todas las reservas confirmadas para esta cancha en esta fecha
        occupied_slots = Booking.query.filter(
            Booking.court_id == court_id,
            Booking.booking_date == current_date,
            Booking.status == 'Confirmada'
        ).all()

        daily_slots = []
        
        # Generar todas las posibles franjas de una hora (o la que consideres)
        # y verificar si están ocupadas
        current_slot_start = operating_start_hour
        while current_slot_start < operating_end_hour:
            current_slot_end = (datetime.combine(current_date, current_slot_start) + timedelta(hours=1)).time()
            
            is_occupied = False
            for booking in occupied_slots:
                # Comprobar si la franja actual se superpone con alguna reserva
                # Una superposición ocurre si (slot_start < booking_end) AND (slot_end > booking_start)
                if (current_slot_start < booking.end_time) and (current_slot_end > booking.start_time):
                    is_occupied = True
                    break
            
            daily_slots.append({
                'start_time': current_slot_start.isoformat(timespec='minutes'),
                'end_time': current_slot_end.isoformat(timespec='minutes'),
                'is_available': not is_occupied
            })
            current_slot_start = current_slot_end # Avanza a la siguiente franja

        availability[current_date.isoformat()] = daily_slots
        current_date += timedelta(days=1)

    return jsonify(availability), 200

# Punto de entrada principal para la aplicación Flask
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Crea las tablas si no existen
    app.run(host='0.0.0.0', port=5003, debug=True) # Este servicio usará el puerto 5003