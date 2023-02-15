#########################################
#  QSense | pulse_ui.py
#########################################
#
# Ce fichier permet de contrôler le PulseBlasterUSB, de créer une séquence, l'exécuter, l'exporter/importer, ..
#

import datetime
import json
import os
from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from matplotlib import pyplot as plt
from nicegui import ui, app
from nicegui.events import UploadEventArguments

from ..utils import Error
from ..utils import enable
from ..utils import disable

from ..settings import get_setting
from ..theme import frame
from .login import is_authenticated

from .subscripts.pulse import Pulse

def create_pulse_ui():

    # Récupération des paramètres
    settings = get_setting('pulse')

    ##################
    # Création de l'UI
    ##################

    @ui.page('/pulse')
    def pico_ui_page(request: Request):

        if not is_authenticated(request):
            return RedirectResponse('/login')
        else:
            with frame('Contrôle PulseBlasterUSB', request):

                error = Error()

                #######################
                # Contrôle PulseBlaster
                #######################

                # Lors de la connexion du Pulse
                def connect_pulse():
                    if connect_button.enabled:
                        # Initialisation du Pulse
                        global pulse
                        pulse = Pulse()
                        if pulse.status != 0:
                            error.show_error("Impossible de se connecter au PulseBlaster", pulse.get_error())
                            return 
                        pulse.initialize(clock_freq=settings['pulse_core_freq'])
                        if pulse.status != 0:
                            error.show_error("Impossible d'initialiser le PulseBlaster", pulse.get_error())
                            return
                        
                        # Activation des éléments de l'UI
                        enable(control_card)
                        enable(start_button)
                        enable(reset_button)
                        
                        enable(disconnect_button)
                        disable(connect_button)
                
                # Lors de la déconnexion du pulse
                def disconnect_pulse():
                    if disconnect_button.enabled:
                        # On arrête le signal au cas où il serait exécuté
                        pulse.stop()
                        pulse.reset()
                        # Fermeture de la connexion au Pulse
                        pulse.close()

                        # Mise à jour des éléments de l'Ui
                        disable(control_card)
                        disable(start_button)
                        disable(reset_button)
                        disable(file_card)
                        disable(import_button)
                        disable(export_button)
                        pause_button.set_text("Pause")

                        enable(connect_button)
                        disable(disconnect_button)

                # Permet de lancer l'exécution des séquences configurées
                def start_pulse():
                    if start_button.enabled:
                        # Programmation des séquences dans le Pulse
                        upload_sequences()
                        # Exécution 
                        pulse.reset()
                        pulse.start()
                        if pulse.status != 0:
                            error.show_error("Impossible de lancer la séquence", pulse.get_error())
                            return
                        
                        # Mise à jour de l'UI : on peut seulement mettre en pause lors de l'exécution
                        disable(start_button)
                        enable(pause_button)
                        disable(file_card)
                        disable(import_button)
                        disable(export_button)

                # Permet de mettre en pause (stop sans reset) / reprendre l'exécution
                def pause_pulse():
                    if pause_button.enabled:
                        if pause_button.text == "Pause":
                            # Mise en pause
                            pulse.stop()
                            if pulse.status !=0:
                                error.show_error("Impossible de mettre en pause la séquence", pulse.get_error())
                                return
                            # Mise à jour de l'UI : le bouton reset n'est accessible qu'après avoir mis en pause
                            pause_button.set_text("Resume")
                            enable(reset_button)
                        else:
                            # Reprise
                            pulse.start()
                            if pulse.status != 0:
                                error.show_error("Impossible de reprendre la séquence", pulse.get_error())
                                return
                            pause_button.set_text("Pause")
                            disable(reset_button)
                
                # Réinitialisation de l'exécution
                def reset_pulse():
                    if reset_button.enabled:
                        pulse.reset()
                        if pulse.status != 0:
                            error.show_error("Impossible de remettre à zéro la séquence", pulse.get_error())
                            return
                        
                        # Mise à jour de l'UI : retour situation initiale, seulement bouton de start actif
                        enable(start_button)
                        disable(pause_button)
                        disable(reset_button)
                        enable(file_card)
                        enable(import_button)
                        enable(export_button)
                        pause_button.set_text("Pause")

                #########################
                # Importation/Exportation
                #########################

                # Importer un fichier de séquences
                def import_file(e:UploadEventArguments):
                    global sequences_list
                    global sequences_values
                    # On récupère le fichier uploadé via l'event d'upload
                    file = e.content.read()
                    try:
                        # On essaye de charger le fichier JSON en tant que dictionnaire python
                        dict_file = json.loads(file)
                    except json.JSONDecodeError as err:
                        error.show_error("Impossible d'importer le fichier", err)
                        import_popup.close
                    else:
                        # Mise à zéro des séquences actuelles
                        sequences_list = []
                        sequences_values = []
                        sequences.clear()

                        nb_sequences = len(dict_file) - 1

                        # Activation des bits : puisque la valeur par défaut dans le fichier JSON est "0" pour un bit non actif,
                        # et est modifié par True/False pour chaque séquence lorsque le bit est activé
                        # On vérifie donc le type (bool ou int) de chaque valeur des bits dans la première séquence pour savoir si un bit est actif
                        #  (on ne peut pas faire == 0 puisque 0 et False serait interprétés comme ayant la même valeur)
                        for i in range(24):
                            if isinstance(dict_file['0']['data'][str(i)], bool):
                                active_bits[i].set_value(True)
                    
                        # Création des séquences
                        for i in range(nb_sequences):
                            # Nouvelle séquence par défaut
                            add_sequence()
                            sequence = sequences_list[-1]

                            # Récupération des valeurs qui doivent lui être appliquées
                            sequence_values = dict_file[str(i)]

                            # Mise à jour des valeurs de la nouvelle séquence
                            sequence[1].set_value(sequence_values['delay'])    
                            for j in range(24):
                                if isinstance(sequence_values['data'][str(j)], bool):
                                    sequence[2][j].set_value(sequence_values['data'][str(j)])

                        # Mise à jour de la checkbox de boucle
                        loop_checkbox.set_value(dict_file['loop_to_start'])
                        
                        ui.notify("Configuration chargée")
                        import_popup.close()

                    return

                # Permet d'exporter en fichier JSON la configuration actuelle
                def export_file():

                    global sequences_list
                    global sequences_values

                    if export_button.enabled:
                        # Sauvegarde des valeurs actuelles dans sequences_values
                        save_sequences()
                        
                        export_dict = {} 
                        nb_sequences = len(sequences_values)
                        
                        # Pour chaque séquence
                        for i in range(nb_sequences):
                            sequence_values = sequences_values[i]
                            # Création de la structure du dictionnaire
                            export_dict[i] = {'delay' : sequence_values[0],
                                              'data' : {} }
                            # Mise à jour du sous-dictionnaire contenant les valeurs des bits
                            for j in range(24):
                                export_dict[i]['data'][j] = sequence_values[1][j]

                        # Sauvegarde de la valeur de la checkbox
                        export_dict['loop_to_start'] = loop_checkbox.value

                        # Création du fichier à exporter
                        export_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../exports/'))
                        time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") #date actuelle pour différencier les fichiers
                        exported_file_name = time + "__pulse.json" # nom du fichier
                        path_export = os.path.normpath(export_dir + "/" + exported_file_name) # chemin du fichier

                        # Exportation
                        export_file = open(path_export, 'x')
                        json.dump(export_dict, export_file)
                        export_file.close()

                        # Affichage du lien vers le fichier
                        export_links.clear()
                        with export_links:
                            ui.link("Fichier exporté : {}".format(exported_file_name), "/exports/" + exported_file_name, new_tab=True)
                    return

                #######################
                # Création de séquences
                #######################

                # Permet de sauvegarder les différentes valeurs actuelles des séquences dans sequences_values
                def save_sequences():
                    
                    global sequences_values
                    global sequences_list
                    # Initialisation
                    sequences_values = []
                    for sequence in sequences_list:
                        # On créer une sous-liste pour chaque séquence : [<durée> [Liste de 0 ou True/False pour chaque bit]]
                        # Par défaut, la valeur de chaque bit est attribuée à 0, si un bit est actif (qu'il soit haut ou bas), on le remplace par True ou False
                        # (Pour pouvoir différencier bit actif/non actif dans l'export/import)
                        new_sequence_values = [0.0, [0 for i in range(24)]]

                        # Sauvegarde du délai
                        new_sequence_values[0] = sequence[1].value
                        for i in range(24):
                            bit_switch = sequence[2][i]
                            # La liste des switch ne contenant par défaut que des 0, remplacé par un objet Switch si le bit est actif, on vérifie d'abord si la valeur n'est pas 0,
                            # avant de pouvoir, si ce n'est pas le cas, lire la valeur de l'objet switch. Contrairement à import(), il n'est pas nécessaire de vérifier le type,
                            # puisque "0" et un objet switch ne peuvent pas être confondus
                            if bit_switch != 0: 
                                new_sequence_values[1][i] = bit_switch.value

                        # Rajout de la nouvelle séquence
                        sequences_values.append(new_sequence_values)

                # Permet de mettre à jour l'affichage des séquences lorsqu'on modifie les bits activés, sans devoir tout rerentrer manuellement
                def update_sequences_bits():

                    global sequences_list
                    global sequences_values
                    # Sauvegarde des valeurs précédentes dans sequences_values
                    save_sequences()
                    # Remise à zéro des séquences actuelles
                    sequences_list = []
                    sequences.clear()
                    for sequence_values in sequences_values:
                        with sequences:
                            # On recréer chaque séquence, cette fois ci avec les nouveaux bits activés/désactivés
                            add_sequence()
                            sequence = sequences_list[-1]
                            sequence[1].set_value(value=sequence_values[0]) # Récupération de la durée 
                            # Pour chaque bit resté inchangé, on lui réaffecte la valeur sauvegardée
                            for i in range(24):
                                # On parcours tous les bits actifs : pour ceux n'ayant pas changé, on leur attribue directement la valeur True/False stockée dans sequences_values
                                # Pour ceux nouvellement activés, on veut leur attribuer la valeur False par défaut, cela correspond bien au "0" stocké dans sequences_values pour des bits (précédemment) désactivés
                                # Il suffit donc de rajouter la conversion en booléen bool() pour traiter tous les cas simultanément
                                if active_bits[i].value: 
                                    sequence[2][i].set_value(value=bool(sequence_values[1][i]))

                # Permet de rajouter une séquence à la liste
                def add_sequence():
                    global sequences_list
                    global sequences_values
                    with sequences:
                        with ui.row() as new_sequence:
                            # Numéro de la séquence rajoutée
                            n = len(sequences_list)
                            # Bouton de délai
                            new_number = ui.number(label="Durée (ms)", value=200, format='%.3f')

                            # Liste des switchs correspondants aux bits, initialisés à la valeur 0
                            new_switches = [0 for i in range(24)]

                            for i in range(24):
                                # Pour chaque bit, s'il est actif, on rajoute un switch à l'emplacement correspondant dans new_switches
                                if active_bits[i].value:
                                    new_switches[i] = ui.switch(str(i))

                            # On rajoute un bouton à la fin, configuré pour supprimer la séquence "n"
                            new_button = ui.button(on_click=lambda: remove_sequence(n)).props('icon=close')
                            # On rajoute les différents éléments dans sequences_list, pour pouvoir y accéder plus tard
                            sequences_list.append([
                                new_sequence,
                                new_number,
                                new_switches,
                                new_button
                                ])
                
                # Permet de supprimer la séquence i dans sequences_list
                def remove_sequence(i):
                    global sequences_list
                    global sequences_values
                    # On récupère la ligne contenant tous les éléments de la séquence
                    sequence_row = sequences_list[i][0]
                    # On efface la séquence de la liste
                    del(sequences_list[i])
                    # On supprime la ligne du conteneur contenant toutes les séquences
                    sequences.remove(sequence_row)

                    # On met à jour l'affichage des séquences, pour recréer les différents boutons permettant de supprimer une séquence
                    # (puisqu'une séquence a été enlevée de la liste, les boutons de suppressionne pointent plus vers le même élément 'n')
                    update_sequences_bits()


                #################################
                # Conversion séquences vers Pulse
                #################################

                # Permet de programmer les séquences dans le pulse
                def upload_sequences():
                    global sequences_values
                    global sequences_list
                    global pulse
                    
                    # Sauvegarde des valeurs dans sequences_values
                    save_sequences()
                    # Remise à zéro des instructions stockées dans l'objet pulse
                    pulse.inst = []

                    for sequence in sequences_list:
                        bin_inst = ""
                        for i in range(24):
                            # Pour chaque séquence, on récupère pour chaque bit le "switch" correspondant
                            # S'il s'agit bien d'un switch, on rajoute sa valeur, sinon (s'il s'agit d'un "0", i.e. bit non actif) on rajoute "0"
                            switch = sequence[2][i]
                            if switch != 0:
                                bin_inst += str(int(switch.value))
                            else:
                                bin_inst += '0'
                        # Conversion du texte binaire en int
                        int_inst = int(bin_inst[::-1], 2)
                        # Récupération de la durée
                        delay = sequence[1].value
                        # Sauvegarde de l'instruction dans l'objet pulse 
                        pulse.add_sequence(int_inst, delay, "ms")

                    loop_to_start = loop_checkbox.value
                    # Lancement de la programmation du pulse
                    pulse.program(loop_to_start)
                
                ##################
                # Mise à jour plot
                ##################

                # Permet de mettre à jour les chronogrammes en fonction des séquences configurées
                def update_plot():
                    global sequences_values
                     # Sauvegarde des valeurs
                    save_sequences()
                    nb_sequences = len(sequences_values)
                    nb_active_bits = 0

                    # On calcule le nombre de plots à créer (i.e. de bits actifs)
                    for i in range(24):
                        if active_bits[i].value:
                            nb_active_bits += 1
                    # Initialisation des listes, tous les graphes commencent à l'origine
                    time = [0]
                    values = [[0] for i in range(24)]

                    # On créer le premier point de chaque plot, pour rajouter un "créneau" à l'origine, pour les bits initialement non nuls 
                    time.append(0)
                    for i in range(24):
                        if active_bits[i].value:
                            values[i].append(int(sequences_values[0][1][i]))

                    # On rajoute les points ; à chaque instant où le signal peut changer, on rajoute deux points, l'un pour l'état actuel et l'autre pour l'état suivant,
                    # qui ont la même abscisse : comme ça, s'il y a effectivement changement d'état, matplotlib tracera une ligne droite verticale entre ces deux points (sinon, il relierait le point du nouvel état à celui de l'instant d'avant,
                    # ce qui donnerait une forme triangulaire au signal)
                    for i in range(nb_sequences - 1):
                        new_time = time[-1] + sequences_values[i][0]*0.001
                        # Deux points avec même absisse temporelle
                        time.append(new_time)
                        time.append(new_time)
                        for j in range(24):
                            if active_bits[j].value:
                                # Valeur actuelle et suivante
                                values[j].append(int(sequences_values[i][1][j]))
                                values[j].append(int(sequences_values[i+1][1][j]))

                    # Rajout du dernier point séparemment (pour éviter de sortir de la liste)
                    time.append(sequences_values[nb_sequences-1][0]*0.001 + time[-1])
                    for j in range(24):
                            if active_bits[j].value:
                                values[j].append(int(sequences_values[nb_sequences-1][1][j]))
                    # Mise à jour du plot
                    with plot:
                        # On garde en mémoire la dernière figure pour pouvoir la fermer une fois la nouvelle créée
                        previous_fig = plot.fig.number
                        # Création d'une nouvelle figure et axs dépendant du nombre de bits actifs
                        fig,axs = plt.subplots(nb_active_bits)
                        # Mise à jour de la figure affichée par l'UI
                        plot.fig = fig
                        # Fermeture de la précédente
                        plt.close(previous_fig)
                        fig.set_size_inches((15,1.75*nb_active_bits))
                        # j permet de compter le nombre de bits actifs, et donc de pouvoir gérer séparément les axs[]
                        j = 0
                        for i in range(24):
                            if active_bits[i].value:
                                # cas où il y a plusieurs bits activés : axs est bien une liste d'ax
                                if nb_active_bits > 1:
                                    axs[j].plot(time, values[i], label=("Bit %d" % i))
                                    axs[j].legend(loc="upper left")
                                    axs[j].set_ylim(-0.1, 1.1)
                                    j += 1 # On passe à l'ax suivant pour le prochain bit actif trouvé
                                else :
                                # cas où un seul bit est actif : axs n'est pas une liste mais un simple ax
                                    axs.plot(time, values[i], label=("Bit %d" %i))
                                    axs.legend(loc="upper left")
                                    axs.set_ylim(-0.1,1.1)

                ####################
                # Création du layout
                ####################

                ###
                # Partie haute : Initialisation, contrôle exécution, et Import/Export
                ###
                with ui.row():
                    ###
                    # Initialisation Pulse
                    ###
                    with ui.card():
                        ui.label("PulseBlasterUSB")
                        with ui.row():
                            connect_button = ui.button("Connect", on_click=connect_pulse)
                            disconnect_button = ui.button("Disconnect", on_click= disconnect_pulse)
                        enable(connect_button)
                        disable(disconnect_button)
                    ###
                    # Contrôle (Start, Pause/Resume, Stop/Reset) de l'exécution
                    ###
                    with ui.card() as control_card:
                        ui.label("Contrôle")
                        with ui.row():
                            start_button = ui.button("Start", on_click=start_pulse)
                            pause_button = ui.button("Pause", on_click=pause_pulse)
                            reset_button = ui.button("Stop/Reset", on_click=reset_pulse)
                        disable(control_card)
                        disable(start_button)
                        disable(pause_button)
                        disable(reset_button)
                    ###
                    # Importation et exportation de la configuration en tant que JSON
                    ###
                    with ui.card() as file_card:
                        with ui.dialog() as import_popup:
                            with ui.card().classes("fixed-center"):
                                ui.label("Importer une configuration").classes("text-h6")
                                ui.separator()
                                ui.upload(on_upload=import_file)
                                ui.button("Annuler",on_click=import_popup.close)

                        ui.label("Import/Export")
                        with ui.row():
                            import_button = ui.button("Importer un fichier", on_click=import_popup.open)
                            export_button = ui.button("Exporter cette configuration", on_click=export_file)
                        with ui.row() as export_links:
                            pass
                        enable(file_card)
                        enable(import_button)
                        enable(export_button)
                    
                global sequences_values
                global sequences_list
                sequences_list = []
                sequences_values = []
                ###
                # Création de séquences
                ###
                with ui.card():
                    ###
                    # Structure globale
                    ###
                    ui.label("Bits activés :").classes("text-h6")
                    active_bits_row = ui.row()
                    ui.separator()
                    ui.label("Séquences").classes("text-h6")
                    sequences = ui.column() 
                    ###
                    # Remplissage de active_bits_row par des switchs permettant de modifier les bits actifs
                    ###
                    with active_bits_row:
                        active_bits: list[ui.switch] = []
                        for i in range(24):
                            new_switch = ui.switch(str(i), on_change=update_sequences_bits)
                            active_bits.append(new_switch)
                        active_bits[0].set_value(True)
                    ###
                    # Ajoute d'une séquence par défaut dans sequences
                    ###
                    with sequences:
                        add_sequence()
                    ###
                    # Autres boutons
                    ###
                    ui.button("Ajouter une séquence",on_click=add_sequence)
                    loop_checkbox = ui.checkbox("Loop to start")
                ###
                # Initialisation des chronogrammes
                ###
                ui.button("Mettre à jour les graphes", on_click=update_plot)
                with ui.plot(close=False) as plot:
                    pass
                update_plot()

                #######################################
                # Divers utilitaires pour l'UI
                #######################################
                
                def on_disconnect():
                    if control_card.enabled:
                        if not start_button.enabled:
                            pulse.stop()
                            pulse.reset()
                        pulse.close()

                app.on_disconnect(on_disconnect)