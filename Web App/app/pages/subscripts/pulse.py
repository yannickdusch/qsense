#########################################
#  QSense | pulse.py
#########################################
#
# Ce fichier permet la communication et la gestion interne du pulse
# On peut connecter/déconnecter le PulseBlaster, ajouter et programmer des séquences, et contrôler leur exécution
#

from .spinapi import *

class Pulse():
    
    # Connexion et initialisation
    def __init__(self):
        pb_select_board(0)
        self.status = pb_init()

    # Réglage de la fréquence d'horloge, instructions par défaut
    def initialize(self,clock_freq):
        self.clock_freq = clock_freq
        self.inst = [
            [0xFFFFFF, Inst.CONTINUE, 0, 200.0 * ms],
            [0x000000, Inst.CONTINUE, 0, 200.0 * ms]
        ]
        pb_core_clock(clock_freq)

    # Ajout d'une séquence simple (Inst.CONTINUE) en fonction des bits hauts et de la durée
    def add_sequence(self, hex, delay, delay_unit):
        self.inst.append([hex, Inst.CONTINUE, 0, delay * eval(delay_unit)])

    # Permet d'afficher la dernière erreur rencontrée
    def get_error(self):
        return pb_get_error()

    # Permet de programmer dans le pulse les instructions stockés dans self.inst
    def program(self, loop_to_start=True):

        pb_start_programming(PULSE_PROGRAM)
        # On gère séparément l'instruction de dépat pour la sauvegarder dans start (pour pouvoir faire le lien dans le cas où loop_to_start est activé)
        start_inst = self.inst[0]
        start = pb_inst_pbonly(start_inst[0], start_inst[1], start_inst[2], start_inst[3])

        # Pour toutes les autres instructions sauf la dernière, on récupère les arguments que l'on envoie au pulse
        for i in range(1, len(self.inst)-1):
            instruction = self.inst[i]
            pb_inst_pbonly(instruction[0], instruction[1], instruction[2], instruction[3])

        # On traite la dernière séparément :
        # Si loop_to_start n'est pas actif, rien ne change, mais s'il est actif, le type d'instruction est maintenant Inst.BRANCH, et l'on redirige vers start
        last_inst = self.inst[-1]
        if loop_to_start:
            last_inst[1] = Inst.BRANCH
            last_inst[2] = start
        pb_inst_pbonly(last_inst[0], last_inst[1], last_inst[2], last_inst[3])
        pb_stop_programming()

    # Permet de remettre à zéro l'exécution (seulement si elle a déjà été stoppée
    def reset(self):
        self.status = pb_reset()
        return self.status

    # Permet de démarrer/reprendre l'exécution
    def start(self):
        self.status = pb_start()
        return self.status

    # Permet d'arrêter/mettre en pause l'exécution
    def stop(self):
        self.status = pb_stop()
        return self.status

    # Permet de fermer la connexion au pulse
    def close(self):
        self.status = pb_close()
        return self.status