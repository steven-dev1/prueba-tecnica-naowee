from flask_sqlalchemy import SQLAlchemy
import datetime # Aunque no se usa directamente aquí, es una buena práctica incluirlo si tus modelos tienen campos de fecha/hora

# db se pasará desde app.py, no se inicializa aquí directamente
db = SQLAlchemy()

# =========================================================================
# MODELOS DE LA BASE DE DATOS
# =========================================================================

class Role(db.Model):
    """
    Modelo para la tabla 'roles'.
    Representa los diferentes roles que un usuario puede tener en el sistema (ej. Administrador, Usuario).
    """
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        """Representación en cadena del objeto Role."""
        return f'<Role {self.name}>'

class Permission(db.Model):
    """
    Modelo para la tabla 'permissions'.
    Representa los permisos específicos dentro del sistema (ej. 'canchas:crear', 'reservas:cancelar').
    """
    __tablename__ = 'permissions'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __repr__(self):
        """Representación en cadena del objeto Permission."""
        return f'<Permission {self.name}>'

class UserRole(db.Model):
    """
    Modelo para la tabla de unión 'user_roles'.
    Establece la relación de muchos a muchos entre usuarios y roles.
    'user_id' es el ID del usuario del microservicio de Autenticación.
    """
    __tablename__ = 'user_roles'
    user_id = db.Column(db.Integer, primary_key=True) # ID del usuario del servicio de autenticación
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)

    # Relación con el modelo Role para facilitar la navegación de objetos.
    role = db.relationship('Role', backref=db.backref('user_roles', lazy=True))

class RolePermission(db.Model):
    """
    Modelo para la tabla de unión 'role_permissions'.
    Establece la relación de muchos a muchos entre roles y permisos.
    """
    __tablename__ = 'role_permissions'
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), primary_key=True)
    permission_id = db.Column(db.Integer, db.ForeignKey('permissions.id'), primary_key=True)

    # Relaciones con los modelos Role y Permission para facilitar la navegación.
    role = db.relationship('Role', backref=db.backref('role_permissions', lazy=True))
    permission = db.relationship('Permission', backref=db.backref('role_permissions', lazy=True))