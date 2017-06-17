#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: javier
'''
from gluon import *
import datetime
import db_packages,db_basemodules,db_permissions,db_contenttypes,db_workflows,db_pagemodules,db_pages,db_security,db_options,db_eventlog
from gluon.compileapp import LoadFactory
from gluon.tools import Mail
import datetime
import zipfile
import urllib
from gluon.fileutils import up, fix_newlines, abspath, recursive_unlink
from gluon.fileutils import read_file, write_file, parse_version
from urllib import urlopen
import os.path

class PyNuke(object):

    def __init__(self):
        from gluon.globals import current
        self.current = current
        self.db = current.db
        self.T = current.T
        self.auth = current.auth
        self.request = current.request
        self.response = current.response
        self.auth = current.auth
        self.settings = current.settings
        self.options = current.options

    def def_fields_signature(self):
        '''
            Se define una tabla "dummy" para reutilizarla en otros sitios.
            En concreto "Signature" son los campos de quien ha creado o
            modificado un registro. Estos campos se repiten en muchas tablas.
            Pag. 305 Web2py book,
        '''
        db = self.db
        auth = self.auth
        T = self.T

        value = db.Table(db, 'signature',
            Field('createdbyuserid', db.auth_user, default=auth.user_id,
                  writable=False, label=T('Created by')),
            Field('createdon', 'datetime', default=datetime.datetime.now(),
                  writable=False, label=T('Created On')),
            Field('lastmodifiedbyuserid', db.auth_user, update=auth.user_id,
                  writable=False, label=T('Last modified by')),
            Field('lastmodifiedondate', 'datetime',
                  update=datetime.datetime.now(), writable=False,
                  label=T('Last modified on')))

        return value

    def define_tables(self, mptt_pages):
        # Definición de tablas base
        db = self.db
        request = self.request
        clpagdf = db_pages.Pages.Db_Functions()
        db_workflows.WorkFlows().define_tables()
        db_packages.Packages().define_tables()
        db_basemodules.BaseModules.Db_Functions().define_tables()
        db_permissions.Permissions().define_tables()        
        db_contenttypes.ContentTypes().define_tables()
        mptt_pages.settings.table_node_name = 'pages'
        mptt_pages.settings.extra_fields = clpagdf.define_tables()
        mptt_pages.define_tables()
        db.pages.slug.requires = IS_EMPTY_OR(IS_NOT_IN_DB(db, db.pages.slug))
        return

    def pre_render_modules(self, objpage):
        """
            This function loads two lists: listload and listcontrols
            With this two lists, we can render the page later.
        """
        db = self.db
        settings = current.settings
        auth = current.auth
        listload = []
        listcontrols = []
        dbmd = db.moduledefinitions
        dbmc = db.modulecontrols
        clpm = db_pagemodules.PageModules()
        clbm = db_basemodules.BaseModules()
        clpk = db_packages.Packages()
        clse = db_security.PNSecurity()
        pageid = objpage.id
        recs_page_modules = clpm.get_pagemodules(pageid)
        layoutsrc = clpk.get_src_layout_by_layoutid(objpage.layoutsrc) or settings.layoutsrc
        idlayout = clpk.get_id_layout_by_layoutsrc(layoutsrc)
        panesav = clpk.get_panesfromlayoutid(idlayout)
        if len(recs_page_modules) > 0:
            for mip in recs_page_modules:
                modx = db.modules[mip.moduleid]
                if clbm.is_module_visible_bydates(modx):
                    moddef = dbmd[modx.moduledefid]
                    '''Todos los modulos tienen un control settings,
                    lo agregamos a listcontrols, siempre que el user actual
                    sea admin. mas adelante será si el usuario tiene permisos
                    adecuados, independientemente si es admin siempre los
                    verá todos...
                    '''
                    if settings.currentuser_is_admin:
                        dict_module_controls = {'moduleid': str(modx.id),
                                                'pagemoduleid': str(mip.id),
                                'link': clbm.get_button_settings(modx,
                                                                 panesav,
                                                                 mip.id,
                                                                 pageid,
                                                                 moddef)}
                        listcontrols.append(dict_module_controls)

                    # mas los controles que tenga definidos en la tabla
                    query = (dbmc.moduledefid == moddef.id) & (dbmc.controlkey == "view") 
                    modctls = db(query).select()
                    if len(modctls) > 0:
                        for mc in modctls:
                            panename = clpk.get_panename_byid(mip.panename)
                            page_panes = settings.current_page_panes
                            if panename in page_panes:
                                pane = panename
                            else:
                                pane = "contentpane"

                            dict_pagemodules = {'moduleid': str(modx.id),
                                                'pageid': settings.currentpage,
                                           'pagemoduleid': str(mip.id),
                               'controller': str(mc.controlsrc_controller),
                               'view': str(mc.controlsrc_view),
                               'ajax': bool(mc.useajax),
                               'pane': pane,
                               'title': mip.moduletitle,
                               'title_visible': mip.displaytitle,
                               'header': mip.header,
                               'footer': mip.footer,
                               'table_meta': moddef.table_meta,
                               }
                            listload.append(dict_pagemodules)
        return listload, listcontrols

    def render_modules_in_pane(self, pane):
        # Renderiza los módulos y sus controles en un panel
        settings = current.settings
        response = current.response

        #Si el modo seleccionado en el panel de control es "DESIGN"
        #independientemente de si hay módulos o no, rodea el panel con un estilo que lo hace visible        
        if (str(settings.controlpanelmode) == 'DESIGN'):
            #se rodea el panel -- Aqui se abre un div
            abrediv = '<div style="border:1px #CCCCCC dotted"><h6><center>%s</center></h6>'% (pane)            
            response.write(XML(abrediv))
        if settings.listload != None:
            for pagemodule in settings.listload:
                if pagemodule['pane'] == pane:
                    self.render_pagemodule(pagemodule)
        #Si el panel de control está visible
        if (str(settings.controlpanelmode) == 'DESIGN'):
            #se rodea el panel -- Aqui se cierra el div
            cierradiv = '</div>'
            response.write(XML(cierradiv))
        return

    def render_controls_module(self, moduleid):
        # Renderiza los controles de un módulo especificado
        settings = current.settings
        results=[]
        for mc in settings.listcontrols:
            if mc['moduleid'] == moduleid:
                result = mc['link'] + ' '
                results.append(result)
        #str_result = DIV(results)
        str_result = results[0] or ""
        return XML(str_result)

    def render_pagemodule(self, pagemodule):
        # Renderiza un módulo
        response = current.response
        request = current.request
        T = current.T
        auth = current.auth
        settings = current.settings
        db = current.db
        # Idea extraida de instant_press fichero comments.py (Martin Mulone)
        environment = {}
        environment['request'] = request
        environment['response'] = response
        environment['auth'] = auth
        environment['settings'] = settings
        environment['db'] = db
        environment['T'] = T
        LOAD = LoadFactory(environment)  # Experimental i expect this surveys!
        #querypagemoduleid = (db.pagemodules.pageid == settings.currentpage) and (db.pagemodules.moduleid == int(pagemodule['moduleid']))  
        #recpagemoduleid = db(querypagemoduleid).select().first()
        recpagemoduleid = db(db.pagemodules.id == pagemodule['pagemoduleid']).select().first()
        if pagemodule['title_visible']:
            moduletitle = pagemodule['title']
        else:
            moduletitle = ''

        scp = settings.controlpanelmode

        if (scp == 'DESIGN') or (scp == 'EDIT'):
            controls = self.render_controls_module(pagemodule['moduleid'])
            controls = DIV(controls, _class="ctrmodule")
        else:
            controls = ''
        rutacontainer = settings.containersrc_pag  or settings.containersrc
        container_modulo = recpagemoduleid.containersrc
        if container_modulo != None:
            rutacontainer = container_modulo.layoutsrc
        #si en el modulo hay un container, rutacontainer es eso
        rutacontainer = request.folder[:len(request.folder) -1] + "/views/" + \
                                                                rutacontainer
        #renderizar header
        if pagemodule['header']:
            response.write(XML(pagemodule['header']))

        content_module = '[ACTIONS][TITLE][MODULE]'

        try:
            with open(rutacontainer, "r") as container:
                content_module = container.read().replace('\n', '')
        except:
            pass

        moduletoload = LOAD(pagemodule['controller'],
                            pagemodule['view'],
                            ajax=pagemodule['ajax'],
                            vars={'moduleid': pagemodule['moduleid'],
                                  'pageid': pagemodule['pageid'],
                                  'pagemoduleid': pagemodule['pagemoduleid'],
                                  }
                            )
        if not pagemodule['ajax']:
            moduletoload = moduletoload.components[0].components[0]

        content_module = content_module.replace("[ACTIONS]", str(controls))
        content_module = content_module.replace("[TITLE]", str(moduletitle))
        content_module = content_module.replace("[MODULE]", str(moduletoload))

        response.write(XML(content_module))

        #renderizar footer
        if pagemodule['footer']:
            response.write(XML(pagemodule['footer']))

        return

    def config_settings(self, options):
        '''
            Global Settings to use in render cycle of each page.

            A lot of settings are copied here from the general settings in
            options['any_option'] then, in menu.py, these settings are modified
            with the data stored in the page settings.

            Some settings hace a default value specified here

            options: a dictionary with the site general settings

        '''
        db = self.db
        settings = current.settings
        auth = current.auth
        session = current.session
        request = current.request
        dict_default_helps, dict_default_site_settings = db_options.Options().default_site_settings()
        #Settings de sistema
        settings.is_local = request.client in ['127.0.0.1', 'localhost']
        #Settings Generales del sitio, se usarán por defecto como propiedades
        settings.site_title = options['site_title']
        settings.site_description = options['site_description']
        settings.author = options['author']
        settings.keywords = options['keywords']
        settings.generator = options['generator']
        settings.copyright = options['copyright']
        settings.admin_email = options['admin_email']
        settings.google_meta = options['google_meta']
        settings.google_analytics_id = options['google_analytics_id']
        #TODO: settings.admin_role_name si fuera en options nos ahorrariamos algo
        settings.admin_role_name = db_security.PNSecurity().get_name_role_admin()
        settings.registered_users_role_name = db.auth_group[2].role

        #Settings de configuración general de mail
        settings.mail_settings_logging = options['mail_settings_logging']
        settings.mail_settings_login = options['mail_settings_login']
        settings.mail_settings_server = options['mail_settings_server']
        settings.mail_settings_sender = options['mail_settings_sender']
        
        settings.rutas_SSL = options['force_SSL']
        settings.controlpanelvisibility = session.cpanelvisibility or 'MAX'
        settings.startpageid = options['startpageid']
        try:
            settings.redirectafterlogin = options['redirectafterlogin']
            settings.redirectafterregister = options['redirectafterregister']
            settings.redirectafterlogout = options['redirectafterlogout']
        except:
            settings.redirectafterlogin = options['startpageid']
            settings.redirectafterregister = options['startpageid']
            settings.redirectafterlogout = options['startpageid']
        settings.currentpage = -1
        settings.portal_admin = int(options['portal_admin'])
        settings.controlpanelmode = ''
        settings.currentuser_is_admin = False
        if ((auth.user_id != None) and (auth.has_membership(role = settings.admin_role_name))):
            settings.controlpanelmode = session.controlpanelmode or "EDIT"
            settings.currentuser_is_admin = True            
        settings.use_mail_as_username = self.Utils().str2bool(options['use_mail_as_username'])
        settings.listload = []
        settings.currentpageslug=''
        settings.currentpage_panes=[]
        #seguridad
        settings.currentpage_is_system_page = None
        settings.forcessl = self.Utils().str2bool(options['force_SSL'])
        #Podría ser una opcion el valor por defecto
        settings.masthead = True
        #Diseño general del sitio
        settings.plugin_layout_default = int(options['plugin_layout_default'])
        settings.plugin_container_default = int(options['plugin_container_default'])
        settings.page_layoutsrc = None  # Mas adelante en menu.py se rellena con el valor de la pagina
        settings.currentversion = options['pynuke_version']
        tmpshortversion = options['pynuke_version'].replace("Version", "")
        tmpshortversion = tmpshortversion[0:tmpshortversion.find("(")]
        settings.shortcurrentversion = tmpshortversion
        settings.breadcrumbs = ''
        settings.imglogo = options['img_logo']

        settings['cssclass_icon_edit'] = options.get('cssclass_icon_edit',dict_default_site_settings['cssclass_icon_edit'])
        settings['cssclass_icon_remove'] = options.get('cssclass_icon_remove', dict_default_site_settings['cssclass_icon_remove'])
        settings['cssclass_icon_return'] = options.get('cssclass_icon_return',dict_default_site_settings['cssclass_icon_return'])
        settings['cssclass_button_small'] = options.get('cssclass_button_small', dict_default_site_settings['cssclass_button_small'])
        settings['cssclass_button_extrasmall'] = options.get('cssclass_button_extrasmall', dict_default_site_settings['cssclass_button_extrasmall'])
        settings['cssclass_button_warning'] = options.get('cssclass_button_warning', dict_default_site_settings['cssclass_button_warning'])
        settings['cssclass_button_danger'] = options.get('cssclass_button_danger', dict_default_site_settings['cssclass_button_danger'])

        return

    def config_mail(self, objMimeMail, options):
        objMimeMail.settings.server = options['mail_settings_server']

        if self.Utils().str2bool(options['mail_settings_TLS'][0]):
            objMimeMail.settings.tls = True
        else:
            objMimeMail.settings.tls = False

        if self.Utils().str2bool(options['mail_settings_SSL'][0]):
            objMimeMail.settings.ssl = True
        else:
            objMimeMail.settings.ssl = False

        objMimeMail.settings.sender = options['mail_settings_sender']
        objMimeMail.settings.login = options['mail_settings_login']

        if self.Utils().str2bool(options['mail_settings_logging'][0]):
            objMimeMail.settings.server = 'logging'

        return

    def get_pagemodules_by_type(self, typemodule):
        '''
            Obtener la lista de módulos de cualquier página del tipo pasado
            en typemodule
        '''
        db = self.db
        dbm = db.modules
        dbpm = db.pagemodules
        dbbm = db.basemodules
        dbmd = db.moduledefinitions
        xbasemodule_pressblog = db(dbbm.modulename == typemodule).select().first()
        xmodule_def_pressblog = db(dbmd.basemoduleid == xbasemodule_pressblog['id']).select().first()
        xmodules = db(dbm.moduledefid == xmodule_def_pressblog['id']).select()
        result = {}
        for xm in xmodules:
            xpagemodules = db(dbpm.moduleid == xm['id']).select().first()
            pagemoduleid = str(xpagemodules['moduleid']) + ";" + str(xpagemodules['pageid']) + ";" + str(xpagemodules['id'])
            titulom = xpagemodules['moduletitle']
            mid = xpagemodules['moduleid']
            result[pagemoduleid] = titulom
        return result

    def get_modules_by_type(self, typemodule):
        '''
            Obtener la lista de módulos de cualquier página del tipo pasado
            en typemodule
        '''
        db = self.db
        dbpm = db.pagemodules
        #obtener basemodule de pressblog (select * from basemodules where modulename = 'pressblog')
        xbasemodule_pressblog = db(db.basemodules.modulename==typemodule).select().first()
        #obtener sus module_definitions
        xmodule_def_pressblog = db(db.moduledefinitions.basemoduleid==xbasemodule_pressblog['id']).select().first()
        #Averiguar modules que estarán agregados a páginas
        query = (db.modules.moduledefid==xmodule_def_pressblog['id']) 
        query = query & (db.modules.isdeleted==False)
        xmodules = db(query).select()
        result={}
        for xm in xmodules:
            #coger el primero de pagemodules para mostrar el titulo del modulo
            xpagemodules = db(dbpm.moduleid==xm['id']).select().first()
            moduleid = str(xpagemodules['moduleid']) + ';' + str(xpagemodules['pageid']) 
            titulom = xpagemodules['moduletitle']            
            result[moduleid]=titulom
            #result['moduleid']=moduleid
        #devolver ('moduleid','moduletitle')
        return result

    def proccess_update_settings(self, request_vars):
        #Guardar los valores en la tabla modulesettings como en options
        db = self.db
        options = self.options
        dict_values = self.Utils().clean_form_vars(request_vars)
        for v in dict_values:
            try:
                if request_vars[v][0] == 'on':
                    dict_values[v] = 'True'
                else:
                    dict_values[v] = request_vars[v]
            except:
                pass

            db.options.update_or_insert((db.options.name == v),
                                                name=v,
                                                value=dict_values[v])
            if v == 'plugin_layout_default':
                if request_vars[v] != options['plugin_layout_default']:
                    rec_pages = db(db.pages.layoutsrc == None).select()
                    for pag in rec_pages:
                        db_pages.Pages.WebForms().proccess_change_page_layout(pag.id,
                                                            dict_values[v])
        return

    class Utils(object):
        def __init__(self):
            self.current = current
            #self.db = current.db
            self.T = current.T
            self.request = current.request
            self.response = current.response
            
        #http://stackoverflow.com/questions/715417/converting-from-a-string-to-boolean-in-python

        def str2bool(self, v):
            if v != None:
                return v.lower() in ("yes", "true", "t", "1", "on")

        def bool2str(self, v):
            if v:
                return 'True'
            else:
                return 'False'

        def last_day_of_month(self, date):
            if date.month == 12:
                return date.replace(day=31)
            return date.replace(month=date.month+1, day=1) - \
                   datetime.timedelta(days=1)

        def is_in_interval_of_dates(self,date_to_test,startdate,enddate):
            # Devuelve True o False si la fecha proporcionada está entre el intervalo de las otras
            # Tarea 6 comprobar fechas de comienzo y expiración de paginas y modulos
            result = False
            comp_startdate = startdate or datetime.datetime(datetime.MINYEAR,01,01)
            comp_enddate = enddate or datetime.datetime(datetime.MAXYEAR, 12, 31)
            if (datetime.datetime.now() >= comp_startdate) & (datetime.datetime.now() <= comp_enddate):
                result = True

            return result

        def prettydate(self,d):
            T=self.T
            try:
                dt = datetime.datetime.now() - d
            except:
                return ''
            if dt.days >= 2*365:
                return T('%d years ago') % int(dt.days / 365)
            elif dt.days >= 365:
                return T('1 year ago')
            elif dt.days >= 60:
                return T('%d months ago') % int(dt.days / 30)
            elif dt.days > 21:
                return T('1 month ago')
            elif dt.days >= 14:
                return T('%d weeks ago') % int(dt.days / 7)
            elif dt.days >= 7:
                return T('1 week ago')
            elif dt.days > 1:
                return T('%d days ago') % dt.days
            elif dt.days == 1:
                return T('1 day ago')
            elif dt.seconds >= 2*60*60:
                return T('%d hours ago') % int(dt.seconds / 3600)
            elif dt.seconds >= 60*60:
                return T('1 hour ago')
            elif dt.seconds >= 2*60:
                return T('%d minutes ago') % int(dt.seconds / 60)
            elif dt.seconds >= 60:
                return T('1 minute')
            elif dt.seconds > 1:
                return T('%d seconds') % dt.seconds
            elif dt.seconds == 1:
                return T('1 second')
            else:
                return T('now')

        def clean_form_vars(self, reqvars):
            """
                Elimina del diccionario reqvars las variables de formulario
                    _formkey
                    _formname
                    _signature
                    _moduleid
                    _pageid
                    _pagemoduleid

            Parametros
            ----------
            reqvars:
                diccionario del cual se eliminarán las variables de formulario

            Notas
            ------
            Suele utilizarse para luego pasar todo vars como argumento de un
            insert o un update *kwargs

            """
            cprequestvars = reqvars
            if cprequestvars._formkey:
                cprequestvars.pop('_formkey')

            if cprequestvars._formname:
                cprequestvars.pop('_formname')

            if cprequestvars._signature:
                cprequestvars.pop("_signature")

            if cprequestvars.moduleid:
                cprequestvars.pop("moduleid")

            if cprequestvars.pageid:
                cprequestvars.pop("pageid")

            if cprequestvars.pagemoduleid:
                cprequestvars.pop("pagemoduleid")

            return cprequestvars

        def localized_date_long(self, date):
            T = self.T
            result = ''

            #entry.publisheddate.strftime("%A %d %B %Y")

            if date:
                day_long = date.strftime("%A")
                xday = date.strftime("%d")
                month_long = date.strftime("%B")
                xyear = date.strftime("%Y")

                format_long = T("%Y %B %d %A")
                format_long = format_long.replace("%Y", xyear)
                format_long = format_long.replace("%B", str(T(month_long)))
                format_long = format_long.replace("%d", xday)
                format_long = format_long.replace("%A", str(T(day_long)))

                result = format_long

            return result

        def localized_str_to_date(self, datestr):
            T = self.T
            formatdate = str(T('%Y-%m-%d'))
            objdate = datetime.datetime.strptime(datestr, formatdate)
            return objdate

        def localized_datetimenow(self):
            T = self.T
            formatdate = str(T('%Y-%m-%d %H:%M:%S'))
            objdate = datetime.datetime.now().strftime(formatdate)
            return objdate

        def translation_strings(self):
            #Dummy function to allow a web2py translate these strings
            T = self.T
            a = T("Monday")
            a = T("Tuesday")
            a = T("Wednesday")
            a = T("Thursday")
            a = T("Friday")
            a = T("Saturday")
            a = T("Sunday")
            a = T("January")
            a = T("January")
            a = T("February")
            a = T("March")
            a = T("April")
            a = T("May")
            a = T("June")
            a = T("July")
            a = T("August")
            a = T("September")
            a = T("October")
            a = T("November")
            a = T("December")
            return a

        def read_modsettings(self, pagemoduleid, moduleclass=None):
            #'Default values configuration of the module'
            dbpm = db_pagemodules.PageModules()
            dict_default_helps = {}
            modsettings = {}
            if moduleclass != None:
                dict_default_values = moduleclass.dict_default_values
                dict_default_helps = moduleclass.dict_default_helps
                #leer los valores actuales de configuracion para asignar por defecto
                modsettings = dbpm.get_all_modulesettings(pagemoduleid,
                                                          dict_default_values)

            return modsettings, dict_default_helps

    class SQLObjects():
        def __init__(self):
            from gluon.globals import current
            self.current = current
            self.db = current.db
            self.T = current.T
            self.auth = current.auth
            self.request = current.request
            self.response = current.response
            self.auth = current.auth
            self.settings = current.settings

        def generic_grid(self, moduleid, pageid, objtable, fields,
                         maxtextlengths, orderby, gridlinks, addlink):

            """ return a generic grid ready to pynuke """

            T = self.T
            #db = self.db
            request = self.request

            query = (objtable.id > 0) and (objtable.moduleid == moduleid) 

            grid = SQLFORM.grid(query,
                            fields=fields,
                            maxtextlengths=maxtextlengths,
                            links=gridlinks,
                            orderby=orderby,
                            csv=False,
                            searchable=True,
                            create=False,
                            editable=False,
                            details=False,
                            deletable=False,
                            paginate=10,
                            args=request.args
                            )

            icon_add = SPAN(_class='icon plus icon-plus')
            text_add = SPAN(T('Add'),_class='buttontext button')
            button_add =  A(icon_add + text_add,_href=addlink,_class='w2p_trap button btn')

            icon_return = SPAN(_class='icon plus icon-arrow-left')
            text_return = SPAN(T('Return'),_class='buttontext button')
            button_return = A(icon_return + text_return,_href=db_pages.Pages.Navigation().friendly_url_to_page(pageid),_class='w2p_trap button btn')

            grid.element('div[class=web2py_console').insert(0,XML('<br/>'))
            grid.element('div[class=web2py_console').insert(0,button_add + ' ')
            grid.element('div[class=web2py_console').insert(0,button_return + ' ')

            return grid

    class Navigation(object):
        def __init__(self):
            self.current = current
            self.db = current.db
            self.T = current.T
            self.auth = current.auth
            self.request = current.request
            self.response = current.response
            self.auth = current.auth
            self.settings = current.settings

        def extract_value_from_arg(self, completepath, arg, ret_int=False):
            """
            Extrae un valor de los args de una cadena de path

            por ej. a partir de "/init/default/page/blog?pag=10&search=windows"
            puede extraer el valor 10, pasandole el path, "pag" y True si
            queremos que el valor devuelto sea devuelto como un entero.

            Parameters
            ----------
            completepath:
                Una URL completa con los parametros incluidos
            arg:
                El argumento a buscar
            ret_int:
                Opcional, un booleano que indica si el valor se devolverá 
                como un entero, por defecto es False

            """

            result = None
            search = arg + "="

            '''hacemos un split por "?" y en el 2 elemento estan los args '''
            arr_path = completepath.split("?")

            ''' si hemos conseguido dividirlo quiere decir que en la ruta
            viene algo de esto al final ?arg=valor&arg2=valor2 '''
            if len(arr_path) > 1:
                for s in arr_path[1].split("&"):  # recorremos la lista de args
                    if s.find(search) != -1:
                        v = s.split("=")
                        result = v[1]
                        break

            if result != None:
                if ret_int == True:
                    result = int(result)

            return result

        def clean_slug(self, txtslug):
            """
                Clean slug, removes the "/" from the begin and the end

                Parameters
                ----------
                txtslug:
                    the slug to clean

                Returns
                -------
                txtslug modified
            """
            if txtslug.endswith("/"):
                txtslug = txtslug[:-1]

            if txtslug.startswith("/"):
                txtslug = txtslug[1:]

            return txtslug

        def linkbutton(self, text, iconcss, buttoncss, nextpage_slug):
            settings = self.settings

            lnk = A(I(_class=iconcss), " " + text,
                    _class=buttoncss,
                    _href=URL(c='default',
                              f='page',
                              args=nextpage_slug))

            return lnk



    class Upgrades():
        def __init__(self):
            from gluon.globals import current
            self.current = current
            self.db = current.db
            self.T = current.T
            self.auth = current.auth
            self.request = current.request
            self.response = current.response
            self.auth = current.auth
            self.settings = current.settings

        def check_new_version(self,myversion, version_URL):
            """
            Compares current pynuke's version with the latest stable pynuke

            Parameters
            ----------
            myversion:
                the current version as stored in table options "pynuke_version"
            version_URL:
                the URL that contains the version of the latest stable release

            Returns
            -------
            state:
                `True` if upgrade available, `False` if current version if up-to-date,
                -1 on error
            version:
                the most up-to-version available
            """
            try:
                from urllib import urlopen
                version = urlopen(version_URL).read()
                pversion = self.parse_version(version)
                pmyversion = self.parse_version(myversion)
            except Exception, e:
                import traceback
                print traceback.format_exc()
                return -1, myversion

            if pversion[:3]+pversion[-6:] > pmyversion[:3]+pmyversion[-6:]:
                return True, version
            else:
                return False, version

        def check_new_packversion(self,myversion, version):
            """
            Compares current package version with the latest stable

            Parameters
            ----------
            myversion:
                the current version as stored in table
            version_URL:
                the URL that contains the version of the latest stable

            Returns
            -------
            state:
                `True` if upgrade available, `False` if current version if up-to-date,
                -1 on error
            version:
                the most up-to-version available
            """
            try:
                from urllib import urlopen
                pversion = self.parse_version(version)
                pmyversion = self.parse_version(myversion)
            except Exception, e:
                import traceback
                print traceback.format_exc()
                return -1, myversion

            if pversion[:3]+pversion[-6:] > pmyversion[:3]+pmyversion[-6:]:
                return True, version
            else:
                return False, version

        def parse_semantic(self,version="Version 1.99.0-rc.1+timestamp.2011.09.19.08.23.26"):
            "http://semver.org/"
            import re
            re_version = re.compile('(\d+)\.(\d+)\.(\d+)(\-(?P<pre>[^\s+]*))?(\+(?P<build>\S*))')
            m = re_version.match(version.strip().split()[-1])
            if not m:
                return None
            a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
            pre_release = m.group('pre') or ''
            build = m.group('build') or ''
            if build.startswith('timestamp'):
                build = datetime.datetime.strptime(build.split('.',1)[1], '%Y.%m.%d.%H.%M.%S')
            return (a, b, c, pre_release, build)

        def parse_legacy(self, version="Version 0.0.0 (2011-01-01 00:00:00)"):
            import re
            if version == "0.0.0":
                version="Version 0.0.0 (2011-01-01 00:00:00)"
            re_version = re.compile('[^\d]+ (\d+)\.(\d+)\.(\d+)\s*\((?P<datetime>.+?)\)\s*(?P<type>[a-z]+)?')
            m = re_version.match(version)
            a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3)),
            pre_release = m.group('type') or 'dev'
            build = datetime.datetime.strptime(m.group('datetime'), '%Y-%m-%d %H:%M:%S')
            return (a, b, c, pre_release, build)

        def parse_version(self,version):            
            version_tuple = self.parse_semantic(version)
            if not version_tuple:
                version_tuple = self.parse_legacy(version)
            return version_tuple
        def unzip(self,filename, xdir, version, subfolder='', modulename=""):
            """
            Unzips filename into xdir (.zip only, no .gz etc)
            if subfolder!='' it unzip only files in subfolder
            """
            listnames = []
            filename = abspath(filename)
            if not zipfile.is_zipfile(filename):
                raise RuntimeError('Not a valid zipfile')
            zf = zipfile.ZipFile(filename)
            if not subfolder.endswith('/'):
                subfolder = subfolder + '/'
            for name in sorted(zf.namelist()):
                subfolder = name.split("/")[0]
                n = len(subfolder)
                print name[n:]
                if name.endswith('/'):
                    folder = os.path.join(xdir, name)
                    if not os.path.exists(folder):
                        os.mkdir(folder)
                else:
                    namesave = name.replace(subfolder + "/", "")
                    listnames.append(namesave)

                    if not namesave.startswith("."):
                        folder = namesave.replace(os.path.basename(namesave), "")
                        if not os.path.exists(os.path.join(xdir, folder)):
                            os.makedirs(os.path.join(xdir, folder))
                        write_file(os.path.join(xdir, namesave), zf.read(name), 'wb')
            return listnames


    class Pages():
        def __init__(self):
            from gluon.globals import current
            self.current = current
            self.db = current.db
            self.T = current.T
            self.auth = current.auth
            self.request = current.request
            self.response = current.response
            self.auth = current.auth
            self.settings = current.settings
            self.mptt_pages = current.mptt_pages
            
        def get_pages_hierarchical(self, exclude=-1, show_root=False, tree_id=1):
            '''
                Return a list to populate controls with a tree of pages...
                optionally you can exclude one page of the tree, this is util for
                select a parent page to one page

                By default the tree_id is 1 (the root My webSite)

            '''
            T = self.T
            response = self.response
            result = []
            if show_root:
                titulom = T("<None specified>")
                value = '1'
                item = (value, titulom)
                result.append(item)

            sourcettt = response.ttt_allpages

            if tree_id == 2:
                sourcettt = response.ttt2

            for xp in sourcettt:
                titulom = xp['name']
                if xp.level > 1:
                    titulom = ("__" * xp.level) + titulom
                value = xp['id']
                item = (value, titulom)
                if exclude == -1:
                    result.append(item)
                else:
                    if int(value) != int(exclude):
                        result.append(item)

            return result

        def get_pageslug_hierarchical(self, pageid, name_currentpage):
            '''
                Return a string to populate slug if leaves empty in add page
                or edit page.
            '''
            mptt_pages = self.mptt_pages
            result = ""
            sourcettt = mptt_pages.ancestors_from_node(pageid,include_self=True).select(
                                                          orderby='pages.lft')
            for xp in sourcettt:
                if xp.node_type != 'root':
                    tmpslug = IS_SLUG()(xp['name'])[0]
                    result += tmpslug + "/"

            result += IS_SLUG()(name_currentpage)[0]
            return result

    class Messages():
        def __init__(self):
            from gluon.globals import current
            self.current = current
            self.db = current.db
            self.T = current.T
            self.auth = current.auth
            self.request = current.request
            self.response = current.response
            self.auth = current.auth
            self.settings = current.settings
            self.options = current.options
            self.MimeMail = current.MimeMail
            self.clEventLog = db_eventlog.EventLog()

        def define_tables(self):
            db = self.db
            T = self.T
            auth = self.auth
            db.define_table(
                'messagestypes',
                Field('name', label=T('Name')),
                Field('description', 'text', label=T('Description')),
                Field('moduleid', db.modules, requires=IS_EMPTY_OR(IS_IN_DB(db,'modules.id')),
                      ondelete='CASCADE', label=T('Module ID')),
                Field('createdbyuserid', db.auth_user, default=auth.user_id,
                  writable=False, label=T('Created by'),ondelete='CASCADE'),
                Field('createdon', 'datetime', default=datetime.datetime.now(),
                  writable=False, label=T('Created On')),
                Field('lastmodifiedbyuserid', db.auth_user, update=auth.user_id,
                  writable=False, label=T('Last modified by')),
                Field('lastmodifiedondate', 'datetime',
                  update=datetime.datetime.now(), writable=False,
                  label=T('Last modified on')),
                plural=T('Notification Types'),
                singular=T('Notification Type'),
                )

            db.define_table(
                'messages',
                Field('messagetype', db.messagestypes,
                       label=T('Notification Type')),
                Field('messageto', 'string', length=2000, label=T('To')),
                Field('messagefrom', 'string', length=200, label=T('from')),
                Field('messagesubject', 'string', length=400, label=T('Created by')),
                Field('messagebody', 'text', label=T('Body')),
                Field('messagetxtversion', 'text', label=T('TXT Version')),
                Field('conversationid', 'integer', label=T('Conversation ID')),
                Field('senderuserid', 'integer', label=T('Conversation ID')),
                Field('expirationdate', 'datetime', label=T('Expiration date')),
                Field('createdbyuserid', db.auth_user, default=auth.user_id,
                  writable=False, label=T('Created by')),
                Field('createdon', 'datetime', default=datetime.datetime.now(),
                  writable=False, label=T('Created On')),
                Field('lastmodifiedbyuserid', db.auth_user, update=auth.user_id,
                  writable=False, label=T('Last modified by')),
                Field('lastmodifiedondate', 'datetime',
                  update=datetime.datetime.now(), writable=False,
                  label=T('Last modified on')),
                plural=T('Notification Types'),
                singular=T('Notification Type'),
                )

            db.define_table(
                'messagerecipients',
                Field('messageid', db.messages,
                       label=T('Message')),
                Field('userid', db.auth_user, label=T('User')),
                Field('email', 'string', label=T('Email')),
                Field('emailsent', 'boolean', label=T('Email sent')),
                Field('emailsentdate', 'datetime', label=T('Email sent date')),
                Field('createdbyuserid', db.auth_user, default=auth.user_id,
                  writable=False, label=T('Created by')),
                Field('createdon', 'datetime', default=datetime.datetime.now(),
                  writable=False, label=T('Created On')),
                Field('lastmodifiedbyuserid', db.auth_user, update=auth.user_id,
                  writable=False, label=T('Last modified by')),
                Field('lastmodifiedondate', 'datetime',
                  update=datetime.datetime.now(), writable=False,
                  label=T('Last modified on')),
                )

            db.define_table(
                'messageattachments',
                Field('messageid', db.messages,
                       label=T('Message')),
                Field('pathtofile', 'string', label=T('File')),
                Field('createdbyuserid', db.auth_user, default=auth.user_id,
                  writable=False, label=T('Created by')),
                Field('createdon', 'datetime', default=datetime.datetime.now(),
                  writable=False, label=T('Created On')),
                Field('lastmodifiedbyuserid', db.auth_user, update=auth.user_id,
                  writable=False, label=T('Last modified by')),
                Field('lastmodifiedondate', 'datetime',
                  update=datetime.datetime.now(), writable=False,
                  label=T('Last modified on')),
                )


            return

        def insert_initial_records(self):
            db = self.db
            dbtable = db.messagestypes
            dbtable.insert(name="NewUserRegistration",
                           description="New User Registration",
                           )
            dbtable.insert(name="HTMLMessage",
                           description="HTML Message",
                           )
            return

        def sendmail_to_userid(self, userid, messagetype, subject, bodymessage,
                               enqueue=False, fromaddress=None,
                               attachments=[]):

            db = self.db
            options = self.options
            auth = self.auth
            MimeMail = self.MimeMail

            if fromaddress == None:
                messagefrom = options['mail_settings_sender']
            else:
                messagefrom = fromaddress

            usrx = db.auth_user[userid]
            emailsentdate = None
            msgtable = db.messages
            rcptable = db.messagerecipients
            atttable = db.messageattachments

            msgid = msgtable.insert(messagetype=messagetype,
                                    messageto=usrx.displayname or usrx.first_name,
                                    messagefrom=messagefrom,
                                    messagesubject=subject,
                                    messagebody=bodymessage[1],
                                    messagetxtversion=bodymessage[0]
                                    )

            for a in attachments:
                if not isinstance(a, tuple):
                    atttable.insert(messageid=msgid, pathtofile=a)
                else:
                    atttable.insert(messageid=msgid, pathtofile=[a[0],a[1]])

            if enqueue:
                emailsent = False
            else:
                emailsent = False
                objmessage = db.messages[msgid]
                maildest = db.auth_user[userid].email
                mail = auth.settings.mailer
                mail.settings.sender = messagefrom
                if mail.send(to=maildest,
                             subject=objmessage.messagesubject,
                             message=bodymessage):
                    emailsent = True
                    emailsentdate = datetime.datetime.now()

            rcptable.insert(messageid=msgid,
                            userid=usrx.id,
                            emailsent=emailsent,
                            emailsentdate=emailsentdate)
            db.commit()

        def proccess_queue_smtp(self):
            db= self.db
            MimeMail = self.MimeMail

            mail_maximo_num_envios = 1
            orderby = db.messagerecipients.createdon
            query = (db.messagerecipients.emailsent != True)

            if mail_maximo_num_envios > 0:
                limitby = (0, mail_maximo_num_envios)
                rows = db(query).select(orderby=orderby, limitby=limitby)
            else:
                rows = db(query).select(orderby=orderby)

            for row in rows:
                objmessage = db.messages[row.messageid]
                if row.userid != None:
                    maildest = db.auth_user[row.userid].email
                else:
                    maildest = row.email

                query_attachments = (db.messageattachments.messageid == row.id)
                attachments = db(query_attachments).select()
                lst_attachments = []
                if attachments is not None and len(attachments) > 0:
                    for a in attachments:
                        if not a.pathtofile.count("|") > 0:
                            lst_attachments.append(MimeMail.Attachment(a.pathtofile))
                        else:
                            a_decompose = a.pathtofile.split("|")
                            lst_attachments.append(MimeMail.Attachment(a_decompose[1], content_id=a_decompose[2]))

                if MimeMail.send(to=maildest,
                                 subject=objmessage.messagesubject,
                                 message=(objmessage.messagetxtversion,
                                          objmessage.messagebody
                                          ),
                                 attachments=lst_attachments,
                                 sender=objmessage.messagefrom,
                                 ):
                    row.update_record(emailsent=True, emailsentdate=datetime.datetime.now())
                else:
                    row.update_record(emailsent=False)
                db.commit()

    class Scheduler():
        def __init__(self):
            from gluon.globals import current
            self.current = current
            self.db = current.db
            self.T = current.T
            self.auth = current.auth
            self.request = current.request
            self.response = current.response
            self.auth = current.auth
            self.settings = current.settings
            self.options = current.options

        def define_tasks(self):
            db = self.db
            if "scheduler_task_pynuke" in db.tables():
                if db(db.scheduler_task_pynuke.task_name=="send_queue").count() == 0:
                    db.scheduler_task_pynuke.insert(application_name="init/scheduled_tasks",
                                             task_name='send_queue',
                                             group_name='main',
                                             function_name='send_queue',
                                             enabled=True,
                                             start_time=datetime.datetime.now(),
                                             repeats=0,
                                             retry_failed=-1,
                                             period=60,
                                             timeout=60
                                             )
                if db(db.scheduler_task_pynuke.task_name=="clear_event_log").count() == 0:
                    db.scheduler_task_pynuke.insert(application_name="init/scheduled_tasks",
                                             task_name='clear_event_log',
                                             group_name='main',
                                             function_name='clear_event_log',
                                             enabled=True,
                                             start_time=datetime.datetime.now(),
                                             repeats=0,
                                             retry_failed=-1,
                                             period=86400,
                                             timeout=60
                                             )
