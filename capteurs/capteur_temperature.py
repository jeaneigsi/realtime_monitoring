import paho.mqtt.client as mqtt
import time
import random
import json
import math
import numpy as np
from datetime import datetime
import logging
import os

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('capteur_temperature')

# Configuration du client MQTT
TOPIC = "capteurs/temperature"
CLIENT_ID = "capteur_temperature"

class CapteurTemperature:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        
        # Configuration du client MQTT avec reconnexion automatique
        self.client = mqtt.Client(CLIENT_ID)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        
        # Connexion au broker MQTT
        self.connect_mqtt()
        
        # Paramètres réels pour un réacteur de raffinerie
        self.min_temp_normale = 700.0  # °C (température minimale en fonctionnement normal)
        self.max_temp_normale = 950.0  # °C (température maximale en fonctionnement normal)
        self.temp_critique = 1050.0    # °C (température critique)
        
        # État du réacteur (pour simuler les variations de charge)
        self.etat_reacteur = "normal"  # "normal", "démarrage", "arrêt", "surcharge", "maintenance"
        self.duree_etat = 0
        self.max_duree_etat = random.randint(30, 120)  # Durée max d'un état (nombre de cycles)
        
        # État du capteur lui-même
        self.etat_capteur = "normal"  # "normal", "dérive", "défaillant"
        self.precision = 0.98  # 98% de précision
        self.drift_factor = 0  # Facteur de dérive du capteur
        self.last_temp = 800.0  # Température initiale
        
        # Paramètres pour simuler la charge du réacteur
        self.charge_reacteur = 0.8  # 80% de charge
        self.tendance = 0.0  # Tendance de température (augmente ou diminue)
        
        # Paramètres pour les événements aléatoires
        self.proba_evenement = 0.01  # 1% de chance d'avoir un événement spécial
        
        # Horodatage du dernier entretien du capteur
        self.dernier_entretien = time.time() - random.randint(0, 60*60*24*30)  # Entre maintenant et 30 jours dans le passé
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Connecté au broker MQTT: {self.broker_host}:{self.broker_port}")
        else:
            logger.error(f"Échec de connexion au broker MQTT avec code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        logger.warning(f"Déconnecté du broker MQTT avec code {rc}")
        # Tentative de reconnexion
        time.sleep(5)
        self.connect_mqtt()
    
    def connect_mqtt(self):
        try:
            logger.info(f"Tentative de connexion au broker MQTT: {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Erreur de connexion au broker MQTT: {str(e)}")

    def simuler_conditions_reacteur(self):
        """Simule les changements d'état du réacteur"""
        self.duree_etat += 1
        
        # Changement d'état possible après la durée maximale
        if self.duree_etat >= self.max_duree_etat:
            etats_possibles = ["normal", "démarrage", "arrêt", "surcharge"]
            
            # Ajouter une possibilité de maintenance, mais avec une faible probabilité
            if random.random() < 0.05:  # 5% de chance
                etats_possibles.append("maintenance")
                
            self.etat_reacteur = random.choice(etats_possibles)
            self.duree_etat = 0
            self.max_duree_etat = random.randint(30, 120)
            
            # Ajuster la charge en fonction de l'état
            if self.etat_reacteur == "normal":
                self.charge_reacteur = random.uniform(0.7, 0.9)
            elif self.etat_reacteur == "démarrage":
                self.charge_reacteur = random.uniform(0.3, 0.6)
            elif self.etat_reacteur == "arrêt":
                self.charge_reacteur = random.uniform(0.1, 0.4)
            elif self.etat_reacteur == "surcharge":
                self.charge_reacteur = random.uniform(0.9, 1.0)
            elif self.etat_reacteur == "maintenance":
                self.charge_reacteur = random.uniform(0.0, 0.2)
    
    def simuler_etat_capteur(self):
        """Simule l'état du capteur (dérive, défaillance, etc.)"""
        # Vérifier si le capteur a besoin d'entretien (après 6 mois)
        temps_depuis_entretien = time.time() - self.dernier_entretien
        
        # La probabilité de dérive augmente avec le temps depuis le dernier entretien
        if temps_depuis_entretien > 60*60*24*180:  # 180 jours
            if random.random() < 0.1:  # 10% de chance
                self.etat_capteur = "dérive"
                self.drift_factor = random.uniform(-0.1, 0.2)  # Dérive entre -10% et +20%
        
        # Possibilité de défaillance aléatoire
        if random.random() < 0.001:  # 0.1% de chance
            self.etat_capteur = "défaillant"
        
        # Possibilité de récupération d'un capteur défaillant (après reboot)
        if self.etat_capteur == "défaillant" and random.random() < 0.05:  # 5% de chance
            self.etat_capteur = "normal"
            self.drift_factor = 0
    
    def simuler_evenements(self):
        """Simule des événements rares qui peuvent affecter la température"""
        if random.random() < self.proba_evenement:
            evenements = [
                "défaut_refroidissement",  # Problème de refroidissement
                "baisse_catalyseur",       # Baisse d'efficacité du catalyseur
                "contamination",          # Contamination des matières premières
                "surchauffe_ponctuelle"   # Surchauffe ponctuelle
            ]
            
            return random.choice(evenements)
        return None
        
    def lire_temperature(self):
        """Simule la lecture de température du réacteur de manière réaliste"""
        # Simuler l'évolution des conditions du réacteur
        self.simuler_conditions_reacteur()
        
        # Simuler l'état du capteur
        self.simuler_etat_capteur()
        
        # Générer un événement aléatoire
        evenement = self.simuler_evenements()
        
        # Calculer la température de base en fonction de l'état du réacteur
        if self.etat_reacteur == "normal":
            temp_base = self.min_temp_normale + (self.max_temp_normale - self.min_temp_normale) * self.charge_reacteur
        elif self.etat_reacteur == "démarrage":
            # Température croissante pendant le démarrage
            progress = min(1.0, self.duree_etat / 20)  # 20 cycles pour atteindre la température normale
            temp_base = 100 + (self.min_temp_normale - 100) * progress
        elif self.etat_reacteur == "arrêt":
            # Température décroissante pendant l'arrêt
            progress = min(1.0, self.duree_etat / 15)  # 15 cycles pour refroidir
            temp_base = self.min_temp_normale - (self.min_temp_normale - 100) * progress
        elif self.etat_reacteur == "surcharge":
            # Température plus élevée en surcharge
            temp_base = self.max_temp_normale + (self.temp_critique - self.max_temp_normale) * (self.charge_reacteur - 0.9) * 10
        elif self.etat_reacteur == "maintenance":
            # Température ambiante pendant la maintenance
            temp_base = 40 + random.uniform(-10, 20)
        
        # Ajouter une variation aléatoire (bruit)
        bruit = np.random.normal(0, 5)  # Distribution normale avec écart-type de 5°C
        
        # Ajouter l'effet de la tendance
        self.tendance = self.tendance * 0.9 + random.uniform(-0.5, 0.5) * 0.1
        effet_tendance = self.tendance * 10  # Amplifier l'effet de la tendance
        
        # Ajouter l'effet des événements
        effet_evenement = 0
        if evenement:
            if evenement == "défaut_refroidissement":
                effet_evenement = random.uniform(20, 50)
            elif evenement == "baisse_catalyseur":
                effet_evenement = random.uniform(-30, -10)
            elif evenement == "contamination":
                effet_evenement = random.uniform(-20, 40)
            elif evenement == "surchauffe_ponctuelle":
                effet_evenement = random.uniform(40, 80)
        
        # Calculer la température réelle
        temperature_reelle = temp_base + bruit + effet_tendance + effet_evenement
        
        # Simuler la lecture du capteur en fonction de son état
        if self.etat_capteur == "normal":
            # Capteur précis avec une petite erreur
            lecture = temperature_reelle * random.uniform(0.99, 1.01)
        elif self.etat_capteur == "dérive":
            # Capteur qui dérive progressivement
            lecture = temperature_reelle * (1 + self.drift_factor)
        elif self.etat_capteur == "défaillant":
            # Capteur défaillant donnant des valeurs aberrantes
            lecture = random.choice([
                0,                      # Valeur nulle
                9999,                   # Valeur maximale
                self.last_temp,         # Valeur bloquée
                random.uniform(100, 1500)  # Valeur aléatoire
            ])
        else:
            lecture = temperature_reelle
        
        # Arrondir la température et la stocker
        lecture_arrondie = round(lecture, 2)
        self.last_temp = lecture_arrondie
        
        return {
            "valeur": lecture_arrondie,
            "etat_reacteur": self.etat_reacteur,
            "etat_capteur": self.etat_capteur,
            "evenement": evenement
        }
    
    def publier_donnees(self):
        try:
            donnees_capteur = self.lire_temperature()
            temperature = donnees_capteur["valeur"]
            
            # Formatage JSON conforme à ce qu'attend Flink
            donnees = {
                "capteur": "temperature",  # Utiliser "temperature" sans accent
                "valeur": temperature,
                "unite": "C",
                "etat_reacteur": donnees_capteur["etat_reacteur"],
                "etat_capteur": donnees_capteur["etat_capteur"],
                "evenement": donnees_capteur["evenement"],
                "timestamp": time.time()
            }
            
            # Conversion en JSON et publication
            message_json = json.dumps(donnees)
            result = self.client.publish(TOPIC, message_json)
            
            # Vérification de la publication
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Température publiée: {temperature}°C | État réacteur: {donnees_capteur['etat_reacteur']} | État capteur: {donnees_capteur['etat_capteur']}")
                if donnees_capteur["evenement"]:
                    logger.warning(f"⚠️ ÉVÉNEMENT: {donnees_capteur['evenement']}")
            else:
                logger.error(f"Échec de publication MQTT: {result.rc}")
        except Exception as e:
            logger.error(f"Erreur lors de la publication: {str(e)}")
        
    def demarrer(self, intervalle=5):
        """Démarre la publication à intervalle régulier"""
        logger.info(f"Démarrage du capteur de température avec intervalle de {intervalle}s")
        try:
            while True:
                self.publier_donnees()
                time.sleep(intervalle)
        except KeyboardInterrupt:
            logger.info("Arrêt du capteur de température")
        except Exception as e:
            logger.error(f"Erreur: {str(e)}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    # Récupération des paramètres d'environnement
    broker_host = os.getenv("MQTT_BROKER_HOST", "localhost")
    broker_port = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    intervalle = int(os.getenv("INTERVAL", "5"))
    
    logger.info(f"Configuration: broker={broker_host}:{broker_port}, intervalle={intervalle}s")
    
    capteur = CapteurTemperature(broker_host, broker_port)
    capteur.demarrer(intervalle) 