# -*- coding: utf-8 -*-
#from gluon import *
#import uuid

# The code below is not executed, only is for hide errors in eclipse '''
if False:
    from applications.init.modules import *
    from db import *
    request, session, response, T, cache = current.request, current.session,\
                                    current.response, current.t, current.cache
    auth = Auth(db, hmac_key=Auth.get_or_create_key())
    crud, service, plugins = Crud(db), Service(), PluginManager()
    settings = current.settings

''' Defaults '''
default_a = request.application
default_c = None
default_f = None

''' Direct access to some request objects '''
req_cont = request.controller
req_func = request.function
req_args = request.args

''' Direct access to some classes '''
clpagsdb = db_pages.Pages.Db_Functions()
clpagnav = db_pages.Pages.Navigation()
clpackages = db_packages.Packages()
clpynuke = db_pynuke.PyNuke()
clperm = db_pagepermissions.PagePermissions()
clsec = security.Security()
clpk = db_packages.Packages()

''' Customize Logo, bootstrap Brand, Titles etc... '''
imglogo = options["img_logo"]
linklogo = options["link_logo"]
bootstrap_brand = options["bootstrap_brand"]
head_page, footer_page = '', ''
if (imglogo == ""):
    response.site_title = settings.site_title
    response.site_description = settings.site_description
else:
    urlimg = URL('static', imglogo)
    htmlimg = "<a href='" + linklogo + "'>" "<img style='max-width:100%;height:auto' src ='" + urlimg + "' />" \
                                                                 + "</a>"
    response.logo = XML(htmlimg)

# Metas by default for the whole site
response_meta_description = settings.site_description
response_meta_keywords = settings.keywords
response_title = settings.site_title

'''Layout in options (Admin - Sitesettings) or bootstrap basic layout 
or specified at page settings level '''

try:
    pld = int(options['plugin_layout_default'])
    pcd = int(options['plugin_container_default'])
    settings.layoutsrc = clpackages.get_src_layout_by_layoutid(pld)
    settings.containersrc = clpackages.get_src_layout_by_layoutid(pcd)
    settings.plugin_layout_default = pld
    settings.plugin_container_default = pcd
    
except Exception, e:
    settings.layoutsrc = "plugin_layout_bootstrap/layout.html"
    settings.containersrc = "plugin_containers_bootstrap/containerh1.html"
    settings.plugin_layout_default = 1
    settings.plugin_container_default = 2



#########################################################################
## In wich pageid we are ??
#########################################################################
if (req_cont == 'default') and (req_func == 'page') and len(req_args) > 0:
    try:
        pageid = clpagnav.get_pageid_by_requestargs(req_args)
        if pageid == -1:
            if req_args(0) == 'index':
                pageid = int(settings.startpageid)
    except Exception, e:
        pageid = -1
        #pageid = int(settings.startpageid)
else:
    pageid = clpagnav.get_pageid_by_controller_function(req_cont, req_func)
    if pageid == -1:
        if (req_cont == 'default') and (req_func == 'page'):
            pageid = int(settings.startpageid)

idpage = pageid
settings.currentpage = pageid
settings.breadcrumbs_links = []
settings.breadcrumbs_titles = []


def get_scheme(menu_entry):
    txtscheme = 'http'
    if settings.forcessl or menu_entry.issecure:
        txtscheme = 'https'
    return txtscheme


def get_linked_to(menu_entry):
    linked_to = ''
    txtscheme = get_scheme(menu_entry)
    a = menu_entry.a or default_a
    c = menu_entry.c or default_c
    f = menu_entry.f or default_f

    if xstr(menu_entry.c) != '' and xstr(menu_entry.f) != '' and not menu_entry.disablelink:                                                               
        linked_to = URL(a, c, f, args=[menu_entry.slug] if menu_entry.slug!= None else None,
                        user_signature=menu_entry.signature,
                        scheme=txtscheme)
    else:
    # Si no tiene nada en Controlador o Funcion se apunta a default / index / id / slug #agregado slug
        if not menu_entry.disablelink:
            linked_to = URL(a=a, c='default',f='page',args=[menu_entry.slug],user_signature=menu_entry.signature,scheme=txtscheme)
        #si coincide el default/page/10 de la pagina (request) con el registro hemos de seleccionarlo también
            if req_cont == 'default' and req_func == "page" and req_args(0) == str(menu_entry.id):
                sel = True

    return linked_to


def xstr(s):
    return '' if s is None else str(s)


def def_settings_breadcrumbs():
    settings.ancestors_from_page = mptt_pages.ancestors_from_node(settings.currentpage,
                              include_self=True).select(orderby=db.pages.lft)
    sep = ""
    tmplisbc = []
    objstartpage = db.pages[settings.startpageid]

    if settings.currentpage == objstartpage.id:
        titpaginicio = objstartpage.name or T("Home")
        tmplisbc = [LI(A(titpaginicio, _href="/"))]
    else:
        contains_startpage = False
        for br in settings.ancestors_from_page:
            if br.id == objstartpage.id:
                contains_startpage = True
                break
        is_first = True
        if not contains_startpage:
            titpaginicio = objstartpage.name or T("Home")
            tmplisbc = [LI(A(titpaginicio, _href="/"))]
            is_first = False
        for br in settings.ancestors_from_page:
            if br.node_type != 'root':
                if br.id != obj_current_page.id:
                    lnk = get_linked_to(br)
                    if br.disablelink is not True:
                        if is_first:
                            tmplisbc.append(LI(A(br.name, _href=lnk)))
                            is_first = False
                        else:
                            tmplisbc.append(LI(sep, A(br.name, _href=lnk)))
                    else:
                        tmplisbc.append(LI(sep, br.name, _class="active"))
                else:
                    if br.id != int(settings.startpageid):
                        if is_first:
                            tmplisbc.append(LI(br.name, _class="active"))
                        else:
                            tmplisbc.append(LI(sep, br.name, _class="active"))
    return UL(tmplisbc, _class="breadcrumb")


def global_page_settings(obj_current_page):
    # This function replace default settings defined in config_settings pynuke.py
    settings.currentpage = obj_current_page.id
    settings.masthead = obj_current_page.sectionheadervisible
    settings.currentpageslug = obj_current_page.slug
    settings.current_page_panes = clpk.get_panes_from_layout_file(obj_current_page.layoutsrc or pld)

    # seguridad
    if clperm.user_canviewpage(obj_current_page.id, auth.user_id):
        settings.listload, settings.listcontrols = clpynuke.pre_render_modules(obj_current_page)
    else:
        pageid = int(settings.startpageid)
        settings.currentpage = obj_current_page.id
        settings.authorized = False
        settings.listload, settings.listcontrols = None, None

    settings.currentpage_is_system_page = clpagsdb.is_system_page(obj_current_page)
    txtscheme = 'http'
    if settings.forcessl or obj_current_page.issecure:
        txtscheme = 'https'

    settings.currentpage_scheme = txtscheme
    # diseño
    if obj_current_page.layoutsrc != None:
        if obj_current_page.layoutsrc > 0 and obj_current_page.layoutsrc != '':
            settings.page_layoutsrc = obj_current_page.layoutsrc
            settings.layoutsrc = clpackages.get_src_layout_by_layoutid(obj_current_page.layoutsrc)
    if xstr(obj_current_page.containersrc) != '':
            settings.containersrc_pag = clpackages.get_src_layout_by_layoutid(obj_current_page.containersrc)

    #breadcrumbs
    settings.breadcrumbs = def_settings_breadcrumbs()

    

    return

if pageid != -1:
    obj_current_page = db.pages[pageid]
    global_page_settings(obj_current_page)

    if xstr(obj_current_page.description) != '':
        response_meta_description = XML(obj_current_page.description)

    if xstr(obj_current_page.title) != '':
        response_title = XML(obj_current_page.title)

    if xstr(obj_current_page.keywords) != '':
        response_meta_keywords = XML(obj_current_page.keywords)

    if xstr(obj_current_page.pageheadtext) != '':
        head_page = XML(obj_current_page.pageheadtext)

    if xstr(obj_current_page.pagefootertext) != '':
        footer_page = XML(obj_current_page.pagefootertext)

    response.showcontrolpanel = clsec.user_can_view_controlpanel(auth.user_id)

#Escribir los metas finales de la pagina
response.meta.author = XML(settings.author)
response.title = response_title
response.meta.generator = settings.generator
response.meta.copyright = settings.copyright
response.meta.description = response_meta_description
response.meta.keywords = settings.keywords

if settings.google_analytics_id != '':
    response.google_analytics_id = settings.google_analytics_id

response.ttt_allpages = mptt_pages.descendants_from_node(1,
                                        onlyactivated=False,
                                        onlyvisibles=False).select(
                                        orderby='pages.lft')
response.ttt = mptt_pages.descendants_from_node(1,
                                              onlyactivated=False,
                                              onlyvisibles=True).select(
                                                    orderby='pages.lft')
response.ttt2 = mptt_pages.descendants_from_node(2).select(orderby='pages.lft',
                                                           )
response.tttmenu = [dict(), dict()]
response.tttmenu2 = [dict(), dict()]


def get_entry_selected(menu_entry):
    '''
        ¿Está esta entrada seleccionada?

        pageid --> contiene la pagina a la que vamos
        menu_entry --> a esta función venimos desde la creación del menu
                        para chequear si esa opción ha de aparecer seleccionada

    '''
    a = menu_entry.a or default_a
    c = menu_entry.c or default_c
    f = menu_entry.f or default_f
    '''
        Esto es una comprobación inicial, al final, sel puede variar
        según diversos factores que se van a comprobar

    '''
    sel = (req_cont == c and req_func == f and \
            (req_args and req_args == menu_entry.args or True))
    '''
        Si es una entrada padre (tiene parent_id = 1)
        la dejamos seleccionada si el req_cont es el mismo
    '''
    if menu_entry.parent == 1 and req_cont == menu_entry.c \
                                and req_func == menu_entry.f:
        sel = True
    '''
        Si es una entrada padre (tiene parent_id = 1)
        la dejamos seleccionada si el req_cont es el mismo
        pero no es un page
    '''
    if menu_entry.parent == 1 and req_cont == menu_entry.c \
                                    and req_func != "page":
        sel = True

    '''Si es una pagina de tipo /default/page/algodeslug '''
    if req_cont == 'default' and req_func == "page":
        if req_args(0) == menu_entry.slug:
            sel = True
        '''
            si la pagina a la que voy tiene esta como padre,
            dejamos esta seleccionada
        '''
        if settings.ancestors_from_page != None:
            for r in settings.ancestors_from_page:
                if pageid != -1  and r.id == menu_entry.id:
                    sel = True
                    break
    return sel


for menu_entry in response.ttt:
    if clperm.user_canviewpage(menu_entry.id, auth.user_id) and menu_entry.isvisible:
        sel = get_entry_selected(menu_entry)
        #If has url, we link to this url
        if xstr(menu_entry.url) != '' and not menu_entry.disablelink:
            linked_to = menu_entry.url
        else:
            linked_to = get_linked_to(menu_entry)

        response.tttmenu[0][str(menu_entry.id)] = [menu_entry.name, sel,
                                                   linked_to, menu_entry.parent
                                                   ]

        if str(menu_entry.parent) in response.tttmenu[1]:
            response.tttmenu[1][str(menu_entry.parent)].append(menu_entry.id)
        else:
            # si hay permisos para ver la pagina padre, agregamos esta al menu
            if menu_entry.parent > 1:
                if clperm.user_canviewpage(menu_entry.parent, auth.user_id):
                    response.tttmenu[1][str(menu_entry.parent)] = [menu_entry.id]
            else:
                response.tttmenu[1][str(menu_entry.parent)] = [menu_entry.id]

for menu_entry in response.ttt2:
    if clperm.user_canviewpage(menu_entry.id, auth.user_id) and menu_entry.isvisible:
        txtscheme = get_scheme(menu_entry)
        a = menu_entry.a or default_a
        c = menu_entry.c or default_c
        f = menu_entry.f or default_f
        sel = get_entry_selected(menu_entry)
        linked_to = ''

        #Si tiene URL va linkado directamente a la URL
        if xstr(menu_entry.url) != '' and not menu_entry.disablelink:
            linked_to = URL(menu_entry.url, scheme=txtscheme)
        else:
            # Si tiene algo en Controlador o Funcion se monta el linked_to con esos valores
            if xstr(menu_entry.c) != '' and xstr(menu_entry.f) != '' and not menu_entry.disablelink:
                linked_to = URL(a, c, f, args=menu_entry.args or None,
                                user_signature=menu_entry.signature,
                                scheme=txtscheme)
            else:
            # Si no tiene nada en Controlador o Funcion se apunta a default / index / id
                if not menu_entry.disablelink:
                    linked_to = URL(a=a, c='default',f='page',args=[menu_entry.slug],user_signature=menu_entry.signature,scheme=txtscheme)                #si coincide el default/page/10 de la pagina (request) con el registro hemos de seleccionarlo también
                    if req_cont == 'default' and req_func == "page" and req_args(0) == str(menu_entry.id):
                        sel = True 

        response.tttmenu2[0][str(menu_entry.id)] = [T(menu_entry.name),sel,linked_to,menu_entry.parent]

        if str(menu_entry.parent) in response.tttmenu2[1]:
            response.tttmenu2[1][str(menu_entry.parent)].append(menu_entry.id)
        else:
            response.tttmenu2[1][str(menu_entry.parent)] = [menu_entry.id]


def buildmenu(parent, menu):
    #TODO:Extraido del grupo de usuarios web2py en Ingles... pendiente buscar y reconocer autor
    html = []
    if len(menu[1]) > 0:
        if menu[1][str(parent)]:
            for itemid in menu[1][str(parent)]:
                if str(itemid) in menu[1]:
                    #children
                    selected = menu[0][str(itemid)][1]
                    pageurl = str(menu[0][str(itemid)][2])
                    html.append((str(menu[0][str(itemid)][0]), selected, pageurl, buildmenu(itemid, menu)))
                else:
                    selected = menu[0][str(itemid)][1]
                    #no children
                    pageurl = str(menu[0][str(itemid)][2])
                    html.append((str(menu[0][str(itemid)][0]), selected, pageurl))
    return html

if pageid != -1 or (req_cont == "default" and req_func == "user"):
    response.menu = buildmenu(1, response.tttmenu)
    if (auth.user_id != None) and (clsec.user_is_admin(auth.user_id)):
        response.menu += buildmenu(2, response.tttmenu2)
        pass
