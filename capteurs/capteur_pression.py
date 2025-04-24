import paho.mqtt.client as mqtt
import time
import random
import json
import math
import numpy as np
from datetime import datetime

# Configuration du client MQTT
TOPIC = "capteurs/pression"

CLIENT_ID = "capteur_pression"

class CapteurPression:
    def __init__(self, broker_host="localhost", broker_port=1883):
        self.client = mqtt.Client(CLIENT_ID)
        self.client.connect(broker_host, broker_port, 60)
        
        # Paramètres réels d'un réacteur de raffinerie
        self.min_pression_normale = 15.0  # bar (pression minimale en fonctionnement normal)
        self.max_pression_normale = 25.0  # bar (pression maximale en fonctionnement normal)
        self.pression_critique = 32.0     # bar (pression critique)
        self.pression_minimale_alerte = 10.0  # bar (pression minimale avant alerte)
        
        # État du réacteur (partagé avec le capteur de température)
        self.etat_reacteur = "normal"  # "normal", "démarrage", "arrêt", "surcharge", "maintenance"
        self.duree_etat = 0
        self.max_duree_etat = random.randint(30, 120)  # Durée max d'un état (nombre de cycles)
        
        # État du capteur lui-même
        self.etat_capteur = "normal"  # "normal", "dérive", "défaillant", "bloqué"
        self.precision = 0.98  # 98% de précision
        self.drift_factor = 0  # Facteur de dérive du capteur
        self.last_pression = 20.0  # Pression initiale
        
        # Paramètres pour simuler l'état des conduites
        self.etat_conduites = "normal"  # "normal", "fuites_mineures", "fuite_importante", "obstruction"
        self.severite_probleme = 0.0  # Sévérité du problème (0.0 à 1.0)
        
        # Paramètres pour simuler la charge du réacteur
        self.charge_reacteur = 0.8  # 80% de charge
        self.tendance = 0.0  # Tendance de pression (augmente ou diminue)
        
        # Paramètres pour les événements aléatoires
        self.proba_evenement = 0.01  # 1% de chance d'avoir un événement spécial
        
        # Horodatage du dernier entretien du capteur
        self.dernier_entretien = time.time() - random.randint(0, 60*60*24*60)  # Entre maintenant et 60 jours dans le passé
        
        # Relations avec d'autres capteurs (température)
        self.derniere_temperature = 800.0  # Température par défaut
        
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
        # Vérifier si le capteur a besoin d'entretien
        temps_depuis_entretien = time.time() - self.dernier_entretien
        
        # La probabilité de dérive augmente avec le temps depuis le dernier entretien
        if temps_depuis_entretien > 60*60*24*90:  # 90 jours
            if random.random() < 0.05:  # 5% de chance
                self.etat_capteur = "dérive"
                self.drift_factor = random.uniform(-0.15, 0.15)  # Dérive entre -15% et +15%
        
        # Possibilité d'un capteur bloqué (plus fréquent pour les capteurs de pression)
        if temps_depuis_entretien > 60*60*24*120 and random.random() < 0.02:  # 2% de chance après 120 jours
            self.etat_capteur = "bloqué"
            
        # Possibilité de défaillance aléatoire
        if random.random() < 0.0005:  # 0.05% de chance
            self.etat_capteur = "défaillant"
        
        # Possibilité de récupération d'un capteur
        if (self.etat_capteur == "défaillant" or self.etat_capteur == "bloqué") and random.random() < 0.02:  # 2% de chance
            self.etat_capteur = "normal"
            self.drift_factor = 0
    
    def simuler_etat_conduites(self):
        """Simule l'état des conduites qui peut affecter la pression"""
        # Probabilité de changement d'état des conduites
        if random.random() < 0.005:  # 0.5% de chance de changement
            etats_possibles = [
                "normal",           # 70% de chance
                "fuites_mineures",  # 20% de chance
                "fuite_importante", # 5% de chance
                "obstruction"       # 5% de chance
            ]
            probas = [0.7, 0.2, 0.05, 0.05]
            
            nouvel_etat = random.choices(etats_possibles, weights=probas, k=1)[0]
            
            # Si l'état change, réinitialiser la sévérité
            if nouvel_etat != self.etat_conduites:
                self.etat_conduites = nouvel_etat
                
                # Définir la sévérité en fonction de l'état
                if self.etat_conduites == "normal":
                    self.severite_probleme = 0.0
                elif self.etat_conduites == "fuites_mineures":
                    self.severite_probleme = random.uniform(0.1, 0.3)
                elif self.etat_conduites == "fuite_importante":
                    self.severite_probleme = random.uniform(0.4, 0.8)
                elif self.etat_conduites == "obstruction":
                    self.severite_probleme = random.uniform(0.2, 0.6)
        
        # Faire évoluer la sévérité avec le temps
        if self.etat_conduites != "normal":
            # Pour les fuites, la sévérité augmente avec le temps
            if "fuite" in self.etat_conduites:
                self.severite_probleme = min(1.0, self.severite_probleme + random.uniform(0, 0.02))
            # Pour les obstructions, la sévérité peut fluctuer
            elif self.etat_conduites == "obstruction":
                self.severite_probleme = max(0.1, min(1.0, self.severite_probleme + random.uniform(-0.01, 0.03)))
    
    def simuler_evenements(self):
        """Simule des événements rares qui peuvent affecter la pression"""
        if random.random() < self.proba_evenement:
            evenements = [
                "vanne_defectueuse",      # Vanne ne régulant pas correctement
                "fluctuation_debit",       # Fluctuation soudaine du débit
                "coup_de_belier",         # Coup de bélier hydraulique
                "surpression_ponctuelle"  # Surpression ponctuelle
            ]
            
            return random.choice(evenements)
        return None
        
    def lire_pression(self):
        """Simule la lecture de pression du réacteur de manière réaliste"""
        # Simuler l'évolution des conditions du réacteur
        self.simuler_conditions_reacteur()
        
        # Simuler l'état du capteur
        self.simuler_etat_capteur()
        
        # Simuler l'état des conduites
        self.simuler_etat_conduites()
        
        # Générer un événement aléatoire
        evenement = self.simuler_evenements()
        
        # Calculer la pression de base en fonction de l'état du réacteur
        if self.etat_reacteur == "normal":
            pression_base = self.min_pression_normale + (self.max_pression_normale - self.min_pression_normale) * self.charge_reacteur
        elif self.etat_reacteur == "démarrage":
            # Pression croissante pendant le démarrage
            progress = min(1.0, self.duree_etat / 15)  # 15 cycles pour atteindre la pression normale
            pression_base = 5 + (self.min_pression_normale - 5) * progress
        elif self.etat_reacteur == "arrêt":
            # Pression décroissante pendant l'arrêt
            progress = min(1.0, self.duree_etat / 10)  # 10 cycles pour dépressuriser
            pression_base = self.min_pression_normale - (self.min_pression_normale - 5) * progress
        elif self.etat_reacteur == "surcharge":
            # Pression plus élevée en surcharge
            pression_base = self.max_pression_normale + (self.pression_critique - self.max_pression_normale) * (self.charge_reacteur - 0.9) * 10
        elif self.etat_reacteur == "maintenance":
            # Pression minimale pendant la maintenance
            pression_base = random.uniform(1, 5)
        
        # Ajouter une variation aléatoire (bruit)
        bruit = np.random.normal(0, 0.3)  # Distribution normale avec écart-type de 0.3 bar
        
        # Ajouter l'effet de la tendance
        self.tendance = self.tendance * 0.9 + random.uniform(-0.2, 0.2) * 0.1
        effet_tendance = self.tendance * 2  # Amplifier l'effet de la tendance
        
        # Ajouter l'effet de l'état des conduites
        effet_conduites = 0
        if self.etat_conduites == "fuites_mineures":
            # Les fuites mineures diminuent légèrement la pression
            effet_conduites = -1 * self.severite_probleme * 3
        elif self.etat_conduites == "fuite_importante":
            # Les fuites importantes diminuent fortement la pression
            effet_conduites = -1 * self.severite_probleme * 10
        elif self.etat_conduites == "obstruction":
            # Les obstructions augmentent la pression en amont
            effet_conduites = self.severite_probleme * 8
        
        # Ajouter l'effet des événements
        effet_evenement = 0
        if evenement:
            if evenement == "vanne_defectueuse":
                effet_evenement = random.uniform(-5, 5)
            elif evenement == "fluctuation_debit":
                effet_evenement = random.uniform(-3, 3)
            elif evenement == "coup_de_belier":
                effet_evenement = random.uniform(4, 8)
            elif evenement == "surpression_ponctuelle":
                effet_evenement = random.uniform(6, 12)
        
        # Calculer la pression réelle
        pression_reelle = pression_base + bruit + effet_tendance + effet_conduites + effet_evenement
        
        # Empêcher les valeurs négatives
        pression_reelle = max(0, pression_reelle)
        
        # Simuler la lecture du capteur en fonction de son état
        if self.etat_capteur == "normal":
            # Capteur précis avec une petite erreur
            lecture = pression_reelle * random.uniform(0.99, 1.01)
        elif self.etat_capteur == "dérive":
            # Capteur qui dérive progressivement
            lecture = pression_reelle * (1 + self.drift_factor)
        elif self.etat_capteur == "bloqué":
            # Capteur bloqué sur une valeur
            lecture = self.last_pression
        elif self.etat_capteur == "défaillant":
            # Capteur défaillant donnant des valeurs aberrantes
            lecture = random.choice([
                0,                      # Valeur nulle
                99.9,                   # Valeur maximale
                random.uniform(0, 50)   # Valeur aléatoire
            ])
        else:
            lecture = pression_reelle
        
        # Arrondir la pression et la stocker
        lecture_arrondie = round(lecture, 2)
        self.last_pression = lecture_arrondie
        
        return {
            "valeur": lecture_arrondie,
            "etat_reacteur": self.etat_reacteur,
            "etat_capteur": self.etat_capteur,
            "etat_conduites": self.etat_conduites,
            "evenement": evenement
        }
    
    def publier_donnees(self):
        donnees_capteur = self.lire_pression()
        pression = donnees_capteur["valeur"]
        
        donnees = {
            "capteur": "pression",
            "valeur": pression,
            "unite": "bar",
            "etat_reacteur": donnees_capteur["etat_reacteur"],
            "etat_capteur": donnees_capteur["etat_capteur"],
            "etat_conduites": donnees_capteur["etat_conduites"],
            "evenement": donnees_capteur["evenement"],
            "timestamp": time.time()
        }
        
        self.client.publish(TOPIC, json.dumps(donnees))
        print(f"Pression publiée: {pression} bar | État réacteur: {donnees_capteur['etat_reacteur']} | État capteur: {donnees_capteur['etat_capteur']} | Conduites: {donnees_capteur['etat_conduites']}")
        
        if donnees_capteur["evenement"]:
            print(f"⚠️ ÉVÉNEMENT: {donnees_capteur['evenement']}")
        
    def demarrer(self, intervalle=5):
        """Démarre la publication à intervalle régulier"""
        self.client.loop_start()
        try:
            while True:
                self.publier_donnees()
                time.sleep(intervalle)
        except KeyboardInterrupt:
            print("Arrêt du capteur de pression")
        except Exception as e:
            print(f"Erreur: {str(e)}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    capteur = CapteurPression()
    capteur.demarrer() 