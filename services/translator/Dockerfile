# Usa una imagen base de Python
FROM python:3.10-slim

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de dependencias
COPY pyproject.toml requirements.txt ./

# Instala dependencias
RUN pip install --no-cache-dir -r requirements.txt

# 📦 Copia todo el código fuente de tu aplicación
COPY . .

# Expone el puerto que usará uvicorn
EXPOSE 80

# Comando de arranque
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
