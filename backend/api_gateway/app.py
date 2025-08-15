from flask import Flask, request, jsonify, redirect
import requests
import json # Para manejar posibles errores de JSON en respuestas de los microservicios
from urllib.parse import urljoin # Para construir URLs de forma segura

from .config import Config # Importa la clase de configuración

app = Flask(__name__)
app.config.from_object(Config) # Carga la configuración

# =========================================================================
# FUNCIÓN AUXILIAR PARA PROXY DE PETICIONES
# =========================================================================

def proxy_request(service_url, path):
    """
    Función genérica para reenviar la petición entrante a un microservicio interno.
    Conserva el método HTTP, los encabezados y el cuerpo de la petición original.
    """
    # Construye la URL completa del microservicio interno
    target_url = urljoin(service_url, path)

    # Prepara los encabezados de la petición original
    # Excluye encabezados que Flask añade o que Docker ya maneja internamente
    headers = {key: value for key, value in request.headers if key.lower() not in ['host', 'accept-encoding']}
    
    # Añade el encabezado 'X-Forwarded-For' para registrar la IP del cliente original
    if 'X-Forwarded-For' not in headers:
        headers['X-Forwarded-For'] = request.remote_addr # O request.access_route[0]

    # Reenvía la petición
    try:
        # Usa requests.request para manejar todos los métodos HTTP
        # data=request.get_data() para reenviar el cuerpo raw de la petición
        response = requests.request(
            method=request.method,
            url=target_url,
            headers=headers,
            data=request.get_data(), # Usa get_data() para mantener el cuerpo original (raw)
            params=request.args,     # Reenvía los query parameters
            allow_redirects=False    # No seguir redirecciones automáticamente
        )
        
        # Copia los encabezados de la respuesta del microservicio
        response_headers = [(name, value) for name, value in response.headers.items()]

        # Retorna la respuesta del microservicio al cliente
        return response.content, response.status_code, response_headers

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code
        try:
            error_details = e.response.json()
        except json.JSONDecodeError:
            error_details = {'message': e.response.text}
        return jsonify({'error': f'Error del servicio interno ({status_code}): {error_details.get("message", "Desconocido")}'}), status_code
    except requests.exceptions.ConnectionError:
        return jsonify({'error': f'No se pudo conectar al servicio: {service_url}'}), 503 # Service Unavailable
    except Exception as e:
        return jsonify({'error': f'Error inesperado al reenviar la petición: {str(e)}'}), 500

# =========================================================================
# RUTAS DEL API GATEWAY
# =========================================================================

# Ruta para el microservicio de Autenticación
@app.route('/api/auth/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def auth_proxy(path):
    """Reenvía peticiones a auth_service."""
    return proxy_request(app.config['AUTH_SERVICE_URL'], path)

# Ruta para el microservicio de Roles y Permisos
@app.route('/api/roles/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def roles_proxy(path):
    """Reenvía peticiones a roles_service."""
    return proxy_request(app.config['ROLES_SERVICE_URL'], path)

# Ruta para el microservicio de Gestión de Canchas
@app.route('/api/canchas/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def canchas_proxy(path):
    """Reenvía peticiones a canchas_service."""
    return proxy_request(app.config['CANCHAS_SERVICE_URL'], path)

# Ruta para el microservicio de Gestión de Reservas
@app.route('/api/reservas/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def reservas_proxy(path):
    """Reenvía peticiones a reservas_service."""
    return proxy_request(app.config['RESERVAS_SERVICE_URL'], path)

# Ruta para el microservicio de Dashboard Administrativo
@app.route('/api/dashboard/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def dashboard_proxy(path):
    """Reenvía peticiones a dashboard_service."""
    return proxy_request(app.config['DASHBOARD_SERVICE_URL'], path)

# Ruta raíz para verificar que el Gateway esté activo
@app.route('/', methods=['GET'])
def root():
    return jsonify({"message": "API Gateway está funcionando"}), 200

# Punto de entrada principal para la aplicación Flask
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app.config['GATEWAY_PORT'], debug=True)