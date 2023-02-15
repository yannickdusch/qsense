#########################################
#  QSense | rabi.py
#########################################
#
# WIP
#

from fastapi.requests import Request
from fastapi.responses import RedirectResponse
from nicegui import ui

from ..settings import get_setting
from .login import is_authenticated
from ..theme import frame
from ..utils import Error
from ..utils import enable
from ..utils import disable
from .subscripts.pico import Picoscope
from .subscripts.pulse import Pulse


def create_rabi_ui():

    # Récupération des paramètres
    settings = get_setting('rabi')

    ##################
    # Création de l'UI
    ##################

    @ui.page('/rabi')
    def rabi_ui_page(request: Request):

        if not is_authenticated(request):
            return RedirectResponse('/login')
        else:
            with frame('Expérience de Rabi', request):
                
                error = Error()
                
                ###########
                # Picoscope
                ###########

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

                            enable(pico_disconnect_button)
                            
                            disable(pico_connect_button)

                # Lors de la déconnexion manuelle du picoscope
                def disconnect_pico():
                    if pico_disconnect_button.enabled: 
                        pico.ps.close()
                        ui.notify("Déconnexion effectuée")

                        # Désactivation des éléments de l'UI nécessitant le picoscope
                        disable(pico_disconnect_button)
                        
                        enable(pico_connect_button)

                #################
                # PulseBlasterUSB
                #################

                def pulse_connect():
                    # WIP
                    return
                def pulse_disconnect():
                    # WIP
                    return


                ####################
                # Création du layout
                ####################
                with ui.row():
                    with ui.card(): # Initialisation du picoscope
                        ui.label("Initialisation").classes("text-h6")
                        with ui.row():
                            with ui.column():
                                ui.label("Picoscope").classes("text-subtitle2")
                                pico_connect_button = ui.button('Connect', on_click=init_pico)
                                enable(pico_connect_button)
                                pico_disconnect_button = ui.button('Disconnect', on_click=disconnect_pico)
                                disable(pico_disconnect_button)
                            with ui.column(): # Initialisation du pulseblaster
                                ui.label("PulseBlasterUSB").classes("text-subtitle2")
                                pulse_connect_button = ui.button('Connect', on_click=pulse_connect)
                                enable(pulse_connect_button)
                                pulse_disconnect_button = ui.button('Disconnect', on_click=pulse_disconnect)
                                disable(pulse_disconnect_button)