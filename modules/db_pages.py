# -*- coding: utf-8 -*-
'''
Created on 24/01/2012
@author: javier
'''
from gluon import *
import uuid
import datetime
import plugin_mptt
import db_packages
import db_permissions
import db_pynuke

class Pages(object):
    '''
        Funciones relacionadas con las páginas del sitio. (Tabla db.pages)
    '''
    def __init__(self):
        self.db = current.db
        self.T = current.T
        self.settings = current.settings
        self.auth = current.auth
        self.mptt = plugin_mptt.MPTT(self.db)
        self.mptt.settings.table_node_name = 'pages'
        self.mptt.settings.extra_fields = self.Db_Functions().define_tables()
        self.mptt.define_tables()
        self.options = current.options

    class Db_Functions(object):
        '''
            Esta clase proporciona las funciones relacionadas con la base de
            datos, Define un diccionario con campos adicionales al modelo
            mptt_pages, estos campos se añaden al modelo mptt_pages
        '''
        def __init__(self):
            self.db = current.db
            self.T = current.T
            self.auth = current.auth
            self.settings = current.settings
            self.request = current.request

        def define_tables(self):
            T = self.T
            db = self.db
            request = self.request
            signature = db_pynuke.PyNuke().def_fields_signature()
            dict_layouts = db_packages.Packages().get_layouts_available()
            dict_containers = db_packages.Packages().get_layouts_available(2)
            dict_result = {'pages':                               [
                Field('node_type'),
                Field('name', 'string', length=50,
                      required=True, notnull=True, label=T("Name"),
                      comment=T("Name of the page. This text is displayed in the menu system.")),
                Field('title', 'string', length=255,label=T("Title"),
                    comment=T("Enter a title for this page. The inserted text is displayed in the title of the browser window.")),
                Field('slug', 'string', requires=IS_SLUG(),label=T("Friendly URL"),
                      comment=T("You can enter a custom URL for the page.")),
                Field('description', 'text',label=T("Description"),
                      comment=T("Enter a description for this page")),
                Field('keywords', 'text', label=T("Keywords"),
                      comment=T("Enter some keywords for this page (separated by commas). These keywords are used by some internet search engines like Google to help index your site's pages.") ),
                Field('isvisible', 'boolean', default=True,
                      label=T("Page Visible"),
                      comment=T("You can choose to include or exclude this page from the main menu. If the page is not included in the menu, you can link it using its URL..")),
                Field('sectionheadervisible', 'boolean', 
                      label=T("Section Header Visible"),
                      default=True, 
                      comment=T("In some designs there is a area marked as section header, with this check you can select if this area is visible or not")),
                Field("a", 'string', label="Application"),
                Field("c",'string', label="Controller"),
                Field("f",'string', label="Function"),
                Field("args",'string', label="Arguments"),
                Field("sortable", 'integer',writable=False,readable=False),
                Field('iconfile','upload',length=100),
                Field('signature','boolean',),
                Field('disablelink','boolean',label=T("Disabled"), 
                      comment=T("If the page is disabled it cannot be clicked in any navigation menu. This option is used to provide place-holders for child menu items.")),
                Field('isdeleted','boolean',writable=False,readable=False),
                Field('url','string',length=255,writable=True,readable=True,
                      comment=T("If you would like this page to behave as a navigation link to another resource, you can specify the Link URL value here. Please note that this field is optional."),
                      label=T("Link URL")
                      ),
                Field('layoutsrc', db.layouts,label=T("Layout"),
                      comment=T("The selected skin will be applied to this page."),
                      requires=IS_EMPTY_OR(IS_IN_SET(dict_layouts)),
                      length=255),
                Field('viewsrc','string',length=255),
                Field('containersrc',db.layouts, label=T("Container"),
                      comment = T("The selected container will be applied by default to all modules on this page without container specified."),
                      requires=IS_EMPTY_OR(IS_IN_SET(dict_containers)),
                      length=255),
                Field('pagepath','string',length=255,writable=False,readable=False),    
                Field('startdate','datetime',label=T("Start date"),
                      comment=T("Enter the start date for displaying this page. You may use the Calendar to pick a date.")
                      ),
                Field('enddate','datetime',label=T("End date"),
                      comment=T("Enter the end date for displaying this page. You may use the Calendar to pick a date.")
                      ),
                Field('refreshinterval','integer',writable=False,readable=False),
                Field('pageheadtext','text',label=T("Page header tags"),
                      comment = T('Enter any tags (i.e. META tags) that should be rendered in the "HEAD" tag of the HTML for this page.')
                      ),
                Field('pagefootertext','text',label=T("Page footer tags"),
                      comment = T('Enter any text that should be rendered in the footer for this page.')
                      ),
                Field('issecure','boolean', label=T("Secure"),
                      comment=T("Specify whether or not this page should be forced to use a secure connection (SSL).")
                      ),
                Field('permanentredirect','boolean',writable=False,readable=False),
                Field('sitemappriority','double', label=T("Site Map Priority"),
                      comment=T("Enter the desired priority (between 0 and 1.0). This helps determine how this page is ranked in Google with respect to other pages on your site (0.5 is the default)."),
                      default=0.5,
                      required=True,
                      represent = lambda value, row: DIV('%.1f' % (0.5
        if value == None else value)),
                      ),
                Field('iconfilelarge','upload',length=255),
                Field('culturecode','string',writable=False,readable=False,length=10),
                Field('contentitemid','integer',writable=False,readable=False),
                Field('uniqueid',length=64,default=lambda:str(uuid.uuid4()),notnull=True,writable=False,readable=False),
                Field('versionguid',length=64,default=lambda:str(uuid.uuid4()),notnull=True,writable=False,readable=False),
                Field('defaultlanguageguid',length=64,default=lambda:str(uuid.uuid4()),notnull=True,writable=False,readable=False),
                Field('localizedversionguid',length=64,default=lambda:str(uuid.uuid4()),notnull=True,writable=False,readable=False),
                signature,
                   ],
                }

            def make_slug(r):
                db = self.db
                value = IS_SLUG()(r.name)[0]
                return value

            return dict_result

        def insert_initial_records(self):
            """
            """
            return

        def can_page_be_deleted(self, pageid):
            """
                Si la pagina puede borrarse devuelve True, si no se puede
                borrar por que es "de sistema" devuelve False
            """
            result = self.is_system_page(pageid)
            return not result

        def is_system_page(self, objpage):
            """
                Si la pagina es de sistema, es decir se creó durante la
                instalacion y es necesaria para el funcionamiento de pynuke,
                devuelve True, en cualquier otro caso devuelve False
            """
            result = False
            if objpage.c == 'admin' or objpage.c == 'appadmin':
                result = True
            return result

    class WebForms(object):
        """
            En la clase WebForms se agrupan aquellas funciones relacionadas con
            la presentación HTML de formularios.
        """
        def __init__(self):
            self.db = current.db
            self.T = current.T
            self.response = current.response
            self.auth = current.auth
            # TODO: Mirar si esto puede cambiarse por un objeto self.mptt global
            self.mptt = plugin_mptt.MPTT(self.db)
            self.mptt.settings.table_node_name = 'pages'
            self.mptt.settings.extra_fields = Pages.Db_Functions().define_tables()
            self.mptt.define_tables()
            self.cldbper = db_permissions.Permissions()
            self.clPyPages = db_pynuke.PyNuke.Pages()
            self.options = current.options

        def editar(self, page_id, dchecks={}, can_delete=False):
            """
            Devuelve un formulario de edición HTML para el registro
            especificado en page_id, opcionalmente puede incluirse una checkbox
            para borrar el registro.

            Parametros
            ----------
            page_id:
                id del registro de la tabla db.pages a editar

            dchecks:
                un diccionario de checksboxes que pueden llegar vacias

            can_delete:
                especifica si en el formulario se va a incluir el checkbox
                delete

            Notas
            ------
            Según se explica en:
            http://stackoverflow.com/questions/476426/submit-an-html-form-with-
            empty-checkboxes

            Si el formulario tiene checkboxes que pueden llegar vacías, estos
            valores no se procesarán. El truco aquí consiste en incluir un
            diccionario con los mismos nombres y valor ='F', así nos aseguramos
            de que siempre llegue algún valor. Cuando se construye el SQLForm, 
            incluimos dicho diccionario en el parámetro hidden.

            """
            db = self.db
            clPyPages = self.clPyPages
            self.invisibilize_fields()
            record = db.pages[page_id]

            #Agregamos a dchecks algunos valores mas
            dchecks['isvisible'] = 'F'
            dchecks['issecure'] = 'F'
            dchecks['disablelink'] = 'F'
            dchecks['sectionheadervisible'] = 'F'
            dchecks['allusersr'] = 'F'
            dchecks['allusersw'] = 'F'
            dchecks['tree_id'] = record.tree_id

#            db.pages.tree_id.readable = True
#            db.pages.tree_id.writable = True

            #Modificamos el campo parent para que muestre el arbol de pages
            db.pages.parent.requires = IS_IN_SET(clPyPages.get_pages_hierarchical(page_id,True,record.tree_id))

            #Modificamos el default del campo parent para que muestre el parent actual
            db.pages.parent.default = record.parent

            result = SQLFORM(db.pages, record, deletable=can_delete,
                             hidden=dchecks)

            #TODO: si la página tiene descendientes, agregar boton copiar perm.

            return result

        def invisibilize_fields(self):
            """
            Oculta algunos campos de la tabla pages, normalmente se usa antes
            de  mostrar un formulario.
            """
            db = self.db
            dbp = db.pages
            fields = [dbp.node_type,
                      #dbp.parent,
                      dbp.tree_id, dbp.level,
                      dbp.lft, dbp.rgt]

            for f in fields:
                f.writable = False
                f.readable = False

            return

        def nuevo(self):
            """
                Devuelve un formulario para crear una nueva pagina
            """

            T = self.T
            db = self.db
            self.invisibilize_fields()
            #personalizar para que el campo slug contenga sus padres...
            submit_button = T('Add Page')

            return SQLFORM(db.pages,
                           submit_button=submit_button
                           )

        def proccess_form_add_page(self, request_vars):
            ''' Procesa el formulario de agregar nueva página '''
            mptt_pages = self.mptt
            db = self.db
            cldbper = self.cldbper
            # Preparamos en extra_vars las variables para la insercion de pag.
            extra_vars = db_pynuke.PyNuke.Utils().clean_form_vars(request_vars)
            perm_vars = {}
            pag_vars = {}
            #eliminamos las checks de permisos guardandolas en perm_vars
            for r in extra_vars:
                if r.find('check') > -1:
                    perm_vars[r] = extra_vars[r]
                else:
                    if r.find('allusers') > -1:
                        perm_vars[r] = extra_vars[r]
                    else:
                        pag_vars[r] = extra_vars[r]

            parent_id = int(pag_vars['parent'])
            pag_vars.pop('parent')
            new_pageid = mptt_pages.insert_node(parent_id,
                                                position='last-child',
                                          **pag_vars)

            Pages().insert_modules_visibles_all_pages(new_pageid)

            '''
            Al crear la pagina también agregamos los permisos, el grupo
            administrators (el 1 por definición) siempre puede modificar y ver
            todas las pags.
            '''
            perviewpage = cldbper.get_permissionid_by_codeandkey("SYSTEM_PAGE",
                                                           "View")
            pereditpage = cldbper.get_permissionid_by_codeandkey("SYSTEM_PAGE",
                                                           "Edit")

            db.pagepermissions.insert(page=new_pageid, permission=perviewpage,
                                      allowaccess=True, groupid=1)

            db.pagepermissions.insert(page=new_pageid, permission=pereditpage,
                                      allowaccess=True, groupid=1)

            for check in perm_vars:
                '''
                Hay otro grupo llamado "All users" que lo gestionamos desde aquí
                este grupo se refiere a "Todos los Usuarios" autenticados o no...

                En la base de datos el groupid de la tabla permisos queda en blanco
                para este grupo... por tanto aquellos registros que tengan el campo
                groupid en blanco son referentes a "todos los usuarios"

                '''
                if check.find("checkw") == 0:
                    #Permisos de escritura al role
                    idrole = int(check.replace("checkw", ""))
                    # Si viene marcado:
                    try:
                        if perm_vars[check][0] == "on":
                            db.pagepermissions.insert(page=new_pageid,
                                                      permission=pereditpage,
                                                      allowaccess=True,
                                                      groupid=idrole)
                    except:
                        pass

                elif check.find("allusersr") == 0:
                    #permisos de lectura todos los usuarios
                    try:
                        if perm_vars[check][0] == "on":
                            db.pagepermissions.insert(page=new_pageid,
                                                      permission=perviewpage,
                                                      allowaccess=True,
                                                      groupid=None)
                    except:
                        pass
                elif check.find("allusersw") == 0:
                    #Permisos de escritura todos los usuarios
                    try:
                        if perm_vars[check][0] == "on":
                            db.pagepermissions.insert(page=new_pageid,
                                                      permission=pereditpage,
                                                      allowaccess=True,
                                                      groupid=None)
                    except:
                        pass
                elif check.find("checkr"):
                    #Permisos de lectura al role
                    idrole = int(check.replace("checkr", ""))
                    # Si viene marcado:
                    try:
                        if perm_vars[check][0] == "on":
                            db.pagepermissions.insert(page=new_pageid,
                                                      permission=perviewpage,
                                                      allowaccess=True,
                                                      groupid=idrole)
                    except:
                        pass

            return

        def proccess_update_or_delete_page(self, pageid, requestvars):
            db = self.db
            cldbper = self.cldbper
            options = self.options
            # Preparamos en extra_vars las variables para la insercion de pag.
            cpreqvars = db_pynuke.PyNuke.Utils().clean_form_vars(requestvars)
            perm_vars = {}
            pag_vars = {}
            for r in cpreqvars:
                if r.find('check') > -1:
                    perm_vars[r] = cpreqvars[r]
                else:
                    if r.find('allusers') > -1:
                        perm_vars[r] = cpreqvars[r]
                    else:
                        pag_vars[r] = cpreqvars[r]
            #===================================================================
            # if pag_vars['slug'] == '':
            #     final_slug = IS_SLUG()(pag_vars['title'])[0]
            # else:
            #     final_slug = IS_SLUG()(pag_vars['slug'])[0]
            #===================================================================
            pag_vars['slug'] = requestvars.slug
            if cpreqvars.delete_this_record == 'on':
                #TODO: Move this page to recycle bin, not delete
                db(db.pages.id == pageid).delete()
                db.commit()
                redirect(URL(c='admin', f='pages'))

            if (db.pages[pageid].layoutsrc == None and pag_vars['layoutsrc']=='')==False:
                if str(db.pages[pageid].layoutsrc) != pag_vars['layoutsrc']:
                    self.proccess_change_page_layout(pageid, int(pag_vars['layoutsrc'] or options['plugin_layout_default']))

            if pag_vars['parent'] == '' and pag_vars['tree_id'] == '1':
                pag_vars['parent'] = 1 # By default the parent is node 1 "My Website"
            elif pag_vars['parent'] == '' and pag_vars['tree_id'] == '2':
                pag_vars['parent'] = 2 # By default the parent is node 2 "System menu"

            if int(pag_vars['parent']) != db.pages[pageid].parent:
                self.mptt.move_node(pageid, pag_vars['parent'],'last-child')
                pag_vars.pop('parent')


            db(db.pages.id == pageid).update(**pag_vars)

            #Proccess permission checkboxes
            perviewpage = cldbper.get_permissionid_by_codeandkey("SYSTEM_PAGE",
                                                           "View")
            pereditpage = cldbper.get_permissionid_by_codeandkey("SYSTEM_PAGE",
                                                           "Edit")
            for p in perm_vars:
                querycommon = (db.pagepermissions.groupid == None)
                querycommon = querycommon & (db.pagepermissions.page == pageid)
                if p.find("allusersr") > -1:
                    #All Users Read
                    queryr = querycommon & (db.pagepermissions.permission == perviewpage)
                    recpermr = db(queryr).select()
                    if len(recpermr) > 0:
                        if perm_vars[p]=="F":
                            db(queryr).delete()
                        else:
                            try:
                                if perm_vars[p][0]=="on":
                                    recpermr.first().update_record(
                                                            allowaccess=True)
                            except:
                                pass
                    else:
                        if perm_vars[p][0]=="on":
                            db.pagepermissions.insert(page=pageid,
                                                      groupid=None,
                                                      permission=perviewpage,
                                                      allowaccess=True)

                elif p.find("allusersw") > -1:
                    #All Users Write
                    queryw = querycommon & (db.pagepermissions.permission == pereditpage)
                    recpermw = db(queryw).select()

                    if len(recpermw) > 0:
                        if perm_vars[p]=="F":
                            db(queryw).delete()
                        else:
                            try:
                                if perm_vars[p][0]=="on":
                                    recpermw.first().update_record(
                                                            allowaccess=True)
                            except:
                                pass
                    else:
                        if perm_vars[p][0]=="on":
                            db.pagepermissions.insert(page=pageid,
                                                      groupid=None,
                                                      permission=pereditpage,
                                                      allowaccess=True)
                elif p.find("checkw") > -1:
                    #Other groups write
                    groupid = int(p.replace("checkw", ""))
                    #Evitamos el grupo administrador, ya que siempre va a tener
                    # permisos de ver y edición
                    if groupid > 1:
                        query = (db.pagepermissions.groupid == groupid)
                        query = query & (db.pagepermissions.page == pageid)
                        query = query & (db.pagepermissions.permission == pereditpage)
                        recpermwg = db(query).select()
                        if len(recpermwg) > 0:
                            if perm_vars[p]=="F":
                                db(query).delete()
                            else:
                                try:
                                    if perm_vars[p][0]=="on":
                                        recpermwg.first().update_record(
                                                                allowaccess=True)
                                except:
                                    pass
                        else:
                            if perm_vars[p][0]=="on":
                                db.pagepermissions.insert(page=pageid,
                                                          groupid=groupid,
                                                          permission=pereditpage,
                                                          allowaccess=True)

                elif p.find("checkr") > -1:
                    #Other groups read
                    groupid = int(p.replace("checkr", ""))
                    #Evitamos el grupo administrador, ya que siempre va a tener
                    # permisos de ver y edición
                    if groupid > 1:
                        query = (db.pagepermissions.groupid == groupid)
                        query = query & (db.pagepermissions.page == pageid)
                        query = query & (db.pagepermissions.permission == perviewpage)
                        recpermrg = db(query).select()
                        if len(recpermrg) > 0:
                            if perm_vars[p]=="F":
                                db(query).delete()
                            else:
                                try:
                                    if perm_vars[p][0]=="on":
                                        recpermrg.first().update_record(
                                                                allowaccess=True)
                                except:
                                    pass
                        else:
                            if perm_vars[p][0]=="on":
                                db.pagepermissions.insert(page=pageid,
                                                          groupid=groupid,
                                                          permission=perviewpage,
                                                          allowaccess=True)

                #TODO: verificar que el administrador tiene permisos
                # Quitar mas adelante
                query = (db.pagepermissions.groupid == 1)
                query = query & (db.pagepermissions.page == pageid)
                query = query & (db.pagepermissions.permission == pereditpage)
                recpermwga = db(query).select()
                if len(recpermwga) == 0:
                    db.pagepermissions.insert(page=pageid,
                                                  groupid=1,
                                                  permission=pereditpage,
                                                  allowaccess=True)

                #verificar que el administrador tiene permisos
                # Quitar mas adelante
                query = (db.pagepermissions.groupid == 1)
                query = query & (db.pagepermissions.page == pageid)
                query = query & (db.pagepermissions.permission == perviewpage)
                recpermrga = db(query).select()
                if len(recpermrga) == 0:
                    db.pagepermissions.insert(page=pageid,
                                                  groupid=1,
                                                  permission=perviewpage,
                                                  allowaccess=True)

            return None

        def proccess_change_page_layout(self, pageid, newlayoutid):
            """
                Cambia el diseño de una página, a los modulos existentes
                en esa página se les asigna el panel correspondiente al nuevo 
                layout.

                Si hay un panel con el mismo nombre se le pone ese, si no se le 
                pone el 'contentpane' que es el unico panel obligatorio.

                Parametros
                ----------
                page_id:
                    id de la página a la cual le cambiamos el layout

                newlayoutid:
                    El id de la tabla layout correspondiente al nuevo layout

                """
            db = self.db
            options = self.options
            obj_page = db.pages[pageid]
            if (str(obj_page.layoutsrc) != newlayoutid):
                modulesinpage = db(db.pagemodules.pageid == pageid).select()
                for mip in modulesinpage:
                    current_layout_mip_name = db_packages.Packages().get_panename_byid(mip.panename)
                    nuevolayout = int(options['plugin_layout_default'])
                    if newlayoutid:
                        nuevolayout = int(newlayoutid)
                    #hay un panel que se llama igual en el nuevo diseño?
                    if db_packages.Packages().existe_panename(current_layout_mip_name, nuevolayout): 
                        #Si lo hay, se mueve ahí 
                        newpane = db_packages.Packages().get_idpanename_from_name_and_layout(current_layout_mip_name, nuevolayout)
                        db(db.pagemodules.id == mip.id).update(panename=newpane)
                    else:
                        #search a common name 'contentpane' or 'toppane' must be in skin
                        newpane = db_packages.Packages().get_idpanename_from_name_and_layout('contentpane', nuevolayout)
                        if newpane == -1:
                            newpane = db_packages.Packages().get_idpanename_from_name_and_layout('toppane', nuevolayout)
                        db(db.pagemodules.id == mip.id).update(panename=newpane)
            return

    class Navigation(object):
        """
            Funciones que tienen que ver con la navegación del sitio y su
            relación con las páginas.
        """
        def __init__(self):
            self.settings = current.settings
            self.db = current.db
            self.T = current.T
            self.mptt = plugin_mptt.MPTT(self.db)
            self.mptt.settings.table_node_name = 'pages'
            self.mptt.settings.extra_fields = Pages.Db_Functions().define_tables()
            self.mptt.define_tables()

        def get_pageid_by_slug(self, slug):
            """
                Intenta averiguar el id de página a partir del slug
                Se consulta en la base de datos por ese registro

                Parametros
                ----------
                slug:
                    slug de la pagina

                Devuelve
                -------
                el id de la página o -1 si no hay nada coincidente

            """
            db = self.db
            result = -1
            query = (db.pages.slug == slug)
            rec_result = db(query).select().first()
            if rec_result != None:
                result = rec_result.id
            return result

        def get_pageid_by_controller_function(self, scontroller, sfunction):
            """
                Intenta averiguar el id de página a partir de un controlador y
                una función. Se consulta en la base de datos por esos registros

                Parametros
                ----------
                scontroller:
                    controlador

                sfunction:
                    funcion

                Devuelve
                -------
                el id de la página o -1 si no hay nada coincidente

            """
            db = self.db
            result = -1
            try:
                query = (db.pages.c == scontroller) & (db.pages.f == sfunction)
                rec_result = db(query).select().first()
                result = rec_result.id
            except Exception:
                result = -1
            return result

        def get_pageid_by_requestargs(self, requestargs):
            """
                Intenta averiguar el id de página a partir de requestargs
                (una copia del valor request.args)

                Parametros
                ----------
                requestargs:
                    request.vars de la petición para averiguar el id de pag.

                Devuelve
                -------
                el id de la página o -1 si no hay nada coincidente

            """
            result = -1
            settings = self.settings
            if len(requestargs) > 0:
                db = self.db
                slug_tmp = ''
                for element in requestargs:
                    if element not in settings.strings_to_remove_from_url:
                        slug_tmp += element + "/"
                    #a partir de que encuentra moduleid en la ruta acaba...
                    #elif element == 'moduleid':
                    else:
                        break

                if slug_tmp.endswith('/'):
                    slug_tmp = slug_tmp[:-1]

                query = (db.pages.slug == slug_tmp)
                rec_result = db(query).select().first()
                if rec_result != None:
                    result = rec_result.id

                if result == -1:
                    if requestargs[0].isdigit(): # hemos venido con algo como 11?
                        result = int(requestargs[0])

            return result

        def friendly_url_to_page(self, pageid, dictvars=None):
            """
                Construye una URL "amigable" a una página concreta

                Parametros
                ----------
                pageid:
                    id de la pagina
                
                dictvars:
                    Para arrastrar variables (vars) en la url

                Devuelve
                -------
                una URL amigable completa como http://www.example.com/inicio

            """

            db = self.db
            query = (db.pages.id == pageid)
            slug = db(query).select(db.pages.slug).first()['pages.slug']
            url_return = URL(c='default', f='page', args=slug,
                             vars=dictvars)
            return url_return

        def page_slug(self, pageid, txtslug=''):
            """
                Devuelve una ruta completa como /padre1/hija1/hija2

                Parametros
                ----------
                pageid:
                    id de la pagina

                txtslug:

                Devuelve
                -------
                ruta completa a una página: /padre1/hija1/hija2

            """
            ''' Pasandole un pageid devuelve la ruta completa a la página, algo
            como /padre1/hija1/hija2
            Si el usuario quiere explicitamente algo concreto como slug lo
            procesa y limpia de caracteres extraños y devuelve ese valor.
            Limpia el resultado de "\" al principio y al final...
            '''
            mptt_pages = self.mptt
            db = self.db
            obj_page = db.pages[pageid]
            final_slug = ''

            if txtslug == '':
                breadcrumbs_links = []
                final_slug = ''
                pag_ancest = mptt_pages.ancestors_from_node(pageid).select()
                for pag in pag_ancest:
                    if pag.node_type != 'root':
                        args = [IS_SLUG()(pag.name)[0]]
                        breadcrumbs_links.append(URL(a='init', c='default',
                                                     f='page', args=args))
    
                if len(breadcrumbs_links) > 0:
                    for i in breadcrumbs_links:
                        final_slug += i
    
                final_slug += "/" + IS_SLUG()(obj_page.name)[0]
    
            else:
                array_rutas = txtslug.split("/")
                for ar in array_rutas:
                    final_slug += IS_SLUG()(ar)[0] + "/"
    
            if final_slug.endswith("/"):
                final_slug = final_slug[:-1]
    
            if final_slug.startswith("/"):
                final_slug = final_slug[1:]
    
            return final_slug

    class Recycle_Bin(object):
        """
            Aquí se incluyen aquellas funciones que tienen que ver con la
            papelera de reciclaje
        """
        def __init__(self):
            self.db = current.db
            self.T = current.T
            self.auth = current.auth

        def view_pages_deleted(self):
            """
                Devuelve un grid en HTML con las páginas borradas. 
                Dicho grid incluye unos botones para borrar definitivamente
                registros y para recuperar...
            """

            db = self.db
            query = (db.pages.isdeleted == True)
            fields = [db.pages.id, db.pages.title, db.pages.name]
            gridlinks = [lambda row: self.get_icons_view_pagesdeleted(row)]

            table = SQLFORM.grid(query,
                            fields=fields,
                            orderby=db.pages.id,
                            user_signature=True,
                            create=False,
                            searchable=False,
                            editable=False,
                            csv=False,
                            details=False,
                            links=gridlinks
                            )
            return table

        def get_icons_view_pagesdeleted(self, row):
            """
                Obtiene los iconos para cada fila del grid view_pages_deleted
            """
            T = self.T
            enlace = A(I(_class='icon icon-eye-open'),
                            SPAN(T('')), _href="%s" % URL('default', 'page',
                                args=[row.id]), _title=T('Ver'),
                                _class='btn btn-mini')

            enlace.append(A(SPAN(_class='icon icon-backward'),
                           SPAN(T('')),
                            _href="%s" % URL('admin',
                                'restore_page',
                                vars={'pageid': str(row.id)},
                                ), _title=T('Restore'), _class='btn btn-mini'
                      )
                    )
            return enlace

    def page_delete(self, pageid):
        ''' marca una pagina y todos sus módulos como borrados '''
        db = self.db
        settings = self.settings
        mptt = self.mptt
        startpageid = int(settings.startpageid)
        result = False
        if pageid != startpageid:
            mptt.delete_node(pageid)
            db(db.pagemodules.pageid == pageid).update(isdeleted=True)
            result = True
        else:
            result = False

        return result

    def insert_modules_visibles_all_pages(self, pageid):
        """
            Crea una instancia de cada módulo marcado "Visible en todas las
            paginas" en la página que se le pase

            Parametros
            ----------
            page_id:
                id del registro de la tabla db.pages a editar

            can_delete:
                especifica si en el formulario se va a incluir el checkbox
                delete
        """

        db = self.db
        modules_all_pages = db(db.modules.allpages == True).select()
        settings = self.settings
        objpage = db.pages[pageid]
        for mod_ap in modules_all_pages:
            query = (db.pagemodules.moduleid == mod_ap.id)
            query = query & ((db.pagemodules.isdeleted==False) | (db.pagemodules.isdeleted==None))
            first_pagemodule = db(query).select(orderby=db.pagemodules.id).first() 
            tmp_namepane = db_packages.Packages().get_panename_byid(first_pagemodule.panename)
            tmp_layout = objpage.layoutsrc or settings.plugin_layout_default
            if db_packages.Packages().existe_panename(tmp_namepane, tmp_layout):
                idpane = db_packages.Packages().get_idpanename_from_name_and_layout(tmp_namepane, tmp_layout)
            else:
                idpane = db_packages.Packages().get_idpanename_from_name_and_layout("contentpane", tmp_layout)

            new_pagemoduleid = db.pagemodules.insert(moduleid=mod_ap.id,
                   moduletitle=first_pagemodule.moduletitle,
                   moduleorder=first_pagemodule.moduleorder,
                   alignment=first_pagemodule.alignment,
                   pageid=pageid,
                   color=first_pagemodule.color,
                   iconfile=first_pagemodule.iconfile,
                   panename=idpane,
                   cachetime=first_pagemodule.cachetime,
                   visibility=first_pagemodule.visibility,
                   containersrc=first_pagemodule.containersrc,
                   displaytitle=first_pagemodule.displaytitle, 
                   displayprint=first_pagemodule.displayprint,
                   displaysyndicate=first_pagemodule.displaysyndicate,
                   iswebslice=first_pagemodule.iswebslice,
                   webslicetitle=first_pagemodule.webslicetitle,
                   websliceexpirydate=first_pagemodule.websliceexpirydate,
                   webslicettl=first_pagemodule.webslicettl,
                   isdeleted=first_pagemodule.isdeleted,
                   cachemethod=first_pagemodule.cachemethod,
                   header=first_pagemodule.header,
                   footer=first_pagemodule.footer,
                   culturecode=first_pagemodule.culturecode,
                   uniqueid=first_pagemodule.uniqueid,
                                      )
            settings_to_duplicate = db(db.modulesettings.pagemoduleid==first_pagemodule.id).select()
            for setting in settings_to_duplicate:
                db.modulesettings.insert(pagemoduleid=new_pagemoduleid,
                                         settingname=setting.settingname,
                                         settingvalue=setting.settingvalue)

            db.commit()
