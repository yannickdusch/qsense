#########################################
#  QSense | main.py
#########################################
#
# Ce fichier permet de lancer le GUI
# Il importe les différentes pages, rend le fichier resources accessible, puis rajoute toutes les pages à l'UI et le lance
#

from nicegui import ui, app
from app.pages.home import create_homepage
from app.pages.pico_ui import create_pico_ui
import os

abs_file_path = os.path.abspath(__file__) # On récupère le chemin absolu du fichier actuel
main_dir = os.path.dirname(abs_file_path) # On récupère le dossier racine de la web app
resources_dir = os.path.join(main_dir, 'app/resources') # On se déplace jusqu'à resources en s'affranchissant du système de fichiers
app.add_static_files('/resources', resources_dir) # On rajoute le dossier resources à l'application, pour qu'il soit accessible depuis /resources et qu'on puisse charger les images (pour ./app/pages/home.py)

create_homepage() # On créé la page d'accueil définie dans /app/pages/home.py

create_pico_ui() # On créé les autres pages de l'UI (Les pages ne sont exécutés que lorsqu'un utilisateur est dessus, grâce aux @ui.page)

# Lancement de l'UI
ui.run()