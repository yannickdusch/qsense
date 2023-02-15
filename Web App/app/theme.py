#########################################
#  QSense | theme.py
#########################################
#
# Ce fichier permet de définir le thème qui sera appliqué à chaque page
# Il définit le header, sur lequel on trouve le nom de l'app, de la page, et le menu (voir menu.py)
# Il définit aussi le footer, sur lequel on trouve le bouton de déconnexion si jamais l'utilisateur est connecté
# Chaque page fera appel à with frame(navtitle, request):, navtitle étant le nom de page que l'on souhaite voir affiché sur le header, 
# et request permettant de vérifier si l'utilisateur est connecté, et si oui, sous quel nom
#

from contextlib import contextmanager

from fastapi.requests import Request
from .menu import menu
from nicegui import ui, app
from .pages.login import is_authenticated
from .pages.login import get_username
from .pages.login import disconnect
from .pages.login import login_required

@contextmanager
def frame(navtitle: str, request: Request):
    # Header
    with ui.header().classes('justify-between text-white items-center').style('background-color: #3874c8').props('elevated'):
        ui.link('Qsense Web App', '/').classes(replace='text-white font-bold text-h6')
        ui.label(navtitle).classes("text-h5") # Titre de la page
        with ui.row():
            menu() # Création du menu
    # Footer
    with ui.footer().classes('justify-end text-white items-center').style('background-color: #3874c8').props('elevated'):
        # On affiche le contenu seulement si l'utilisateur est connecté
        if login_required and is_authenticated(request):
            ui.label("Bienvenue, %s |" % get_username(request))
            ui.button("Se déconnecter", on_click=lambda: disconnect(request))
            ui.button("Eteindre l'UI", on_click=app.shutdown)
    yield