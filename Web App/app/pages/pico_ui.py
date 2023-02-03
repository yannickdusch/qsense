#########################################
#  QSense | pico_ui.py
#########################################
#
# Ce fichier permet la création de l'UI de la page de contrôle du picoscope avec create_pico_ui()
# Cette page permet de connecter/Déconnecter le picoscope, contrôler son générateur de fonctions interne,
# règler les paramètres d'acquisition, et afficher les données pour un ou plusieurs channels
# Elle communique avec pico.py pour la gestion interne au picoscope
#

import datetime
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from .subscripts.pico import Picoscope
from ..theme import frame
from nicegui import app, ui
from nicegui.events import ClickEventArguments


def create_pico_ui():
    #################################
    # Classes/Fonctions utilitaires :
    #################################

    # Permet de stocker une erreur et un message allant avec, utilisé pour afficher une popup d'erreur si nécessaire
    class Error():
        def __init__(self):
            self.error_message = "Unknown error"
            self.err = "Unknown"

    # Marquer un objet comme "désactivé" (classe Quasar "disabled" + booléen)
    def disable(object):
        object.classes("disabled")
        object.active = False

    # Marquer un ojet comme "activé"
    def enable(object):
        object.classes(remove="disabled")
        object.active = True

    ##################
    # Création de l'UI
    ##################

    @ui.page('/pico')
    def pico_ui_page():
        with frame('Contrôle Picoscope 5444D'):

            ####################################
            # Connexion/Déconnexion du picoscope
            ####################################

            # Lors de la connexion au picoscope
            def init_pico():
                if connect_button.active:
                    ui.notify("Tentative de connexion...")
                    global pico
                    try:
                        # Initialisation de la classe Pico
                        pico = Picoscope()
                        pico.initialize()
                        pico.type_signal = "None"
                    except OSError as err:
                        # Picoscope introuvable (usb pas connecté et/ou déjà utilisé par une autre session)
                        error.error_message = "Impossible de se connecter au picoscope"
                        error.err = str(err)
                        error_popup.open()
                    else:
                        ui.notify("Connexion réussie à ID : {}".format(str(pico.serialNumber)))
                        # Initialisation du générateur de signal
                        select_wafeform.bind_value(pico, 'type_signal')
                        gen_signal()

                        # Activation des différents éléments de l'UI nécessitant le picoscope
                        enable(rangeA_toggle)
                        enable(rangeB_toggle)
                        enable(rangeC_toggle)
                        enable(rangeD_toggle)

                        enable(acquisition_card)
                        enable(acquisition_state_button)
                        enable(disconnect_button)
                        enable(sig_generator)
                        enable(channels_grid)
                        channelA_active.set_value(True) # Seul channel A actif par défaut
                        
                        disable(connect_button)

            # Lors de la déconnexion manuelle du picoscope
            def disconnect_pico():
                if disconnect_button.active:
                    data_update.active = False 
                    pico.ps.stop()
                    pico.ps.close()
                    ui.notify("Déconnexion effectuée")

                    # Remise des valeurs par défaut pour le générateur de fonction
                    amplitude_number.set_value(0)
                    offset_number.set_value(0)
                    frequency_number.set_value(1)
                    select_wafeform.set_value("None")

                    acquisition_state_button.set_text("Start")

                    # Désactivation des éléments de l'UI nécessitant le picoscope
                    disable(channels_grid)
                    disable(rangeA_toggle)
                    disable(rangeB_toggle)
                    disable(rangeC_toggle)
                    disable(rangeD_toggle)
                    disable(disconnect_button)
                    disable(sig_generator)
                    disable(acquisition_card)
                    disable(acquisition_state_button)

                    enable(connect_button)
            
            ######################
            # Générateur de signal
            ######################
            
            # Mise à jour globale du générateur de signal
            def gen_signal():
                if sig_generator.active == True:
                    if pico.type_signal == "None":
                        pico.remove_signal()
                    else:
                        pico.set_signal() # Toutes les paramètres sont déjà stockés dans l'objet pico, pas besoin de les passer
                else:
                    pico.type_signal == "None"

            # Mise à jour de la fréquence du signal
            def set_signal_frequency():
                if sig_generator.active:
                    freq_value = frequency_number.value
                    pico.freq_signal = freq_value
                    gen_signal() # Mise à jour du picoscope

                else: # Valeur par défaut
                    frequency_number.set_value(1)

            # Mise à jour de l'amplitude du signal
            def set_signal_amplitude():
                if sig_generator.active:
                    amp_value = amplitude_number.value
                    offset_value = offset_number.value

                    # Vérifications par rapport au limites du générateur
                    if amp_value < 0: # Amplitude négative
                        amplitude_number.set_value(0)
                        pico.amp_signal = 0
                    elif amp_value/2 + abs(offset_value) > pico.max_gen_output:  # Amplitude qui dépasse la limite haute ou basse, en prenant en compte l'offset
                        max_amp = 2*(pico.max_gen_output-abs(offset_value))
                        amplitude_number.set_value(max_amp)
                        pico.amp_signal =  max_amp
                    else: #Amplitude OK
                        pico.amp_signal= amp_value
                    gen_signal() # Mise à jour du picoscope

                else: # Valeur par défaut
                    amplitude_number.set_value(0)

            # Mise à jour de l'offset du signal
            def set_signal_offset():
                if sig_generator.active:
                    amp_value = amplitude_number.value
                    offset_value = offset_number.value

                    if offset_value >= 0 and amp_value/2 + offset_value > pico.max_gen_output: # Amplitude + offset qui dépasse la limite haute
                        max_offset = pico.max_gen_output - amp_value/2
                        offset_number.set_value(max_offset)
                        pico.offset_signal = max_offset
                    elif offset_value < 0 and amp_value/2 - offset_value > pico.max_gen_output: # Amplitude + offset qui dépasse la limite basse
                        min_offset = -pico.max_gen_output + amp_value/2
                        offset_number.set_value(min_offset)
                        pico.offset_signal = min_offset
                    else: # Offset OK
                        pico.offset_signal = offset_value
                    gen_signal() # Mise à jour du picoscope

                else: # Valeur par défaut
                    offset_number.set_value(0)
            
            ##########################
            # Paramètres d'acquisition
            ##########################

            # Mise à jour des paramètres d'acquisition
            def set_acquisition():
                if acquisition_card.active:
                    pico.nosamples = int(number_samples.value)
                    pico.sample_duration = acquisition_time.value*1e-3 # Conversion ms en s
                    pico.update_sampling() # Mise à jour des paramètres internes du picoscope
                else:
                    # Valeurs par défaut lorsque le picoscope n'est pas connecté
                    number_samples.set_value(1000)
                    acquisition_time.set_value(100)

            # Permet de démarrer ou  mettre en pause l'acquisition
            def set_acquisition_state():
                if acquisition_state_button.active:
                    if acquisition_state_button.text == "Pause": # Si l'acquisition est en cours
                        data_update.active = False
                        acquisition_state_button.set_text("Resume")
                    else: # Si elle est en pause ou pas encore démarrée
                        data_update.active = True
                        acquisition_state_button.set_text("Pause")
                
            # Mise à jour des channels actifs 
            def update_active_channels():
                if channels_grid.active:
                    for channel in ['A', 'B', 'C', 'D']:
                        pico.channels[channel] = channel_actives[channel].value
                    pico.update_channels() # Mise à jour du picoscope

                else: # Valeurs par défaut lorsque picoscope déconnecté
                    for channel in ['A', 'B', 'C', 'D']:
                        channel_actives[channel].set_value(False)
                
            # Mise à jour des échelles en tension
            def update_ranges():
                for channel in ['A', 'B', 'C', 'D']:
                    if channel_range_toggles[channel].active:
                        # Mise à jour des valeurs puis du picoscope
                        pico.ranges[channel] = channel_range_toggles[channel].value
                        pico.update_channels()
                        # Mise à jour du plot
                        with channel_plots[channel]:
                            range = channel_range_toggles[channel].value
                            plt.ylim([-range,range])
                    else: # Valeur par défaut
                        channel_range_toggles[channel].set_value(20)
            
            
            
            # Mise à jour des couplages AC/DC
            def update_modes():
                if channels_grid.active:
                    for channel in ['A', 'B', 'C', 'D']:
                        if channel_switch_modes[channel].value : # Mode AC activé
                            pico.couplings[channel] = 'AC'
                        else : # DC par défaut
                            pico.couplings[channel] = 'DC'
                        pico.update_channels() # Mise à jour du picoscope
                else : # Valeurs par défaut lorsque picoscope déconnecté
                    for channel in ['A', 'B', 'C', 'D']:
                        channel_switch_modes[channel].value = False

            #############
            # Acquisition
            #############

            # Récupération des données et mise à jour des graphes
            def do_data_update():
                global get_data_in_progress
                if not get_data_in_progress: # On vérifie qu'une acquisition n'est pas déjà en cours (i.e. si jamais la durée d'acquisition est fixée à plus de 1000 ms, on risque d'accumuler les demandes de run block au picoscope et de ralentir considérablement l'UI)
                    get_data_in_progress = True
                    data = pico.get_data_block() # Récupération des données du picoscope
                    for channel in ['A', 'B', 'C', 'D']:
                        if (pico.channels[channel]):

                            with channel_plots[channel]: # On remet le contexte du plot pour pouvoir le modifier
                                plt.clf() # On clear le plot
                                plt.plot(data[channel][0], data[channel][1], channel_plots_color[channel], label="Channel {}".format(channel)) # On retrace les données
                                
                                # Mise à jour des axes
                                range = pico.ranges[channel]
                                plt.legend(loc="upper left")
                                plt.ylim([-range, range])
                    get_data_in_progress = False

            # Routine de mise à jour des graphes, toutes les secondes
            data_update = ui.timer(1, do_data_update, active=False)

            #############
            # Exportation
            #############

            # Permet d'exporter le graphe d'un channel donnée dans le format donné
            def export_plot(e: ClickEventArguments):
                if channels_grid.active:

                    export_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../exports/'))
                    time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") #date actuelle pour différencier les fichiers
                    channel = export_menus_list[e.sender.id][0] # On récupère le channel correspondant
                    export_type = export_menus_list[e.sender.id][1]
                    export_links = export_menus_list[e.sender.id][2]

                    if (export_type == 'png'): # Exportation PNG
                        exported_file_name = time + "__pico_exported_plot_" + channel + ".png" # nom du fichier
                        file_to_export = os.path.normpath(export_dir + "/" + exported_file_name) # chemin du fichier
                        with channel_plots[channel]:
                            plt.savefig(file_to_export) # exportation en png du plot

                    elif (export_type == 'tpng'): # Exportation PNG Transparent
                        exported_file_name = time + "__pico_exported_plot_" + channel + ".png" # nom du fichier
                        file_to_export = os.path.normpath(export_dir + "/" + exported_file_name) # chemin du fichier
                        with channel_plots[channel]:
                            plt.savefig(file_to_export, transparent=True) # exportation en png transparent du plot

                    else : # Exportation CSV
                        exported_file_name = time + "__pico_exported_plot_" + channel + ".csv" # nom du fichier
                        file_to_export = os.path.normpath(export_dir + "/" + exported_file_name) # chemin du fichier
                        with channel_plots[channel]:
                            ax = plt.gca() # On récupère les données du plot
                            line = ax.lines[0]
                            datax = line.get_xdata()
                            datay = line.get_ydata()

                        data_file_str = ""  # Construction du fichier csv
                        data_file_str += ("Temps (s) ; Channel " + channel + "(V)\n")
                        for i in range(len(datax)):
                            data_file_str += (str(datax[i]) + ";" +str(datay[i]) + "\n")

                        data_file = open(file_to_export, 'x') # Ecriture du fichier
                        data_file.write(data_file_str)
                        data_file.close()

                    # Affichage d'un lien vers le fichier exporté (ui.open() ne permet pas d'ouvrir dans un nouvel onglet, et ferme la page pico)
                    export_links.clear()
                    with export_links:
                        ui.link("Fichier exporté : {}".format(exported_file_name), "/exports/" + exported_file_name, new_tab=True).props('target=_blank')



            ###################################
            # Création du layout de l'interface
            ###################################

            with ui.column():

                ###
                # Partie haute (Init, Acqui, Gen)
                ###

                with ui.row(): 
                    with ui.card(): # Initialisation du picoscope
                        ui.label("Initialisation").classes("text-h6")
                        with ui.row():
                            with ui.column():
                                ui.label("Picoscope").classes("text-subtitle2")
                                with ui.row():
                                    connect_button = ui.button('Connect', on_click=init_pico)
                                    enable(connect_button)
                                    disconnect_button = ui.button('Disconnect', on_click=disconnect_pico)
                                    disable(disconnect_button)

                    with ui.card() as acquisition_card: # Acquisition des données
                        ui.label("Réglages de l'acquisition").classes("text-h6")
                        with ui.column():
                            acquisition_time = ui.number("Durée d'acquisition (ms)", value=1, format="%.6f", on_change=set_acquisition)
                            number_samples = ui.number("Nombre d'échantillons", value=1000, on_change=set_acquisition)
                        with ui.column():
                            acquisition_state_button = ui.button('Start', on_click=set_acquisition_state)
                            disable(acquisition_state_button)
                        disable(acquisition_card)

                    with ui.card() as sig_generator: # Générateur de signal intégré      
                        ui.label("Générateur de signal").classes("text-h6")
                        with ui.row():
                            with ui.row().classes("items-baseline"):
                                ui.label("Forme : ")
                                select_wafeform = ui.select(["None", "Sine", "Square", "Triangle", "RampUp"], value="None", on_change=gen_signal)
                            amplitude_number = ui.number(label="Amplitude PeakToPeak (V)", value=0, format="%.3f", on_change=set_signal_amplitude)
                            offset_number = ui.number(label="Offset (V)", value=0, format="%.3f", on_change=set_signal_offset)
                            frequency_number = ui.number(label="Fréquence (Hz)", value=1, format="%.2f", on_change=set_signal_frequency)
                    disable(sig_generator)

                with ui.column() as channels_grid:

                    ###
                    # Première ligne (channels A et B)
                    ###

                    with ui.row().classes("items-center"): 

                        # Channel A
                        with ui.column():
                            with ui.plot(close=False, figsize=(6,4)) as channelA_plot:
                                xA = (0,0)
                                yA = (0,0)
                                plt.plot(xA,yA, 'b-', label="Channel A")
                                plt.legend(loc="upper left")
                            with ui.card():
                                with ui.row():
                                    channelA_active = ui.checkbox("Channel A",value=False,on_change=update_active_channels) # Permet d'activer/désactiver la récupération de données depuis ce channel
                                    switch_modeA = ui.switch("Mode AC", on_change=update_modes) # Permet d'activer/désactiver le couplage AC (sinon, DC)
                                
                                ui.label("Range :")
                                rangeA_toggle = ui.toggle(options={20: "20V", 10: "10V", 5: "5V", 2: "2V", 1: "1V", 0.500:"500mV", 0.200:"200mV",0.100:"100mV",0.050:"50mV",0.020:"20mV",0.010:"10mV"}, value=20,on_change=update_ranges).props("no-caps")
                                disable(rangeA_toggle)
                                with ui.menu() as export_A:
                                    export_A_png = ui.menu_item('PNG',  export_plot)
                                    export_A_tpng = ui.menu_item('Transparent PNG', export_plot)
                                    export_A_csv = ui.menu_item('CSV', export_plot)
                                    ui.separator()
                                    ui.menu_item('Retour', export_A.close)
                                ui.button('Exporter le graphe', on_click=export_A.open)
                                with ui.column() as channelA_export_links:
                                    pass

                        # Channel B
                        with ui.column():
                            with ui.plot(close=False, figsize=(6,4)) as channelB_plot:
                                xB = (0,0)
                                yB = (0,0)
                                plt.plot(xB,yB, 'r-', label="Channel B")
                                plt.legend(loc="upper left")
                            with ui.card():
                                with ui.row():
                                    channelB_active = ui.checkbox("Channel B",value=False,on_change=update_active_channels)
                                    switch_modeB = ui.switch("Mode AC", on_change=update_modes)
                                ui.label("Range :")
                                rangeB_toggle = ui.toggle(options={20: "20V", 10: "10V", 5: "5V", 2: "2V", 1: "1V", 0.500:"500mV", 0.200:"200mV",0.100:"100mV",0.050:"50mV",0.020:"20mV",0.010:"10mV"}, value=20,on_change=update_ranges).props("no-caps")
                                disable(rangeB_toggle)
                                with ui.menu() as export_B:
                                    export_B_png = ui.menu_item('PNG',  export_plot)
                                    export_B_tpng = ui.menu_item('Transparent PNG', export_plot)
                                    export_B_csv = ui.menu_item('CSV', export_plot)
                                    ui.separator()
                                    ui.menu_item('Retour', export_B.close)
                                ui.button('Exporter le graphe', on_click=export_B.open)
                                with ui.column() as channelB_export_links:
                                    pass
                    
                    ###
                    # Deuxième ligne (Channels C et D)
                    ###

                    with ui.row().classes("items-center"): 

                        # Channel C
                        with ui.column():
                            with ui.plot(close=False, figsize=(6,4)) as channelC_plot:
                                xC = (0,0)
                                yC = (0,0)
                                plt.plot(xC,yC, 'g-', label="Channel C")
                                plt.legend(loc="upper left")
                            with ui.card():
                                with ui.row():
                                    channelC_active = ui.checkbox("Channel C",value=False,on_change=update_active_channels)
                                    switch_modeC = ui.switch("Mode AC", on_change=update_modes)
                                ui.label("Range :")
                                rangeC_toggle = ui.toggle(options={20: "20V", 10: "10V", 5: "5V", 2: "2V", 1: "1V", 0.500:"500mV", 0.200:"200mV",0.100:"100mV",0.050:"50mV",0.020:"20mV",0.010:"10mV"}, value=20,on_change=update_ranges).props("no-caps")
                                disable(rangeC_toggle)
                                with ui.menu() as export_C:
                                    export_C_png = ui.menu_item('PNG',  export_plot)
                                    export_C_tpng = ui.menu_item('Transparent PNG', export_plot)
                                    export_C_csv = ui.menu_item('CSV', export_plot)
                                    ui.separator()
                                    ui.menu_item('Retour', export_C.close)
                                ui.button('Exporter le graphe', on_click=export_C.open)
                                with ui.column() as channelC_export_links:
                                    pass

                        # Channel D
                        with ui.column():
                            with ui.plot(close=False, figsize=(6,4)) as channelD_plot:
                                xD = (0,0)
                                yD = (0,0)
                                plt.plot(xD,yD, 'y-', label="Channel D")
                                plt.legend(loc="upper left")
                            with ui.card():
                                with ui.row():
                                    channelD_active = ui.checkbox("Channel D",value=False,on_change=update_active_channels)
                                    switch_modeD = ui.switch("Mode AC", on_change=update_modes)
                                ui.label("Range :")
                                rangeD_toggle = ui.toggle(options={20: "20V", 10: "10V", 5: "5V", 2: "2V", 1: "1V", 0.500:"500mV", 0.200:"200mV",0.100:"100mV",0.050:"50mV",0.020:"20mV",0.010:"10mV"}, value=20,on_change=update_ranges).props("no-caps")
                                disable(rangeD_toggle)
                                with ui.menu() as export_D:
                                    export_D_png = ui.menu_item('PNG',  export_plot)
                                    export_D_tpng = ui.menu_item('Transparent PNG', export_plot)
                                    export_D_csv = ui.menu_item('CSV', export_plot)
                                    ui.separator()
                                    ui.menu_item('Retour', export_D.close)
                                ui.button('Exporter le graphe', on_click=export_D.open)
                                with ui.column() as channelD_export_links:
                                    pass
                disable(channels_grid) # Interface channels désactivée par défaut

            #######################################
            # Divers utilitaires pour l'UI
            #######################################

                # On stocke les différents éléments dans des dictionnaires pour pouvoir y accéder par itération et éviter de répéter 4x le même code pour chaque channel
                channel_plots = {'A' : channelA_plot,'B' : channelB_plot, 'C' : channelC_plot,'D' : channelD_plot} # Pour accéder aux plots
                channel_plots_color = {'A' : "b-",'B' : "r-",'C' : "g-",'D' : "g-"} # Pour accéder aux couleurs de chaque channel
                channel_actives = {'A' : channelA_active,'B' : channelB_active,'C' : channelC_active,'D' : channelD_active} # Pour accéder aux checkboxs d'activation des channels
                channel_switch_modes = {'A' : switch_modeA,'B' : switch_modeB,'C' : switch_modeC,'D' : switch_modeD} # Pour accéder aux switchs d'activation du mode AC
                channel_range_toggles = {'A' : rangeA_toggle,'B': rangeB_toggle,'C' : rangeC_toggle,'D' : rangeD_toggle} # Pour accéder aux toggles de choix des échelles de tension
                export_menus_list = { # Pour accéder, grâce à l'ID du bouton activé, au channel, type d'exportation, et où afficher le lien du fichier, pour chaque exportation de chaque channel
                    export_A_png.id : ('A', 'png', channelA_export_links), export_A_tpng.id : ('A', 'tpng', channelA_export_links), export_A_csv.id : ('A', 'csv', channelA_export_links),
                    export_B_png.id : ('B', 'png', channelB_export_links), export_B_tpng.id : ('B', 'tpng', channelB_export_links), export_B_csv.id : ('B', 'csv', channelB_export_links),
                    export_C_png.id : ('C', 'png', channelC_export_links), export_C_tpng.id : ('C', 'tpng', channelC_export_links), export_C_csv.id : ('C', 'csv', channelC_export_links),
                    export_D_png.id : ('D', 'png', channelD_export_links), export_D_tpng.id : ('D', 'tpng', channelD_export_links), export_D_csv.id : ('D', 'csv', channelD_export_links) }

            # Création d'une popup d'erreur affichant les valeurs de l'objet error, que l'on pourra ensuite afficher avec error_popup
            error = Error()
            with ui.dialog() as error_popup:
                with ui.card():
                    ui.label("Une erreur est survenue").classes("font-bold text-h6")
                    ui.label().bind_text(error, "error_message")
                    ui.label().bind_text(error, "err")
                    ui.button('Fermer', on_click=error_popup.close)

            # Lors de la déconnexion de l'utilisateur (page fermée)
            def on_disconnect():
                if disconnect_button.active: 
                    data_update.active = False # On stoppe la collecte de donnée si elle est toujours en cours
                    pico.ps.close() # Et on ferme le Pico

            # On règle l'app pour qu'elle exécute on_disconnect lorsqu'un utilisateur ferme la page, pour libérer la connexion au picoscope
            app.on_disconnect(on_disconnect)
