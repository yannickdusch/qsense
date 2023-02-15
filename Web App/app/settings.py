#########################################
#  QSense | settings.py
#########################################
#
# Ce fichier permet d'ouvrir le fichier contenant les paramètres, de les récupérer, et de les mettre à disposition
# des autres modules via get_setting
#

import json
import os

abs_file_path = os.path.abspath(__file__) # On récupère le chemin absolu du fichier actuel
app_dir = os.path.dirname(abs_file_path) # On récupère le dossier app
settings_path  = os.path.join(app_dir, "settings.json") # On récupère le chemin du fichier settings
with open(settings_path) as file: # On stocke le contenu JSON sous forme de dict python
    settings = json.load(file)

# Permet aux autres pages d'accéder à un ensemble de paramètres
def get_setting(page):
    try:
        value = settings[page]
    except :
        return None
    else:
        return value