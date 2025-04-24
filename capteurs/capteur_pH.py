import paho.mqtt.client as mqtt
import time
import random
import json
from datetime import datetime

# Configuration du client MQTT
BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "capteurs/pH"
CLIENT_ID = "capteur_pH"

# États possibles du capteur
ETATS = ["normal", "defaillant", "instable"]

class CapteurPH:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.client = mqtt.Client(CLIENT_ID)
        self.client.connect(broker_host, broker_port, 60)
        self.etat = "normal"

    def simuler_etat(self):
        """Choisit un état de fonctionnement aléatoire avec pondération"""
        self.etat = random.choices(ETATS, weights=[0.8, 0.1, 0.1])[0]

    def lire_pH(self):
        """Génère des valeurs en fonction de l'état simulé du capteur"""
        if self.etat == "normal":
            return round(random.uniform(6.5, 7.5), 2)
        elif self.etat == "defaillant":
            return round(random.uniform(0.0, 3.0), 2) if random.random() < 0.5 else None
        elif self.etat == "instable":
            return round(random.uniform(5.0, 9.0), 2)

    def publier_donnees(self):
        self.simuler_etat()
        pH = self.lire_pH()
        
        if pH is None:
            print("Défaillance du capteur pH - Aucune donnée envoyée")
            return

        donnees = {
            "capteur": "pH",
            "valeur": pH,
            "unite": "pH",
            "etat": self.etat,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.client.publish(TOPIC, json.dumps(donnees))
        print(f"pH publié: {donnees}")

    def demarrer(self, intervalle=5):
        self.client.loop_start()
        try:
            while True:
                self.publier_donnees()
                time.sleep(intervalle)
        except KeyboardInterrupt:
            print("Arrêt manuel du capteur pH")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    capteur = CapteurPH()
    capteur.demarrer()
