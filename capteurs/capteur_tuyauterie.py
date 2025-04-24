import paho.mqtt.client as mqtt
import time
import random
import json

# Configuration du client MQTT
BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "capteurs/tuyauterie"

CLIENT_ID = "capteur_tuyauterie"

class CapteurTuyauterie:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.client = mqtt.Client(CLIENT_ID)
        self.client.connect(broker_host, broker_port, 60)
        self.min_pression = 0.5  # bar
        self.max_pression = 3.0  # bar
        self.etats_possibles = ["bon", "fuite_mineure", "fuite_majeure", "maintenance"]
        self.probabilites = [0.85, 0.10, 0.02, 0.03]  # probabilités correspondantes
        
    def lire_pression(self):
        """Simule la lecture de pression dans les tuyaux"""
        return round(random.uniform(self.min_pression, self.max_pression), 2)
    
    def detecter_etat(self):
        """Simule la détection de l'état des tuyaux"""
        return random.choices(self.etats_possibles, weights=self.probabilites, k=1)[0]
    
    def publier_donnees(self):
        pression = self.lire_pression()
        etat = self.detecter_etat()
        
        # Ajuster la pression selon l'état
        if etat == "fuite_mineure":
            pression *= 0.9
        elif etat == "fuite_majeure":
            pression *= 0.6
        
        donnees = {
            "capteur": "tuyauterie",
            "pression": pression,
            "etat": etat,
            "unite_pression": "bar",
            "timestamp": time.time()
        }
        self.client.publish(TOPIC, json.dumps(donnees))
        print(f"Tuyauterie - État: {etat}, Pression: {pression} bar")
        
    def demarrer(self, intervalle=5):
        """Démarre la publication à intervalle régulier"""
        self.client.loop_start()
        try:
            while True:
                self.publier_donnees()
                time.sleep(intervalle)
        except KeyboardInterrupt:
            print("Arrêt du capteur de tuyauterie")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    capteur = CapteurTuyauterie()
    capteur.demarrer() 