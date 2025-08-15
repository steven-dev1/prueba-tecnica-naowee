from flask import Flask, request, jsonify
from functools import wraps
import requests
import json # Para manejar posibles errores de JSON en respuestas de otros servicios

from .config import Config # Importa la clase de configuración
from .core.security import token_required, admin_required # Importa los decoradores de seguridad

app = Flask(__name__)
app.config.from_object(Config) # Carga la configuración

# =========================================================================
# FUNCIONES AUXILIARES PARA LLAMADAS INTER-SERVICIO
# =========================================================================

def _make_service_request(method, url, auth_token, json_data=None, params=None):
    """
    Función auxiliar para realizar llamadas HTTP a otros microservicios.
    Maneja el token de autenticación y errores básicos.
    """
    headers = {'Authorization': f'Bearer {auth_token}', 'Content-Type': 'application/json'}
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=json_data, params=params)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=json_data, params=params)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, params=params)
        else:
            return {'error': 'Método HTTP no soportado por la función auxiliar'}, 405

        response.raise_for_status() # Lanza HTTPError para respuestas 4xx/5xx
        return response.json(), response.status_code
    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        try:
            error_details = e.response.json()
        except json.JSONDecodeError:
            error_details = {'message': e.response.text}
        return {'error': f'Error del servicio externo ({status_code}): {error_details.get("message", "Desconocido")}'}, status_code
    except requests.exceptions.ConnectionError:
        return {'error': f'No se pudo conectar al servicio: {url}'}, 503 # Service Unavailable
    except Exception as e:
        return {'error': f'Error inesperado al llamar al servicio: {str(e)}'}, 500

# =========================================================================
# RUTAS DEL DASHBOARD ADMINISTRATIVO
# =========================================================================

@app.route('/dashboard/summary', methods=['GET'])
@admin_required # Solo administradores pueden ver el resumen del dashboard
def get_dashboard_summary():
    """
    Obtiene un resumen de datos de todos los microservicios para el dashboard.
    Requiere token de Administrador.
    """
    auth_token = request.headers.get('Authorization', '').split(" ")[1]
    summary_data = {}

    # 1. Obtener usuarios
    users_url = f"{app.config['AUTH_SERVICE_URL']}/users" # Asumiendo que el servicio de auth tiene /users para admins
    users_data, users_status = _make_service_request('GET', users_url, auth_token)
    if users_status == 200:
        summary_data['total_users'] = len(users_data)
        summary_data['users'] = users_data # O una versión simplificada
    else:
        summary_data['users_error'] = users_data.get('error', 'Error al obtener usuarios')

    # 2. Obtener canchas
    courts_url = f"{app.config['CANCHAS_SERVICE_URL']}/courts"
    courts_data, courts_status = _make_service_request('GET', courts_url, auth_token)
    if courts_status == 200:
        summary_data['total_courts'] = len(courts_data)
        summary_data['active_courts'] = len([c for c in courts_data if c.get('is_active')])
        summary_data['courts'] = courts_data
    else:
        summary_data['courts_error'] = courts_data.get('error', 'Error al obtener canchas')

    # 3. Obtener reservas
    bookings_url = f"{app.config['RESERVAS_SERVICE_URL']}/bookings"
    bookings_data, bookings_status = _make_service_request('GET', bookings_url, auth_token)
    if bookings_status == 200:
        summary_data['total_bookings'] = len(bookings_data)
        summary_data['confirmed_bookings'] = len([b for b in bookings_data if b.get('status') == 'Confirmada'])
        summary_data['bookings'] = bookings_data
    else:
        summary_data['bookings_error'] = bookings_data.get('error', 'Error al obtener reservas')

    # 4. Obtener roles y permisos
    roles_url = f"{app.config['ROLES_SERVICE_URL']}/roles"
    roles_data, roles_status = _make_service_request('GET', roles_url, auth_token)
    if roles_status == 200:
        summary_data['total_roles'] = len(roles_data)
        summary_data['roles'] = roles_data
    else:
        summary_data['roles_error'] = roles_data.get('error', 'Error al obtener roles')

    permissions_url = f"{app.config['ROLES_SERVICE_URL']}/permissions"
    permissions_data, permissions_status = _make_service_request('GET', permissions_url, auth_token)
    if permissions_status == 200:
        summary_data['total_permissions'] = len(permissions_data)
        summary_data['permissions'] = permissions_data
    else:
        summary_data['permissions_error'] = permissions_data.get('error', 'Error al obtener permisos')

    return jsonify(summary_data), 200

# Endpoint para gestionar usuarios (redirige a auth_service)
@app.route('/dashboard/users', methods=['GET'])
@admin_required
# Asumiendo que AUTH_SERVICE_URL tiene un endpoint /users para administradores
def manage_users():
    auth_token = request.headers.get('Authorization', '').split(" ")[1]
    users_url = f"{app.config['AUTH_SERVICE_URL']}/users" # Este endpoint NO existe actualmente en auth_service
    # Para que esto funcione, necesitaríamos añadir un GET /users en auth_service
    # que sea admin_required y devuelva todos los usuarios.
    
    # Placeholder: Si no se implementa /users en auth_service, este devolverá un error.
    # Por ahora, simplemente intentaremos obtener la lista completa y reportar.
    response_data, status_code = _make_service_request('GET', users_url, auth_token)
    return jsonify(response_data), status_code

# Puedes añadir más rutas para acciones específicas del dashboard,
# como:
# - POST /dashboard/courts (para crear una cancha a través del dashboard, reenviando la petición a canchas_service)
# - PUT /dashboard/users/<user_id>/role (para asignar roles a usuarios, reenviando a roles_service)

# Endpoint de ejemplo para promover un usuario a Administrador a través del dashboard (requerirá un endpoint en roles_service)
# @app.route('/dashboard/users/<int:user_id>/promote_to_admin', methods=['PUT'])
# @admin_required
# def promote_user_to_admin(user_id):
#    auth_token = request.headers.get('Authorization', '').split(" ")[1]
#    roles_service_url = f"{app.config['ROLES_SERVICE_URL']}/users/{user_id}/roles"
#    # Primero, necesitamos obtener el ID del rol 'Administrador'
#    roles_data, roles_status = _make_service_request('GET', f"{app.config['ROLES_SERVICE_URL']}/roles", auth_token)
#    admin_role_id = None
#    if roles_status == 200:
#        for role in roles_data:
#            if role['name'] == 'Administrador':
#                admin_role_id = role['id']
#                break
#    if not admin_role_id:
#        return jsonify({'message': 'Rol Administrador no encontrado en el servicio de roles'}), 500
#
#    # Luego, asignamos ese rol al usuario
#    json_data = {'role_id': admin_role_id}
#    response_data, status_code = _make_service_request('POST', roles_service_url, auth_token, json_data=json_data)
#
#    return jsonify(response_data), status_code


# Punto de entrada principal para la aplicación Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True) # Este servicio usará el puerto 5004