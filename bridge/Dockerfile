FROM python:3.9-slim

# Installer netcat pour les diagnostics réseau
RUN apt-get update && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le script 
COPY mqtt_to_kafka_bridge.py .

# Créer un script de santé
RUN echo '#!/bin/bash\n\
echo "Vérification de la connexion à Kafka..."\n\
nc -z kafka 9092\n\
kafka_available=$?\n\
echo "Vérification de la connexion à MQTT..."\n\
nc -z mosquitto 1883\n\
mqtt_available=$?\n\
if [ $kafka_available -eq 0 ] && [ $mqtt_available -eq 0 ]; then\n\
  echo "Les deux services sont accessibles"\n\
  exit 0\n\
else\n\
  if [ $kafka_available -ne 0 ]; then echo "Kafka inaccessible"; fi\n\
  if [ $mqtt_available -ne 0 ]; then echo "MQTT inaccessible"; fi\n\
  exit 1\n\
fi' > /app/healthcheck.sh && chmod +x /app/healthcheck.sh


# Commande pour démarrer le bridge
CMD ["python", "mqtt_to_kafka_bridge.py"]
