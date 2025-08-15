# Usa una imagen base de Python
FROM python:3.10-slim

# Establece el directorio de trabajo en /app dentro del contenedor
WORKDIR /app

# Copia el archivo requirements.txt y las dependencias
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copia el resto del código de la aplicación (incluyendo app.py)
COPY . .

# Expone el puerto en el que se ejecutará la aplicación (Flask por defecto usa 5000)
EXPOSE 5000

# Comando para ejecutar la aplicación cuando el contenedor se inicie
# Usa flask run con el host 0.0.0.0 para que sea accesible desde fuera del contenedor
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]