# -*- coding: utf-8 -*-
'''
debugs in Eclipse
'''
import logging, logging.handlers
import datetime  # Important, to include in modules!
from gluon.tools import Auth, Crud, Service, PluginManager, Mail, Recaptcha
from gluon.globals import current #Important!
from gluon.storage import Storage
from applications.init.modules import db_contenttypes, db_userregistrations,db_pages,db_options,db_permissions,db_pagepermissions,db_basemodules,db_sitelog
from applications.init.modules import db_pagemodules,db_packages,db_workflows, plugin_htmltext,db_security,db_pynuke,db_redirects,security, db_eventlog
from applications.init.modules.plugin_mptt import MPTT
from applications.init.modules.plugin_ckeditor import CKEditor
import os
import yaml

if False:
    from gluon import *
    request,session,response,T,cache=current.request,current.session,current.response,current.t,current.cache
    from gluon.storage import Storage
    settings = Storage()


dbbm = db_basemodules.BaseModules
clpnpu = db_pynuke.PyNuke.Utils()

# Assign application logger to a global var 


def get_configured_logger(name):
    logger = logging.getLogger(name)
    if (len(logger.handlers) == 0):
        # This logger has no handlers, so we can assume it hasn't yet been configured
        # (Configure logger)
        # Create default handler
        if not request.env.web2py_runtime_gae:
            # Create GAEHandler
#            handler = GAEHandler()
#        else:
            # Create RotatingFileHandler
            import os
            formatter="%(asctime)s %(levelname)s %(process)s %(thread)s %(funcName)s():%(lineno)d %(message)s"
            handler = logging.handlers.RotatingFileHandler(os.path.join(request.folder,'private/logs/app.log'),maxBytes=1048576,backupCount=5)
            handler.setFormatter(logging.Formatter(formatter))

        # parece una mala idea intentar leer esto de la configuración, se entra en un bucle de a ver que se 
        # carga primero, si las tablas o el logger. Esto es por que en los módulos de las tablas se utiliza
        # el logger, quizá separando la creación de las tablas en otro módulo se solucionaria, 
        handlerlevel = 'INFO'
        
        if handlerlevel == 'INFO':
            handler.setLevel(logging.INFO)
        elif handlerlevel == 'DEBUG':
            handler.setLevel(logging.INFO)
        
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        # Test entry:
        #logger.debug(name + ' logger created')
#    else:
#        # Test entry:
#        logger.debug(name + ' already exists')

    return logger

# Assign application logger to a global var 
logger = get_configured_logger(request.application)
#logger.debug('debug this')
#logger.info('info this')

current.logger = logger

''' Asignamos una cadena de conexión por defecto a SQLite
    si existiera un fichero local_settings o prod_settings sobreescribiriamos
    estas variables. Lo normal es que existan, pero con esto puede ser opcional
'''
settings = Storage()
settings.migrate = True
settings.database_uri = 'sqlite://storage.sqlite4'

settings.strings_to_remove_from_url = ["moduleid", "search", "archives",
                                       "read", "tag", "page","categories", "date"]

# on webfaction request.is_local will return true --> this is True...
is_local = request.client in ['127.0.0.1', 'localhost']

try:
    if is_local:
        from local_settings import *
    else:
        from prod_settings import *
except:
    pass

settings.is_local = is_local

db = DAL(settings.database_uri, migrate_enabled=settings.migrate)

# by default give a view/generic.extension to all actions from localhost
# none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []

# Config ckeditor
ckeditor = CKEditor(db)
ckeditor.define_tables()

auth = Auth(db, hmac_key=Auth.get_or_create_key())
crud, service, plugins = Crud(db), Service(), PluginManager()

# Estas dos lineas junto con el --> from gluon import current de arriba, 
# hacen posible utilizar la base de datos desde los módulos
current.db = db
current.auth = auth

current.settings = settings

# MPTT
mptt_pages = MPTT(db)
current.mptt_pages = mptt_pages

db_options.Options().define_tables()
options = db_options.Options().get_all_options()
if not options:
    db_options.Options().insert_default_options()
    options = db_options.Options().get_all_options()

current.options = options

if 'compress_css_files' in options:
    if clpnpu.str2bool(options['compress_css_files']):
        response.optimize_css = 'concat,minify,inline'

if 'compress_js_files' in options:
    if clpnpu.str2bool(options['compress_js_files']):
        response.optimize_js = 'concat,minify,inline'

rcprivatekey = options['recaptcha_privatekey']
rcpublickey = options['recaptcha_publickey']
rcoptions = options['recaptcha_options']
login_captcha = clpnpu.str2bool(options['auth_require_recaptcha'])
register_captcha = False
ret_username_captcha = False
ret_password_captcha = False
if 'auth_register_require_recaptcha' in options:
    register_captcha = clpnpu.str2bool(options['auth_register_require_recaptcha'])
if 'auth_retrieve_username_require_recaptcha' in options:
    ret_username_captcha = clpnpu.str2bool(options['auth_retrieve_username_require_recaptcha'])
if 'auth_retrieve_username_require_recaptcha' in options:
    ret_password_captcha = clpnpu.str2bool(options['auth_retrieve_password_require_recaptcha'])

if rcpublickey is not None and len(rcpublickey) > 0:
    if login_captcha:
        auth.settings.login_captcha = Recaptcha(request,
                                        rcpublickey,
                                        rcprivatekey,
                                        error_message=T('invalid'),
                                        label=T('Verify'),
                                        options=rcoptions)
    if register_captcha:
        auth.settings.register_captcha = Recaptcha(request,
                                                rcpublickey,
                                                rcprivatekey,
                                                error_message=T('invalid'),
                                                label=T('Verify'),
                                                options=rcoptions)
    if ret_username_captcha:
        auth.settings.retrieve_username_captcha = Recaptcha(request,
                                                rcpublickey,
                                                rcprivatekey,
                                                error_message=T('invalid'),
                                                label=T('Verify'),
                                                options=rcoptions)
    if ret_password_captcha:
        auth.settings.retrieve_password_captcha = Recaptcha(request,
                                                rcpublickey,
                                                rcprivatekey,
                                                error_message=T('invalid'),
                                                label=T('Verify'),
                                                options=rcoptions)

# Email config
MimeMail = Mail()
db_pynuke.PyNuke().config_mail(MimeMail, options)
current.MimeMail = MimeMail

#Auth options
auth.settings.mailer = MimeMail
auth.settings.extra_fields['auth_user'], auth.settings.extra_fields['auth_group']= db_security.PNSecurity().define_tables()
auth_username = not db_pynuke.PyNuke.Utils().str2bool(options['use_mail_as_username'])
auth.define_tables(username=auth_username)

#Site Settings
db_pynuke.PyNuke().config_settings(options)

if options['message_onregister'] == 'True':
    usradmin = int(options['portal_admin'])
    auth.settings.register_onaccept.append(lambda form: \
           db_pynuke.PyNuke.Messages().sendmail_to_userid(usradmin,
                  messagetype=1,
                  subject=T('New user registered'),
                  bodymessage=T("New user registered with e-mail ") + form.vars.email,
                  enqueue=False))


if options['message_onvalidation'] == 'True':
    auth.settings.verify_email_onaccept.append(lambda user:\
                               MimeMail.send(to=settings.admin_email,
                             subject=T('New user verified'),
                             message=(T("New user verified with e-mail ") +
                                      user.email)))

tr = options['registration_type'].lower()

if tr == "verified" or tr == "private":
    auth.settings.register_onaccept.append(lambda form:\
                       auth.add_membership(3, form.vars.id))

    auth.settings.verify_email_onaccept.append(lambda user:\
                       auth.del_membership(3, user.id))

    auth.settings.verify_email_onaccept.append(lambda user:\
                       auth.add_membership(2, user.id))

elif tr == "public":
    auth.settings.register_onaccept.append(lambda form:\
                       auth.add_membership(2, form.vars.id))
#Config janrain
## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
if options['use_janrain']=='True':
    from gluon.contrib.login_methods.rpx_account import use_janrain
    use_janrain(auth,filename='private/janrain.key')

# #MPTT
# mptt_pages, current.mptt_pages = MPTT(db)

# Table definitions
db_pynuke.PyNuke().define_tables(mptt_pages)
db_pagepermissions.PagePermissions().define_tables()
db_pagemodules.PageModules().define_tables()
db_redirects.Redirects().define_tables()
db_pynuke.PyNuke.Messages().define_tables()

# auth policy
if options['registration_type'].lower() == "verified":
    auth.settings.registration_requires_verification = True
elif options['registration_type'].lower() == "public":
    auth.settings.registration_requires_verification = False
elif options['registration_type'].lower() == "public-verified":
    auth.settings.registration_requires_approval = True
    auth.settings.login_after_registration = True
elif options['registration_type'].lower() == "private":
    auth.settings.registration_requires_approval = True
else:
    auth.settings.actions_disabled.append('register')

if options['reset_password_requires_verification'] == 'True':
    auth.settings.reset_password_requires_verification = True
else:
    auth.settings.reset_password_requires_verification = False

if 'registros_iniciales' in options:
    if options['registros_iniciales'] == 'True':
        db_options.Options().update_option('registros_iniciales', False)
        db_packages.Packages().insert_initial_records()
        db_workflows.WorkFlows().insert_initial_records()
        db_pynuke.PyNuke.Messages().insert_initial_records()
        db.commit()

'''Si no hay páginas quiere decir que empezamos una nueva instalación '''
if not mptt_pages.roots().count():
    #idg, idu, idru, idunv = db_security.PNSecurity().create_firsts_records_auth(options)
    pvpage, pepage = db_permissions.Permissions().insert_initial_records()
    htmltext_mod_id = dbbm.Db_Functions().insert_initial_records()
    # Todo el arbol de menús del portal cuelga de 2 raices:
    _root1 = mptt_pages.insert_node(None, name=T('My WebSite'), node_type='root',
                              slug='my-website')

    _root2 = mptt_pages.insert_node(None, name=T('System Menu'), node_type='root',
                              slug='system-menu')
    #Creamos el nodo Admin
    _childAdmin = mptt_pages.insert_node(_root2, name=T('Admin'), c='admin',
                                   f='index', isvisible='T')
    #Creamos el nodo Host
    _childHost = mptt_pages.insert_node(_root2, name=T('Host'), isvisible='T')

    db.pagepermissions.insert(page=_childAdmin, permission=pvpage,
                              allowaccess=True, groupid=1)
    db.pagepermissions.insert(page=_childAdmin, permission=pepage,
                              allowaccess=True, groupid=1)

    db.pagepermissions.insert(page=_childHost, permission=pvpage,
                              allowaccess=True, groupid=1)
    db.pagepermissions.insert(page=_childHost, permission=pepage,
                              allowaccess=True, groupid=1)

    crf = current.request.folder
    fname = os.path.join(crf, "modules", "template_portal.yaml")
    pages = yaml.load(file(fname, 'r'))
    cont_pages = len(pages['pages'].items())
    for i in range(1, cont_pages + 1):
        obj_page = pages['pages']['page_' + str(i)]
        if 'admin_page' not in obj_page or obj_page['admin_page'] is False:
            if 'host_page' not in obj_page or obj_page['host_page'] is False:
                r = _root1
            else:
                r = _childHost
        else:
            r = _childAdmin

        obj_page_insert = obj_page.copy()
        obj_page_insert["name"] = str(T(obj_page_insert["name"]))
        if "modules" in obj_page_insert:
            obj_page_insert.pop("modules")
        if "host_page" in obj_page_insert:
            obj_page_insert.pop("host_page")
        if "admin_page" in obj_page_insert:
            obj_page_insert.pop("admin_page")

        newpageid = mptt_pages.insert_node(r, **obj_page_insert)

        #group id 1 is administrators group, all pages go
        #with permission to admins
        db.pagepermissions.insert(page=newpageid, permission=pvpage,
                                  allowaccess=True, groupid=1)

        db.pagepermissions.insert(page=newpageid, permission=pepage,
                                  allowaccess=True, groupid=1)

        # Permissions for all users normally all users can view the page
        if 'admin_page' not in obj_page or obj_page['admin_page'] is False:
                if 'host_page' not in obj_page or obj_page['host_page'] is False:
                        db.pagepermissions.insert(page=newpageid,
                                                  permission=pvpage,
                                                  allowaccess=True,
                                                  groupid=None)

        if 'modules' in obj_page:
            modules = obj_page['modules']
            cont_modules = 0
            if modules != None:
                cont_modules = len(modules.items())
            while cont_modules >= 1:
                obj_module = modules['module_' + str(cont_modules)]
                recmod = dbbm.ModuleDefinitions().get_ModDefinition_by_name(obj_module['type'])
                mod_id = db.modules.insert(moduledefid=recmod.id,
                                           inheritviewpermissions=True)
                obj_module_insert = obj_module.copy()
                if 'html' in obj_module_insert:
                    obj_module_insert.pop("html")
                if 'type' in obj_module_insert:
                    obj_module_insert.pop("type")
                
                db.pagemodules.insert(pageid=newpageid, moduleid=mod_id,
                                      **obj_module_insert)
                #creamos la tabla del modulo html para poder introducir contenidos
                if not db.tables().count('htmltext'):
                    plugin_htmltext.Plugin_HTMLText().define_tables()
    
                if 'html' in obj_module and len(obj_module['html']) > 0:
                    db.htmltext.insert(moduleid=mod_id, content=obj_module['html'],
                                       version=1, stateid=1, ispublished=True)
                cont_modules -= 1
            cont_pages -= 1
        db.commit()

dbpn = db_pages.Pages.Navigation()
#TODO: Podrian ser en lugar de la pag. de inicio hacer opciones en el config...
auth.settings.create_user_groups = False

auth.settings.login_next = dbpn.friendly_url_to_page(settings.redirectafterlogin)
auth.settings.logout_next = dbpn.friendly_url_to_page(settings.redirectafterlogout)
auth.settings.register_next = dbpn.friendly_url_to_page(settings.redirectafterregister)

cldbper = db_permissions.Permissions()

settings.pereditpage = cldbper.get_permissionid_by_codeandkey("SYSTEM_PAGE",
                                                       "Edit")
settings.perviewpage = cldbper.get_permissionid_by_codeandkey("SYSTEM_PAGE",
                                                       "View")

clPagNav = db_pages.Pages.Navigation()
clPyNav = db_pynuke.PyNuke.Navigation()
clsec = db_security.PNSecurity()

db_sitelog.SiteLog().define_tables()
db_eventlog.EventLog().define_tables()

auth.settings.login_onaccept.append(lambda form: db_eventlog.EventLog().eventlog('LOGIN_SUCCESS',form.vars,[('Action','Login'),
                                          ('User',form.vars.username),
                                          ]))
auth.settings.register_onaccept.append(lambda form: db_eventlog.EventLog().eventlog('USER_CREATED',form.vars,[('Action','Register'),
                                          ('User',form.vars.username),
                                          ('first name',form.vars.first_name),
                                          ('last_name',form.vars.last_name),
                                          ('email',form.vars.email),
                                          ('id',form.vars.id),
                                          ]))
auth.settings.profile_onaccept.append(lambda form: db_eventlog.EventLog().eventlog('USER_UPDATED',form.vars,[('Action','Profile modified'),
                                     ('profile',form.vars)
                                     ]))
auth.settings.verify_email_onaccept.append(lambda user: db_eventlog.EventLog().eventlog('USER_UPDATED',user,[('Action','Mail Verified'),
                                         ('User',user.username),
                                         ('email',user.email),
                                                                                                             ]))
auth.settings.logout_onlogout = lambda user: db_eventlog.EventLog().eventlog('LOGOUT_SUCCESS',user,[('Action','Logout'),
                                        ('User',user.username),
                                        ])
auth.settings.change_password_onvalidation = lambda user: db_eventlog.EventLog().eventlog('USER_UPDATED',user,[('Action','Reset Password Validation')])
auth.settings.change_password_onaccept = lambda user: db_eventlog.EventLog().eventlog('USER_UPDATED',user,[('Action','Change Password')])

