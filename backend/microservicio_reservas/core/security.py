from flask import request, jsonify, current_app
import jwt
import datetime
from functools import wraps
import requests


def token_required(f):
    """
    Decorador para proteger rutas, verificando la validez del JWT.
    Extrae el 'user_id' y 'role' del token y los pasa como kwargs a la función decorada.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1] # Formato: Bearer <token>

        if not token:
            return jsonify({'message': 'Se requiere un token de autenticación'}), 401

        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            kwargs['user_id_from_token'] = data.get('user_id')
            kwargs['user_role_from_token'] = data.get('role')
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token ha expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido'}), 401
        except Exception as e:
            return jsonify({'message': f'Error al procesar el token: {str(e)}'}), 401

        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """
    Decorador para proteger rutas, asegurando que solo los usuarios con el rol 'Administrador' puedan acceder.
    Debe usarse DESPUÉS de @token_required en la cadena de decoradores.
    """
    @wraps(f)
    @token_required # Asegura que el token ya esté validado y la info del usuario disponible
    def decorated(*args, **kwargs):
        if kwargs.get('user_role_from_token') != 'Administrador':
            return jsonify({'message': 'Acceso denegado: Se requiere rol de Administrador'}), 403 # Forbidden
        
        # Elimina los argumentos de token para evitar conflictos
        kwargs.pop('user_id_from_token', None)
        kwargs.pop('user_role_from_token', None)
        
        return f(*args, **kwargs)
    return decorated

def permission_required(permission_name):
    """
    Decorador para proteger rutas, verificando si el usuario autenticado tiene un permiso específico.
    Este decorador intentará verificar el permiso llamando al microservicio de Roles.
    """
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated_function(*args, **kwargs):
            user_id = kwargs.get('user_id_from_token')
            user_role = kwargs.get('user_role_from_token')
            auth_token = request.headers.get('Authorization', '').split(" ")[1] # Obtiene el token original

            if user_id is None:
                return jsonify({'message': 'Error de autenticación: user_id no encontrado en token.'}), 401

            # Si el usuario es Administrador, tiene todos los permisos
            if user_role == 'Administrador':
                kwargs.pop('user_id_from_token', None)
                kwargs.pop('user_role_from_token', None)
                return f(*args, **kwargs)

            # Para otros roles, consultar al microservicio de Roles y Permisos
            try:
                roles_service_url = current_app.config['ROLES_SERVICE_URL']
                # Construye la URL del endpoint para verificar el permiso
                # Asumimos un endpoint como /users/<user_id>/has_permission/<permission_name> en el servicio de Roles
                # O un endpoint que reciba el user_id y el permission_name en el body
                
                # Opción 1: Llamar a un endpoint que verifique si el user_id tiene el permiso.
                # Tendrías que implementar este endpoint en roles_service.
                # response = requests.post(f"{roles_service_url}/verify_permission", json={'user_id': user_id, 'permission_name': permission_name}, headers={'Authorization': f'Bearer {auth_token}'})
                
                # Por simplicidad y sin un endpoint de verificación granular en roles_service,
                # vamos a simular la verificación o asumir que el rol ya implica el permiso.
                # Si necesitas la llamada real al servicio de Roles, lo implementaremos después de tener ese endpoint.
                
                # Por ahora, si no es admin, negamos el permiso para demostrar el flujo.
                # ESTO DEBERÍA SER REEMPLAZADO POR UNA LLAMADA REAL A ROLES_SERVICE
                has_permission = False
                # Aquí iría la lógica de llamada al servicio de Roles
                # Por ejemplo:
                # resp = requests.get(f"{roles_service_url}/users/{user_id}/permissions", headers={'Authorization': f'Bearer {auth_token}'})
                # if resp.status_code == 200:
                #     user_permissions = [p['name'] for p in resp.json()]
                #     if permission_name in user_permissions:
                #         has_permission = True
                # else:
                #     # Manejar error en la comunicación con el servicio de roles
                #     print(f"Error calling roles service: {resp.status_code} {resp.text}")
                #     return jsonify({'message': 'Error interno al verificar permisos'}), 500

                # Temporalmente, si no es admin y se requiere un permiso, se niega.
                # Esto es un placeholder para la lógica de comunicación con el servicio de roles.
                if not has_permission: # Siempre será False si no es Admin en este placeholder
                    return jsonify({'message': f'Acceso denegado: Se requiere el permiso "{permission_name}"'}), 403

            except requests.exceptions.RequestException as e:
                return jsonify({'message': f'Error de comunicación con el servicio de roles: {str(e)}'}), 500
            except Exception as e:
                return jsonify({'message': f'Error al verificar permisos: {str(e)}'}), 500
            
            kwargs.pop('user_id_from_token', None)
            kwargs.pop('user_role_from_token', None)
            return f(*args, **kwargs)
        return decorated_function
    return decorator