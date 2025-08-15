# Usa una imagen base de Python (coincide con la de los otros servicios)
FROM python:3.10-slim

# Establece el directorio de trabajo en /app dentro del contenedor
WORKDIR /app

# Copia el archivo requirements.txt y las dependencias
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copia el resto del código de la aplicación (incluyendo app.py, config.py, core/, db/)
COPY . .

# Expone el puerto en el que se ejecutará la aplicación (5002 para este servicio)
EXPOSE 5002

# Comando para ejecutar la aplicación cuando el contenedor se inicie
# Define la variable de entorno FLASK_APP
ENV FLASK_APP=app.py
CMD ["flask", "run", "--host=0.0.0.0", "--port=5002"]