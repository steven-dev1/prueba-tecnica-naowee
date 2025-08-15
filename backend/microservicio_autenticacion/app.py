from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from functools import wraps
from .config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Modelo de Usuario (asegúrate de que este modelo ya esté definido como lo tienes)
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='Usuario', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    reset_token = db.Column(db.String(255), unique=True, nullable=True)
    reset_token_expiration = db.Column(db.DateTime, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        self.reset_token = jwt.encode(
            {'user_id': self.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        self.reset_token_expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        db.session.commit()
        return self.reset_token

# Decorador para proteger rutas (debe ser el mismo que tienes)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]

        if not token:
            return jsonify({'message': 'Se requiere un token de autenticación'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'message': 'Token inválido: usuario no encontrado'}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token ha expirado'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token inválido'}), 401
        except Exception as e:
            return jsonify({'message': f'Error al procesar el token: {str(e)}'}), 401

        return f(current_user, *args, **kwargs)
    return decorated

# Nuevo decorador para requerir rol de Administrador
def admin_required_auth_service(f): # Nombre diferente para evitar conflicto con los de core/security.py
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        current_user = args[0] # Obtiene el current_user del decorador token_required
        if current_user.role != 'Administrador':
            return jsonify({'message': 'Acceso denegado: Se requiere rol de Administrador'}), 403
        
        # Elimina el argumento current_user de args antes de llamar a la función original
        # si la función decorada no lo espera explícitamente, o si el f(*args, **kwargs)
        # no maneja bien args con current_user ya incluido.
        # Si la función lo espera, no necesitas pop. En este caso, get_all_users lo esperará.
        
        # Simplemente pasa current_user como el primer argumento.
        return f(current_user, *args[1:], **kwargs) # Pasa current_user y el resto de args/kwargs
    return decorated

# -------------------------------------------------------------------------
# RUTAS DEL MICROSERVICIO DE AUTENTICACIÓN Y USUARIOS
# -------------------------------------------------------------------------

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify({'message': 'Faltan campos obligatorios (username, email, password)'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'El nombre de usuario ya existe'}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'El correo electrónico ya está registrado'}), 409

    try:
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'Usuario registrado exitosamente'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al registrar usuario: {str(e)}'}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'message': 'Faltan campos obligatorios (email, password)'}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({'message': 'Credenciales inválidas'}), 401

    token_payload = {
        'user_id': user.id,
        'email': user.email,
        'role': user.role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
    return jsonify({'token': token}), 200

@app.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    user_data = {
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'role': current_user.role,
        'created_at': current_user.created_at.isoformat()
    }
    return jsonify(user_data), 200

@app.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    data = request.get_json()
    new_username = data.get('username')
    new_email = data.get('email')
    new_password = data.get('password')

    try:
        if new_username and new_username != current_user.username:
            if User.query.filter_by(username=new_username).first():
                return jsonify({'message': 'El nuevo nombre de usuario ya está en uso'}), 409
            current_user.username = new_username

        if new_email and new_email != current_user.email:
            if User.query.filter_by(email=new_email).first():
                return jsonify({'message': 'El nuevo correo electrónico ya está en uso'}), 409
            current_user.email = new_email

        if new_password:
            current_user.set_password(new_password)

        db.session.commit()
        return jsonify({'message': 'Perfil actualizado exitosamente'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al actualizar perfil: {str(e)}'}), 500

@app.route('/forgot_password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'message': 'Se requiere el correo electrónico'}), 400

    user = User.query.filter_by(email=email).first()

    if user:
        reset_token = user.generate_reset_token()
        print(f"DEBUG: Token de recuperación para {user.email}: {reset_token}")
        return jsonify({'message': 'Si el correo existe, se ha enviado un enlace de recuperación'}), 200
    else:
        return jsonify({'message': 'Si el correo existe, se ha enviado un enlace de recuperación'}), 200

@app.route('/reset_password', methods=['POST'])
def reset_password():
    data = request.get_json()
    reset_token = data.get('reset_token')
    new_password = data.get('new_password')

    if not all([reset_token, new_password]):
        return jsonify({'message': 'Faltan campos obligatorios (reset_token, new_password)'}), 400

    try:
        token_data = jwt.decode(reset_token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = token_data.get('user_id')

        user = User.query.get(user_id)

        if not user or user.reset_token != reset_token or \
           (user.reset_token_expiration and user.reset_token_expiration < datetime.datetime.utcnow()):
            return jsonify({'message': 'Token de recuperación inválido o expirado'}), 400

        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiration = None
        db.session.commit()

        return jsonify({'message': 'Contraseña restablecida exitosamente'}), 200

    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token de recuperación expirado'}), 400
    except jwt.InvalidTokenError:
        return jsonify({'message': 'Token de recuperación inválido'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error al restablecer contraseña: {str(e)}'}), 500

# NUEVO ENDPOINT: Obtener todos los usuarios (solo para administradores)
@app.route('/users', methods=['GET'])
@admin_required_auth_service # Solo los administradores pueden acceder a esta ruta
def get_all_users(current_user): # <-- ¡Añadido 'current_user' aquí!
    """
    Obtiene una lista de todos los usuarios registrados.
    Requiere rol de Administrador.
    """
    # Aunque current_user se pasa, no es estrictamente necesario usarlo aquí
    # ya que la verificación de admin se hace en el decorador.
    users = User.query.all()
    output = []
    for user in users:
        output.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'created_at': user.created_at.isoformat()
        })
    return jsonify(output), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)