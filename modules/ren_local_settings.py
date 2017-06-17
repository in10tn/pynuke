# -*- coding: utf-8 -*-
# Esto es para que no tenga que ir reiniciando el servidor web en cada cambio en los módulos 
# Fuente : http://groups.google.com/group/web2py/browse_thread/thread/130f41915be5b91c
# En entorno de produccion estas opciones no deberían estar activas, podría probarse a hacer una opción
# Desde la versión 2.0.9 esto no funciona    
from gluon.custom_import import track_changes; track_changes(True)
from gluon.storage import Storage
settings = Storage()
settings.migrate = True
settings.database_uri = 'sqlite://storage.sqlite4'