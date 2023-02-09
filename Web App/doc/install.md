# Installation
## Drivers
---
L'interfaçage avec les différents appareils utilisés nécessite l'installation de différent drivers pour communiquer avec chaque appareil :
## Picoscope 
Le picoscope utilisé est le **PicoScope 5444D**. Pour pouvoir l'utiliser avec python, il faut tout d'abord installer les drivers fournis par Picotech.  
  
Sur Windows ou Mac, il faut installer **PicoSDK**, disponible sur [le site de Picotech](https://www.picotech.com/downloads) (Picoscope 5000 Series > Picoscope 5444D, puis choisir la version adaptée)  
  
Sur Linux, le driver seul peut être installé via :
 
> sudo apt-get install libps5000a

## VISA
Le standard VISA permet de communiquer avec de nombreux appareils de mesure l'utilisant. L'interface utilise la library Python PyVISA (voir plus bas), qui permet de communiquer simplement avec ces appareils. Elle nécessite néanmoins l'installation d'une implémentation de VISA telle que celle de National Instrument, qu'il faut donc installer depuis [leur site officiel](https://www.ni.com/fr-fr/support/downloads/drivers/download.ni-visa.html#460225).

  
## Interface
---
## NiceGUI
Cette interface se base sur le framework web python [NiceGUI](https://github.com/zauberzeug/nicegui), lui même basé sur [FastAPI](https://fastapi.tiangolo.com/).  
En supposant que Python 3.7 ait déjà été installé, NiceGUI peut directement être installé via PyPI :

> pip install nicegui  

La version utilisée pour l'interface à l'heure de l'écriture de ce guide est [NiceGUI v1.1.5](https://github.com/zauberzeug/nicegui/releases/tag/v1.1.5) (le 02/02/2023)

## Pico-python

L'implémentation du picoscope en python se fait à l'aide de la library [Pico-Python](https://github.com/colinoflynn/pico-python), qui permet une utilisation simplifiée, par rapport au [wrapper officiel](https://github.com/picotech/picosdk-python-wrappers). La library peut être installée via PyPI :

> pip install picoscope

## PyVISA
La library Python [PyVISA](https://pyvisa.readthedocs.io/en/latest/index.html) permet de communiquer avec les appareils VISA, en supposant qu'une installation de VISA soit déjà présente sur l'ordinateur (voir plus haut). La library peut également être installée via PyPI :

> pip install pyvisa

## Autres libraries Python
L'interface nécessite également quelques librairies Python courantes, telles que Numpy ou Matplotlib, que l'on peut installer, si elles ne sont pas déjà présentes, via :

> pip install matplotlib numpy 


# Lancement de l'UI

Une fois les dépendances installées, on peut démarrer l'UI simplement en exécutant `main.py` :

> python3 main.py

NiceGUI créé alors un serveur interne qui devient accessible localement depuis [https://127.0.0.1:8080/](https://127.0.0.1:8080/)

### Note :
Chaque page créée par l'UI (en utilisant la directive `@ui.page`), créé une session locale pour chaque utilisateur, qui ne verra donc pas la même page qu'un autre. Il faut donc faire attention à ne pas "superposer" les accès, puisqu'une personne connecté sur une page utilisant un appareil, empêchera tout autre personne d'utiliser le même appareil. Il faut, en particulier, penser à fermer toutes les connexions lorsqu'un utilisateur se déconnecte d'une page, pour éviter de bloquer tous les utilisateurs suivants.