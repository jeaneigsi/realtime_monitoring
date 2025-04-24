import paho.mqtt.client as mqtt
import time
import random
import json

# Configuration du client MQTT
BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "capteurs/torchere"

CLIENT_ID = "capteur_torchere"

class CapteurTorchere:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.client = mqtt.Client(CLIENT_ID)
        self.client.connect(broker_host, broker_port, 60)
        self.min_temperature = 500.0  # °C
        self.max_temperature = 1200.0  # °C
        self.etats = ["allumee", "eteinte", "demarrage", "arret"]
        self.etat_actuel = "allumee"
        self.changement_etat_timer = 0
        
    def lire_temperature(self):
        """Simule la lecture de température de la torchère"""
        if self.etat_actuel == "eteinte":
            return random.uniform(20, 50)
        elif self.etat_actuel == "demarrage":
            return random.uniform(100, 500)
        elif self.etat_actuel == "arret":
            return random.uniform(100, 800)
        else:  # allumée
            return round(random.uniform(self.min_temperature, self.max_temperature), 2)
    
    def gerer_etat(self):
        """Gère les transitions d'état"""
        self.changement_etat_timer += 1
        
        # Changement d'état toutes les 10-20 secondes en moyenne
        if self.changement_etat_timer >= random.randint(2, 4):
            if self.etat_actuel == "demarrage":
                self.etat_actuel = "allumee"
            elif self.etat_actuel == "arret":
                self.etat_actuel = "eteinte"
            elif random.random() < 0.1:  # 10% de chance de changer d'état
                if self.etat_actuel == "allumee":
                    self.etat_actuel = "arret"
                else:  # éteinte
                    self.etat_actuel = "demarrage"
            
            self.changement_etat_timer = 0
            
        return self.etat_actuel
    
    def lire_debit_gaz(self):
        """Simule la lecture du débit de gaz"""
        if self.etat_actuel == "eteinte":
            return 0.0
        elif self.etat_actuel == "demarrage":
            return random.uniform(5, 20)
        elif self.etat_actuel == "arret":
            return random.uniform(1, 10)
        else:  # allumée
            return round(random.uniform(15, 50), 2)
    
    def publier_donnees(self):
        etat = self.gerer_etat()
        temperature = self.lire_temperature()
        debit_gaz = self.lire_debit_gaz()
        
        donnees = {
            "capteur": "torchere",
            "etat": etat,
            "temperature": temperature,
            "unite_temperature": "C",
            "debit_gaz": debit_gaz,
            "unite_debit_gaz": "m3/h",
            "timestamp": time.time()
        }
        self.client.publish(TOPIC, json.dumps(donnees))
        print(f"Torchère - État: {etat}, Température: {temperature}°C, Débit: {debit_gaz} m3/h")
        
    def demarrer(self, intervalle=5):
        """Démarre la publication à intervalle régulier"""
        self.client.loop_start()
        try:
            while True:
                self.publier_donnees()
                time.sleep(intervalle)
        except KeyboardInterrupt:
            print("Arrêt du capteur de torchère")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    capteur = CapteurTorchere()
    capteur.demarrer() 