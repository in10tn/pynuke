# -*- coding: utf-8 -*-
#import gluon.contenttype
import yaml
import os.path
from gluon.tools import *
from applications.init.modules.plugin_jstree import JsTree
from applications.init.modules.plugin_mptt import MPTT
from applications.init.modules import db_pages, db_options, db_basemodules,\
    db_packages
from applications.init.modules import db_pagemodules, db_packages, db_redirects
from applications.init.modules import db_security, db_pynuke
from applications.init.modules import db_pagepermissions
from applications.init.modules import db_permissions, db_sitelog, db_eventlog

import datetime
import zipfile
import urllib
from gluon.fileutils import up, fix_newlines, abspath, recursive_unlink
from gluon.fileutils import read_file, write_file, parse_version
from urllib import urlopen
#from docutils.transforms.universal import Messages

if False:
    from gluon import *
    from applications.init import *
    db = DAL()
    auth = Auth(db)
    request, session = current.request, current.session
    db = current.db
    settings = current.settings
    options = current.options
    auth = Auth(db, hmac_key=Auth.get_or_create_key())
    crud, service, plugins = Crud(db), Service(), PluginManager()
    response = current.response
    T = current.T


jstree = JsTree(tree_model=mptt_pages, renderstyle=True)

clPagNav = db_pages.Pages.Navigation()
clPackWF = db_packages.Packages.WebForms()
clPackYAML = db_packages.Packages.yaml_utils()
clPack = db_packages.Packages()
clpwf = db_pages.Pages.WebForms()
clper = db_pagepermissions.PagePermissions()
cldbper = db_permissions.Permissions()
cldbpn = db_pynuke.PyNuke()
clPyNav = db_pynuke.PyNuke.Navigation()
clPyMes = db_pynuke.PyNuke.Messages()
clSiteLog = db_sitelog.SiteLog()
clEventLog = db_eventlog.EventLog()
clBaseModules = db_basemodules.BaseModules()
clPyPages = db_pynuke.PyNuke.Pages()
req_uri = request.env.request_uri
cldbpnu = db_pynuke.PyNuke.Upgrades()
clpk = db_packages.Packages()

@auth.requires_membership(settings.admin_role_name)
def pages():
    ''' Funcion Admin - Pages donde se ve el arbol de paginas y pinchando
        en un elemento del arbol se visualiza el formulario de ediciÃ³n llamando
        a page_get en este mismo controlador
    '''
    response.view = 'views_plugin_generics/tree_and_form.html'
    module_title=T('Pages')

    if request.vars.issecure != None and int(request.vars.id or 0) > 0:            
            id_page_parent = int(request.vars.parent)
            page_id = request.vars.id
            if request.vars.slug == "":
                request.vars.slug = clPyPages.get_pageslug_hierarchical(id_page_parent,request.vars.name)
            else:
                request.vars.slug = clPyNav.clean_slug(request.vars.slug)

            clpwf.proccess_update_or_delete_page(page_id, request.vars)

    button_return = clPyNav.linkbutton(
       T("Return"),
       settings.cssclass_icon_return,
       settings.cssclass_button_small + " " + settings.cssclass_button_warning,
       settings.startpageid)

    return dict(tree_block=DIV(jstree(), _style='width:300px;'),
                module_title=module_title,
                button_return=button_return
                )


@auth.requires_membership(settings.admin_role_name)
def page_get():
    '''
        This function is called from jstree when click in some page (pageid)

        The root nodes "My web site" and "System Menu" are created automatically
        when installing Pynuke, we filter these nodes...

    '''
    response.view = 'admin/form_page.html'
    pageid = int(request.vars.id)
    title = T('Edit Page')
    form_edit_page = ''
    valcheckallusersr = ''
    valcheckallusersw = ''
    recroles = ''
    linktopage = ''
    dchecks = ''
    can_edit_page = pageid > 2

    if pageid > 2:
        linktopage = clPagNav.friendly_url_to_page(pageid)

        pereditpage = settings.pereditpage
        perviewpage = settings.perviewpage

        valcheckallusersr = clper.user_canviewpage(pageid, None)
        valcheckallusersw = clper.user_caneditpage(pageid, None)

        queryroles = ~(db.auth_group.role.like('user_%'))
        queryroles = queryroles & (db.auth_group.id > 1)
        recroles = db(queryroles).select(orderby=db.auth_group.id)

        dchecks = {}
        dcheckshidden = {}

        for r in recroles:
            #Read permissions
            dchecks['checkr' + str(r.id)] = cldbper.rol_has_permission(r.id,
                                                                    pageid,
                                                                    perviewpage)

            #write permissions
            dchecks['checkw' + str(r.id)] = cldbper.rol_has_permission(r.id,
                                                                    pageid,
                                                                    pereditpage)
            dcheckshidden['checkr' + str(r.id)] = 'F'
            dcheckshidden['checkw' + str(r.id)] = 'F'

        form_edit_page = clpwf.editar(pageid, dcheckshidden)

        if form_edit_page.process(dbio=False).accepted:
            if request.vars.issecure is not None and int(request.vars.id) > 0:
                id_page = int(request.vars.id)
                request.vars.slug = clPyNav.clean_slug(request.vars.slug)
                if request.vars.slug == '':
                    request.vars.slug = IS_SLUG()(request.vars.name)[0]
                else:
                    request.vars.slug = IS_SLUG()(request.vars.slug)[0]

                reqvars = request.vars
                clpwf.proccess_update_or_delete_page(id_page, reqvars)
                response.flash = T("Saved Page")
    settings.layoutsrc = None
    return dict(form=form_edit_page,
                valcheckallusersr=valcheckallusersr,
                valcheckallusersw=valcheckallusersw,
                recroles=recroles,
                dchecks=dchecks,
                title=title,
                can_edit_page=can_edit_page,
                linktopage=linktopage
                )


@auth.requires_membership(settings.admin_role_name)
def page_delete():
    ''' called via ajax from control panel when delete a page '''
    id_page = int(request.vars.pageid)

    if db_pages.Pages().page_delete(id_page):
        startpageid = int(settings.startpageid)
        result = ('window.location = "' +
            str(clPagNav.friendly_url_to_page(startpageid)) + '";')
    else:
        result = ('javascript:alert("' + T("You Cannot delete this page")
                   + '");')

    return result


@auth.requires_membership(settings.admin_role_name)
def copy_page_permissions_to_descendents(pageorigin):

    return


@auth.requires_membership(settings.admin_role_name)
def edit_page():
    response.view = 'admin/form_page.html'
    title = T('Edit Page')
    pageid = -1
    pereditpage = settings.pereditpage
    perviewpage = settings.perviewpage
    try:
        request_args = request.args
        pageid = int(request_args[0])
        objpage = db.pages[pageid]
    except Exception:
        pageid = -1

    valcheckallusersr = clper.user_canviewpage(pageid, None)
    valcheckallusersw = clper.user_caneditpage(pageid, None)

    queryroles = ~(db.auth_group.role.like('user_%'))
    queryroles = queryroles & (db.auth_group.id > 1) & (db.auth_group.id != 3)
    recroles = db(queryroles).select(orderby=db.auth_group.id)

    dchecks = {}
    dcheckshidden = {}

    for r in recroles:
        #Permisos de lectura
        dchecks['checkr' + str(r.id)] = cldbper.rol_has_permission(r.id,
                                                                pageid,
                                                                perviewpage)

        #Permisos de escritura
        dchecks['checkw' + str(r.id)] = cldbper.rol_has_permission(r.id,
                                                                pageid,
                                                                pereditpage)
        dcheckshidden['checkr' + str(r.id)]='F'
        dcheckshidden['checkw' + str(r.id)]='F'
    form_edit_page = clpwf.editar(pageid, dcheckshidden)
    if form_edit_page.process(dbio=False).accepted:
        if request.vars.issecure is not None and int(request.vars.id) > 0:
            id_page = int(request.vars.id)
            reqvars = request.vars
            if request.vars.slug == '':
                # request.vars.slug = IS_SLUG()(request.vars.name)[0]
                request.vars.slug = clPyPages.get_pageslug_hierarchical(
                                                        request.vars.parent,
                                                        request.vars.name
                                                                        )
            else:
                slugfinal = ""
                request.vars.slug = clPyNav.clean_slug(request.vars.slug)
                for s in request.vars.slug.split("/"):
                    slugfinal += IS_SLUG()(s)[0] + "/"
                if slugfinal.endswith("/"):
                    slugfinal = slugfinal[:-1]
                request.vars.slug = slugfinal

            clpwf.proccess_update_or_delete_page(id_page, reqvars)
            clEventLog.eventlog("PAGE_UPDATED", locals())
            response.flash = T("Page saved")
            redirect(URL(c='default', f='page', args=request.vars.slug))

    return dict(form=form_edit_page,
                layout=settings.layoutsrc,
                title=title,
                valcheckallusersr=valcheckallusersr,
                valcheckallusersw=valcheckallusersw,
                recroles=recroles,
                dchecks=dchecks,
                linktopage=clPagNav.friendly_url_to_page(objpage.id),
                pageid=pageid
                )


@auth.requires_membership(settings.admin_role_name)
def add_page():
    response.view = 'admin/form_page.html'
    title = T('Add Page')

    try:
        request_args = request.args
        pageid = int(request_args[0])
        objpage = db.pages[pageid]
    except Exception:
        pageid = -1

    ''' Permissions by page '''
    queryroles = ~(db.auth_group.role.like('user_%'))
    queryroles = queryroles & (db.auth_group.id > 1)
    recroles = db(queryroles).select(orderby=db.auth_group.id)
    list_checks = []
    dict_checks = {}  # Para evitar que si llega blanco no se pase el control

    namefieldr = ('allusersr')
    namefieldw = ('allusersw')
    writ = True
    defa = False
    citemr = Field(namefieldr, 'boolean', writable=writ,
                    label=T("All Users"), default=defa)
    list_checks.append(citemr)
    citemw = Field(namefieldw, 'boolean', writable=writ,
                   label=T("All Users"), default=defa)
    list_checks.append(citemw)
    dict_checks[namefieldr] = 'F'
    dict_checks[namefieldw] = 'F'

    for r in recroles:
        writ = True
        defa = False
        namefieldr = ('checkr' + str(r.id))
        namefieldw = ('checkw' + str(r.id))
        citemr = Field(namefieldr, 'boolean', writable=writ,
                        label=r.role, default=defa)
        list_checks.append(citemr)
        citemw = Field(namefieldw, 'boolean', writable=writ,
                       label=r.role, default=defa)
        list_checks.append(citemw)
        dict_checks[namefieldr] = False
        dict_checks[namefieldw] = False

    hiddenchecks = dict_checks

    db.pages.parent.requires = IS_IN_SET(clPyPages.get_pages_hierarchical(show_root=True))
    db.pages.parent.required = True
    db.pages.parent.default = 1

    form_new_page = SQLFORM.factory(db.pages, *list_checks, hidden=hiddenchecks)

    if form_new_page.accepts(request, session, dbio=False):
        if request.vars.slug == '':               
                request.vars.slug = clPyPages.get_pageslug_hierarchical(request.vars.parent,request.vars.name)
        else:
            slugfinal = ""
            request.vars.slug = clPyNav.clean_slug(request.vars.slug)
            for s in request.vars.slug.split("/"):
                slugfinal += IS_SLUG()(s)[0] + "/"
            if slugfinal.endswith("/"):
                slugfinal = slugfinal[:-1]
            request.vars.slug = slugfinal
            
        db_pages.Pages().WebForms().proccess_form_add_page(request.vars)
        redirect(URL(c='default', f='page', args=request.vars.slug))

    return dict(form=form_new_page,
                layout=settings.layoutsrc,
                title=title,
                recroles=recroles,
                valcheckallusersr=False,
                valcheckallusersw=False,
                dchecks=dict_checks,
                linktopage=clPagNav.friendly_url_to_page(objpage.id)
                )


@auth.requires_membership(settings.admin_role_name)
def export_page():
    #TODO: Trabajo en curso
    # El objetivo es generar un fichero XML o YAML que se pueda descargar y
    # luego se pueda importar, no estÃ¡ acabado
    pageid = int(request.args(0))
    obj_page = db.pages[pageid]
    modulesinpage = db_pagemodules.PageModules().get_pagemodules(obj_page.id)
    mp ={}
    for m in modulesinpage:
        mp[m] = m
        pass

    # http://www.stealthcopter.com/blog/2010/02/saving-settings-in-python-with-yaml-an-xml-alternative/
    #    {'product': 
    #        [{'sku': 'BL394D', 
    #          'price': 450.0, 
    #          'description': 'Basketball', 
    #          'quantity': 4
    #          }, 
    #         {'sku': 'BL4438H', 
    #          'price': 2392.0,
    #          'description': 'Super Hoop', 
    #          'quantity': 1
    #          }
    #         ], 
    #            'total': 4443.5, 
    #            'tax':251.41999999999999, 
    #            'name': 'Joe Bloggs'
    #    }

    datamap = {'page': [{'title': obj_page.title,
                        'description': obj_page.description,
                        'keywords': obj_page.keywords,
                        }
                        ]
               }

    response.headers['Content-Type']='application/x-yaml'

    return yaml.dump(datamap, default_flow_style=False)


@auth.requires_membership(settings.admin_role_name)
def admin():
    return dict(message=T('Put Here icons with Admin Functions'))


@auth.requires_membership(settings.admin_role_name)
def site_settings():
    form = db_options.Options().form_settings()
    upgrade = check_version()
    currentversion = current.options['pynuke_version']
    version_URL = current.options['url_check_version']
    lastversion = urlopen(version_URL).read()
    if form.accepts(request.vars, session):
        db_pynuke.PyNuke().proccess_update_settings(request.vars)
        session.flash = T('Settings saved')
        redirect(clPagNav.friendly_url_to_page(settings.startpageid))
    return locals()

@auth.requires_membership(settings.admin_role_name)
def proccess_queue():
    clPyMes.proccess_queue_smtp()
    return "Procesed"


@auth.requires_membership(settings.admin_role_name)
def test_mail():
    #MimeMailTest = Mail()
    #cldbpn.config_mail(MimeMailTest, request.post_vars)
    admin_email = db.auth_user[int(settings.portal_admin)].email
    resultmail = MimeMail.send(to=admin_email,
                         subject=T('Email test'),
                         message=T("This is a test "))
    if resultmail == True:
        text_to_add = """ <div class="alert alert-success">
    <button type="button" class="close" data-dismiss="alert">&times;</button>
    <strong>%s</strong> %s</div>"""%(T('Success!'), T("Message sent successfully!"))
    else:
        text_to_add = """<div class="alert">
    <button type="button" class="close" data-dismiss="alert">&times;</button>
    <strong>%s</strong> %s</div>"""%(T('Warning!'), T("Review the mail settings, error in send message."))

    return XML(text_to_add)


@auth.requires_membership(settings.admin_role_name)
def index():
    return dict(message=T('Admin Icons'), layoutsrc=settings.layoutsrc)


@auth.requires_membership(settings.admin_role_name)
def system():
    return dict(message=T('System Icons'), layoutsrc=settings.layoutsrc)


@auth.requires_membership(settings.admin_role_name)
def manage_users():
    #form = db_security.PNSecurity().view_users()

    query = (db.auth_user.id > 0)
    if not request.args(0) == "viewall":
        viewingall = False
        query = query & (db.auth_user.registration_key == '')
    else:
        viewingall = True

    fields = [db.auth_user.id,
                  db.auth_user.first_name,
                  db.auth_user.last_name,
                  db.auth_user.email,
                  db.auth_user.superuser,
                  db.auth_user.affiliateid,
                  db.auth_user.displayname,
                  db.auth_user.lastipaddress,
                 ]
    links = [lambda row: A(I(_class=settings['cssclass_icon_edit']), #'glyphicon glyphicon-pencil'),
                           SPAN(' '),
                            _href="%s" % URL('admin',
                                'user_edit',
                                args=[row.id], user_signature=True),
                                _title=T('Edit'), _class="btn btn-sm")
            ]
    form = SQLFORM.grid(query,
                    fields=fields,
                    orderby=db.auth_user.id,
                    csv=True,
                    searchable=True,
                    create=False,
                    editable=False,
                    details=False,
                    links=links,
                    deletable=False,
                    user_signature=True,
                    args=request.args
                    )

    return dict(form=form, layoutsrc=settings.layoutsrc, viewingall=viewingall)


@auth.requires_membership(settings.admin_role_name)
def unauthorize_user():
    userid = int(request.args[0])
    query = (db.auth_user.id == userid)
    db(query).update(registration_key='pending')
    auth.add_membership(3, userid)
    auth.del_membership(2, userid)
    redirect(URL(c='admin', f='user_edit', args=userid, user_signature=True))


@auth.requires_membership(settings.admin_role_name)
def authorize_user():
    userid = int(request.args[0])
    query = (db.auth_user.id == userid)
    db(query).update(registration_key='')
    auth.add_membership(2, userid)
    auth.del_membership(3, userid)
    redirect(URL(c='admin', f='user_edit', args=userid, user_signature=True))


@auth.requires_membership(settings.admin_role_name)
def delete_unauthorized_users():
    query = (db.auth_user.registration_key != '')
    db(query).delete()
    result = ('window.location = "' +
            str(URL(c='admin', f='manage_users', user_signature=True) + '";'))
    return result


@auth.requires_membership(settings.admin_role_name)
def block_user():
    userid = int(request.args[0])
    query = (db.auth_user.id == int(request.args[0]))
    db(query).update(registration_key='disabled')
    redirect(URL(c='admin', f='user_edit', args=userid, user_signature=True))


@auth.requires_membership(settings.admin_role_name)
def unblock_user():
    userid = int(request.args[0])
    query = (db.auth_user.id == int(request.args[0]))
    db(query).update(registration_key='')
    redirect(URL(c='admin', f='user_edit', args=userid, user_signature=True))


@auth.requires_membership(settings.admin_role_name)
def user_edit():
    objuser = db.auth_user[int(request.args[0])]
    rolesasignados = db_security.PNSecurity().get_roles_from_user(objuser.id)
    qryallroles = (db.auth_group.id == 1) | (db.auth_group.id > 3)
    todoslosroles = db(qryallroles).select()
    form = db_security.PNSecurity().user_edit(objuser.id)
    if form.accepts(request, session):
        if request.vars.delete_this_record == 'on':
            db_security.PNSecurity().delete_unique_rol(objuser.id)
            message = T('User deleted')
        else:
            message = T('User saved')

        session.flash = message
        redirect(URL(c='admin', f='manage_users'))

    rk = objuser.registration_key.lower()
    if rk == "pending" or rk != "":
        authorized = False
    else:
        authorized = True

    if objuser.registration_key.lower() == "disabled":
        blocked = True
    else:
        blocked = False

    deletable = db_security.PNSecurity().user_can_be_deleted(objuser.id)

#    roladmins = settings.admin_role_name
#    if db_security.PNSecurity().user_has_membership(userid, rolid)

    return dict(form=form,
                layoutsrc=settings.layoutsrc,
                objuser=objuser,
                rolesasignados=rolesasignados,
                todoslosroles=todoslosroles,
                authorized=authorized,
                blocked=blocked,
                deletable=deletable
                )


@auth.requires_membership(settings.admin_role_name)
def rol_edit():
    objrol = db.auth_group[int(request.args[0])]
    form = db_security.PNSecurity().rol_edit(objrol.id)
    usersasignados = db_security.PNSecurity().get_users_from_role(objrol.id)
    todoslosusers = db(db.auth_user.id > 0).select()

    if form.accepts(request, session):
        session.flash = T('Group saved')
        redirect(URL(c='admin', f='manage_groups'))

    return dict(form=form,
                layoutsrc=settings.layoutsrc,
                objrol=objrol,
                usersasignados=usersasignados,
                todoslosusers=todoslosusers
                )


@auth.requires_membership(settings.admin_role_name)
def role_add():
    '''
        Esta funciÃ³n se usa via AJAX en la vista de editar usuarios
        para agregar un rol al usuario
    '''
    roleid = int(request.vars.roles or 0)
    userid = int(request.vars.userid or 0)
    objuser = db.auth_user[int(request.vars.userid)]
    objgroup = db.auth_group[int(request.vars.roles)]
    notification = False
    try:
        if request.vars.avisar_usuario == "on":
            notification = True
    except Exception:
        notification = False

    result = ''
    if roleid + userid > 0:
        db_security.PNSecurity().add_user_to_role(userid, roleid, notification)

        if request.vars.mode == None:
            #TODO:Pasar a varias lineas
            text_to_add = "<a class='btn btn-mini btn-danger'  href='javascript:void(0)' onclick='confirm_deleterol(""%s"");'><i class='icon-remove icon-white'></i><strong>"%roleid + T('Borrar') + "</strong></a>"
#            text_to_add = "<a class='btn btn-mini btn-danger'  \
#                    href='javascript:void(0)' \
#                    onclick='confirm_deleterol(""%s"");'> \
#                    <i class='icon-remove icon-white'></i><strong>%s</strong></a>"%roleid, \
#                                            T('Delete')
            result = '$("#tableroles").last().append("<tr id=' + str(roleid) + '><td>' + text_to_add + '</td><td>' + objgroup.role + '</td></tr>");'
        else:
            text_to_add = "<a class='btn btn-mini btn-danger' href='javascript:void(0)' onclick='confirm_deleteusuario(""%s"");'><i class='icon-remove icon-white'></i><strong>"%objuser.id + T('Delete') + "</strong></a>"
            result = '$("#tableroles").last().append("<tr id=' + str(userid) + '><td>' + text_to_add + '</td><td>' + objuser.email + '</td></tr>");'

    return XML(result)


@auth.requires_membership(settings.admin_role_name)
def roleuser_delete():
    '''
        Esta funciÃ³n se usa via AJAX en la vista de editar usuarios
        para borrar la pertenencia a un grupo del usuario

    '''
    roleid = int(request.vars.role)
    obj_rol = db.auth_group[roleid]
    userid = int(request.vars.userid)
    obj_user = db.auth_user[userid]
    db_security.PNSecurity().remove_user_from_role(userid, roleid)

    if request.vars.mode == None:
        #TODO:Pasar a varias lineas
        result = "$('#' + " + str(roleid) + ").remove();"
        result += 'var opt = document.createElement("option");'
        result += 'opt.text = "' + obj_rol.role + '";'
        result += 'opt.value = ' + str(obj_rol.id) + ';'
        result += 'document.getElementById("roles").options.add(opt);'
    else:
        result = "$('#' + " + str(userid) + ").remove();"
        result += 'var opt = document.createElement("option");'
        result += 'opt.text = "' + obj_user.email + '(' + obj_user.first_name \
                    + ' ' + obj_user.last_name + ' Id: ' + str(obj_user.id) \
                    + ')' + '";'
        result += 'opt.value = ' + str(obj_user.id) + ';'
        result += 'document.getElementById("userid").options.add(opt);'

    return result


@auth.requires_membership(settings.admin_role_name)
def manage_groups():
    form = db_security.PNSecurity().view_groups()
    return dict(form=form, layoutsrc=settings.layoutsrc)


@auth.requires_membership(settings.admin_role_name)
def layouts():
    module_title = T("Layouts")
    response.view = 'views_plugin_generics/moduletitle_form.html'
    return dict(module_title=module_title,
                form=db_packages.Packages.WebForms().ver_packages(1),
                layoutsrc=settings.layoutsrc
                )

@auth.requires_membership(settings.admin_role_name)
def containers():
    module_title = T("Containers")
    response.view = 'views_plugin_generics/moduletitle_form.html'
    return dict(module_title=module_title,
                form=db_packages.Packages.WebForms().ver_packages(2),
                layoutsrc=settings.layoutsrc
                )


@auth.requires_membership(settings.admin_role_name)
def edit_layoutpackage():
    """ Form to edit Packages and layoutspackages """
    obj_layoutpackage = db.layoutspackages[int(request.args[0])]
    response.view = 'admin/edit_layoutpackage.html'
    form = clPackWF.editar_layoutpackage(obj_layoutpackage.id)
    tablelayouts = clPackWF.grid_layouts(obj_layoutpackage.id, -1, False, False,
                                        False)
    urlreturn = URL(c='admin', f='layouts')
    if form.process().accepted:
        redirect(URL(c='admin', f='layouts'))

    elif form.errors:
        response.flash = T("Errors in form")

#    download_def = A(I(_class="icon-download"), SPAN(' ' + \
#                T('Download definition')), _href=URL(c='admin',\
#                f='download_lay', args=[int(request.args[0])],\
#                user_signature=True), _class="btn", _style='float:left')

    return dict(form=form,
                obj_layoutpackage=obj_layoutpackage,
                tablelayouts=tablelayouts,
                urlreturn=urlreturn
                )


@auth.requires_membership(settings.admin_role_name)
def edit_package():
    """ Form to edit Packages and layoutspackages """
    obj_package = db.packages[int(request.args[0])]
    response.view = 'admin/edit_package.html'
    form = clPackWF.editar_package(obj_package.id)
    tablelayouts = clPackWF.grid_layoutspackages(obj_package.id, -1, False, False,
                                        False)
    if obj_package.packagetype == 1:
        urlreturn = URL(c='admin', f='layouts')
    elif obj_package.packagetype == 2:
        urlreturn = URL(c='admin', f='containers')
    if form.process().accepted:
        db(db.layoutspackages.packageid == request.vars.id).update(layoutname=request.vars.name,
                                                            layouttype=obj_package.packagetype.packagetype)
        response.flash = T('Item saved')
        if obj_package.packagetype == 1:
            redirect(URL(c='admin', f='layouts'))
        elif obj_package.packagetype == 2:
            redirect(URL(c='admin', f='containers'))

    elif form.errors:
        response.flash = T("Errors in form")

    download_def = A(I(_class="icon-download"), SPAN(' ' + \
                T('Download definition')), _href=URL(c='admin',\
                f='download_lay', args=[int(request.args[0])],\
                user_signature=True), _class="btn", _style='float:left')

    return dict(form=form,
                obj_package=obj_package,
                tablelayouts=tablelayouts,
                download_def=download_def,
                urlreturn=urlreturn
                )


@auth.requires_membership(settings.admin_role_name)
def edit_packagem():
    """ Formulario de edicion de Packages Modules """
    obj_package = db.packages[int(request.args[0])]
    response.view = 'admin/edit_packagem.html'
    form = clPackWF.editar_package(obj_package.id)
    tablemodules = clPackWF.ver_basemodules(obj_package.id)

    if form.process().accepted:
        response.flash = T('Item saved')
        redirect(URL(c='admin', f='plugins'))
    elif form.errors:
        response.flash = T("Errors in form")

    download_def = A(I(_class="icon-download"), SPAN(' ' + \
                T('Download definition')), _href=URL(c='admin',\
                f='download_package', args=[int(request.args[0])],\
                user_signature=True), _class="btn", _style='float:left')

    currentversion = obj_package.version or "0.0.0"
    lastversion = clPack.get_packagelastversion(obj_package)
    upgrade = check_packageversion(obj_package.id, currentversion, lastversion)

    return dict(form=form,
                obj_package=obj_package,
                tablemodules=tablemodules,
                download_def=download_def,
                urlreturn=URL(c='admin', f='plugins'),
                currentversion=currentversion,
                lastversion=lastversion,
                upgrade=upgrade
                )


@auth.requires_membership(settings.admin_role_name)
def edit_layout():
    idlayout = int(request.args[0])
    obj_layout = db.layouts[idlayout]
    response.view = 'admin/edit_layout.html'
    db.layouts.layoutspackagesid.readable = True
    db.layouts.layoutspackagesid.writable = False
    deletable = db_packages.Packages.WebForms().layout_isdeletable(idlayout)
    form = SQLFORM(db.layouts, obj_layout, deletable=deletable)
    if form.process().accepted:
        response.flash = T('Item saved')
#        typelayout = int(db(db.packages.id==packageid).select(db.packages.packagetype).first()['packages.packagetype'])
#        if typelayout == 1:
        redirect(URL(a='init', c='admin', f='edit_layoutpackage', args=[obj_layout.layoutspackagesid]))
#        elif typelayout == 2:
#            redirect(URL(a='init',c='admin', f='containers'))
    elif form.errors:
        response.flash = T("Errors in form")
    return dict(form=form,
                tablepanes=clPackWF.ver_panes(obj_layout.layoutspackagesid, obj_layout.id),
                obj_layout=obj_layout
                )


@auth.requires_membership(settings.admin_role_name)
def duplicate_layout():
    """ Duplicacion de un Layout con sus paneles """
    layoutid = int(request.args[0])
    packageid = int(request.args[1])
    obj_layout = db.layouts[layoutid]
    newidlayout = db.layouts.insert(layoutspackagesid=obj_layout.layoutspackagesid,
                              layoutsrc=obj_layout.layoutsrc + " (Copy)")
    panels = db_packages.Packages().get_panesfromlayoutid(obj_layout.id)
    for p in panels:
        db.layouts_panes.insert(layout=newidlayout,
                                panename=p.panename)
    if newidlayout > 1:
        response.flash = T("Item duplicated")

    redirect(URL(a="init",c="admin",f="edit_layout",args=[newidlayout]))
    return


@auth.requires_membership(settings.admin_role_name)
def edit_pane():
    """ Formulario de ediciÃ³n de Panes """
    obj_pane = db.layouts_panes[int(request.args[0])]
    packageid = int(request.args[1])
    layoutid = int(request.args[2])
    response.view = 'admin/edit_pane.html'
    form = SQLFORM(db.layouts_panes, obj_pane, deletable=True)
    if form.process().accepted:
        response.flash = T('Item saved')
        redirect(URL(a='init', c='admin', f='edit_package', args=[packageid]))
    elif form.errors:
        response.flash = T("Errors in form")
    return dict(form=form,
                packageid=packageid,
                layoutid=layoutid
                )


@auth.requires_membership(settings.admin_role_name)
def plugins():
    response.view = 'views_plugin_generics/moduletitle_form.html'
    return dict(module_title=T('Plugins'),
                form=db_packages.Packages.WebForms().ver_packages(3),
                layoutsrc=settings.layoutsrc
                )

@auth.requires_membership(settings.admin_role_name)
def editar_basemodules():
    """ Formulario de edición de basemodules """
    obj_basemodule = db.basemodules[int(request.args[0])]
    urlreturn = URL(c="admin", f="edit_packagem", args=obj_basemodule.packageid)
    response.view = 'admin/editar_basemodule.html'
    form = db_basemodules.BaseModules.WebForms().editar(obj_basemodule.id)
    if form.process().accepted:
        response.flash = T('Item saved')
        redirect(URL(c='admin', f='plugins'))

    elif form.errors:
        response.flash = T("Errors in form")

    download_def = A(I(_class="icon-download"), SPAN(' ' + \
                T('Download definition')), _href=URL(c='admin',\
                f='download_def', args=[int(request.args[0])],\
                user_signature=True), _class="btn", _style='float:left')

    return dict(form=form,
                urlreturn=urlreturn,
                moduledefinitions=db_basemodules.BaseModules.WebForms().ver_definitions(obj_basemodule.id),
                obj_basemoduleid=obj_basemodule.id,
                download_def=download_def,
                obj_basemodule=obj_basemodule
#                upgrade=upgrade,
#                currentversion=currentversion,
#                lastversion=lastversion 
                )

@auth.requires_membership(settings.admin_role_name)
def edit_definition():
    """ Edit definitions """
    obj_definition = db.moduledefinitions[int(request.args[0])]
    urlreturn = URL(c="admin", f="editar_basemodules", args=obj_definition.basemoduleid)
    response.view = 'admin/edit_definition.html'
    form = db_basemodules.BaseModules.WebForms().edit_definition(obj_definition.id)
    if form.process().accepted:
        response.flash = T('Item saved')
        redirect(urlreturn)

    elif form.errors:
        response.flash = T("Errors in form")

    return dict(form=form,
                urlreturn=urlreturn,
                controls=db_basemodules.BaseModules.WebForms().ver_controls(obj_definition.id),
                obj_definition=obj_definition
                )

@auth.requires_membership(settings.admin_role_name)
def edit_control():
    """ Edit control """
    obj_control = db.modulecontrols[int(request.args[0])]
    urlreturn = URL(c="admin", f="edit_definition", args=obj_control.moduledefid)
    response.view = 'admin/edit_control.html'
    form = db_basemodules.BaseModules.WebForms().edit_control(obj_control.id)
    if form.process().accepted:
        response.flash = T('Item saved')
        redirect(urlreturn)

    elif form.errors:
        response.flash = T("Errors in form")

    return dict(form=form,
                urlreturn=urlreturn,
                obj_control=obj_control
                )


@auth.requires_membership(settings.admin_role_name)
def download_lay():
    '''
        Genera un fichero yaml y lo envÃ­a a la pantalla para descargarselo
        este fichero se podrÃ¡, posteriormente "Subir" a otro portal pynuke y
        el package quedarÃ¡ registrado en la BD

        Subiendo desde web2py un plugin y subiendo este fichero yaml tenemos
        un diseÃ±o transportable en distintas webs con pynuke

    '''
    package = db.packages[int(request.args(0))]
    nomfichero = package.name.replace(" ", "_") + ".txt"
    mydata = db_packages.Packages.yaml_utils().download_yaml_package(package.id)
    response.headers['Content-Type'] = 'application/text'
    response.headers['Content-disposition'] = "attachment; filename=\"%s\""\
                                                                 % nomfichero
    return yaml.dump(mydata, default_flow_style=False)


@auth.requires_membership(settings.admin_role_name)
def download_package():
    '''
        Genera un fichero yaml y lo envÃ­a a la pantalla para descargarselo
        este fichero se podrÃ¡, posteriormente "Subir" a otro portal pynuke y
        el mÃ³dulo quedarÃ¡ registrado en la BD

        Subiendo desde web2py un plugin y subiendo este fichero yaml tenemos
        un mÃ³dulo transportable en distintas webs con pynuke

    '''
    packageid = int(request.args(0))
    package = db.packages[packageid]
    nomfichero = package.friendlyname.replace(" ", "_") + ".txt"
    mydata = clPack.download_yaml_package(package.id)
    response.headers['Content-Type'] = 'application/text'
    response.headers['Content-disposition'] = "attachment; filename=\"%s\""\
                                                                 % nomfichero
    return yaml.dump(mydata, default_flow_style=False)


@auth.requires_membership(settings.admin_role_name)
def upload_def():
    '''
        permite subir un fichero yaml con la definición de un plugin y
        registrarlo en la BD o descargar un nuevo modulo desde pynuke.net
        ....
    '''
    response.view = 'admin/upload_def.html'
    form = clPackYAML.form_upload_packagemod()
    if form.accepts(request.vars, session):
        if request.vars.YAML_File != '':
            filecontent = request.vars.YAML_File.value
            clPackYAML.proccess_yaml_packdefinitionmod(filecontent)
        else:
            clPackYAML.proccess_install_packdefinition(request.vars.download)

        redirect(URL(c="admin", f="plugins"))

    return dict(form=form, layoutsrc=settings.layoutsrc)


@auth.requires_membership(settings.admin_role_name)
def upload_pac():
    '''
       Allows upload a yaml file with the definition of a package of type
       Layout or Container and register it in the database

    '''

    if request.args[0] == '1':
        url_return = URL(c="admin", f="layouts")
    elif request.args[0] == '2':
        url_return = URL(c="admin", f="containers")

    form = clPackYAML.form_upload_package(request.args[0])
    if form.accepts(request.vars, session):
        if request.vars.YAML_File != '':
            filecontent = request.vars.YAML_File.value
            typepack = clPackYAML.proccess_yaml_packdefinition(filecontent)
            if typepack == 1:
                redirect(URL(c="admin", f="layouts"))
            elif typepack == 2:
                redirect(URL(c="admin", f="containers"))
        else:
            plugin_layout = request.vars.register_layout
            db_packages.Packages.WebForms().proccess_package_in_folder(plugin_layout,request.vars.Type)
        
        redirect(url_return)
    
    return dict(form=form, layoutsrc=settings.layoutsrc,
                url_return=url_return)


@auth.requires_membership(settings.admin_role_name)
def recycle_bin():
    formpages_deleted = db_pages.Pages.Recycle_Bin().view_pages_deleted()
    frmmods_deleted = db_pagemodules.PageModules().view_pagemodules_deleted()
    return dict(
                formpages_deleted=formpages_deleted,
                formmodules_deleted=frmmods_deleted
                )


@auth.requires_membership(settings.admin_role_name)
def empty_recycle_bin():
    db_pagemodules.PageModules().empty_recyclebin()
    Url_dest = URL(c="admin", f="recycle_bin") + '#!modules_deleted'
    return "window.location = '%s'" % Url_dest


@auth.requires_membership(settings.admin_role_name)
def restore_page():
    pageid = int(request.vars.pageid)
    target = db.pages[1]
    db(db.pages.id == pageid).update(isdeleted=False, level=1, parent=1)

    db(db.pages.rgt >= target.rgt)(db.pages.tree_id == target.tree_id
                   ).update(rgt=db.pages.rgt + 2)
    db(db.pages.lft >= target.rgt)(db.pages.tree_id == target.tree_id
                   ).update(lft=db.pages.lft + 2)

    db(db.pages.id == pageid).update(lft=target.rgt, rgt=target.rgt + 1)

    redirect(clPagNav.friendly_url_to_page(pageid))

    return


@auth.requires_membership(settings.admin_role_name)
def restore_pagemodule():
    pagemoduleid = int(request.vars.pagemoduleid)
    regpm = db.pagemodules[pagemoduleid]
    xmodid = regpm.moduleid
    db(db.pagemodules.id == pagemoduleid).update(isdeleted=False)
    db(db.modules.id == xmodid).update(isdeleted=False)

    obj_pm = db.pagemodules[pagemoduleid]
    redirect(clPagNav.friendly_url_to_page(obj_pm.pageid))

    return


@auth.requires_membership(settings.admin_role_name)
def delete_pagemodule():
    pagemoduleid = int(request.vars.pagemoduleid)
    db_pagemodules.PageModules().delete_pagemodule(pagemoduleid)
    redirect(URL(c="admin", f="recycle_bin") + '#!modules_deleted')

    return


@auth.requires_membership(settings.admin_role_name)
def redirects_301():
    #Visualizar mantenimiento de redirects
    form_redirects = db_redirects.Redirects().ver()
    return dict(
                form_redirects=form_redirects
                )


@auth.requires_membership(settings.admin_role_name)
def check_version():
    """ Checks if pynuke is up to date """
    pynuke_url_version = current.options['url_check_version']
    pynuke_url = "http://www.pynuke.net"
    pcv = current.options['pynuke_version']
    new_version, version = db_pynuke.PyNuke.Upgrades().check_new_version(pcv,
                                             pynuke_url_version)

    if new_version == -1:
        return A(T('Unable to check for upgrades'), _href=pynuke_url)
    elif new_version != True:
        return A(T('pynuke is up to date'), _href=pynuke_url)
#    elif platform.system().lower() in ('windows', 'win32', 'win64') and os.path.exists("web2py.exe"):
#        return SPAN('You should upgrade to %s' % version.split('(')[0])
    else:
        return sp_button(URL('upgrade_pynuke'), T('upgrade now to %s') % version.split('(')[0])


@auth.requires_membership(settings.admin_role_name)
def check_packageversion(obj_packageid, currentversion, lastversion):
    """ Checks if package is up to date """

    pcv = currentversion
    new_version, version = db_pynuke.PyNuke.Upgrades().check_new_packversion(pcv,lastversion)

    if new_version == -1:
        return A(T('Unable to check for upgrades'), _href="#")
    elif new_version != True:
        return A(T('Module is up to date'), _href="#")
#    elif platform.system().lower() in ('windows', 'win32', 'win64') and os.path.exists("web2py.exe"):
#        return SPAN('You should upgrade to %s' % version.split('(')[0])
    else:
        return sp_button(URL('upgrade_package',args=obj_packageid), T('upgrade now to %s') % version.split('(')[0])


@auth.requires_membership(settings.admin_role_name)
def sp_button(href, label):
    if request.user_agent().is_mobile:
        ret = A_button(SPAN(label), _href=href)
    else:
        ret = A(SPAN(label), _class='button special btn btn-inverse', _href=href)
    return ret


@auth.requires_membership(settings.admin_role_name)
def A_button(*a, **b):
    b['_data-role'] = 'button'
    b['_data-inline'] = 'true'
    return A(*a, **b)


@auth.requires_membership(settings.admin_role_name)
def upgrade_pynuke():
    urllastversion = current.options['url_check_version']
    currentversion = current.options['pynuke_version']
    new_version, version = cldbpnu.check_new_version(currentversion,
                                                     urllastversion)

    dialog = FORM.confirm(T('Upgrade'),
                          {T('Cancel'): URL('site')})
    if dialog.accepted:
        (success, error) = upgrade(request, currentversion, new_version, version,
                                   urllastversion)
        if success:
            session.flash = T('pynuke upgraded; please restart it')
        else:
            session.flash = T('unable to upgrade because "%s"', error)
        redirect(URL(c='admin', f='site_settings'))
    return dict(dialog=dialog)

@auth.requires_membership(settings.admin_role_name)
def upgrade_package():
    obj_packagemoduleid = request.args(0)
    obj_package = db.packages[obj_packagemoduleid]
    currentversion = obj_package.version or "0.0.0"
    lastversion = clPack.get_packagelastversion(obj_package)

    new_version, version = cldbpnu.check_new_packversion(currentversion,
                                                        lastversion)

    dialog = FORM.confirm(T('Upgrade'),
                          {T('Cancel'): URL('site')})
    if dialog.accepted:
        (success, error) = upgrade_packagex(request, currentversion,
                                          new_version, version, obj_packagemoduleid)
        if success:
            session.flash = T('Package upgraded; please restart')
        else:
            session.flash = T('unable to upgrade because "%s"', error)
        redirect(URL(c='admin', f='plugins'))
    return dict(dialog=dialog)

@auth.requires_membership(settings.admin_role_name)
def upgrade_packagex(request, currentversion, new_version, version, obj_packagemoduleid):
    """
    Extraido de las funciones de act. de web2py y adaptado a pynuke...

    Parameters
    ----------
    request:
        the current request object, required to determine version and path
    url:
        the incomplete url where to locate the latest web2py
        actual url is url+'/examples/static/web2py_(src|osx|win).zip'

    Returns
    -------
        True on success, False on failure (network problem or old version)
    """
    gluon_parent = request.env.gluon_parent
    obj_package = db.packages[obj_packagemoduleid]
    if not gluon_parent.endswith('/'):
        gluon_parent = gluon_parent + '/'

    if not new_version:
        return (False, 'Already latest version')
    if os.path.exists(os.path.join(gluon_parent, 'web2py.exe')):
        version_type = 'win'
        destination = gluon_parent
        subfolder = 'web2py/'
    elif gluon_parent.endswith('/Contents/Resources/'):
        version_type = 'osx'
        destination = gluon_parent[:-len('/Contents/Resources/')]
        subfolder = 'web2py/web2py.app/'
    else:
        version_type = 'src'
        destination = gluon_parent + "applications/init"
        subfolder = 'pynukedev-' + obj_package.name + '-' + version.split(";")[1]

    #https://bitbucket.org/pynukedev/pynuke/get/fef75d9c0931.zip
    full_url = "https://bitbucket.org/pynukedev/" + obj_package.name + "/get/" + '%s.zip' % version.split(";")[1]
    filename = abspath(obj_package.name + '_%s_downloaded.zip' % version_type)
    file = None
    try:
        write_file(filename, urllib.urlopen(full_url).read(), 'wb')
    except Exception, e:
        return False, e
    try:
        listnames = cldbpnu.unzip(filename, destination, version, subfolder, obj_package.name)
        package_version = version
        db(db.packages.id == obj_packagemoduleid).update(version=package_version)
        db.commit()
        clEventLog.eventlog("HOST_ALERT", locals(),[('Package Upgraded', obj_package.name),
                                                    ('Old version', currentversion),
                                                    ('New version', package_version),
                                                    ('Files upgraded', listnames)
                                                    ])
        return True, None
    except Exception, e:
        return False, e


@auth.requires_membership(settings.admin_role_name)
def upgrade(request, currentversion, new_version, version, urllastversion):
    """
    Extraido de las funciones de act. de web2py y adaptado a pynuke...

    Parameters
    ----------
    request:
        the current request object, required to determine version and path
    url:
        the incomplete url where to locate the latest web2py
        actual url is url+'/examples/static/web2py_(src|osx|win).zip'

    Returns
    -------
        True on success, False on failure (network problem or old version)
    """
    #pynuke_version = current.options['pynuke_version']
    #pynuke_url_version = current.options['url_check_version']
    #pynuke_url = "http://www.pynuke.net"

    gluon_parent = request.env.gluon_parent
    if not gluon_parent.endswith('/'):
        gluon_parent = gluon_parent + '/'
#    (check, version) = db_pynuke.PyNuke.Upgrades().check_new_version(currentversion,
#                                         pynuke_url_version)

    if not new_version:
        return (False, 'Already latest version')
    if os.path.exists(os.path.join(gluon_parent, 'web2py.exe')):
        version_type = 'win'
        destination = gluon_parent
        subfolder = 'web2py/'
    elif gluon_parent.endswith('/Contents/Resources/'):
        version_type = 'osx'
        destination = gluon_parent[:-len('/Contents/Resources/')]
        subfolder = 'web2py/web2py.app/'
    else:
        version_type = 'src'
        destination = gluon_parent + "applications/init"
        subfolder = 'pynukedev-pynuke-' + version.split(";")[1]
    #https://bitbucket.org/pynukedev/pynuke/get/fef75d9c0931.zip
    full_url = "https://bitbucket.org/pynukedev/pynuke/get/" + '%s.zip' % version.split(";")[1]
    filename = abspath('pynuke_%s_downloaded.zip' % version_type)
    file = None
    try:
        write_file(filename, urllib.urlopen(full_url).read(), 'wb')
    except Exception, e:
        return False, e
    try:
        cldbpnu.unzip(filename, destination, version, subfolder)
        pynuke_version = version
        db(db.options.name=="pynuke_version").update(value=version)
        db.commit()
        return True, None
    except Exception, e:
        return False, e


# @auth.requires_membership(settings.admin_role_name)
# def unzip(filename, dir, version, subfolder='', modulename=""):
#     """
#     Unzips filename into dir (.zip only, no .gz etc)
#     if subfolder!='' it unzip only files in subfolder
#     """
#     listnames = []
#     filename = abspath(filename)
#     if not zipfile.is_zipfile(filename):
#         raise RuntimeError('Not a valid zipfile')
#     zf = zipfile.ZipFile(filename)
#     if not subfolder.endswith('/'):
#         subfolder = subfolder + '/'
#     
#     for name in sorted(zf.namelist()):
#         subfolder = name.split("/")[0]
#         n = len(subfolder)
#         print name[n:]
#         if name.endswith('/'):
#             folder = os.path.join(dir, name)
#             if not os.path.exists(folder):
#                 os.mkdir(folder)
#         else:
#             if modulename == "":
#                 namesave = name.replace(subfolder + "/", "")
#             else:
#                 namesave =  name.replace(subfolder + "/", "")
# 
#             listnames.append(namesave)
# 
#             if not namesave.startswith("."):
#                 folder = namesave.replace(os.path.basename(namesave), "")
#                 if not os.path.exists(os.path.join(dir, folder)):
#                     os.makedirs(os.path.join(dir, folder))
#                 write_file(os.path.join(dir, namesave), zf.read(name), 'wb')
#     return listnames


@auth.requires_membership(settings.admin_role_name)
def movemodpane():
    pagemoduleid = request.vars.mip
    newpaneid = request.vars.pane
    pageidret = request.vars.pageidret
    query = (db.pagemodules.id == pagemoduleid)
    if int(pageidret) > 0:
        objpage = db.pages[pageidret]
        real_panes_in_page = clpk.get_panes_from_layout_file(objpage.layoutsrc)
        to_panename = db.layouts_panes[newpaneid].panename
        if to_panename in real_panes_in_page:
            db(query).update(panename=newpaneid)

    redirect(clPagNav.friendly_url_to_page(pageidret))


@auth.requires_membership(settings.admin_role_name)
def sitelog():
    title = T("Site Log")
    pag = clPyNav.extract_value_from_arg(req_uri, "pag", True) or 1
    startdate = request.post_vars.startdate or request.vars.startdate
    enddate = request.post_vars.enddate or request.vars.enddate
    reporttype = request.post_vars.reporttype or request.vars.reporttype
    formsitelog = db_sitelog.SiteLog().form_getlog(startdate, enddate, reporttype)
    tablelog = ""

    if formsitelog.accepts(request.post_vars, session, keepvalues=True):
        tablelog = clSiteLog.grid_log(reporttype, startdate, enddate, 1)
        #response.js = '''jQuery('#logholder').html('%s')''' %tablelog
    else:
        tablelog = clSiteLog.grid_log(reporttype, startdate, enddate, pag)

    return dict(formlog=formsitelog, tablelog=tablelog, title=title)


@auth.requires_membership(settings.admin_role_name)
def eventlog():
    response.view = "admin/eventlog.html"
    title = T("Event Log")
    #TODO: Filter by event
    #formeventlog = db_eventlog.EventLog().form_eventlog() 

    pag = clPyNav.extract_value_from_arg(req_uri, "pag", True) or 1
    tablelog = clEventLog.grid_eventlog(pag)

    return dict(formeventlog='', tablelog=tablelog, title=title)

@auth.requires_membership(settings.admin_role_name)
def pagemodule_delete():
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
