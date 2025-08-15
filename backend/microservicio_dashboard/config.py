import os

class Config:
    """
    Configuración específica para el Microservicio de Dashboard Administrativo.
    Define las URLs de los otros microservicios y la clave secreta para JWT.
    """
    # Clave secreta para JWT. Necesaria para verificar tokens y generar nuevos para llamadas inter-servicio.
    # ¡MUY IMPORTANTE: Usar la misma clave que en el microservicio de Autenticación para JWT!
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'tu_clave_secreta_jwt_muy_segura_y_larga_DEFAULT'

    # URLs de los microservicios que el Dashboard consumirá
    AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL') or 'http://auth_service:5000'
    ROLES_SERVICE_URL = os.environ.get('ROLES_SERVICE_URL') or 'http://roles_service:5001'
    CANCHAS_SERVICE_URL = os.environ.get('CANCHAS_SERVICE_URL') or 'http://canchas_service:5002'
    RESERVAS_SERVICE_URL = os.environ.get('RESERVAS_SERVICE_URL') or 'http://reservas_service:5003'