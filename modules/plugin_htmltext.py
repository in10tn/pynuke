#!/usr/bin/env python
# encoding: utf-8

from applications.init.modules.plugin_ckeditor import CKEditor
from gluon import *
import datetime
import db_pynuke
import db_pagemodules


class Plugin_HTMLText(object):
    def __init__(self):
        from gluon.globals import current
        self.db = current.db
        self.T = current.T
        self.auth = current.auth
        self.PyUtils = db_pynuke.PyNuke.Utils()
        self.dict_default_helps = {'render_type': 'This is the render type of the module'}
        self.dict_default_values = {'render_type': 'HTML'}

    def define_tables(self):
        T = self.T
        db = self.db
        auth = self.auth
        signature = db_pynuke.PyNuke().def_fields_signature()
        ckeditor = ckeditor = CKEditor(db)
        db.define_table('htmltext',
                    Field('moduleid', db.modules, readable=False, 
                          writable=False, ondelete='CASCADE'),
                    Field('content', 'text', widget=ckeditor.widget),
                    Field('version', 'integer', writable=False),
                    Field('stateid', db.workflowstates, default=1, writable=False),
                    Field('ispublished', 'boolean', default=True,writable=False,readable=False),
                    signature,
                    format='%(moduleid)s',
                    plural='htmltext',
                    singular='htmltext',
                )

        db.define_table('htmltextlog',
                Field('content','text',widget=ckeditor.widget),
                Field('version','integer'),
                Field('stateid',db.workflowstates),
                Field('ispublished','boolean'),
                signature,
                format='%(id)s',
                plural='htmltextlog',
                singular='htmltextlog',
                )
        return

    def get_next_version_number(self,moduleid):
        db = self.db
        result = 1
        query = db.htmltext.moduleid == moduleid
        orderby = ~db.htmltext.version
        lastrecord_htmltext = db(query).select(orderby=orderby).first()
        if lastrecord_htmltext != None:
            result = lastrecord_htmltext['version'] + 1
            if result == None:
                result = 1
        return result

    def get_last_html_by_version_number(self,moduleid):

        db = self.db
        result = 'Your content goes here'
        lastrecord_htmltext = db(db.htmltext.moduleid==moduleid).select(orderby=~db.htmltext.version).first()        
        if lastrecord_htmltext != None:
            result = lastrecord_htmltext['content']
            if result == None:
                result = 'Your content goes here'
        return result

    def get_versions(self, moduleid):
        db = self.db
        versions = db(db.htmltext.moduleid==moduleid).select(orderby=~db.htmltext.version)                        
        return versions

    def render_form_settings(self, pagemoduleid, modsettings, dict_default_helps):
        db = self.db
        T = self.T
#        #leer los valores actuales de configuracion para asignar por defecto
#        modsettings, dict_defaults_help = self.read_modsettings(pagemoduleid)

        #construir formulario de configuración para incrustar en msettings

        formsettings = SQLFORM.factory(Field('pagemoduleid',db.pagemodules,label='pagemoduleid',writable=False,default=pagemoduleid),
           Field('render_type','string',label='Render Type',
                 default=modsettings['render_type'],
                 requires=IS_IN_SET(('HTML','TEXT','MARKMIN')),
                 comment=dict_default_helps['render_type'],
                 widget=SQLFORM.widgets.radio.widget),
           #por cada campo boolean (checkbox) agregar abajo su equivalente oculto con el valor 'F'
           #Esto es por que los checkboxes si no están seleccionados no se envían. Al poner el campo oculto
           #con el mismo nombre, cogerá este si el checkbox no está seleccionado.
           #http://stackoverflow.com/questions/476426/submit-an-html-form-with-empty-checkboxes
           #hidden=dict(captcha='F')
            )
        return formsettings