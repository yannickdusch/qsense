#########################################
#  QSense | main.py
#########################################
#
# Ce fichier permet de lancer le GUI
# Il importe les différentes pages, rend les dossiers resources et exports accessibles, puis rajoute toutes les pages à l'UI et le lance
#
import os
import glob

from starlette.middleware.sessions import SessionMiddleware

from nicegui import ui, app
from app.pages.home import create_home_page
from app.pages.pico_ui import create_pico_ui
from app.pages.odmr import create_odmr_ui
from app.pages.login import create_login_page
from app.pages.pulse_ui import create_pulse_ui
from app.pages.rabi import create_rabi_ui

# Rajoute un middleware pour pouvoir gérer les sessions, Cf. l'exemple d'authentification sur le github de nicegui
app.add_middleware(SessionMiddleware, secret_key='sxx0raOVQlgB6YErA3LG9Xg7TkpWu9oa')

abs_file_path = os.path.abspath(__file__) # On récupère le chemin absolu du fichier actuel
main_dir = os.path.dirname(abs_file_path) # On récupère le dossier racine de la web app
resources_dir = os.path.join(main_dir, 'app/resources') # On se déplace jusqu'à resources
app.add_static_files('/resources', resources_dir) # On rajoute le dossier resources à l'application, pour qu'il soit accessible depuis /resources et qu'on puisse charger les images (pour ./app/pages/home.py)

exports_dir = os.path.join(main_dir, 'app/exports') # On fait de même pour le dossier exports
if not os.path.exists(exports_dir): # Création s'il n'existe pas
    os.mkdir(exports_dir)
app.add_static_files('/exports', exports_dir) # Rendre exports accessible depuis /exports

exported_files_to_remove = glob.glob(exports_dir + "/*")
for file in exported_files_to_remove: # On supprime les fichiers exportés précédemment, s'il y en a, pour éviter qu'ils s'accumulent
    try:
        os.remove(file)
    except OSError as err:
        print("[ERR] Impossible de supprimer le fichier : {}".format(str(file)))
        print(str(err))

create_home_page() # On créé la page d'accueil définie dans /app/pages/home.py
create_login_page()

create_pico_ui() # On créé les autres pages de l'UI (Les pages ne sont exécutés que lorsqu'un utilisateur est dessus, grâce aux @ui.page)
create_odmr_ui()
create_pulse_ui()
create_rabi_ui()

# Lancement de l'UI
ui.run(reload=False)