from flask import request, jsonify, current_app
import jwt
import datetime # Importamos datetime porque jwt.decode puede lanzar ExpiredSignatureError
from functools import wraps
from ..db.models import db, Role, Permission, UserRole, RolePermission # Importamos los modelos y la instancia db

# =========================================================================
# DECORADORES DE AUTORIZACIÓN
# =========================================================================

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

        return f(*args, **kwargs) # Pasa los argumentos originales y los nuevos del token
    return decorated

def admin_required(f):
    """
    Decorador para proteger rutas, asegurando que solo los usuarios con el rol 'Administrador' puedan acceder.
    Debe usarse DESPUÉS de @token_required en la cadena de decoradores.
    """
    @wraps(f)
    @token_required # Asegura que el token ya esté validado y la info del usuario disponible
    def decorated(*args, **kwargs):
        # user_role_from_token es pasado por el decorador @token_required
        if kwargs.get('user_role_from_token') != 'Administrador':
            return jsonify({'message': 'Acceso denegado: Se requiere rol de Administrador'}), 403 # Forbidden
        
        # Elimina los argumentos de token para evitar conflictos si la función decorada no los espera
        kwargs.pop('user_id_from_token', None)
        kwargs.pop('user_role_from_token', None)
        
        return f(*args, **kwargs)
    return decorated

def permission_required(permission_name):
    """
    Decorador para proteger rutas, verificando si el usuario autenticado tiene un permiso específico.
    Un administrador siempre tiene todos los permisos. Para otros roles, se consulta la DB.
    Debe usarse DESPUÉS de @token_required en la cadena de decoradores.
    """
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated_function(*args, **kwargs):
            user_id = kwargs.get('user_id_from_token')
            user_role = kwargs.get('user_role_from_token')

            if user_id is None:
                return jsonify({'message': 'Error de autenticación: user_id no encontrado en token.'}), 401

            # Si el usuario es Administrador, tiene todos los permisos
            if user_role == 'Administrador':
                # Elimina los argumentos de token para evitar conflictos
                kwargs.pop('user_id_from_token', None)
                kwargs.pop('user_role_from_token', None)
                return f(*args, **kwargs)

            # Obtener los roles del usuario desde la base de datos de roles
            # Nota: user_id proviene del JWT del servicio de autenticación
            user_roles = UserRole.query.filter_by(user_id=user_id).all()
            if not user_roles:
                return jsonify({'message': 'Acceso denegado: Usuario sin roles asignados.'}), 403

            # Obtener los permisos de todos los roles del usuario
            has_permission = False
            for ur in user_roles:
                # Busca si alguna combinación de rol-permiso existe para el rol del usuario y el permiso requerido
                role_permissions = db.session.query(RolePermission).\
                                   join(Permission).\
                                   filter(RolePermission.role_id == ur.role_id, Permission.name == permission_name).first()
                if role_permissions:
                    has_permission = True
                    break

            if not has_permission:
                return jsonify({'message': f'Acceso denegado: Se requiere el permiso "{permission_name}"'}), 403
            
            # Elimina los argumentos de token para evitar conflictos
            kwargs.pop('user_id_from_token', None)
            kwargs.pop('user_role_from_token', None)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator