#########################################
#  QSense | theme.py
#########################################
#
# Ce fichier permet de définir le thème qui sera appliqué à chaque page
# Il définit le header, sur lequel on trouve le nom de l'app, de la page, et le menu (voir menu.py)
# Chaque page fera appel à with frame(navtitle):, navtitle étant le nom de page que l'on souhaite voir affiché sur le header 
#

from contextlib import contextmanager
from .menu import menu
from nicegui import ui

@contextmanager
def frame(navtitle: str):
    with ui.header().classes('justify-between text-white items-center').style('background-color: #3874c8').props('elevated'):
        ui.link('Qsense Web App', '/').classes(replace='text-white font-bold text-h6')
        ui.label(navtitle).classes("text-h5") # Titre de la page
        with ui.row():
            menu() # Création du menu
    # TODO footer avec connexion user / déconnexion user / shutdown gui / restart gui
    yield