from flask import request, jsonify, current_app
import jwt
import datetime
from functools import wraps
import requests # Necesario para hacer llamadas a otros microservicios

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
    Este decorador hará una llamada HTTP al microservicio de Roles para verificar el permiso.
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
                # Endpoint para verificar si un usuario tiene un permiso específico.
                # Necesitamos un endpoint en el servicio de roles que reciba user_id y permission_name
                # y devuelva un booleano o un 200/403.
                # Para esta implementación, asumiremos un endpoint como /users/<user_id>/permissions/<permission_name>/check
                # y que el servicio de roles lo valide.
                
                # IMPLEMENTACIÓN REALIZADA: Llama al microservicio de Roles
                # Asumimos que el servicio de roles tendrá un endpoint /users/<user_id>/has_permission
                # que reciba el permission_name en el body o como query param.
                # Para el ejemplo, usaremos POST /roles/verify_user_permission
                
                # Primero, necesitamos un endpoint en el servicio de roles que pueda verificar esto.
                # Si aún no lo hemos creado, este decorador hará un placeholder.
                # Por ahora, simplemente llamaremos a un endpoint general de permisos del usuario y lo filtraremos.
                # Una implementación más eficiente sería que el servicio de roles tuviera un endpoint dedicado.
                
                response = requests.get(f"{roles_service_url}/users/{user_id}/permissions", headers={'Authorization': f'Bearer {auth_token}'})
                response.raise_for_status() # Lanza un error para estados de respuesta no exitosos (4xx, 5xx)
                
                user_permissions = [p['name'] for p in response.json()]
                
                if permission_name not in user_permissions:
                    return jsonify({'message': f'Acceso denegado: Se requiere el permiso "{permission_name}"'}), 403

            except requests.exceptions.HTTPError as e:
                # Si la respuesta es 4xx o 5xx del servicio de roles
                if e.response.status_code == 403: # Si el servicio de roles ya deniega
                    return jsonify({'message': f'Acceso denegado: {permission_name}'}), 403
                return jsonify({'message': f'Error de comunicación con el servicio de roles: {e.response.text}'}), 500
            except requests.exceptions.ConnectionError:
                return jsonify({'message': 'Error de conexión con el servicio de roles'}), 500
            except Exception as e:
                return jsonify({'message': f'Error al verificar permisos: {str(e)}'}), 500
            
            kwargs.pop('user_id_from_token', None)
            kwargs.pop('user_role_from_token', None)
            return f(*args, **kwargs)
        return decorated_function
    return decorator