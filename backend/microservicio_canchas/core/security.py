from flask import request, jsonify, current_app
import jwt
import datetime
from functools import wraps
# En este microservicio, los decoradores NO necesitan importar los modelos de roles y permisos.
# Solo necesitan acceder a la DB de roles para verificar permisos si se requiere,
# pero en este servicio de canchas, asumiremos que los permisos ya vienen validados
# por el API Gateway o que las verificaciones son sencillas (ej. admin_required).
# Si necesitaras verificar permisos más granulares, deberías realizar una llamada al microservicio de Roles.

# Como la prueba lo pide paso a paso, por ahora no haremos llamadas entre microservicios
# para permisos. Simplificaremos el permission_required para este microservicio
# basándonos solo en el rol de Administrador.

# Si se requiriera verificar un permiso granular (ej. 'canchas:create')
# el decorador permission_required DEBERÍA hacer una llamada HTTP al microservicio de Roles
# para verificar si el user_id tiene ese permiso. Por simplicidad en este paso,
# asumimos que solo 'Administrador' puede hacer todo o ciertos permisos específicos.

# Si necesitas un permission_required que consulte el servicio de roles (más robusto),
# avisame y lo implementaremos. Por ahora, nos quedaremos con un permission_required
# que solo valida si el token es de un administrador para simplificar.

# Para simplificar y seguir el flujo, el permission_required simplemente verificará
# si el rol es 'Administrador'. Si necesitas que consulte el microservicio de roles,
# por favor házmelo saber.

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
            # Usa current_app.config para acceder a la configuración de la aplicación actual
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

# Para el microservicio de canchas, el permission_required se simplifica para
# solo permitir el acceso a Administradores o, si fuera necesario, a roles específicos
# que el API Gateway o el microservicio de Autenticación ya hayan verificado.
# Si se necesita una verificación de permiso granular (ej. 'canchas:create'),
# este decorador debería hacer una LLAMADA HTTP al microservicio de Roles para verificarlo.
# Por ahora, simplemente reusamos admin_required o una lógica simple.
def permission_required(permission_name): # permission_name es solo para contextualizar el error
    """
    Decorador para proteger rutas, verificando si el usuario autenticado tiene el rol de Administrador.
    (Versión simplificada para este microservicio. Para permisos granulares, se requeriría
    llamada a microservicio de Roles).
    """
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated_function(*args, **kwargs):
            user_role = kwargs.get('user_role_from_token')

            if user_role != 'Administrador':
                # En un caso real, aquí podrías verificar el permiso directamente si lo tienes
                # o hacer una llamada al microservicio de roles.
                return jsonify({'message': f'Acceso denegado: Se requiere el permiso "{permission_name}" o rol de Administrador'}), 403
            
            kwargs.pop('user_id_from_token', None)
            kwargs.pop('user_role_from_token', None)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator