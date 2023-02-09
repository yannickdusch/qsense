import json
import os

abs_file_path = os.path.abspath(__file__) # On récupère le chemin absolu du fichier actuel
app_dir = os.path.dirname(abs_file_path) # On récupère le dossier app
settings_path  = os.path.join(app_dir, "settings.json")
with open(settings_path) as file:
    settings = json.load(file)

def get_setting(page):
    try:
        value = settings[page]
    except :
        return None
    else:
        return value