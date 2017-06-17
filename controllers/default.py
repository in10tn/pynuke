# -*- coding: utf-8 -*-
import os
import yaml

if False:
    from gluon import *
    #TODO:si se importan los modulos aqui dentro, todo va..¿cambiarlo en todos?
    from applications.init.modules import db_pages, db_pagepermissions, \
                                    db_pagemodules, db_basemodules, \
                                    db_eventlog, db_packages, db_pynuke
    from gluon.tools import *
    from gluon.tools import Auth
    db = DAL()
    auth = Auth(db)
    request, session, response, T, cache = current.request, current.session,\
                                current.response, current.t, current.cache
    db = current.db
    settings = current.settings
    auth = Auth(db, hmac_key=Auth.get_or_create_key()) 
    crud, service, plugins = Crud(db), Service(), PluginManager()

clPagNav = db_pages.Pages.Navigation()
clEventLog = db_eventlog.EventLog()
clBaseModules = db_basemodules.BaseModules()
clPack = db_packages.Packages()
clPynuke_nav = db_pynuke.PyNuke.Navigation()

strings_to_remove_from_url = settings.strings_to_remove_from_url


def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    resultform = auth()
    if request.args[0] == 'register':
        search = 'id="submit_record__row"'
        cont = 0
        for xrow in resultform.components[0].components:
            if str(xrow).find(search) > -1:
                break
            cont += 1

        resultform.components[0].components[cont] = TR('')

    if response.flash == auth.messages.invalid_login:
        clEventLog.eventlog("LOGIN_FAILURE", locals())

    return dict(form=resultform, layoutsrc=settings.layoutsrc)


def current_version():
    pynuke_current_versions = current.options['pynuke_version']
    return pynuke_current_versions


def current_package_versions():
    package_current_versions = ""
    for package in db(db.packages.packagetype == 3).select():
        package_current_versions += package.name + "|" + clPack.get_packageversion(package.id) + "\n"

    return package_current_versions


def package_yaml():
    packagename = request.args(0)
    recpackage = db(db.packages.name == packagename).select().first()
    package = db.packages[recpackage.id]
    nomfichero = package.friendlyname.replace(" ", "_") + ".txt"
    mydata = db_packages.Packages().download_yaml_package(recpackage.id)
#    response.headers['Content-Type'] = 'application/text'
#    response.headers['Content-disposition'] = "attachment; filename=\"%s\""\
#                                                                 % nomfichero
    return yaml.dump(mydata, default_flow_style=False)
#    return module_yaml


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


def page():
    '''
        This function is responsible for receiving the request to render a
        page. The id of the page to be loaded is set in the model menu.py
    '''

    '''
        Detectar si viene sin nada a la pagina por defecto y forzar una redireccion
        con el slug incluido en la URL, esto se hace para que el menu marque
        la pagina como activa aunque no coincida el slug: 
    '''

    if request.url=='/init/default/page/' and ((len(request.vars) + len(request.args)) ==0):        
        redirect(clPagNav.friendly_url_to_page(settings.startpageid))

    if settings.currentpage > 0:
        '''
            comprobar que coincide el slug con la pagina id, si no coincide,
            redirigir a noauthorized.html
        '''
        layoutsrc = settings.layoutsrc
        cont = 0
        skip_next = False
        rqargs = []
        slug = ''
        for r in request.args:
            if not skip_next:
                if r not in strings_to_remove_from_url:
                    rqargs.append(request.args(cont))
                else:
                    skip_next = True
            else:
                skip_next = False
            cont += 1

        for r in rqargs:
            slug += r + "/"

        if slug.endswith("/"):
            slug = slug[:-1]

        if slug == '':  # or slug==None:
            slug = db.pages[settings.startpageid].slug
        if ((settings.currentpageslug != slug) & (slug != 'index')) or settings.authorized == False:
            response.view = 'default/noauthorized.html'
            msg = T("You don't have access to this page in this site.")
            #TODO: Log attempt
            return dict(layoutsrc=layoutsrc, msg=msg)
        else:
            response.view = 'default/page.html'

        ''' si la URL lleva "read", averiguar slug y detectar si se van a
            sobreescribir los metas de la página, se ha de hacer aquí, no he
            podido moverlo a modelos en menu o db porque en ese momento no
            existen las tablas de press_blog por ejem, que es donde se usa
            ahora
        '''
        if request.args.count("read") > 0:
            slug = request.args(request.args.index("read") + 1)
            table_meta = None
            for m in settings.listload:
                if m['table_meta'] != None and len(m['table_meta']) > 0:
                    arr_tmp = m['table_meta'].split(":")
                    table_meta = db[arr_tmp[0]]
                    field_title = table_meta[arr_tmp[1]]
                    '''solo puede haber un modulo que sobreescriba los metas
                        por pagina '''
                    break
            if table_meta != None:
                rec = db(table_meta.slug == slug).select().first()
                if rec != None:
                    if rec.meta_title != None and len(rec.meta_title) > 0:
                        response.title = rec.meta_title
                    else:
                        response.title = rec[field_title] + " > " + \
                                                                settings.site_title

                    if rec.meta_keywords != None and len(rec.meta_keywords) > 0:
                        response.meta.keywords = XML(rec.meta_keywords)
                    if rec.meta_description != None and len(rec.meta_description)>0:
                        response.meta.description = XML(rec.meta_description)
                else:
                    '''
                        No se ha podido encontrar que registro hay que leer
                        redireccionamos a la home (podría ser a la pag. del propio
                        modulo que está fallando)
                    '''
                    #TODO: Log Alert Read without match
                    raise HTTP(404)

        #Log info about this page view
        referrer = request.env.http_referer or ""
        currenthost = request.env.HTTP_HOST
        if currenthost != None:
            if referrer.find(currenthost) > -1:
                referrer = ""
        # TODO: Intentar con el log en ficheros (ver manual)
#         db.sitelog.insert(referrer=referrer,
#                           url=request.env.path_info,
#                           useragent=request.env.http_user_agent,
#                           userhostaddress=request.env.remote_addr,
#                           userhostname="",
#                           pageid=settings.currentpage)
        return dict(layoutsrc=layoutsrc)

    else:
        ''' request.env.web2py_original_uri "/inicio/fsad/32/default.aspx" '''

        url_in = request.env.web2py_original_uri

        ''' We go to see in the table 301 redirects if exists a match
        to make redirect 301 to url_out '''

        rec = db(db.redirects_301.url_in == url_in).select().first()
        if rec != None:
            if rec.url_out != None and len(rec.url_out) > 0:
                loc = URL(rec.url_out)
                if rec.url_out.find("http://") >= 0 or \
                                         rec.url_out.find("https://") >= 0:
                    loc = rec.url_out
            else:
                stpid = settings.startpageid
                loc = db_pages.Pages.Navigation().friendly_url_to_page(stpid)

            raise HTTP(301, 'Moved Permanently', Location=loc)
        else:
            clEventLog.eventlog("PAGE_LOAD_EXCEPTION", locals())
            raise HTTP(404)


@auth.requires_membership(settings.admin_role_name)
def pagemodule_delete():
    '''
        Se llama via Ajax desde la vista msettings.html cuando se hace click
        en el botón Borrar.
    '''
    pagmoduleid = int(request.vars.pagemoduleid)
    regpagmoduleid = db.pagemodules[pagmoduleid]
    moduleid = regpagmoduleid.moduleid
    db(db.pagemodules.id == pagmoduleid).update(isdeleted=True)
    query = (db.pagemodules.moduleid == moduleid) & ((db.pagemodules.isdeleted == False) | (db.pagemodules.isdeleted == None))
    recs = db(query).select()

    if len(recs) == 0:
        db(db.modules.id == moduleid).update(isdeleted=True)

    Url_dest = db_pages.Pages.Navigation().friendly_url_to_page(request.vars.pageid)
    return "window.location = '%s'" % Url_dest

@auth.requires_membership(settings.admin_role_name)
def pagemodule_deletex():
    '''
        Se llama via Ajax desde la vista msettings.html cuando se hace click
        en el botón Borrar de la pestaña "added to pages".
    '''
    pagmoduleid = int(request.vars.delpagemoduleid)
    db(db.pagemodules.id == pagmoduleid).update(isdeleted=True)

    Url_dest = URL(c="default", f="msettings",vars={
                                        'moduleid': request.vars.moduleid,
                                        'pageid': request.vars.pageid,
                                        'pagemoduleid':request.vars.pagemoduleid,
                                        },
                                        anchor="!smorepages")
    redirect(Url_dest)

@auth.requires_membership(settings.admin_role_name)
def msettings():
    '''
        Controla la Configuración de los módulos.

        Se construyen dos formularios distintos que leen el conjunto de los
        valores de configuración del módulo (tabla modules) y de la instancia
        del módulo (tabla pagemodules).

        También se crean unas variables settings_controller_load ,
        settings_function_load y settings_args que posibilitan renderizar otro
        formulario adicional con las configuraciones específicas del módulo.

        Este formulario específico del módulo se define en el módulo

    '''
    clpage_modules = db_pagemodules.PageModules()
    clbase_modules = db_basemodules.BaseModules()

    moduleid = int(request.vars.moduleid)
    pagemoduleid = int(request.vars.pagemoduleid)

    try:
        pageid = int(request.vars.pageid)
    except:
        pageid = int(request.vars.pageid[0])
        request.vars.pageid = pageid

    objpageid = db.pages[pageid]

    ''' Grid added to pages '''
    is_added_to_more_pages = False
    grid_more_pages = ''
    query = (db.pagemodules.moduleid == moduleid)
    query = query & ((db.pagemodules.isdeleted == False) | (db.pagemodules.isdeleted == None))
    recs = db(query).select()
    if len(recs) > 1:
        is_added_to_more_pages = True
        grid_more_pages = clpage_modules.grid_pagemodules(moduleid, pageid, pagemoduleid)

    '''Page Settings Form contains: title,container,border,color and other specific settings for module in this page...'''
    pagemoduleid = int(request.vars.pagemoduleid)
    form = clpage_modules.edit_pagemodule(pagemoduleid)

    '''Formulario de modules, contiene Fecha de inicio y de fin, all pages..'''
    form_module_settings = clbase_modules.WebForms().editar_module(moduleid)

    obj_pagemodule = db.pagemodules[pagemoduleid]
    moduledefid = db.modules[obj_pagemodule.moduleid].moduledefid
    basemoduleid = db.moduledefinitions[moduledefid].basemoduleid
    friendlyname = db.moduledefinitions[moduledefid].friendlyname
    objbasemodule = db.basemodules[basemoduleid]

    str_settings = T('Settings') + ' ' + friendlyname
    settings_controller_load = objbasemodule.controller
    settings_function_load = 'msettings'
    #settings_args = [str(moduleid), str(pageid), str(pagemoduleid)]
    settings_vars = dict(moduleid=moduleid, pageid=pageid,
                         pagemoduleid=pagemoduleid)
    
    if form_module_settings.accepts(request.vars, session):
            if request.vars.allpages == "on":
                clbase_modules.copy_pagemodule_all_pages(moduleid, pagemoduleid, pageid)
            elif request.vars.allpages == None:
                '''#Si este módulo existe para mas páginas, marcarlo como
                borrado isdeleted en el resto de paginas = True
                coger de pagemodules todos los que tengan moduleid = moduleid
                y pageid != pageid  y marcarlos como isdeleted=True '''
                query = (db.pagemodules.moduleid == moduleid) & \
                                            (db.pagemodules.pageid != pageid)
                db(query).update(isdeleted=True)

            urldest = str(URL(c='default', f='page', args=objpageid.slug))
            urldestf = urldest.replace('.load', '')
            redirect(urldestf)

    if form.accepts(request, session):
        urldest = db_pages.Pages.Navigation().friendly_url_to_page(pageid)
        urldestf = urldest.replace('.load', '')
        redirect(urldestf)
    else:
        response.flash = form.errors

    settings.controlpanelmode = "EDIT"

    btnreturn = clPynuke_nav.linkbutton(T("Volver"),
                                        settings.cssclass_icon_return,
                                        settings.cssclass_button_small + " " + settings.cssclass_button_warning ,
                                        objpageid.slug)

    return dict(form=form,
                settings_controller_load=settings_controller_load,
                settings_function_load=settings_function_load,
                settings_vars=settings_vars,
                layoutsrc=settings.layoutsrc,
                moduleid=moduleid,
                pagemoduleid=pagemoduleid,
                str_settings=str_settings,
                form_module_settings=form_module_settings,
                nextpageid=objpageid.id,
                nextpageslug=objpageid.slug,
                is_added_to_more_pages=is_added_to_more_pages,
                grid_more_pages=grid_more_pages,
                btnreturn=btnreturn)


def sitemap():
    # Adding Schemas for the site map
    xmlns = 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
    xmlns += 'xsi:schemaLocation="http://www.sitemaps.org/schemas/sitemap/0.9" '
    xmlns += 'xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset %s>\n' % (xmlns)
    # Define Domain
    Domain = request.wsgi.environ['wsgi.url_scheme'] + "://"
    Domain += request.wsgi.environ['HTTP_HOST']
    # Dynamic URLs From Pages
    pages = mptt_pages.descendants_from_node(1).select(orderby='pages.lft')
    for menu_entry in pages:
        pagina_visible = db_pagepermissions.PagePermissions().user_canviewpage(menu_entry.id, auth.user_id)
        if pagina_visible:
            sitemappriority = 0.5
            if menu_entry.sitemappriority != None:
                sitemappriority = menu_entry.sitemappriority
            #TODO: subdividir en varias lineas a poder ser con 3' y formateado
            sitemap_xml += '<url>\n<loc>%s/%s</loc>\n<lastmod>%s</lastmod>\n<changefreq>daily</changefreq>\n<priority>%s</priority>\n</url>\n' %(Domain,menu_entry.slug,format(menu_entry.lastmodifiedondate,'%Y-%m-%d'),sitemappriority)
    #TODO: incluir en el sitemap las entradas del blog
    sitemap_xml += '</urlset>'
    return sitemap_xml


def handle_error():
    """ Custom error handler that returns correct status codes."""
    code = request.vars.code
    request_url = request.vars.request_url
    ticket = request.vars.ticket
    # Get ticket URL:
    '''TODO: si estamos en local el scheme no debería ser https '''
    elements = {'scheme':'https','host':request.env.http_host,'ticket':ticket}
    ticket_url = "<a href='%(scheme)s://%(host)s/admin/default/ticket/%(ticket)s' target='_blank'>%(ticket)s</a>" % elements
    '''Make sure error url is not current url to avoid infinite loop.'''
    if code is not None and request_url != request.url:
        ''' Assign the error status code to the current response.
        (Must be integer to work.) '''
        response.status = int(code)

    if code == '403':
        return "Not authorized"
    elif code == '404':
        file_html_error = 'views/errors/error_%i.html' % int(code)
        filename = os.path.join(request.folder, file_html_error)

        if os.access(filename, os.R_OK):
            body = open(filename, 'r').read()
        else:
            body = "<h1>Error 404</h1>"
        return  body

    elif code == '500':
       
        #TODO: Establecer una opcion para envio de correos con errores
#        MimeMail = Mail()
#        #Email a notice, etc:
#        MimeMail.send(to=['admins@myapp.com '],
#        subject="New Error",
#        message="Error Ticket: %s" % ticket_url)
        return "Server error:" + "Error Ticket: %s" % ticket_url
    else:
        return "Other error"

def index():
    ''' Redirecciona a la funcion page donde averiguará y cargará la
    página por defecto '''
    return redirect(URL(c="default", f="page"))

