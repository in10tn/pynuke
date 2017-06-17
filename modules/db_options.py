#!/usr/bin/env python
# encoding: utf-8
# Requiere instalar http://pyyaml.org/wiki/PyYAML
from applications.init.modules.plugin_ckeditor import CKEditor
from gluon import *
import yaml
import os.path
import db_pynuke
import db_security, db_packages, db_pages


class Options(object):
    def __init__(self):
        from gluon.globals import current
        self.db = current.db
        self.T = current.T
        self.auth = current.auth
        self.settings = current.settings
        self.clPyPages = db_pynuke.PyNuke.Pages()

    def define_tables(self):
        T = self.T
        db = self.db
        db.define_table('options',
            Field('name', required=True, writable=False,),
            Field('value',"text"),
            format='%(nombre)s',
            plural='Opciones',
            singular='Opción'
                    )
        return

    def show_grid_params(self,view,):
        '''
        Esta función devuelve los valores necesarios para mostrar el Smartgrid
        en el controlador Auxiliares.py
        '''

        maxtextlengths = {'options.id':10,
                          'option.name':50,
                          'option.value':50,
                         }
        deletable = False

        return maxtextlengths, deletable

    def insert_default_options(self):
        db = self.db

        fname = os.path.join(current.request.folder, "modules", "options.yaml")
        config = yaml.load(file(fname, 'r'))

        if config:
            for option in config['web2pynuke_options']:
                db.options.insert(name=option['option_name'],
                                  value=option['option_value'])
            db.commit()
        return

    def get_option(self, option_name):
        T = self.T
        db = self.db
        value = ''
        try:
            option = db(db.options.name == option_name).select(db.options.ALL)
            if option:
                value = option[0].value
            #Si la opción no existe
            else:
                fname = os.path.join(current.request.folder,"modules", 
                                     "options.yaml")
                config = yaml.load(file(fname, 'r'))
                #leemos del fichero options.yaml
                if config:
                    for option in config['web2pynuke_options']:
                        #si existe esa opción
                        if option_name == option:
                            #la insertamos en la base de datos
                            db.options.insert(name=option['option_name'],
                                              value=option['option_value'])
                            db.commit()
                            value = option['option_value']
                            break
        except:
            value = ''
        return value

    def update_option(self, option_name, option_value):
        db = self.db
        db.options.update_or_insert(db.options.name == option_name,
                                    name=option_name,
                                    value=option_value)

    def get_all_options(self):
        T = self.T
        db = self.db

        result = dict()
        for row in db(db.options.id > 0).select(db.options.ALL):
            result[row.name] = row.value

        return result

    def restore_defaults(self):
        '''
            funcion que recupera los valores por defecto de la aplicación
            borra todas las opciones y las vuelve a cargar del fichero options.yaml        
        '''
        db = self.db
        db.options.truncate()
        db.commit()
        self.insert_default_options()
        return;

    def ver(self):
        # options list
        db = self.db
        query = (db.options.id > 0)
        fields = [db.options.id,
                      db.options.name,
                      db.options.value,
                     ]
        maxtextlengths = {'options.id':8,
                          'options.name':90,
                          'options.value':80,
                          }
        table = SQLFORM.grid(query,
                        fields=fields,
                        maxtextlengths=maxtextlengths,
                        orderby=db.options.id,
                        csv=True,
                        searchable=True,
                        create=False,
                        editable=True,
                        details=False,
                        deletable=False,
                        user_signature=True,
                        )
        return table

    def editar(self,option_id):       
        '''
            devuelve un formulario para editar una opción
        '''        
        sepuedeborrar = False
        db=self.db
        record=db.options[option_id]
        return SQLFORM(db.options, record,
                         deletable=sepuedeborrar)

    def form_settings(self):
        '''
            Opciones generales del sitio
        '''

        db = self.db
        T = self.T
        auth = self.auth
        settings = self.settings
        clPyPages = self.clPyPages
        ckeditor = CKEditor(db)
        #leer los valores actuales de configuracion para asignar por defecto
        options, dict_default_helps = self.read_sitesettings()
        #options = self.get_all_options()
        #dict_default_helps = self.default_dicthelps()
        #querystartpage = (db.pages.tree_id == 1) & (db.pages.id > 1)
        usersadmins = db_security.PNSecurity().get_users_from_role(1)
        dictusers = {}
        for u in usersadmins:
            value = str(u.id) + " - " + u.email
            if "username" in u:
                value += " - " + u.username
            dictusers[u.id] = value

        enabled_change_user = False
        if auth.user_id == int(settings.portal_admin):
            enabled_change_user = True

        dict_layouts = db_packages.Packages().get_layouts_available()
        dict_containers = db_packages.Packages().get_layouts_available(2)

        list_pags = clPyPages.get_pages_hierarchical()
        
        result = SQLFORM.factory(Field('plugin_layout_default', db.layouts, 
                                       requires=IS_IN_SET(dict_layouts),
                                       label=T('Layout'),
                                       default=options['plugin_layout_default'],
                                       comment=dict_default_helps['plugin_layout_default']),
                Field('plugin_container_default', db.layouts,
                      requires=IS_IN_SET(dict_containers),
                      label=T('Container'),
                      default=options['plugin_container_default'],
                      comment=dict_default_helps['plugin_container_default']),
                Field('portal_admin','string',label=T('Portal Administrator'),requires=IS_IN_SET(dictusers),default=options['portal_admin'],comment=dict_default_helps['portal_admin'], writable=enabled_change_user),
                Field('img_logo','string',label=T('Image Logo'),default=options['img_logo'],comment=dict_default_helps['img_logo']),
                Field('link_logo','string',label=T('Link Logo'),default=options['link_logo'],comment=dict_default_helps['link_logo']),
                Field('site_title','string',label=T('Title'),default=options['site_title'],comment=dict_default_helps['site_title']),                    
                Field('site_description','string',label=T('Description'),default=options['site_description'],comment=dict_default_helps['site_description']),
                Field('bootstrap_brand','string',label=T('Bootstrap brand'),default=options['bootstrap_brand'],comment=dict_default_helps['bootstrap_brand']),
                Field('author','string',label=T('Author'),default=options['author'],comment=dict_default_helps['author']),
                Field('keywords','text',label=T('Keywords'),default=options['keywords'],comment=dict_default_helps['keywords']),
                Field('generator','string',label=T('Generator'),default=options['generator'],comment=dict_default_helps['generator']),
                Field('copyright','string',label=T('Copyright'),default=options['copyright'],comment=dict_default_helps['copyright']),
                Field('startpageid',db.pages,label=T('Start Page'),requires=IS_IN_SET(list_pags, zero='', multiple=False),default=options['startpageid'],comment=dict_default_helps['startpageid']),
                Field('gmt_offset','string',label=T('GMT offset'),readable=False, writable=False,default=options['gmt_offset'],comment=dict_default_helps['gmt_offset']),
                Field('google_meta','string',label=T('google_meta'),default=options['google_meta'],writable=False, readable=False,comment=dict_default_helps['google_meta']),
                Field('google_analytics_id','string',label=T('Google Analytics id'),default=options['google_analytics_id'],comment=dict_default_helps['google_analytics_id']),
                Field('migrate','boolean',label=T('Migrate'),default=db_pynuke.PyNuke.Utils().str2bool(options['migrate']),comment=dict_default_helps['migrate']),
                Field('mail_settings_server','string',label=T('Mail settings server'),default=options['mail_settings_server'],comment=dict_default_helps['mail_settings_server']),
                Field('mail_settings_sender','string',label=T('Mail settings sender'),default=options['mail_settings_sender'],comment=dict_default_helps['mail_settings_sender']),
                Field('mail_settings_allmessageswithcopyto','string',label=T('All messages with copy to'),default=options['mail_settings_allmessageswithcopyto'],comment=dict_default_helps['mail_settings_allmessageswithcopyto']),
                Field('mail_settings_TLS','boolean',label=T('Use TLS'),default=db_pynuke.PyNuke.Utils().str2bool(options['mail_settings_TLS']),comment=dict_default_helps['mail_settings_TLS']),
                Field('mail_settings_SSL','boolean',label=T('Use SSL'),default=db_pynuke.PyNuke.Utils().str2bool(options['mail_settings_SSL']),comment=dict_default_helps['mail_settings_SSL']),
                Field('mail_settings_login','string',label=T('Mail login'),default=options['mail_settings_login'],comment=dict_default_helps['mail_settings_login']),
                Field('mail_settings_logging','boolean',label=T('Simulate sending messages'),default=db_pynuke.PyNuke.Utils().str2bool(options['mail_settings_logging']),comment=dict_default_helps['mail_settings_logging']),
                Field('mail_maximo_num_envios_x_sendqueue','string',label=T('Max messages x sendqueue proccess'),default=options['mail_maximo_num_envios_x_sendqueue'],comment=dict_default_helps['mail_maximo_num_envios_x_sendqueue']),
                Field('registration_type',
                      'string',
                      requires=IS_IN_SET({'private':T('Private'),
                                     'public':T('Public'),
                                     'verified':T('Verified'),
                                     'public-verified':T('Public-Verified'),
                                     'none':T('None'),
                                      }),
                                    label=T('Registration type'),
                                    default=options['registration_type'].lower(),
                                    comment=dict_default_helps['registration_type']),
                Field('message_onregister','boolean',label=T('Send mail to portal admin when user registered'),default=db_pynuke.PyNuke.Utils().str2bool(options['message_onregister']),comment=dict_default_helps['message_onregister']),
                Field('message_onvalidation','boolean',label=T('Send mail to portal admin when a user validates the mail address'),default=db_pynuke.PyNuke.Utils().str2bool(options['message_onvalidation']),comment=dict_default_helps['message_onvalidation']),
                Field('use_mail_as_username','boolean',label=T('use mail as username'),default=db_pynuke.PyNuke.Utils().str2bool(options['use_mail_as_username']),comment=dict_default_helps['use_mail_as_username']),
                Field('reset_password_requires_verification','boolean',label=T('reset_password_requires_verification'),default=db_pynuke.PyNuke.Utils().str2bool(options['site_description']),comment=dict_default_helps['reset_password_requires_verification']),
                Field('LevelLogging','string',label=T('Level Logging'),default=options['LevelLogging'],comment=dict_default_helps['LevelLogging']),
                Field('force_SSL','boolean',label=T('Force SSL'),default=db_pynuke.PyNuke.Utils().str2bool(options['force_SSL']),comment=dict_default_helps['force_SSL']),
                Field('auth_require_recaptcha','boolean',label=T('Auth Login requires recaptcha'),default=db_pynuke.PyNuke.Utils().str2bool(options['auth_require_recaptcha']),comment=dict_default_helps['auth_require_recaptcha']),
                Field('auth_register_require_recaptcha','boolean',label=T('Auth Register requires recaptcha'),default=db_pynuke.PyNuke.Utils().str2bool(options['auth_register_require_recaptcha']),comment=dict_default_helps['auth_register_require_recaptcha']),
                Field('auth_retrieve_username_require_recaptcha','boolean',label=T('Retrieve username requires recaptcha'),default=db_pynuke.PyNuke.Utils().str2bool(options['auth_retrieve_username_require_recaptcha']),comment=dict_default_helps['auth_retrieve_username_require_recaptcha']),
                Field('auth_retrieve_password_require_recaptcha','boolean',label=T('Retrieve password requires recaptcha'),default=db_pynuke.PyNuke.Utils().str2bool(options['auth_retrieve_password_require_recaptcha']),comment=dict_default_helps['auth_retrieve_password_require_recaptcha']),

                Field('recaptcha_publickey','string',label=T('Recaptcha publickey'),default=options['recaptcha_publickey'],comment=dict_default_helps['recaptcha_publickey']),
                Field('recaptcha_privatekey','string',label=T('Recaptcha privatekey'),default=options['recaptcha_privatekey'],comment=dict_default_helps['recaptcha_privatekey']),
                Field('recaptcha_options','string',label=T('Recaptcha options'),default=options['recaptcha_options'],comment=dict_default_helps['recaptcha_options']),
                Field('compress_css_files','boolean',
                      label=T('Compress CSS Files'),
                      default=db_pynuke.PyNuke.Utils().str2bool(options['compress_css_files']) ,
                      comment=dict_default_helps['compress_css_files']),                    
                Field('compress_js_files','boolean',label=T('Compress JS Files'),default=db_pynuke.PyNuke.Utils().str2bool(options['compress_js_files']) ,comment=dict_default_helps['compress_js_files']),
                Field('use_janrain','boolean',label=T('Use janrain'),default=db_pynuke.PyNuke.Utils().str2bool(options['use_janrain']),comment=dict_default_helps['use_janrain']),
                Field('redirectafterlogin',db.pages,label=T('Redirect after login'),requires=IS_IN_SET(list_pags, zero='', multiple=False),default=options['redirectafterlogin'],comment=dict_default_helps['redirectafterlogin']),
                Field('redirectafterregister',db.pages,label=T('Redirect after register'),requires=IS_IN_SET(list_pags, zero='', multiple=False),default=options['redirectafterregister'],comment=dict_default_helps['redirectafterregister']),
                Field('redirectafterlogout',db.pages,label=T('Redirect after logout'),requires=IS_IN_SET(list_pags, zero='', multiple=False),default=options['redirectafterlogout'],comment=dict_default_helps['redirectafterlogout']),
                
                Field('cssclass_icon_edit','string',label=T('CSS Icon Edit'),default=options['cssclass_icon_edit'],comment=dict_default_helps['cssclass_icon_edit']),
                Field('cssclass_icon_return','string',label=T('CSS Icon Return'),default=options['cssclass_icon_return'],comment=dict_default_helps['cssclass_icon_return']),
                Field('cssclass_icon_remove','string',label=T('CSS Icon Remove'),default=options['cssclass_icon_remove'],comment=dict_default_helps['cssclass_icon_remove']),
                Field('cssclass_button_small','string',label=T('CSS Button small'),default=options['cssclass_button_small'],comment=dict_default_helps['cssclass_button_small']),
                Field('cssclass_button_extrasmall','string',label=T('CSS Button extrasmall'),default=options['cssclass_button_extrasmall'],comment=dict_default_helps['cssclass_button_extrasmall']),
                Field('cssclass_button_warning','string',label=T('CSS Button warning'),default=options['cssclass_button_warning'],comment=dict_default_helps['cssclass_button_warning']),
                Field('cssclass_button_danger','string',label=T('CSS Button danger'),default=options['cssclass_button_danger'],comment=dict_default_helps['cssclass_button_danger']),
                
                #por cada campo boolean (checkbox) agregar abajo su equivalente oculto con el valor 'F'
               #Esto es por que los checkboxes si no están seleccionados no se envían. Al poner el campo oculto
               #con el mismo nombre, cogerá este si el checkbox no está seleccionado.
               #http://stackoverflow.com/questions/476426/submit-an-html-form-with-empty-checkboxes
               hidden=dict(migrate='False',
                        mail_settings_TLS='False',
                        mail_settings_SSL='False',
                        mail_settings_logging='False',
                        reset_password_requires_verification='False',
                        force_SSL='False',
                        auth_require_recaptcha='False',
                        use_janrain='False',
                        use_mail_as_username='False',
                        message_onregister='False',
                        message_onvalidation='False',
                        compress_css_files='False',
                        compress_js_files='False',
                        auth_register_require_recaptcha='False',
                        auth_retrieve_username_require_recaptcha='False',
                        auth_retrieve_password_require_recaptcha='False'
                        )
                    )
        return result

    def default_site_settings(self):
        T = self.T
        dict_default_helps = {'portal_admin': T('The main administrator of this portal.'),
        'plugin_layout_default': T('Default design used in pages'),
        'plugin_container_default': T('Default container used in portal'),
        'img_logo': T('Depending on the skin chosen, this image will appear in the top left corner of the page.'),
        'link_logo': T('Write here the URL to link the logo image'),
        'site_title': T('The Title for your portal. The text you enter will show up in the navigator window title bar.'),
        'link_title': T('Title'),
        'site_description': T('Enter a description about your site here.'),
        'bootstrap_brand': T('Enter a text to show in bootstrap brand area'),
        'author': T('Enter the name of author of this site. This option is related with Google+ and Google Autorship.'),
        'keywords': T('Enter some keywords for your site (separated by commas). These keywords are used by search engines to help index your site.'),
        'generator': 'Leave pynuke here',
        'copyright': T('If supported by the layout this Copyright text is displayed on your site.'),
        'startpageid': T(' The Home Page for your site.'),
        'gmt_offset': '',
        'google_meta': '',
        'google_analytics_id': '',
        'migrate': '',
        'mail_settings_server': '',
        'use_mail_as_username': '',
        'mail_settings_sender': '',
        'mail_settings_allmessageswithcopyto': '',
        'mail_settings_TLS': '',
        'mail_settings_SSL': '',
        'mail_settings_login': '',
        'mail_settings_logging': T('If this option is checked, the test always is correct'),
        'mail_maximo_num_envios_x_sendqueue': '',
        'registration_type': '',
        'message_onregister': T('Send a message when a user is registered'),
        'message_onvalidation': T('Send a message when a user validates the mail address'),
        'reset_password_requires_verification': '',
        'LevelLogging': '',
        'force_SSL': T('Specify whether an SSL Certificate has been installed for this site and must be used in all pages'),
        'auth_require_recaptcha': T('Recaptcha to Login'),
        'auth_register_require_recaptcha': T('Recaptcha to register'),
        'auth_retrieve_username_require_recaptcha': T('Recaptcha to retrieve username'),
        'auth_retrieve_password_require_recaptcha': T('Recaptcha to retrieve password'),
        'recaptcha_publickey': '',
        'recaptcha_privatekey': '',
        'recaptcha_options': '',
        'use_janrain': '',
        'compress_css_files': '',
        'compress_js_files': '',
        'redirectafterlogin':T('Page to redirect after user login'),
        'redirectafterregister':T('Page to redirect after user register'),
        'redirectafterlogout':T('Page to redirect after user logout'),
        'cssclass_icon_edit':'Edit icon',
        'cssclass_icon_remove':'Delete icon',
        'cssclass_icon_return':'Return icon',
        'cssclass_button_small':'Button small',
        'cssclass_button_extrasmall':'Button extra small',
        'cssclass_button_warning':'Button warning',
        'cssclass_button_danger':'Button danger',
            }

        dict_default_values = {'portal_admin': 1,
        'plugin_layout_default': 1,
        'plugin_container_default': 2,
        'img_logo': '',
        'link_logo': '',
        'site_title': 'Business name',
        'link_title': '',
        'site_description': 'Business description',
        'bootstrap_brand': 'Bootstrap Brand',
        'author': 'Your Name <you@example.com>',
        'keywords': 'web2py, pynuke, python, framework',
        'generator': 'pynuke',
        'copyright': 'Copyright 2013',
        'startpageid': 5,
        'gmt_offset': 1,
        'google_meta': '',
        'google_analytics_id': '',
        'migrate': 'True',
        'mail_settings_server': 'smtp.gmail.com:587',
        'use_mail_as_username':'False',
        'mail_settings_sender': 'xxx@example.com',
        'mail_settings_allmessageswithcopyto': 'example@example.com',
        'mail_settings_TLS': 'False',
        'mail_settings_SSL': 'False',
        'mail_settings_login': 'xxx@example.com:password',
        'mail_settings_logging': 'True',
        'mail_maximo_num_envios_x_sendqueue': '-1',
        'registration_type': 'verified',
        'message_onregister':'True',
        'message_onvalidation':'True',
        'reset_password_requires_verification': 'False',
        'LevelLogging': 'INFO',
        'force_SSL': 'False',
        'auth_require_recaptcha': 'False',
        'auth_register_require_recaptcha': 'False',
        'auth_retrieve_username_require_recaptcha': 'False',
        'auth_retrieve_password_require_recaptcha': 'False',
        'recaptcha_publickey': '',
        'recaptcha_privatekey': '',
        'recaptcha_options': "theme:'clean'",
        'use_janrain': 'False',
        'compress_css_files':'True',
        'compress_js_files':'True',
        'redirectafterlogin': 5,
        'redirectafterregister': 5,
        'redirectafterlogout': 5,
        'cssclass_icon_remove':'glyphicon glyphicon-trash',
        'cssclass_button_small':'btn btn-sm',
        'cssclass_button_extrasmall':'btn btn-xs',
        'cssclass_button_warning':'btn-warning',
        'cssclass_button_danger':'btn-danger',
        'cssclass_icon_edit':'glyphicon glyphicon-pencil',
        'cssclass_icon_return':'glyphicon glyphicon-chevron-left',
            }

        return dict_default_helps, dict_default_values

    def read_sitesettings(self):
        #'Valores por defecto de la configuracion'
        dict_default_helps, dict_default_values = self.default_site_settings()
        #leer los valores actuales de configuracion para asignar por defecto
        modsettings = self.get_all_sitesettings(dict_default_values)
        return modsettings, dict_default_helps

    def get_all_sitesettings(self, dict_defaultvalues):
        db = self.db
        query = (db.options.id > 0)
        options = dict()
        for row in db(query).select(db.options.ALL):
            if row.value == 'on':
                row.value = 'True'
            elif row.value == 'F':
                row.value = 'False'
            options[row.name] = row.value
        for item in dict_defaultvalues:
            try:
                value = options[item]
                dict_defaultvalues[item] = value
            except:
                pass
        return dict_defaultvalues
