#########################################
#  QSense | pico.py
#########################################
#
# Ce fichier permet la communication et la gestion interne du picoscope
# On peut connecter/déconnecter le picoscope, l'initialiser avec des valeurs par défaut, reconfigurer le générateur de signal
# et l'échantillonage, et lancer la récupération d'un échantillon
#

import numpy as np
from picoscope.ps5000a import PS5000a # https://github.com/colinoflynn/pico-python/blob/master/picoscope/picobase.py
from math import ceil

class Picoscope(object):

	def __init__(self,serialNumber="GQ915/0061".encode()):
		self.serialNumber = serialNumber
		self.ps = PS5000a() # Etablissement de la connexion au Picoscope

	# Initialisation du picoscope et setup des paramètres par défaut
	def initialize(self):
		# Valeurs par défaut (channel A activé, DC +-20V)
		self.channels = {'A': 1, 'B': 0, 'C': 0, 'D' :0}
		self.couplings = {'A': "DC", 'B': "DC", 'C': "DC", 'D' :"DC"}
		self.ranges = {'A': 20, 'B': 20, 'C': 20, 'D' :20}
		self.offsets = {'A': 0, 'B': 0, 'C': 0, 'D' :0}

		self.ps.setResolution("12") # Compromis entre très bonne précision (résolution 16) et la possibilité d'avoir 4 channels simultanément

		self.sample_duration = 1e-3 # Acquisition d'1 ms par défaut
		self.nosamples = 1000 #1000 échantillons par défaut

		self.update_channels() # Setup des channels et de l'échantillonage via la library

		# Valeurs par défaut / caractéristiques du générateur interne
		self.max_gen_output = 2 
		self.type_signal = "None"
		self.amp_signal = 0
		self.offset_signal = 0
		self.freq_signal = 1

	# Reconfigure le générateur de signal interne avec la lib selon les paramètres définis dans self
	def set_signal(self):
		self.ps.setSigGenBuiltInSimple(
			offsetVoltage=self.offset_signal,
		    pkToPk=self.amp_signal,
			waveType=self.type_signal,
            frequency=self.freq_signal,
            shots=0, 
			numSweeps=0)

	# Reconfigure le générateur de signal interne pour un signal constant à 0 V (i.e. pour le désactiver)
	def remove_signal(self):
		self.ps.setSigGenBuiltInSimple(offsetVoltage=0, pkToPk=0, waveType="DCVoltage",
            frequency=1,
            shots=0, 
			numSweeps=0)

	# Met à jour les channels selon les paramètres stockés dans self
	def update_channels(self):
		self.ps.setChannel('A', self.couplings['A'], self.ranges['A'], self.offsets['A'], self.channels['A'], "20MHZ")
		self.ps.setChannel('B', self.couplings['B'], self.ranges['B'], self.offsets['B'], self.channels['B'], "20MHZ")
		self.ps.setChannel('C', self.couplings['C'], self.ranges['C'], self.offsets['C'], self.channels['C'], "20MHZ")
		self.ps.setChannel('D', self.couplings['D'], self.ranges['D'], self.offsets['D'], self.channels['D'], "20MHZ")

		self.update_sampling() # On setup à nouveau l'échantillonage
		
	# Met à jour les paramètres d'échantillonnage 
	def update_sampling(self):
		temp_sample_interval = self.sample_duration/self.nosamples # Intervalle de temps voulu, selon les paramètres fournis
		temp_timebase = int(ceil((temp_sample_interval * 62500000) + 3)) # On récupère le timebase le plus proche selon la formule de la doc (en mode résolution 12)
		self.sample_interval = self.ps.getTimestepFromTimebase(temp_timebase) # On récupère l'intervalle exact correspondant avec la lib
		self.sample_interval, self.nosamples,_ = self.ps.setSamplingInterval(self.sample_interval, self.sample_duration) # On setup l'échantillonage, et on récupère le nombre d'échantillons exact
	
	def set_trigger(self,channel, threshold, direction, delay=0,timeout=100, active=True):
		self.ps.setSimpleTrigger(channel, threshold, direction, delay, timeout, active)
		

	# Récupération d'un block de données, en supposant que l'initialisation et le setup aient été faits
	def get_data_block(self):
		for channel in ['A', 'B', 'C', 'D']:
			if self.channels[channel]:
				self.set_trigger(channel, 0.1*self.ranges[channel], 'Rising') # On rajoute un trigger montant à 10% du range

		# On lance le block et on attends que le picoscope soit prêt à le renvoyer
		self.ps.runBlock()
		self.ps.waitReady()
		
		data = {'A':[[0],[0]],'B':[[0],[0]],'C':[[0],[0]],'D':[[0],[0]]}
		np_time = np.linspace(0, self.sample_duration, self.nosamples) # Création de l'axe temporel

		for channel in ['A', 'B', 'C', 'D']:
			if self.channels[channel]: # Si channel actif
				data[channel][1] = np.array(self.ps.getDataV(channel))
				data[channel][0] = np_time

		return data

# Test de fonctionnement du pico si ce fichier est lancé en main
if __name__ == "__main__":
	pico = Picoscope()
	pico.initialize()