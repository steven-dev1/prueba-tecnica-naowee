import os

class Config:
    """
    Configuración específica para el Microservicio de Gestión de Reservas.
    Define la URL de la base de datos y la clave secreta para JWT.
    """
    # URL de conexión a la base de datos de PostgreSQL para reservas.
    # Obtiene de la variable de entorno 'DATABASE_URL' o usa un valor predeterminado.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@reservas_db:5432/reservas_db'
    
    # Deshabilita el seguimiento de modificaciones de SQLAlchemy para optimizar.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Clave secreta para JWT. Necesaria para verificar tokens de otros microservicios (Autenticación).
    # MUY IMPORTANTE: ¡Usar la misma clave que en el microservicio de Autenticación para JWT!
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu_clave_secreta_jwt_muy_segura_y_larga_DEFAULT'

    # URLs de otros microservicios (para llamadas inter-servicio)
    AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL') or 'http://auth_service:5000'
    CANCHAS_SERVICE_URL = os.environ.get('CANCHAS_SERVICE_URL') or 'http://canchas_service:5002'
    ROLES_SERVICE_URL = os.environ.get('ROLES_SERVICE_URL') or 'http://roles_service:5001'