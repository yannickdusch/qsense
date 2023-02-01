#########################################
#  QSense | home.py
#########################################
#
# Ce fichier permet la création de l'UI de la page d'accueil avec create_homepage()
# Cette page permet d'afficher les différentes expériences sous forme de carte, avec un titre, une description, une image, et un bouton faisant le lien avec la page correspondante
# Un exemple pour ajouter une nouvelle page est présent dans la documentation
#

from ..theme import frame
from nicegui import ui
from nicegui.events import ClickEventArguments

def create_homepage():
    @ui.page('/') # Quand l'utilisateur est à la racine, on exécute la fonction suivante
    def home_page():
        # Permet de gérer les events lorsque l'utilisateur passe la souris sur, en dehors de, ou clique sur l'une des cases
        def button_handler(e: ClickEventArguments):
            button_link = list_cards[e.sender.id] # On récupère le lien depuis la carte correspondante
            e.client.open(button_link) # On passe par le socket e.client car ui.open() seul ouvrirait la page pour tous les utilisateurs présents sur le site

        with frame('Accueil'):
                with ui.row():
                    # On rajoute chaque case correspondant à chaque expérience
                    with ui.card() as pico_link:
                        with ui.column().classes("items-center"): 
                            ui.label('Contrôle Picoscope').classes('text-h6') # Titre de la case
                            ui.separator()
                            ui.image('/resources/pico.png') 
                            ui.label('Contrôle des paramètres et du générateur interne du picoscope, visualisation des channels, ...').classes('text-center').style("width:300px") # Description de la case
                            pico_button = ui.button("Voir", on_click=button_handler)
        # On relie ici les ID et les liens correspondant pour chaque carte : cela permettra d'identifier de quelle carte provient l'event de click
        # (L'ID est unique pour chaque objet de l'UI (mais elle peut changer si l'on modifie le layout))
        list_cards = {
            pico_button.id : '/pico'
        }