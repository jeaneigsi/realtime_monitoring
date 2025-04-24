# mqtt_to_kafka_bridge.py
import paho.mqtt.client as mqtt
from kafka import KafkaProducer
import json
import os
import time
import socket
import logging
import sys

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('mqtt-kafka-bridge')

# Configuration
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "raw_data")
MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "capteurs/#")
MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", 12))
RETRY_INTERVAL = int(os.getenv("RETRY_INTERVAL", 10))

# Fonction pour vérifier si Kafka est disponible
def is_kafka_available(bootstrap_servers):
    """Vérifie si Kafka est disponible en essayant d'établir une connexion TCP"""
    try:
        # Extraire host et port
        host, port = bootstrap_servers.split(':')
        port = int(port)
        
        # Essayer d'ouvrir une connexion socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        
        # Si la connexion est réussie, le résultat est 0
        return result == 0
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de disponibilité de Kafka: {e}")
        return False

# Fonction pour vérifier si MQTT est disponible
def is_mqtt_available(broker, port):
    """Vérifie si le broker MQTT est disponible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((broker, port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de disponibilité de MQTT: {e}")
        return False

# Attendre que Kafka soit prêt
def wait_for_kafka():
    retry_count = 0
    while retry_count < MAX_RETRY_ATTEMPTS:
        if is_kafka_available(KAFKA_BOOTSTRAP_SERVERS):
            logger.info(f"Kafka est disponible sur {KAFKA_BOOTSTRAP_SERVERS}")
            return True
        logger.warning(f"Kafka n'est pas disponible. Nouvelle tentative dans {RETRY_INTERVAL} secondes...")
        time.sleep(RETRY_INTERVAL)
        retry_count += 1
    
    logger.error(f"Échec de connexion à Kafka après {MAX_RETRY_ATTEMPTS} tentatives.")
    return False

# Attendre que MQTT soit prêt
def wait_for_mqtt():
    retry_count = 0
    while retry_count < MAX_RETRY_ATTEMPTS:
        if is_mqtt_available(MQTT_BROKER, MQTT_PORT):
            logger.info(f"MQTT est disponible sur {MQTT_BROKER}:{MQTT_PORT}")
            return True
        logger.warning(f"MQTT n'est pas disponible. Nouvelle tentative dans {RETRY_INTERVAL} secondes...")
        time.sleep(RETRY_INTERVAL)
        retry_count += 1
    
    logger.error(f"Échec de connexion à MQTT après {MAX_RETRY_ATTEMPTS} tentatives.")
    return False

# Configuration avec gestion des erreurs et reconnexion
def create_kafka_producer():
    try:
        logger.info(f"Connexion à Kafka sur {KAFKA_BOOTSTRAP_SERVERS}...")
        producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=5,
            retry_backoff_ms=1000,
            request_timeout_ms=30000,
            max_block_ms=60000
        )
        logger.info("Connexion à Kafka réussie")
        return producer
    except Exception as e:
        logger.error(f"Erreur de connexion à Kafka: {str(e)}")
        return None

def on_connect(client, userdata, flags, rc):
    logger.info(f"Connecté au broker MQTT avec le code {rc}")
    # S'abonner à tous les sujets de capteurs
    client.subscribe(MQTT_TOPIC)
    logger.info(f"Abonné à {MQTT_TOPIC}")

def on_message(client, userdata, msg):
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        # Essayer de décoder JSON si c'est le format utilisé
        try:
            data = json.loads(payload)
            logger.info(f"[MQTT->Kafka] Message reçu sur {topic}: {data}")
        except json.JSONDecodeError:
            # Si ce n'est pas du JSON, utiliser le message brut
            data = payload
            logger.info(f"[MQTT->Kafka] Message brut reçu sur {topic}: {payload}")
        
        # Adapter le format pour Kafka
        kafka_message = {
            "topic": topic,
            "value": data
        }
        
        # Envoyer à Kafka
        userdata['producer'].send(KAFKA_TOPIC, kafka_message)
        userdata['producer'].flush()
        logger.info(f"[MQTT->Kafka] Message envoyé à Kafka: {kafka_message}")
    except Exception as e:
        logger.error(f"Erreur lors du traitement du message: {str(e)}")

def main():
    # Attendre un peu que les services démarrent
    logger.info("Démarrage du bridge MQTT-Kafka")
    time.sleep(10)
    
    # Attendre que Kafka soit disponible
    if not wait_for_kafka():
        sys.exit(1)
    
    # Attendre que MQTT soit disponible
    if not wait_for_mqtt():
        sys.exit(1)
    
    # Créer le producteur Kafka
    producer = None
    retry_count = 0
    
    while producer is None and retry_count < MAX_RETRY_ATTEMPTS:
        producer = create_kafka_producer()
        if producer is None:
            retry_count += 1
            logger.warning(f"Échec de création du producteur Kafka. Nouvelle tentative {retry_count}/{MAX_RETRY_ATTEMPTS}...")
            time.sleep(RETRY_INTERVAL)
    
    if producer is None:
        logger.error("Impossible de créer le producteur Kafka après plusieurs tentatives. Arrêt du programme.")
        sys.exit(1)
    
    # Configurer le client MQTT
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.user_data_set({'producer': producer})
    
    # Connecter au broker MQTT
    try:
        logger.info(f"Connexion au broker MQTT {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        logger.info("Connexion au broker MQTT réussie")
    except Exception as e:
        logger.error(f"Erreur de connexion au broker MQTT: {str(e)}")
        sys.exit(1)
    
    # Démarrer la boucle
    try:
        client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Arrêt du bridge MQTT-Kafka")
    except Exception as e:
        logger.error(f"Erreur dans la boucle principale: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
