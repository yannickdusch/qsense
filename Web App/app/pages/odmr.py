#########################################
#  QSense | odmr.py
#########################################
#
# Ce fichier permet de contrôler une expérience simple d'ODMR, en réglant les différents paramètres d'acquisition et du signal à générer
# Il permet également de lancer l'acquisition une fois, ou en continue, d'en afficher les résultats, et de les exporter sous différents formats
#

import datetime
import os
from matplotlib import pyplot as plt
from nicegui import ui, app
from nicegui.events import ClickEventArguments
from fastapi.responses import RedirectResponse
from fastapi.requests import Request
from pyvisa.errors import VisaIOError
from serial import SerialException

from ..theme import frame
from .subscripts.MF3D import MF3D
from .subscripts.AFG3252 import AFG3252
from .subscripts.pico import Picoscope
from ..settings import get_setting
from ..utils import Error
from ..utils import enable
from ..utils import disable
from .login import is_authenticated

def create_odmr_ui():
    # Récupération des différents paramètres
    odmr_settings = get_setting('odmr')
    MF3D_simple_timer = odmr_settings["MF3D_simple_plot_timer"]
    MF3D_multi_timer = odmr_settings["MF3D_simple_plot_timer"]
    MF3D_serial_number = odmr_settings["MF3D_serial_number"]
    AFG3252_usb_address = odmr_settings["AFG3252_usb_address"]
    ODMR_timer = odmr_settings["ODMR_timer"]
    
    # Relation entre tension et fréquence correspondante (Cf. Caractéristique)
    v_to_freq = lambda x: 77.13*x +2467.8

    ##################
    # Création de l'UI
    ##################

    @ui.page("/odmr")
    def odmr_ui(request: Request):

        if not is_authenticated(request):
            return RedirectResponse('/login')
        else:
            with frame("ODMR", request):

                error = Error()

                ###################################
                # Picoscope
                ###################################
                
                # Lors de la connexion au picoscope
                def init_pico():
                    if pico_connect_button.enabled:
                        ui.notify("Tentative de connexion...")
                        global pico
                        try:
                            # Initialisation de la classe Pico
                            pico = Picoscope()
                        except OSError as err:
                            # Picoscope introuvable (usb pas connecté et/ou déjà utilisé par une autre session)
                            error.show_error("Impossible de se connecter au picoscope", err)
                        else:
                            pico.initialize()
                            pico.type_signal = "None"
                            ui.notify("Connexion réussie à ID : {}".format(str(pico.serialNumber)))

                            # Activation des différents éléments de l'UI nécessitant le picoscope
                            if (AFG3252_card.enabled): # Active l'acquisition seulement si le générateur et le picoscope sont tous deux allumés
                                enable(acquisition_card)
                                enable(odmr_card)
                                enable(export_card)
                                enable(odmr_button)
                                enable(odmr_once_button)

                            enable(pico_disconnect_button)
                            enable(pico_card)
                            
                            disable(pico_connect_button)

                # Lors de la déconnexion manuelle du picoscope
                def disconnect_pico():
                    if pico_disconnect_button.enabled: 
                        pico.ps.close()
                        ui.notify("Déconnexion effectuée")

                        # Désactivation des éléments de l'UI nécessitant le picoscope
                        disable(pico_card)
                        disable(pico_disconnect_button)
                        disable(acquisition_card)
                        disable(odmr_card)
                        disable(export_card)
                        disable(odmr_button)
                        disable(odmr_once_button)
                        
                        enable(pico_connect_button)

                # Permet de mettre à jour les différents paramètres internes du picoscope en fonction des valeurs rentrées
                def pico_update_sampling():
                    if acquisition_card.enabled:
                        pico.nosamples = int(nosamples_number.value)
                        pico.sample_duration = int(noperiodes_number.value) * AFG.get_period()
                        pico.update_sampling() # Mise à jour des paramètres internes du picoscope
                        ui.notify('Paramètres envoyés')
                    else:
                        # Valeurs par défaut lorsque le picoscope n'est pas connecté
                        nosamples_number.set_value(1000)
                        noperiodes_number.set_value(1)

                ####################################
                # Tektronix AFG3252 Signal Generator
                ####################################

                # Lors de la connexion au générateur
                def afg_connect():
                    global AFG
                    try:
                        ui.notify("Tentative de connexion...")
                        AFG = AFG3252(AFG3252_usb_address)
                    except VisaIOError as visa_afg_err:
                        error.show_error("Impossible de se connecter au générateur de signal :", visa_afg_err)
                    else:
                        ui.notify("Connexion réussie à ID : " + str(AFG.idn))
                        disable(afg_connect_button)
                        enable(afg_disconnect_button)
                        enable(AFG3252_card)

                        if (pico_card.enabled): # Active l'acquisition seulement si le générateur et le picoscope sont tous deux allumés
                            enable(acquisition_card)
                            enable(odmr_card)
                            enable(export_card)
                            enable(odmr_button)
                            enable(odmr_once_button)

                        # Sélection de la rampe
                        AFG.waveform = "RAMP"
                        AFG.update_waveform()

                        # "Symmétrie" de la rampe
                        AFG.ramp_symmetry = 100
                        AFG.update_ramp_symmetry()

                # Lors de la déconnexion du générateur
                def afg_disconnect():

                    AFG.close()
                    disable(AFG3252_card)
                    disable(acquisition_card)
                    
                    disable(odmr_card) # Dans tous les cas, on désactive l'ODMR/acquisition/etc puisque nécéssitent à la fois le picoscope et le générateur
                    disable(export_card)
                    disable(odmr_button)
                    disable(odmr_once_button)

                    disable(afg_disconnect_button)
                    enable(afg_connect_button)

                # Mise à jour de la fréquence du signal
                def set_signal_frequency():
                    if AFG3252_card.enabled:
                        AFG.frequency = frequency_number.value
                        AFG.update_frequency() # Mise à jour du générateur
                    else: # Valeur par défaut
                        frequency_number.set_value(1)

                # Mise à jour de l'amplitude du signal
                def set_signal_amplitude():
                    if AFG3252_card.enabled:
                        amp_value = amplitude_number.value

                        # Vérifications par rapport au limites du générateur
                        if amp_value < 0: # Amplitude négative
                            amplitude_number.set_value(0)
                            AFG.amplitude = 0
                        elif amp_value > AFG.max_amplitude:  # Amplitude qui dépasse la limite
                            max_amp = AFG.max_amplitude
                            amplitude_number.set_value(max_amp)
                            AFG.amplitude =  max_amp
                        else: #Amplitude OK
                            AFG.amplitude= amp_value
                        AFG.update_amplitude() # Mise à jour du générateur
                        update_freq_labels() # Mise à jour des correspondances en fréquence

                    else: # Valeur par défaut
                        amplitude_number.set_value(0)

                # Mise à jour de l'offset du signal
                def set_signal_offset():
                    if AFG3252_card.enabled:
                        offset_value = offset_number.value

                        if offset_value >= 0 and offset_value > AFG.max_offset: # Offset au dessus de la limite positive
                            max_offset = AFG.max_offset
                            offset_number.set_value(max_offset)
                            AFG.offset = max_offset
                        elif offset_value < 0 and offset_value < -AFG.max_offset: # Offset en dessous de la limite négative
                            min_offset = -AFG.max_offset
                            offset_number.set_value(min_offset)
                            AFG.offset = min_offset
                        else: # Offset OK
                            AFG.offset = offset_value
                        AFG.update_offset()
                        update_freq_labels()
                    else: # Valeur par défaut
                        offset_number.set_value(0)

                # Permet de mettre à jour les correspondances en fréquences affichées en fonction du signal choisi
                def update_freq_labels():
                    # On récupère les valeurs min et max du signal grâce aux valeurs d'amplitude et d'offset
                    min_value = offset_number.value - amplitude_number.value
                    max_value = offset_number.value + amplitude_number.value

                    # Calcul des fréquences correspondantes grâce à la caractéristique
                    min_freq = v_to_freq(min_value)
                    max_freq = v_to_freq(max_value)

                    # Mise à jour du texte
                    min_freq_label.set_text("Min : %.2f Hz" % min_freq)
                    max_freq_label.set_text("Max : %.2f Hz" % max_freq)

                # Permet de mettre à jour globalement le signal (lorsque l'utilisateur valide les valeurs rentrées)
                def update_signal():
                    
                    set_signal_offset()
                    set_signal_amplitude()
                    set_signal_frequency()
                    ui.notify('Paramètres envoyés')

                ###########
                # MF3D Plot
                ###########

                # Permet de créer un MF3D plot, en prenant en compte la possibilité d'une erreur de connexion
                def open_MF3D_plot(fig, multi):
                    try :
                        # Connexion au MV2
                        plot = MF3D(fig, MF3D_serial_number, multi=multi)
                    except SerialException as serial_err:
                        error.show_error("Impossible de se connecter au MV2", serial_err)
                        return None
                    else :
                        enable(MF3D_card)
                        return plot

                # Permet de mettre à jour le type du MF3D plot (i.e. si les figures planes sont actives ou non)
                def update_MF3D_plot_type():
                    if MF3D_card.enabled:
                        global MF3D_plot
                        # Arrêt de la mise à jour du plot
                        MF3D_plot_active.set_value(False)
                        MF3D_update.active = False

                        if MF3D_plot_type_checkbox.value:
                            # Figures planes actives
                            MF3D_update.interval = MF3D_multi_timer # Changement du timer en fonction des paramètres
                            with MF3D_plot_context:
                                # Création d'un nouveau MF3D plot d'un différent type
                                MF3D_plot.close()
                                MF3D_plot = open_MF3D_plot(fig=MF3D_plot_context.fig, multi=True)
                        else:
                            # Figures planes désactivées
                            MF3D_update.interval = MF3D_simple_timer
                            with MF3D_plot_context:
                                MF3D_plot.close()
                                MF3D_plot = open_MF3D_plot(fig=MF3D_plot_context.fig, multi=False)
                
                # Mise à jour des valeurs du plot
                def update_MF3D_plot():
                    global MF3D_plot
                    if MF3D_card.enabled:
                        with MF3D_plot_context:
                            MF3D_plot.animate()

                # Mise à jour du statut du plot 
                def update_MF3D_plot_active():
                    if MF3D_card.enabled:
                        MF3D_update.active = MF3D_plot_active.value
                    else :
                        MF3D_plot_active.set_value(False)

                #####################
                # ODMR et exportation
                #####################
                
                # Initialisation d'une acquisition ODMR
                def odmr_init():
                    if odmr_card.enabled:
                        # On met à jour les paramètres en fonction des dernières valeurs rentrées (dans le cas ou l'utilisateur n'aurait pas validé)
                        update_signal()
                        pico_update_sampling()

                        disable(odmr_card)
                        disable(export_card)
                        disable(AFG3252_card)
                        disable(acquisition_card)

                        wanted_range_A = AFG.amplitude + abs(AFG.offset) # Calcul du range nécessaire pour que le picoscope puisse détecter l'entièreté du signal
                        
                        # Activation des channels
                        pico.channels['A'] = True
                        pico.channels['B'] = True
                        pico.ranges['A'] = wanted_range_A
                        pico.ranges['B'] = 0.010 # Range du capteur d'intensité

                        # Trigger
                        pico.set_trigger('A',0.1*pico.ranges['A'], 'Falling')

                        # Mise à jour du picoscope
                        pico.update_channels()

                # Mise à jour du plot ODMR
                def odmr_update_plot(data):
                    # Séparation des courbes et du temps
                    data_time = data['A'][0]
                    data_A = data['A'][1]
                    data_B = data['B'][1]

                    with pico_plot:
                        # On garde en mémoire la dernière figure pour pouvoir la fermer une fois la nouvelle créée
                        previous_fig = pico_plot.fig.number
                        # Création de la nouvelle figure et ax
                        fig,ax = plt.subplots()
                        fig.subplots_adjust(right=0.90)
                        # Mise à jour de la figure affichée par l'UI
                        pico_plot.fig = fig
                        # Fermeture de la précédente
                        plt.close(previous_fig)
                        fig.set_size_inches((9,5))
                        ax2 = ax.twinx() # On créé un nouvel ax ayant le même axe des abscisses
                        # Création des nouveaux plots
                        p1, = ax.plot(data_time, data_A, "b-", label='Channel A')
                        p2, = ax2.plot(data_time, data_B, "r-", label='Channel B')
                        
                        # Légende
                        ax.set_xlabel("Temps (s)")
                        ax.set_ylabel("Channel A (V)")
                        ax2.set_ylabel("Channel B (V)")

                        ax.yaxis.label.set_color(p1.get_color())
                        ax2.yaxis.label.set_color(p2.get_color())

                        # On délimite les valeurs des axes
                        ax.set_xlim(0,pico.sample_duration)
                        ax.set_ylim(0.95*(AFG.offset - AFG.amplitude/2), 1.05*((AFG.offset + AFG.amplitude/2))) # Générateur
                        ax2.set_ylim(0.05, 0.010) # Capteur

                        # Couleurs des axes correspondante
                        tkw = dict(size=4, width=1.5)
                        ax.tick_params(axis='y', colors=p1.get_color(), **tkw)
                        ax2.tick_params(axis='y', colors=p2.get_color(), **tkw)
                        ax.tick_params(axis='x', **tkw)

                        ax.legend(handles=[p1,p2], loc="upper left")  

                # Acquisition des données, une seule fois
                def odmr_run_once():
                    if odmr_card.enabled and odmr_once_button.enabled:
                        # Initialisation
                        odmr_init()

                        # On allume le générateur, récupère les données, puis on l'arrête
                        AFG.set_output(True)
                        data = pico.get_data_block()                    
                        AFG.set_output(False)
                        # Mise à jour du plot
                        odmr_update_plot(data)

                        # Réactivation de l'interface
                        enable(odmr_card)
                        enable(export_card)
                        enable(acquisition_card)
                        enable(AFG3252_card)

                # Permet de lancer/arrêter l'acquisition continue
                def odmr_run_control():
                    if odmr_card.enabled and odmr_button.enabled:
                        if odmr_button.text == "Run":
                            # Cas du lancement

                            # Initialisation
                            odmr_init()

                            # Mise à jour de l'UI
                            enable(odmr_card)
                            disable(odmr_once_button)
                            odmr_button.set_text("Stop")

                            # On active le générateur et on lance la routine de mise à jour (Cf plus bas)
                            AFG.set_output(True)
                            ODMR_update.active = True
                        else:
                            # Cas de la mise en pause

                            # On arrête la routine et le générateur
                            ODMR_update.active = False
                            AFG.set_output(False)

                            # Mise à jour de l'UI
                            enable(odmr_once_button)
                            odmr_button.set_text("Run")
                            enable(export_card)
                            enable(acquisition_card)
                            enable(AFG3252_card)

                # Fonction exécutée par la routine de mise à jour toutes les x secondes, pour une acquisition continue
                def odmr_run():
                    # On récupère les données et on met à jour le plot
                    data = pico.get_data_block()                    
                    odmr_update_plot(data)



                # Permet d'exporter le graphe dans le format donné
                def export_plot(e: ClickEventArguments):
                    # e : permet de stocker les informations de l'event de click, notamment l'ID du bouton cliqué
                    if export_card.enabled:
                        
                        # On récupère le dossier d'exports 
                        export_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../exports/'))
                        time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S") #date actuelle pour différencier les fichiers

                        if (e.sender.id == export_png.id): # Exportation PNG
                            exported_file_name = time + "__odmr.png" # nom du fichier
                            file_to_export = os.path.normpath(export_dir + "/" + exported_file_name) # chemin du fichier
                            with pico_plot:
                                plt.savefig(file_to_export) # exportation en png du plot

                        elif (e.sender.id == export_tpng.id): # Exportation PNG Transparent
                            exported_file_name = time + "__odmr.png" # nom du fichier
                            file_to_export = os.path.normpath(export_dir + "/" + exported_file_name) # chemin du fichier
                            with pico_plot:
                                plt.savefig(file_to_export, transparent=True) # exportation en png transparent du plot

                        elif (e.sender.id == export_csv.id): # Exportation CSV
                            exported_file_name = time + "__odmr.csv" # nom du fichier
                            file_to_export = os.path.normpath(export_dir + "/" + exported_file_name) # chemin du fichier
                            with pico_plot:
                                fig = pico_plot.fig
                                # On sépare les ax de chaque channel
                                ax = fig.axes[0]
                                ax2 = fig.axes[1]
                                
                                # On récupère les données correspondantes
                                line = ax.lines[0]
                                line2 = ax2.lines[0]
                                datax = line.get_xdata()
                                datay = line.get_ydata()
                                datay2 = line2.get_ydata()
                            
                            # Construction du fichier csv
                            data_file_str = ""  
                            data_file_str += ("Date : " + str(time) + "\n") # Timestamp
                            data_file_str += ("Temps (s) ; Channel A (V); Channel B (V)\n") # Titre colonnes
                            for i in range(len(datax)): # Construction colonnes
                                data_file_str += (str(datax[i]) + ";" +str(datay[i]) + ";" + str(datay2[i]) + "\n")

                            data_file = open(file_to_export, 'x') # Ecriture du fichier
                            data_file.write(data_file_str)

                            data_file.close()

                        # Affichage d'un lien vers le fichier exporté (ui.open() ne permet pas d'ouvrir dans un nouvel onglet, et ferme la page pico)
                        export_links.clear()
                        with export_links:
                            ui.link("Fichier exporté : {}".format(exported_file_name), "/exports/" + exported_file_name, new_tab=True)

                ####################
                # Création du layout
                ####################

                ###
                # Partie haute (Init, Acqui, Gen)
                ###
                with ui.row():

                    ###
                    # Initialisation picoscope et générateur
                    ###
                    with ui.card(): 
                        ui.label("Initialisation").classes("text-h6")
                        with ui.row():
                            with ui.column():
                                ui.label("Picoscope").classes("text-subtitle2")
                                pico_connect_button = ui.button('Connect', on_click=init_pico)
                                enable(pico_connect_button)
                                pico_disconnect_button = ui.button('Disconnect', on_click=disconnect_pico)
                                disable(pico_disconnect_button)
                            with ui.column():
                                ui.label("Générateur de signal AFG3252").classes("text-subtitle2")
                                afg_connect_button = ui.button('Connect', on_click=afg_connect)
                                enable(afg_connect_button)
                                afg_disconnect_button = ui.button('Disconnect', on_click=afg_disconnect)
                                disable(afg_disconnect_button)
                    
                    ###
                    # Paramètre du générateur
                    ###
                    with ui.card() as AFG3252_card:
                        ui.label("Générateur de signal").classes("text-h6")
                        with ui.row():
                            amplitude_number = ui.number(label="Amplitude PeakToPeak (V)", value=0, format="%.3f")
                            offset_number = ui.number(label="Offset (V)", value=0, format="%.3f")
                            frequency_number = ui.number(label="Fréquence (Hz)", value=1, format="%.2f")
                        with ui.row():
                            ui.button("Valider", on_click=update_signal)
                            ui.label("Fréquences correspondantes :")
                            with ui.column():
                                min_freq_label = ui.label("Min : -- Hz")
                                max_freq_label = ui.label("Max : -- Hz")
                    
                    ###
                    # Paramètres d'acquisition
                    ###
                    with ui.card() as acquisition_card:
                        ui.label("Paramètres d'acquisition").classes("text-h6")
                        with ui.row():
                            nosamples_number = ui.number(label = "Nombre de points", value=1000)
                            noperiodes_number = ui.number(label = "Nombre de périodes à afficher", value=1)
                        ui.button("Valider", on_click=pico_update_sampling)
                    
                    disable(AFG3252_card)
                    disable(acquisition_card)

                ###
                # Partie centrale : ODMR et MF3D
                ###
                with ui.row():
                    with ui.column():
                        ###
                        # Plot ODMR 
                        ###
                        with ui.card() as pico_card:
                            ui.label("ODMR").classes("text-h6")
                            with ui.plot(close=False, figsize=(9,5)) as pico_plot:
                                pass

                        with ui.row():
                            ###
                            # Contrôle du lancement/pause d'une acquisition unique/continue
                            ###
                            with ui.card() as odmr_card:
                                ui.label("Contrôle").classes("text-h6")
                                with ui.column():
                                    odmr_once_button = ui.button("Run Once", on_click=odmr_run_once)
                                    odmr_button = ui.button("Run", on_click=odmr_run_control)
                                    disable(odmr_once_button)
                                    disable(odmr_button)
                            ###
                            # Exportation des courbes
                            ###
                            with ui.card() as export_card:
                                ui.label("Exportation").classes("text-h6")
                                with ui.column():
                                    with ui.menu() as export_menu:
                                        export_png = ui.menu_item('PNG',  export_plot)
                                        export_tpng = ui.menu_item('Transparent PNG', export_plot)
                                        export_csv = ui.menu_item('CSV', export_plot)
                                        ui.separator()
                                        ui.menu_item('Retour', export_menu.close)
                                    ui.button('Exporter le graphe', on_click=export_menu.open)
                                    with ui.column() as export_links:
                                        pass
                        disable(odmr_card)
                        disable(export_card)
                        disable(pico_card)

                    ###
                    # Plot MF3D
                    ###
                    with ui.card() as MF3D_card:
                        disable(MF3D_card)
                        ui.label("MF3D").classes("text-h6")
                        with ui.row():
                            MF3D_plot_type_checkbox = ui.checkbox("Activer figures planes", on_change=update_MF3D_plot_type)
                            MF3D_plot_active = ui.checkbox("Actif", on_change=update_MF3D_plot_active)

                        with ui.plot(close=False, figsize=(5,7)) as MF3D_plot_context:
                            global MF3D_plot
                            MF3D_plot = open_MF3D_plot(fig=MF3D_plot_context.fig, multi=False)

                #######################################
                # Divers utilitaires pour l'UI
                #######################################

                # Routines de mise à jour des plots
                MF3D_update = ui.timer(MF3D_simple_timer, update_MF3D_plot, active=False)
                ODMR_update = ui.timer(ODMR_timer, odmr_run, active=False)
                
                # Lors de la déconnexion de l'utilisateur (page fermée)
                def on_disconnect():
                    ODMR_update.active = False
                    MF3D_update.active = False

                    if 'AFG' in globals(): # Si générateur connecté
                        AFG.close()
                    if 'pico' in globals(): # Si picoscope connecté
                        pico.ps.close()
                    if MF3D_card.enabled:
                        MF3D_plot.close()

                # On règle l'app pour qu'elle exécute on_disconnect lorsqu'un utilisateur ferme la page, pour libérer la connexion à l'arduino
                app.on_disconnect(on_disconnect)