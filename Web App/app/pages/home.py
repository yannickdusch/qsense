#########################################
#  QSense | home.py
#########################################
#
# Ce fichier permet la création de l'UI de la page d'accueil avec create_homepage()
# Cette page permet d'afficher les différentes expériences sous forme de carte, avec un titre, une description, une image, et un bouton faisant le lien avec la page correspondante
# Un exemple pour ajouter une nouvelle page est présent dans la documentation
#

from nicegui import ui
from nicegui.events import ClickEventArguments
from fastapi.responses import RedirectResponse
from fastapi.requests import Request

from ..theme import frame
from .login import is_authenticated

def create_home_page():
    @ui.page('/') # Quand l'utilisateur est à la racine, on exécute la fonction suivante
    def home_page(request: Request):
        if not is_authenticated(request):
            return RedirectResponse('/login')
        else :
            # Permet de gérer les events lorsque l'utilisateur clique sur l'une des cases
            def button_handler(e: ClickEventArguments):
                button_link = list_cards[e.sender.id] # On récupère le lien depuis la carte correspondante
                e.client.open(button_link) # On passe par le socket e.client car ui.open() seul ouvrirait la page pour tous les utilisateurs présents sur le site

            with frame('Accueil', request):
                width = "width:300px"
                height = "height:400px"
                with ui.row().style(height):
                    # On rajoute chaque case correspondant à chaque expérience
                    with ui.card().classes("full-height").style(width):
                        with ui.column().classes("items-center"): 
                            ui.label('Contrôle Picoscope').classes('text-h6') # Titre de la case
                            ui.separator()
                            ui.image('/resources/pico.png') 
                            ui.label('Contrôle des paramètres et du générateur interne du picoscope, visualisation des channels, ...').classes('text-center') # Description de la case
                            pico_button = ui.button("Voir", on_click=button_handler)

                    with ui.card().classes("full-height").style(width):
                        with ui.column().classes("items-center"): 
                            ui.label('Contrôle PulseBlaster').classes('text-h6') # Titre de la case
                            ui.separator()
                            ui.image('/resources/pulse.png').classes("full-width")
                            ui.label('Contrôle du PulseBlaster et création/exécution de séquences').classes('text-center') # Description de la case
                            pulse_button = ui.button("Voir", on_click=button_handler)
                    
                    with ui.card().classes("full-height").style(width):
                        with ui.column().classes("items-center"):
                            ui.label('ODMR').classes('text-h6')
                            ui.separator()
                            ui.image('/resources/odmr.png').classes("full-width")
                            ui.label("Contrôle et visualisation d'une expérience simple d'ODMR").classes('text-center')
                            odmr_button = ui.button("Voir", on_click=button_handler)
                    with ui.card().classes("full-height").style(width):
                        with ui.column().classes("items-center"):
                            ui.label('Rabi').classes('text-h6')
                            ui.separator()
                            ui.image('/resources/rabi.png').classes("full-width")
                            ui.label("Description Rabi").classes('text-center')
                            rabi_button = ui.button("Voir", on_click=button_handler)

            # On relie ici les ID et les liens correspondant pour chaque carte : cela permettra d'identifier de quelle carte provient l'event de click
            # (L'ID est unique p,our chaque objet de l'UI (mais elle peut changer si l'on modifie le layout))
            list_cards = {
                pico_button.id : '/pico',
                odmr_button.id : '/odmr',
                pulse_button.id : '/pulse',
                rabi_button.id : '/rabi'
            }