# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#debido a que cuando iniciamos el portal por primera vez, puede ser necesario
#crear la tabla en el fichero db.py que se ejecuta antes, aquí hemos de comprobar
#que la tabla no existe antes de intentar crearla

if not db.tables().count('htmltext'):
    plugin_htmltext.Plugin_HTMLText().define_tables()