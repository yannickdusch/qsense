#########################################
#  QSense | login.py
#########################################
#
# Ce fichier permet de créer la page d'authentification, et de vérifier si un utilisateur est connecté ou non 
#

import uuid
import hashlib
from nicegui import ui
from fastapi import Request
from fastapi.responses import RedirectResponse

from ..utils import Error
from ..settings import get_setting

session_info = {} # Permet de stocker les informations sur l'utilisateur connecté (un seul possible, dans ce cas) ; s'il est vide, personne n'est connecté

# Récupération des paramètres
settings = get_setting('login')
login_required =settings['login_required']
admin_hash = settings['admin_pass_hash']

# Permet de vérifier si un utilisateur (identifié par la requête) est connecté.
# Cette fonction est appelé à chaque création de page, pour voir s'il faut renvoyer l'utilisateur sur la page de login (Cf pico_ui.py, odmr.py, etc...)
def is_authenticated(request: Request):
    if login_required:
        # On récupère l'uuid de l'utilisateur (stocké dans sa session) (get() renvoie le deuxième arg (ici "None"), si 'id' n'existe pas dans session)
        # Puis on regarde si cette id est présente dans session_info
        return (request.session.get('id', 'None') in session_info)
    else: # Si l'authentification est désactivée, on considère l'utilisateur toujours connecté
        return True

# Permet de récupérer le nom sous lequel un utilisateur est connecté
# Utilisée par theme.py, pour afficher "Bienvenue, <username>" dans le footer
def get_username(request:Request):
    return session_info.get(request.session.get('id', 'None'), '')

# Permet de hasher un mot de passe et de renvoyer son hash
def get_password_hash(password):
    hashed_pass = hashlib.sha256(password.encode())
    return hashed_pass.hexdigest()

# Permet de déconnecter manuellement un utilisateur (Cf bouton de déconnexion dans le footer)
def disconnect(request: Request):
    if is_authenticated(request): 
        # Si l'utilisateur est bien connecté, alors 'id' existe dans la session
        # On la récupère donc, puis on l'enlève de session_info
        # (Puisqu'ici, un seul utilisateur peut être connecté simultanément, on pourrait tout aussi bien réinitialiser session_info à zéro)
        session_info.pop(request.session['id'])
        ui.open('./') # Redirection accueil

##################
# Création de l'UI
##################
def create_login_page():
    @ui.page('/login')
    def login_page(request: Request):
        if is_authenticated(request): # Inversement aux autres pages, c'est si l'utilisateur est connecté qu'on doit le renvoyer à l'accueil
            return RedirectResponse('./')
        else :
            from ..theme import frame # On importe frame que ici, pour éviter les problèmes de mutual import entre theme et login
            with frame("Authentification", request):
                error = Error()
                
                # Permet de vérifier si personne n'est connecté, et de connecter l'utilisateur si ce n'est pas le cas
                def try_login(session_id: str, username_value: str):

                    if username.value != "": # Vérification du nom d'utilisateur
                        if len(session_info) == 0: # Si personne connecté
                            session_info[session_id] = username_value
                            ui.open('./')
                        else: # Si quelqu'un connecté
                            logged_in_username = list(session_info.items())[0][1] # On récupère son nom
                            error.show_error("Impossible de se connecter", "%s est déjà connecté à l'interface, réessayez plus tard" % logged_in_username)
                    else:
                        error.show_error("Impossible de se connecter", "Veuillez entrer un nom d'utilisateur")
                
                # Permet, avec l'accès admin, de réinitialiser session_info (si quelqu'un est déjà connecté)
                def try_clear_sessions(password):
                    global session_info
                    if get_password_hash(password) == admin_hash: # vérification mdp
                        session_info = {} 
                        ui.notify("Sessions cleared")
                        password_input.set_value("")
                    else :
                        ui.notify("Mot de passe invalide")
                
                # Bloc exécuté lors de la connexion : si aucune ID attribué, on en rajoute une au dict session
                if not 'id' in request.session:
                    request.session['id'] = str(uuid.uuid4())

                ####################
                # Création du layout
                ####################
                
                with ui.column().classes('absolute-center').style("width:500px"):
                    with ui.card().classes("full-width"):
                        ui.label("Authentification").classes("text-h5")
                        username = ui.input("Nom d'utilisateur")
                        ui.button('Log in', on_click=lambda: try_login(request.session['id'], username.value))
                    
                    ui.separator()

                    with ui.card().classes("full-width"):
                        ui.label("Accès administrateur").classes("text-h5")
                        password_input = ui.input('Mot de passe').classes('w-full').props('type=password')
                        ui.button('Clear sessions', on_click=lambda: try_clear_sessions(password_input.value))
