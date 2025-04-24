import threading
import time
import os
import sys
import logging
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("capteurs.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("simulateur_capteurs")

# Import des classes de capteurs
from capteur_temperature import CapteurTemperature
from capteur_pression import CapteurPression
from capteur_pH import CapteurPH
from capteur_pompe import CapteurPompe
from capteur_tuyauterie import CapteurTuyauterie
from capteur_torchere import CapteurTorchere

def demarrer_capteur(capteur, nom_capteur, intervalle):
    """Fonction pour démarrer un capteur dans un thread séparé"""
    logger.info(f"Démarrage du capteur {nom_capteur}")
    try:
        capteur.demarrer(intervalle)
    except Exception as e:
        logger.error(f"Erreur dans le capteur {nom_capteur}: {str(e)}")

def main():
    """Fonction principale qui démarre tous les capteurs"""
    logger.info("Démarrage du simulateur de capteurs pour raffinerie")

    # Attente pour s'assurer que le broker MQTT est prêt
    broker_host = os.getenv("MQTT_BROKER_HOST", "localhost")
    broker_port = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    
    logger.info(f"Configuration du broker MQTT: {broker_host}:{broker_port}")
    logger.info("Attente de 5 secondes pour laisser le broker MQTT démarrer...")
    time.sleep(5)

    # Intervalle de publication (en secondes)
    intervalle = int(os.getenv("INTERVAL", "5"))
    
    # Création des instances de capteurs
    capteur_temperature = CapteurTemperature(broker_host, broker_port)
    capteur_pression = CapteurPression(broker_host, broker_port)
    capteur_ph = CapteurPH(broker_host, broker_port)
    capteur_pompe = CapteurPompe(broker_host, broker_port)
    capteur_tuyauterie = CapteurTuyauterie(broker_host, broker_port)
    capteur_torchere = CapteurTorchere(broker_host, broker_port)
    
    # Création des threads pour chaque capteur
    threads = [
        threading.Thread(target=demarrer_capteur, args=(capteur_temperature, "température", intervalle)),
        threading.Thread(target=demarrer_capteur, args=(capteur_pression, "pression", intervalle)),
        threading.Thread(target=demarrer_capteur, args=(capteur_ph, "pH", intervalle)),
        threading.Thread(target=demarrer_capteur, args=(capteur_pompe, "pompe", intervalle)),
        threading.Thread(target=demarrer_capteur, args=(capteur_tuyauterie, "tuyauterie", intervalle)),
        threading.Thread(target=demarrer_capteur, args=(capteur_torchere, "torchère", intervalle))
    ]
    
    # Démarrage des threads
    for thread in threads:
        thread.daemon = True
        thread.start()
    
    logger.info(f"Tous les capteurs démarrés avec un intervalle de {intervalle} secondes")
    
    # Garder le programme principal en vie
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Arrêt du simulateur demandé par l'utilisateur")

if __name__ == "__main__":
    main() 