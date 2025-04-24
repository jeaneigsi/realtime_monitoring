import paho.mqtt.client as mqtt
import time
import random
import json

# Configuration du client MQTT
BROKER_HOST = "localhost"
BROKER_PORT = 1883
TOPIC = "capteurs/pompe"
CLIENT_ID = "capteur_pompe"

class CapteurPompe:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.client = mqtt.Client(CLIENT_ID)
        self.client.connect(broker_host, broker_port, 60)

        self.min_debit = 50.0  # L/min
        self.max_debit = 150.0  # L/min
        self.etats = ["actif", "inactif", "maintenance", "defaillant"]
        self.etat_actuel = "actif"

        self.en_defaillance = False
        self.derniere_defaillance = 0
        self.temps_defaillance = 30  # durée de la panne en secondes
        self.proba_defaillance = 0.02  # 2% de chance à chaque itération

    def simuler_defaillance(self):
        """Déclenche une panne avec une certaine probabilité"""
        if not self.en_defaillance and random.random() < self.proba_defaillance:
            self.en_defaillance = True
            self.derniere_defaillance = time.time()
            self.etat_actuel = "defaillant"
            print("[ALERTE] Pompe en panne simulée !")

        if self.en_defaillance and (time.time() - self.derniere_defaillance) > self.temps_defaillance:
            self.en_defaillance = False
            self.etat_actuel = "maintenance"
            print("[INFO] Fin de panne, passage en maintenance.")

    def lire_debit(self):
        """Simule la lecture du débit en fonction de l'état"""
        if self.etat_actuel == "inactif":
            return 0.0
        elif self.etat_actuel == "maintenance":
            return round(random.uniform(0, 30.0), 2)
        elif self.etat_actuel == "defaillant":
            # Débit incohérent ou chute brutale
            return round(random.uniform(-10.0, 10.0), 2)
        else:
            return round(random.uniform(self.min_debit, self.max_debit), 2)

    def lire_etat(self):
        """Gère le changement d'état et simule des défaillances"""
        self.simuler_defaillance()
        if not self.en_defaillance and random.random() < 0.03:  # 3% de chance de changer d’état normal
            self.etat_actuel = random.choice(["actif", "inactif", "maintenance"])
        return self.etat_actuel

    def publier_donnees(self):
        etat = self.lire_etat()
        debit = self.lire_debit()
        donnees = {
            "capteur": "pompe",
            "etat": etat,
            "debit": debit,
            "unite_debit": "L/min",
            "timestamp": time.time()
        }
        self.client.publish(TOPIC, json.dumps(donnees))
        print(f"Pompe - État: {etat}, Débit: {debit} L/min")

    def demarrer(self, intervalle=5):
        """Démarre la publication à intervalle régulier"""
        self.client.loop_start()
        try:
            while True:
                self.publier_donnees()
                time.sleep(intervalle)
        except KeyboardInterrupt:
            print("Arrêt du capteur de pompe")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    capteur = CapteurPompe()
    capteur.demarrer()
