from nicegui import ui

#################################
# Classes/Fonctions utilitaires :
#################################

# Permet de stocker une erreur et un popup qui lui correspondant, pour le faire apparaître si nécessaire
class Error():
    def __init__(self):
    # Création du popup d'erreur
        with ui.dialog() as self.popup:
            with ui.card():
                ui.label("Une erreur est survenue").classes("font-bold text-h6")
                self.label_message = ui.label("Unknown Error")
                self.label_error = ui.label("Unknown")
                ui.button('Fermer', on_click=self.popup.close)

    def show_error(self, error_message, error):
        # On modifie les labels et on affiche la popup
        self.label_message.set_text(error_message)
        self.label_error.set_text(str(error))
        self.popup.open()

# Marquer un objet comme "désactivé" (classe Quasar "disabled" + booléen)
def disable(object):
    object.classes("disabled")
    object.enabled = False

# Marquer un ojet comme "activé"
def enable(object):
    object.classes(remove="disabled")
    object.enabled = True
