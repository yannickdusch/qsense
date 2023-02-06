#########################################
#  QSense | odmr.py
#########################################
#
#
#

from matplotlib import pyplot as plt
from nicegui import ui, app
from ..theme import frame
from .subscripts import MF3D
from serial import SerialException

def create_odmr_ui():

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

    @ui.page("/odmr")
    def odmr_ui():
        with frame("ODMR"):

            error = Error()

            ##########################
            # Agilent Signal Generator
            ##########################
            
            ###########
            # MF3D Plot
            ###########

            # Permet de créer un MF3D plot, en prenant en compte la possibilité d'une erreur de connexion
            def open_MF3D_plot(fig, multi):
                try :
                    # Connexion au MV2
                    plot = MF3D.MF3D(fig, multi=multi)
                except SerialException as serial_err:
                    error.show_error("Impossible de se connecter au MV2", serial_err)
                    return None
                else :
                    enable(MF3D_card)
                    return plot

            def update_MF3D_plot_type():
                global MF3D_plot
                MF3D_plot_active.set_value(False)
                MF3D_update.active = False

                if MF3D_plot_type_checkbox.value:
                    MF3D_update.interval = 1
                    with MF3D_plot_context:
                        MF3D_plot.close()
                        MF3D_plot = open_MF3D_plot(fig=MF3D_plot_context.fig, multi=True)
                else:
                    MF3D_update.interval = 0.5
                    with MF3D_plot_context:
                        MF3D_plot.close()
                        MF3D_plot = open_MF3D_plot(fig=MF3D_plot_context.fig, multi=False)
                        
            def update_MF3D_plot():
                global MF3D_plot
                if MF3D_card.enabled:
                    with MF3D_plot_context:
                        MF3D_plot.animate()

            def update_MF3D_plot_active():
                if MF3D_card.enabled:
                    MF3D_update.active = MF3D_plot_active.value
                else :
                    MF3D_plot_active.set_value(False)

            with ui.card() as MF3D_card:
                disable(MF3D_card)

                ui.label("MF3D").classes("text-h6")
                with ui.row():
                    MF3D_plot_type_checkbox = ui.checkbox("Activer figures planes", on_change=update_MF3D_plot_type)
                    MF3D_plot_active = ui.checkbox("Actif", on_change=update_MF3D_plot_active)

                with ui.plot(close=False, figsize=(5,5)) as MF3D_plot_context:
                    global MF3D_plot
                    MF3D_plot = open_MF3D_plot(fig=MF3D_plot_context.fig, multi=False)

                
            MF3D_update = ui.timer(0.5, update_MF3D_plot, active=False)

            # Lors de la déconnexion de l'utilisateur (page fermée)
            def on_disconnect():
                global MF3D_plot
                if MF3D_card.enabled:
                    MF3D_plot.close()

            # On règle l'app pour qu'elle exécute on_disconnect lorsqu'un utilisateur ferme la page, pour libérer la connexion à l'arduino
            app.on_disconnect(on_disconnect)