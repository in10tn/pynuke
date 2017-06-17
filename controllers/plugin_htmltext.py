# -*- coding: utf-8 -*-
from applications.init.modules import db_pages, plugin_htmltext, db_pagemodules, db_pynuke
from gluon.html import XML, MARKMIN

if False:
    from gluon.tools import *
    from gluon import *
    db = DAL()
    auth = Auth(db)
    request, session, response, T, cache = current.request, current.session, \
                                    current.response, current.t, current.cache
    db = current.db
    settings = current.settings
    auth = Auth(db, hmac_key=Auth.get_or_create_key()) 
    crud, service, plugins = Crud(db), Service(), PluginManager()

clhtml = plugin_htmltext.Plugin_HTMLText()
clpm = db_pagemodules.PageModules()
clPyUtils = db_pynuke.PyNuke.Utils()

moduleid = request.vars.moduleid
pagemoduleid = request.vars.pagemoduleid
pageid = request.vars.pageid
modsettings, dict_default_helps = clPyUtils.read_modsettings(pagemoduleid,
                                         plugin_htmltext.Plugin_HTMLText())

table = db.htmltext

clPynuke_nav = db_pynuke.PyNuke.Navigation()
 
def view():
    content = ''
    last_versionid = clhtml.get_next_version_number(moduleid) - 1
    query = (table.moduleid == moduleid)
    if last_versionid != 0:
        query = (table.moduleid == moduleid)
        query = query & (table.version == last_versionid)
        record_html = db(query).select().first()
        if modsettings['render_type'] == "MARKMIN":
            content = MARKMIN(record_html.content)
        elif modsettings['render_type'] == "TEXT":
            content = XML(record_html.content.replace("\n","<br/>"))
        elif modsettings['render_type'] == "HTML":
            content = XML(record_html.content)
    else:
        content = XML(T('Your content goes here'))

    return dict(content=content)


@auth.requires_membership(settings.admin_role_name)
def edit():

    objpage = db.pages[pageid]
    table.moduleid.default = moduleid
    table.version.default = clhtml.get_next_version_number(moduleid)
    table.content.default = clhtml.get_last_html_by_version_number(moduleid)
    if modsettings['render_type'] == "MARKMIN" or modsettings['render_type'] == "TEXT":
        table.content.widget = SQLFORM.widgets.text.widget
    form = SQLFORM(table)
    if form.accepts(request.vars, session):
        #session.flash = 'submitted %s' % form.vars
        redirect(db_pages.Pages.Navigation().friendly_url_to_page(objpage.id))
    versions = clhtml.get_versions(int(moduleid))

    btnreturn = clPynuke_nav.linkbutton(T("Volver"),
                                        settings.cssclass_icon_return,
                                        settings.cssclass_button_small + " " + settings.cssclass_button_warning,
                                        objpage.slug)

    return dict(form=form,
                versions=versions,
                layoutsrc=settings.layoutsrc,
                currentmoduleid=moduleid,
                modsettings=modsettings,
                nextpageid=objpage.slug,
                btnreturn=btnreturn)


@auth.requires_membership(settings.admin_role_name)
def version_delete():
    # Used via AJAX in the view edit
    selected_version = int(request.vars.versionid)
    query = (table.id == selected_version)
    db(query).delete()
    db.commit()
    return ' '


@auth.requires_membership(settings.admin_role_name)
def version_view():
    # Used via AJAX to view a version
    selected_version = int(request.vars.versionid)
    query = (table.id == selected_version)
    result_record = db(query).select(table.content).first()
    result = XML(result_record['content'])
    return result


@auth.requires_membership(settings.admin_role_name)
def version_revert():
    query = (table.id == int(request.vars.versionid))
    result_record = db(query).select(table.content).first()
    table.insert(moduleid=moduleid,
                       content=XML(result_record['content']),
                       version=clhtml.get_next_version_number(moduleid),
                       )
    db.commit()
    return "window.location = window.location.href"


@auth.requires_membership(settings.admin_role_name)
def msettings():
    response.view = 'views_plugin_generics/msettings.html'
    formsettings = clhtml.render_form_settings(pagemoduleid, modsettings, dict_default_helps)
    if formsettings.accepts(request.vars, session, keepvalues=True):
        clpm.proccess_form_settings(request.vars, pagemoduleid)
        Url_dest = db_pages.Pages.Navigation().friendly_url_to_page(pageid)
        response.js = "window.location = '%s'" % Url_dest

    return dict(formsettings=formsettings)
    