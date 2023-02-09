#########################################
#  QSense | theme.py
#########################################
#
# Ce fichier permet de définir le thème qui sera appliqué à chaque page
# Il définit le header, sur lequel on trouve le nom de l'app, de la page, et le menu (voir menu.py)
# Chaque page fera appel à with frame(navtitle):, navtitle étant le nom de page que l'on souhaite voir affiché sur le header 
#

from contextlib import contextmanager

from fastapi.requests import Request
from .menu import menu
from nicegui import ui, app
from .pages.login import is_authenticated
from .pages.login import get_username
from .pages.login import disconnect
@contextmanager
def frame(navtitle: str, request: Request):
    with ui.header().classes('justify-between text-white items-center').style('background-color: #3874c8').props('elevated'):
        ui.link('Qsense Web App', '/').classes(replace='text-white font-bold text-h6')
        ui.label(navtitle).classes("text-h5") # Titre de la page
        with ui.row():
            menu() # Création du menu

    with ui.footer().classes('justify-end text-white items-center').style('background-color: #3874c8').props('elevated'):
        if is_authenticated(request):
            ui.label("Bienvenue, %s |" % get_username(request))
            ui.button("Se déconnecter", on_click=lambda: disconnect(request))
            ui.button("Eteindre l'UI", on_click=app.shutdown)
    yield