#########################################
#  QSense | pico_ui.py
#########################################
#
# Ce fichier permet la création de l'UI de la page de contrôle du picoscope avec create_pico_ui()
# Cette page permet de connecter/Déconnecter le picoscope, contrôler son générateur de fonctions interne,
# règler les paramètres d'acquisition, et afficher les données pour un ou plusieurs channels
# Elle communique avec pico.py pour la gestion interne au picoscope
#

import matplotlib.pyplot as plt
from .subscripts.pico import Picoscope
from ..theme import frame
from nicegui import app, ui


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

            # Routine de mise à jour des graphes, toutes les secondes
            data_update = ui.timer(1, do_data_update, active=False)

            ###################################
            # Création du layout de l'interface
            ###################################

            with ui.column():
                with ui.row(): # Partie haute (Init, Acqui, Gen)
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
                    with ui.row().classes("items-center"): # Première ligne (channels A et B)

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

                    with ui.row().classes("items-center"): # Deuxième ligne (Channels C et D)

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

                # On stocke les différents éléments dans des dictionnaires pour pouvoir y accéder par itération et éviter de répéter 4x le même code pour chaque channel
                channel_plots = {'A' : channelA_plot,'B' : channelB_plot, 'C' : channelC_plot,'D' : channelD_plot}
                channel_plots_color = {'A' : "b-",'B' : "r-",'C' : "g-",'D' : "g-"}
                channel_actives = {'A' : channelA_active,'B' : channelB_active,'C' : channelC_active,'D' : channelD_active}
                channel_switch_modes = {'A' : switch_modeA,'B' : switch_modeB,'C' : switch_modeC,'D' : switch_modeD}
                channel_range_toggles = {'A' : rangeA_toggle,'B': rangeB_toggle,'C' : rangeC_toggle,'D' : rangeD_toggle}

                disable(channels_grid) # Interface channels désactivée par défaut

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
                    pico.ps.stop()
                    pico.ps.close() # Et on ferme le Pico
            # On règle l'app pour qu'elle exécute on_disconnect lorsqu'un utilisateur ferme la page, pour libérer la connexion au picoscope
            app.on_disconnect(on_disconnect)