import uuid
from nicegui import ui
from fastapi import Request
from fastapi.responses import RedirectResponse

from ..utils import Error

session_info = {}
def is_authenticated(request: Request):
    return (request.session.get('id', 'None') in session_info)

def get_username(request:Request):
    return session_info.get(request.session.get('id', 'None'), '')

def disconnect(request: Request):
    if is_authenticated(request):
        session_info.pop(request.session['id'])
        ui.open('./')

def create_login_page():
    @ui.page('/login')
    def login_page(request: Request):
        if is_authenticated(request):
            return RedirectResponse('./')
        else :
            from ..theme import frame
            with frame("Authentification", request):
                error = Error()

                def try_login(session_id: str, username: str):
                    if len(session_info) == 0:
                        session_info[session_id] = username
                        ui.open('./')
                    else:
                        logged_in_username = list(session_info.items())[0][1]
                        error.show_error("Impossible de se connecter", "%s est déjà connecté à l'interface, réessayez plus tard" % logged_in_username)

                request.session['id'] = str(uuid.uuid4())
                with ui.card().classes('absolute-center'):
                    ui.label("Authentification").classes("text-h5")
                    username = ui.input('Username')
                    ui.button('Log in', on_click=lambda: try_login(request.session['id'], username.value))
