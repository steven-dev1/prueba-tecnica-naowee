import os

class Config:
    """
    Configuración específica para el Microservicio de Roles y Permisos.
    Define la URL de la base de datos y la clave secreta para JWT.
    """
    # URL de conexión a la base de datos de PostgreSQL para roles y permisos.
    # Obtiene de la variable de entorno 'DATABASE_URL' o usa un valor predeterminado.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:password@roles_db:5432/roles_db'
    
    # Deshabilita el seguimiento de modificaciones de SQLAlchemy para optimizar.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Clave secreta para JWT. Necesaria para verificar tokens de otros microservicios (Autenticación).
    # MUY IMPORTANTE: ¡Usar la misma clave que en el microservicio de Autenticación para JWT!
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'naowee'