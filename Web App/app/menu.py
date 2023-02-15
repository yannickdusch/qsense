#########################################
#  QSense | menu.py
#########################################
#
# Ce fichier permet de définir le menu, situé en haut à droite, dans le header, et affiché sur chaque page
# Pour ajouter une page, il suffit de rajouter un lien avec le titre et la page correspondante
#

from nicegui import ui

def menu():
    ui.link('Accueil', '/').classes(replace='text-white text-h5')
    ui.link('Picoscope', '/pico').classes(replace='text-white text-h5')
    ui.link('PulseBlaster', '/pulse').classes(replace="text-white text-h5")
    ui.link('ODMR', '/odmr').classes(replace="text-white text-h5")
    ui.link('Rabi', '/rabi').classes(replace="text-white text-h5")