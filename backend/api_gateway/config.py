import os

class Config:
    """
    Configuración para el Microservicio del API Gateway.
    Define las URLs internas de los microservicios a los que enrutará.
    """
    # URLs de los microservicios internos (nombres de servicio de Docker Compose)
    AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL') or 'http://auth_service:5000'
    ROLES_SERVICE_URL = os.environ.get('ROLES_SERVICE_URL') or 'http://roles_service:5001'
    CANCHAS_SERVICE_URL = os.environ.get('CANCHAS_SERVICE_URL') or 'http://canchas_service:5002'
    RESERVAS_SERVICE_URL = os.environ.get('RESERVAS_SERVICE_URL') or 'http://reservas_service:5003'
    DASHBOARD_SERVICE_URL = os.environ.get('DASHBOARD_SERVICE_URL') or 'http://dashboard_service:5004'

    # Puerto en el que el API Gateway escuchará las peticiones externas
    GATEWAY_PORT = int(os.environ.get('GATEWAY_PORT') or 8000)