FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie des fichiers de capteurs
COPY . /app/capteurs/

# Répertoire de travail
WORKDIR /app/capteurs

# Variables d'environnement
ENV MQTT_BROKER_HOST=mosquitto
ENV MQTT_BROKER_PORT=1883
ENV INTERVAL=5

# Commande par défaut
CMD ["python", "simulateur_capteurs.py"] 