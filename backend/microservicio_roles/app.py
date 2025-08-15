from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import jwt # Todavía necesario para algunos casos si se manejan tokens fuera de los decoradores
import datetime
from functools import wraps # Todavía necesario si quieres usar wraps en alguna función directamente
from .config import Config # Importa la clase de configuración
from .db.models import db, Role, Permission, UserRole, RolePermission # Importa los modelos y la instancia db
from .core.security import token_required, admin_required, permission_required # Importa los decoradores

app = Flask(__name__)
app.config.from_object(Config) # Carga la configuración

# Inicializa SQLAlchemy con la aplicación Flask
db.init_app(app)

# =========================================================================
# RUTAS DE LA API DE ROLES Y PERMISOS
# =========================================================================

# --- Rutas para Roles ---
@app.route('/roles', methods=['POST'])
@admin_required # Solo administradores pueden crear roles
def create_role():
    """Crea un nuevo rol. Requiere rol de Administrador."""
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'message': 'Nombre del rol es requerido'}), 400

    if Role.query.filter_by(name=name).first():
        return jsonify({'message': 'El rol ya existe'}), 409

    try:
        new_role = Role(name=name)
        db.session.add(new_role)
        db.session.commit()
        return jsonify({'message': 'Rol creado exitosamente', 'role': {'id': new_role.id, 'name': new_role.name}}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al crear rol: {str(e)}'}), 500

@app.route('/roles', methods=['GET'])
@token_required # Cualquier usuario autenticado puede leer roles
def get_roles(user_id_from_token, user_role_from_token): # Captura los argumentos del token
    """Obtiene todos los roles."""
    roles = Role.query.all()
    output = []
    for role in roles:
        output.append({'id': role.id, 'name': role.name})
    return jsonify(output), 200

@app.route('/roles/<int:role_id>', methods=['PUT'])
@admin_required # Solo administradores pueden actualizar roles
def update_role(role_id):
    """Actualiza un rol existente por ID. Requiere rol de Administrador."""
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'message': 'Rol no encontrado'}), 404

    data = request.get_json()
    new_name = data.get('name')

    if not new_name:
        return jsonify({'message': 'Nombre del rol es requerido'}), 400

    if Role.query.filter_by(name=new_name).first() and new_name != role.name:
        return jsonify({'message': 'El nuevo nombre de rol ya existe'}), 409

    try:
        role.name = new_name
        db.session.commit()
        return jsonify({'message': 'Rol actualizado exitosamente', 'role': {'id': role.id, 'name': role.name}}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al actualizar rol: {str(e)}'}), 500

@app.route('/roles/<int:role_id>', methods=['DELETE'])
@admin_required # Solo administradores pueden eliminar roles
def delete_role(role_id):
    """Elimina un rol por ID. Requiere rol de Administrador."""
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'message': 'Rol no encontrado'}), 404

    try:
        db.session.delete(role)
        db.session.commit()
        return jsonify({'message': 'Rol eliminado exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al eliminar rol: {str(e)}'}), 500

# --- Rutas para Permisos ---
@app.route('/permissions', methods=['POST'])
@admin_required # Solo administradores pueden crear permisos
def create_permission():
    """Crea un nuevo permiso. Requiere rol de Administrador."""
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'message': 'Nombre del permiso es requerido'}), 400

    if Permission.query.filter_by(name=name).first():
        return jsonify({'message': 'El permiso ya existe'}), 409

    try:
        new_permission = Permission(name=name)
        db.session.add(new_permission)
        db.session.commit()
        return jsonify({'message': 'Permiso creado exitosamente', 'permission': {'id': new_permission.id, 'name': new_permission.name}}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al crear permiso: {str(e)}'}), 500

@app.route('/permissions', methods=['GET'])
@token_required # Cualquier usuario autenticado puede leer permisos
def get_permissions(user_id_from_token, user_role_from_token): # Captura los argumentos del token
    """Obtiene todos los permisos."""
    permissions = Permission.query.all()
    output = []
    for perm in permissions:
        output.append({'id': perm.id, 'name': perm.name})
    return jsonify(output), 200

@app.route('/permissions/<int:permission_id>', methods=['PUT'])
@admin_required # Solo administradores pueden actualizar permisos
def update_permission(permission_id):
    """Actualiza un permiso existente por ID. Requiere rol de Administrador."""
    permission = Permission.query.get(permission_id)
    if not permission:
        return jsonify({'message': 'Permiso no encontrado'}), 404

    data = request.get_json()
    new_name = data.get('name')

    if not new_name:
        return jsonify({'message': 'Nombre del permiso es requerido'}), 400

    if Permission.query.filter_by(name=new_name).first() and new_name != permission.name:
        return jsonify({'message': 'El nuevo nombre de permiso ya existe'}), 409

    try:
        permission.name = new_name
        db.session.commit()
        return jsonify({'message': 'Permiso actualizado exitosamente', 'permission': {'id': permission.id, 'name': permission.name}}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al actualizar permiso: {str(e)}'}), 500

@app.route('/permissions/<int:permission_id>', methods=['DELETE'])
@admin_required # Solo administradores pueden eliminar permisos
def delete_permission(permission_id):
    """Elimina un permiso por ID. Requiere rol de Administrador."""
    permission = Permission.query.get(permission_id)
    if not permission:
        return jsonify({'message': 'Permiso no encontrado'}), 404

    try:
        db.session.delete(permission)
        db.session.commit()
        return jsonify({'message': 'Permiso eliminado exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al eliminar permiso: {str(e)}'}), 500

# --- Rutas para Asignación de Roles/Permisos a Usuarios y Roles ---
@app.route('/users/<int:user_id>/roles', methods=['POST'])
@admin_required # Solo administradores pueden asignar roles a usuarios
def assign_role_to_user(user_id):
    """Asigna un rol a un usuario. Requiere rol de Administrador."""
    data = request.get_json()
    role_id = data.get('role_id')

    if not role_id:
        return jsonify({'message': 'ID del rol es requerido'}), 400

    role = Role.query.get(role_id)
    if not role:
        return jsonify({'message': 'Rol no encontrado'}), 404

    # Verificar si el usuario ya tiene el rol
    if UserRole.query.filter_by(user_id=user_id, role_id=role_id).first():
        return jsonify({'message': 'El usuario ya tiene este rol'}), 409

    try:
        user_role = UserRole(user_id=user_id, role_id=role_id)
        db.session.add(user_role)
        db.session.commit()
        return jsonify({'message': 'Rol asignado exitosamente al usuario'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al asignar rol: {str(e)}'}), 500

@app.route('/users/<int:user_id>/roles', methods=['GET'])
@token_required # Cualquier usuario autenticado puede ver los roles de UN usuario
def get_user_roles(user_id, user_id_from_token, user_role_from_token):
    """Obtiene los roles asignados a un usuario específico.
    Un administrador puede ver cualquier usuario. Un usuario normal solo puede ver sus propios roles.
    """
    if user_role_from_token != 'Administrador' and user_id_from_token != user_id:
        return jsonify({'message': 'Acceso denegado: No autorizado para ver roles de otro usuario'}), 403

    user_roles = UserRole.query.filter_by(user_id=user_id).all()
    output = []
    for ur in user_roles:
        role = Role.query.get(ur.role_id)
        if role:
            output.append({'id': role.id, 'name': role.name})
    return jsonify(output), 200

@app.route('/users/<int:user_id>/roles/<int:role_id>', methods=['DELETE'])
@admin_required # Solo administradores pueden revocar roles de usuarios
def revoke_role_from_user(user_id, role_id):
    """Revoca un rol de un usuario. Requiere rol de Administrador."""
    user_role = UserRole.query.filter_by(user_id=user_id, role_id=role_id).first()
    if not user_role:
        return jsonify({'message': 'Asignación de rol no encontrada para este usuario y rol'}), 404

    try:
        db.session.delete(user_role)
        db.session.commit()
        return jsonify({'message': 'Rol revocado exitosamente del usuario'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al revocar rol: {str(e)}'}), 500

@app.route('/roles/<int:role_id>/permissions', methods=['POST'])
@admin_required # Solo administradores pueden asignar permisos a roles
def assign_permission_to_role(role_id):
    """Asigna un permiso a un rol. Requiere rol de Administrador."""
    data = request.get_json()
    permission_id = data.get('permission_id')

    if not permission_id:
        return jsonify({'message': 'ID del permiso es requerido'}), 400

    role = Role.query.get(role_id)
    permission = Permission.query.get(permission_id)

    if not role:
        return jsonify({'message': 'Rol no encontrado'}), 404
    if not permission:
        return jsonify({'message': 'Permiso no encontrado'}), 404

    # Verificar si el rol ya tiene el permiso
    if RolePermission.query.filter_by(role_id=role_id, permission_id=permission_id).first():
        return jsonify({'message': 'El rol ya tiene este permiso asignado'}), 409

    try:
        role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
        db.session.add(role_permission)
        db.session.commit()
        return jsonify({'message': 'Permiso asignado exitosamente al rol'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al asignar permiso: {str(e)}'}), 500

@app.route('/roles/<int:role_id>/permissions', methods=['GET'])
@token_required # Cualquier usuario autenticado puede ver los permisos de un rol
def get_role_permissions(role_id, user_id_from_token, user_role_from_token):
    """Obtiene los permisos asignados a un rol específico."""
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'message': 'Rol no encontrado'}), 404

    role_permissions = RolePermission.query.filter_by(role_id=role_id).all()
    output = []
    for rp in role_permissions:
        permission = Permission.query.get(rp.permission_id)
        if permission:
            output.append({'id': permission.id, 'name': permission.name})
    return jsonify(output), 200

@app.route('/roles/<int:role_id>/permissions/<int:permission_id>', methods=['DELETE'])
@admin_required # Solo administradores pueden revocar permisos de roles
def revoke_permission_from_role(role_id, permission_id):
    """Revoca un permiso de un rol. Requiere rol de Administrador."""
    role_permission = RolePermission.query.filter_by(role_id=role_id, permission_id=permission_id).first()
    if not role_permission:
        return jsonify({'message': 'Asignación de permiso no encontrada para este rol y permiso'}), 404

    try:
        db.session.delete(role_permission)
        db.session.commit()
        return jsonify({'message': 'Permiso revocado exitosamente del rol'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al revocar permiso: {str(e)}'}), 500

# Punto de entrada principal para la aplicación Flask
if __name__ == '__main__':
    with app.app_context():
        db.create_all() # Crea las tablas si no existen
    app.run(host='0.0.0.0', port=5001, debug=True) # Este servicio usará el puerto 5001