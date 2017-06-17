# -*- coding: utf-8 -*-
from applications.init.modules import db_pagepermissions, db_pagemodules, \
                                        db_pages

if False:
    from applications.init.models import *
    from gluon import *
    from gluon.tools import *
    from applications.init.modules import db_options, db_basemodules
    db = DAL()
    auth = Auth(db)
    request,session,response,T,cache=current.request,current.session,current.response,current.t,current.cache 
    db = current.db
    settings = current.settings
    options = current.options
    auth = Auth(db, hmac_key=Auth.get_or_create_key())
    crud, service, plugins = Crud(db), Service(), PluginManager()

clpf = db_pages.Pages.Db_Functions()
clpm = db_pagepermissions.PagePermissions()

@auth.requires_membership(settings.admin_role_name)
def controlpanel():
    '''
        Esta es la primera funcion que carga el panel de control en la parte
        superior,
    '''
    response.view = settings.layoutsrc.split("/")[0] + '/controlpanel/controlpanel.html'
    #TODO: en la vista mirar los mensajes javascript y traducirlos como en 19
    pageid = settings.currentpage
    ddlmodules = get_modulesdefinitions()
    ddlpages = pages_get()
    can_page_be_deleted = True
    if pageid != -1:
        panes_in_page = get_panes_byidpage(pageid)
        can_page_be_deleted = not settings.currentpage_is_system_page
        can_page_be_exported = not settings.currentpage_is_system_page
        can_add_modules = not clpf.settings.currentpage_is_system_page
        can_copy_page = not clpf.settings.currentpage_is_system_page
    else:
        panes_in_page = 'contentpane'

    return dict(ddlmodules=ddlmodules,
                layoutsrc=settings.layoutsrc,
                panes_in_page=panes_in_page,
                ddlpages=ddlpages,
                pageid=settings.currentpage,
                can_page_be_deleted=can_page_be_deleted,
                can_page_be_exported=can_page_be_exported,
                can_add_modules=can_add_modules,
                can_copy_page=can_copy_page
                )


@auth.requires_membership(settings.admin_role_name)
def togglecpanel():
    if session.cpanelvisibility:  # can use cookie
        if session.cpanelvisibility == "MAX":
            session.cpanelvisibility = "MIN"
        else:
            session.cpanelvisibility = "MAX"
    else:
        session.cpanelvisibility = "MAX"

    settings.controlpanelvisibility = session.cpanelvisibility

    return


@auth.requires_membership(settings.admin_role_name)
def togglecpanelmode():
    mode = request.vars['txtcpmode']
    settings.controlpanelmode = mode
    session.controlpanelmode = mode
    return 'window.location = window.location.href;'


@auth.requires_membership(settings.admin_role_name)
def get_modulesdefinitions():
    '''
        Esta función se usa via AJAX en el panel de control para construir
        la lista desplegable de los modulos disponibles de forma dinámica.
        No muestra los módulos marcados como Admin en Modulebase
    '''
    result = ''
    try:
        pageid = settings.currentpage
        can_add_modules = not settings.currentpage_is_system_page
        tmd = db.moduledefinitions
        modulesdefinitions = db((tmd.id > 0)).select(orderby=tmd.id)
        if len(modulesdefinitions) > 0:
            if can_add_modules:
#                 result = '''
#                 <select style='width:185px;' name='listmodules' id='listmodules'>
#                         '''
                for modef in modulesdefinitions:
                    basemodule = db.basemodules[modef.basemoduleid]
                    if basemodule.isadmin == False:
                        result += "<option value='" + str(modef.id) + "'>" + \
                                                modef.friendlyname + "</option>"
#             else:
#                 result = '''
#                 <select style='width:185px;' name='listmodules' disabled='True' id='listmodules'>
#                         '''
            #result += "</select>"

    except Exception, e:
        result = str(e)

    return XML(result)


@auth.requires_membership(settings.admin_role_name)
def add_module():
    '''
        Esta función se usa via AJAX en el panel de control para agregar
        nuevos modulos o modulos existentes en otras paginas.

        optmoduletype 0 es un nuevo modulo,
        optmoduletype 1 es un modulo existente...

        si es un nuevo modulo, como hasta ahora, 

        si es un modulo existente, se agrega a esta pagina una instancia 
        del módulo original, solo se agrega en la tabla pagemodules

    '''
    rv = request.vars
    moduletype = int(rv.optmoduletype)
    #existingmoduleid = int(request.vars.listpagemodules)
    moduledefid = int(rv.listmodules)
    panetoadd = int(rv.listpanes)
    pagetoadd = int(rv.txtpageid)
    position = int(rv.cboposition)  # -1 bottom - 0 Top
    alignment = rv.cboalignment

    if moduletype == 1:  # Modulo existente
        if int(rv.listpagemodules) > 0: 
            idexistingpagemodule = int(rv.listpagemodules)
            moduleid = db.pagemodules[idexistingpagemodule].moduleid
            obj_module_to_duplicate = db.pagemodules[idexistingpagemodule]
            #if copy settings then copy title if blank ...
            if rv.chkcopysettings <> 'F' and rv.txttitle=='' :
                titlemoduletoadd = obj_module_to_duplicate.moduletitle
            else:
                titlemoduletoadd = rv.txttitle

            new_pagemoduleid = db.pagemodules.insert(pageid=pagetoadd,
                            moduleid=moduleid,
                            moduletitle=titlemoduletoadd,
         moduleorder=obj_module_to_duplicate.moduleorder,
         alignment=obj_module_to_duplicate.alignment, color=obj_module_to_duplicate.color,
         border=obj_module_to_duplicate.color, iconfile=obj_module_to_duplicate.iconfile,
         panename=panetoadd, cachetime=obj_module_to_duplicate.
         cachetime, visibility=obj_module_to_duplicate.visibility,
         containersrc=obj_module_to_duplicate.containersrc,
         displaytitle=obj_module_to_duplicate.displaytitle,
         displayprint=obj_module_to_duplicate.displayprint,
         displaysyndicate=obj_module_to_duplicate.displaysyndicate,
         cachemethod=obj_module_to_duplicate.cachemethod,
         header=obj_module_to_duplicate.header, footer=obj_module_to_duplicate.footer,
         culturecode=obj_module_to_duplicate.culturecode)
            #optionally copy settings ...
            if rv.chkcopysettings <> 'F':
                settings_to_duplicate = db(db.modulesettings.pagemoduleid==idexistingpagemodule).select()
                for setting in settings_to_duplicate:
                    db.modulesettings.insert(pagemoduleid=new_pagemoduleid,
                                             settingname=setting.settingname,
                                             settingvalue=setting.settingvalue)

    else:  # Modulo nuevo de tipo moduledefid
        titlemoduletoadd = rv.txttitle
        db_basemodules.BaseModules().add_module(moduledefid, titlemoduletoadd,
                                            panetoadd, pagetoadd, position,
                                            alignment)
    return 'window.location = window.location.href;'


@auth.requires_membership(settings.admin_role_name)
def get_panes_byidpage(idpage):
    layoutid = int(options["plugin_layout_default"])
    if settings.page_layoutsrc != None and settings.page_layoutsrc > 0:
        layoutid = settings.page_layoutsrc

    query = (db.layouts_panes.layout == layoutid)
    recs_results = db(query).select(orderby=db.layouts_panes.panename)
    can_add_modules = not settings.currentpage_is_system_page
    #result = "<select style='width:150px' name='listpanes'>"
    #result = "<option value=''>" + '' + "</option>"
    result = ""
    if len(recs_results) > 0:
        if can_add_modules:
            #result = "<select style='width:150px;' name='listpanes'>"
            for pane in recs_results:
                result += "<option value='" + str(pane.id) + "'>" + pane.panename \
                             + "</option>"
        #else:
            #result = "<select style='width:150px' disabled='True' name='listpanes'>"
        #    result = "<option value=''>" + '' + "</option>"

        #result += "</select>"

    return XML(result)


@auth.requires_membership(settings.admin_role_name)
def pages_get():
    '''
        Esta función se usa para construir la lista desplegable de las paginas 
        disponibles de forma dinámica.
    '''
    result = ''
    try:
        pages = mptt_pages.descendants_from_node(1).select(orderby='pages.lft')
        result = '''
        <select onchange="changed_pages();" style="width: 185px; display: None;"
            name='listpages' id='listpages'>
            <option value='-1'></option>
        '''

        for menu_entry in pages:
            pagina_visible = clpm.is_page_visible(menu_entry)
            if pagina_visible:
                if settings.currentpage != menu_entry.id:
                    titulom = menu_entry.slug
                    if menu_entry.level > 1:
                        titulom = ("__" * menu_entry.level) + titulom
                    result += "<option value='" + str(menu_entry.id) + "'>" + \
                                                titulom + "</option>"

        result += "</select>"

    except Exception, e:
        result = str(e)

    return XML(result)


@auth.requires_membership(settings.admin_role_name)
def pagemodules_get():
    '''
        Esta función se usa para construir la lista desplegable de los
        módulos de una pagina cuando se selecciona agregar un modulo existente.

        devuelve varias acciones javascript que se ejecutan en la pagina
        1 vacia la lista
        2 para cada elemento crea una nueva option con
            $(“#ComboBox”).html(“”);
    http://elegantcode.com/2009/07/01/jquery-playing-with-select-dropdownlistcombobox/

    '''
    result = "jQuery('select[name=listpagemodules]').empty();"

    try:
        pageid_origen_mods = request.vars.listpages
        pmods = db_pagemodules.PageModules().get_pagemodules(pageid_origen_mods)

        for pm in pmods:
            #TODO:Verificar que el módulo no esté ya agregado a esta página
            #if pm.pageid != int(request.args.pageid):
            result += "jQuery('<option value=%s>%s</option>').appendTo(listpagemodules);"% (pm.id,pm.moduletitle)

    except Exception, e:
        result = str(e)
    return result