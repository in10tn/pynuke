# -*- coding: utf-8 -*-
'''
@author: javier
'''
from gluon import *
import datetime
import db_pynuke
import os
import yaml
import db_packages
import db_security
from urllib import urlopen

class BaseModules(object):
    '''
        En esta clase se definen los métodos relacionados con

        basemodules                |
            moduledefinitions      |  Estas tablas definen el módulo
                modulecontrols     |
                    modules --->      modules, junto a pagemodules definen
                                        un modulo en una página

    '''
    def __init__(self):
        from gluon import current
        self.db = current.db
        self.T = current.T
        self.auth = current.auth
        self.request = current.request
        self.settings = current.settings
    class Db_Functions(object):

        def __init__(self):
            from gluon import current
            self.db = current.db
            self.T = current.T
            self.auth = current.auth
            self.request = current.request
            self.settings = current.settings

        def define_tables(self):
            T = self.T
            db = self.db
            signature = db_pynuke.PyNuke().def_fields_signature()
            db.define_table('basemodules',
                Field('packageid', db.packages, requires=IS_EMPTY_OR(IS_IN_DB(db, 'packages.id', '%(friendlyname)s',
zero=T('choose one'))), label=T('Package')),
                Field('friendlyname', 'string', length = 255, unique=True,
                      label=T('Friendly name')),
                Field('description', 'string', label=T('Description')),
                Field('version', 'string', label=T('Version')),
                Field('ispremium', 'boolean', label=T('Is Premium?'),
                      readable=False,writable=False),
                Field('isadmin', 'boolean', label=T('Is Admin?'),
                      readable=False,writable=False),
                Field('controller', 'string', label=T('Controller')),
                Field('foldername', 'string', label=T('Folder Name'),
                      readable=False,writable=False),
                Field('modulename', 'string', label=T('Module Name')),
                Field('supportedfeatures', 'integer',
                      label=T('Supported Features'),
                      readable=False,writable=False),
                signature,
                format='%(friendlyname)s',
                plural='basemodules',
                singular='basemodule',
                )
            db.define_table(
                'moduledefinitions',
                Field('friendlyname', 'string', length = 255, required=True,
                      unique=True, label=T('Friendly name')),
                Field('basemoduleid', db.basemodules, ondelete='CASCADE'),
                Field('defaultcachetime', 'integer',),
                Field('table_meta', 'string', required=False,
                      label=T('Table Meta')),
                signature,
                format='%(friendlyname)s',
                plural=T('Module definitions'),
                singular=T('Module definition'),
                )

            db.define_table(
                'modulecontrols',
                Field('moduledefid', db.moduledefinitions, ondelete='CASCADE'),
                Field('controlkey', 'string'),
                Field('controltitle', 'string',),
                Field('controlsrc_controller', 'string'),
                Field('controlsrc_function', 'string'),
                Field('controlsrc_args', 'string'),
                Field('controlsrc_view', 'string'),
                Field('iconfile', 'string'),
                Field('linkcssclass', 'string'),
                Field('controltype', 'string'),
                Field('vieworder', 'integer'),
                Field('helpurl', 'string'),
                Field('useajax', 'boolean'),
                signature,
                format='%(controlkey)s',
                plural=T('Module Controls'),
                singular=T('Module Control'),
                )

            db.define_table(
                'modules',
                Field('moduledefid', db.moduledefinitions, required=True, 
                      label=T('Module definition'), ondelete='CASCADE',
                      writable=False),
                Field('allpages', 'boolean', label=T('All Tabs'),
                      default=False, comment=T("Check this for make the module visible in all existent and new pages, uncheck and save to delete all instances of the module and keep only this one ")),
                Field('isdeleted','boolean',label=T('Is deleted'),
                      default=False,readable=False,writable=False),
                Field('inheritviewpermissions',
                      'boolean',
                      writable=False,
                      label=T('Inherit permissions'),
                      comment=T("This module inherits the permissions from the page")),
                Field('startdate','datetime',
                      label=T('Start date'),
                      comment=T("The module will be visible in the specified date")),
                Field('enddate','datetime',
                      label=T('End Date'),
                      comment=T("The module will be not visible in the specified date")),
                signature,
                format='%(moduledefid)s',
                plural='Modules',
                singular='Module',
                )

            return

        def insert_initial_records(self, pagespage=-1):
            db = self.db
            settings = self.settings
            if db(db.basemodules.id > 0).count() == 0:
    #           #Modulo htmltext
                packid = db.packages.insert(name='htmltext',
                     friendlyname='HTML/Text',
                     description="Basic content module",
                     packagetype=3,
                     version='',
                     license='Licensed under the LGPL license version 3 (http://www.gnu.org/licenses/lgpl.html)',
                     manifest='',
                     owner='Pynuke',
                     organization='Pynuke',
                     url='http://www.pynuke.net',
                     email='info@pynuke.net',
                     releasenotes='Original version',
                     issystempackage=True,
                                         )

                bm_id = db.basemodules.insert(friendlyname='HTML/Text',
                                         packageid=packid,
                                         description="Basic content module",
                                         ispremium=False,
                                         controller='plugin_htmltext',
                                         isadmin=False,
                                         modulename='htmltext')

                md_id = db.moduledefinitions.insert(friendlyname='HTML/Text',
                                                    basemoduleid=bm_id)

#                htmltext_mod_id = db.modules.insert(moduledefid=md_id,
#                                           inheritviewpermissions=True,
#                                           )

                db.modulecontrols.insert(moduledefid=md_id,
                                        controlkey='view',
                                        controltitle='HTML-Text',
                                        controlsrc_controller='plugin_htmltext',
                                        controlsrc_function='view',
                                        controlsrc_args='',
                                        controlsrc_view='view.html',
                                        useajax=False
                                        )

                db.modulecontrols.insert(moduledefid=md_id,
                                        controlkey = 'edit',
                                        controltitle = 'Edit',
                                        linkcssclass = settings.cssclass_icon_edit,
                                        controlsrc_controller = 'plugin_htmltext',
                                        controlsrc_function = 'edit',
                                        controlsrc_args = '',
                                        controlsrc_view = 'edit.html',
                                        useajax=False
                                        )
            return

    class ModuleDefinitions(object):
        def __init__(self):
            from gluon import current
            self.db = current.db
            self.T = current.T
            self.auth = current.auth
            self.request = current.request
        
        def get_ModDefinition_by_name(self,name):
            db = self.db
            query = db(db.basemodules.modulename == name)
            rec = query.select().first()
            rec2 = db(db.moduledefinitions.basemoduleid==rec.id).select().first()
            return rec2
            

    class ModuleControls(object):
        def __init__(self):
            from gluon import current
            self.db = current.db
            self.T = current.T
            self.auth = current.auth
            self.request = current.request
        
    class WebForms(object):
        """
            En la clase WebForms se agrupan aquellas funciones relacionadas con
            la presentación HTML de formularios.
        """
        def __init__(self):
            self.db = current.db
            self.T = current.T
            self.auth = current.auth

#        def ver(self):
#            """
#                Devuelve un grid para gestionar la tabla basemodules
#            """
#            db = self.db
#            T = self.T
#            query = (db.basemodules.id > 0)
#            fields = [db.basemodules.id, db.basemodules.friendlyname,
#                          db.basemodules.description, db.basemodules.version
#                     ]
#            maxtextlengths = {'basemodules.id': 8,
#                              'basemodules.friendlyname': 90,
#                              'basemodules.description': 80,
#                              'basemodules.version': 80,
#                              }
#            links = [lambda row: A(I(_class='icon-edit'),
#                                   SPAN(T('')),
#                                    _href="%s" % URL('admin',
#                                    'editar_basemodules' ,
#                                    args=[row.id]),
#                                    _title=T('Edit'), _class="btn btn-mini"),
#                    ]
#            table = SQLFORM.grid(query,
#                            fields=fields,
#                            maxtextlengths=maxtextlengths,
#                            csv=True,
#                            links=links,
#                            searchable=True,
#                            create=False,
#                            editable=False,
#                            details=False,
#                            deletable=False,
#                            user_signature=True,
#                            )
#            return table

        def editar(self, basemodule_id):
            """
                devuelve un formulario para editar un basemodule
            """
            db = self.db
            record = db.basemodules[basemodule_id]
            deletable = True
            db.basemodules.packageid.writable = False
            db.basemodules.version.writable = False
            db.basemodules.version.readable = False

            result = SQLFORM(db.basemodules, record, showid=False,
                             deletable=deletable)
            return result


        def editar_module(self, module_id):
            '''
                devuelve un formulario para editar un module
            '''
            db = self.db
            record = db.modules[module_id]
            deletable = False
            
            result = SQLFORM(db.modules, record, deletable=deletable)
            return result

        def edit_definition(self, moduledefinition_id):
            db = self.db
            record = db.moduledefinitions[moduledefinition_id]
            deletable = False
            result = SQLFORM(db.moduledefinitions, record, deletable=deletable)
            return result

        def edit_control(self, control_id):
            db = self.db
            record = db.modulecontrols[control_id]
            deletable = False
            result = SQLFORM(db.modulecontrols, record, deletable=deletable)
            return result


        def ver_definitions(self, basemoduleid):
            '''
                Devuelve un grid de definitions asociados al module id
            '''
            db = self.db
            T = self.T
            query = (db.moduledefinitions.basemoduleid == basemoduleid)

            fields = [db.moduledefinitions.id,
                          db.moduledefinitions.friendlyname,
                          db.moduledefinitions.defaultcachetime,
                          db.moduledefinitions.table_meta,
                         ]
            maxtextlengths = {'moduledefinitions.friendlyname': 90,
                              'moduledefinitions.defaultcachetime': 10,
                              'moduledefinitions.table_meta': 50,
                              }
            links = [lambda row: self.get_enlaces_verdefinitions(row)]

            table = SQLFORM.grid(query,
                            fields=fields,
                            #maxtextlengths=maxtextlengths,
                            csv=False,
                            links=links,
                            searchable=False,
                            paginate=None,
                            create=False,
                            editable=False,
                            details=False,
                            deletable=False,
                            user_signature=False,
                            )
            return table
        
        def ver_controls(self, moduledefid):
            '''
                Devuelve un grid de definitions asociados al module id
            '''
            db = self.db
            T = self.T
            query = (db.modulecontrols.moduledefid == moduledefid)

            fields = [db.modulecontrols.id,
                          db.modulecontrols.controlkey,
                          db.modulecontrols.controltitle,
                          db.modulecontrols.controlsrc_controller,
                          db.modulecontrols.controlsrc_function,
                         ]
#            maxtextlengths = {'modulecontrols.friendlyname': 90,
#                              'modulecontrols.defaultcachetime': 10,
#                              'modulecontrols.table_meta': 50,
#                              }

            links = [lambda row: self.get_enlaces_vercontrols(row)]

            table = SQLFORM.grid(query,
                            fields=fields,
                            #maxtextlengths=maxtextlengths,
                            csv=False,
                            links=links,
                            searchable=False,
                            paginate=None,
                            create=False,
                            editable=False,
                            details=False,
                            deletable=False,
                            user_signature=False,
                            )
            return table

        def get_enlaces_vercontrols(self, row):
            T = self.T
            enlaces = A(I(_class='icon-edit'),
                                   SPAN(T('')),
                                    _href="%s" % URL('admin',
                                        'edit_control',
                                        args=[row.id]),
                                        _title=T('Edit'), 
                                        _class="btn btn-mini")
            return enlaces

        def get_enlaces_verdefinitions(self,row):
            T = self.T
            enlaces = A(I(_class='icon-edit'),
                                   SPAN(T('')),
                                    _href="%s" % URL('admin',
                                        'edit_definition',
                                        args=[row.id]),
                                        _title=T('Edit'), 
                                        _class="btn btn-mini")
#            enlaces.append(A(I(_class='icon-cog'),
#                                   SPAN(T('')),
#                                    _href="%s" % URL('admin',
#                                        'edit_controls',
#                                        args=[row.id]),
#                                        _title=T('Controls'), 
#                                        _class="btn btn-mini"),)
            return enlaces

#    def get_modules_for_install(self):
#        '''
#            Obtener la lista de módulos que pueden instalarse...
#        '''
#        db= self.db
#        result = {}
#        url_modules = current.options['url_check_version'].replace("current_version", "current_module_versions.txt")
#        lastversions = urlopen(url_modules).read()
#        allversions = lastversions.split("\n")
#        for m in allversions:
#            tmpxlist = m.split("|")
#            if tmpxlist[0] !='':
#                if db(db.basemodules.modulename == tmpxlist[0]).count() == 0:
#                    result[tmpxlist[0]] = tmpxlist[0]
#
#        return result

#    def form_upload_moduledefinition(self):
#        ''' Devuelve un formulario html que permite subir un fichero yaml con
#        la definicion del modulo
#        '''
#        dict_modules = self.get_modules_for_install()
#
#        request = self.request
#        upload_folder = os.path.join(request.folder, 'py_tmp')
#        result = SQLFORM.factory(Field('YAML_File', 'upload', \
#                            uploadfolder=upload_folder, label='YAML File'),
#                                 Field('download', label='Download',
#                                       requires=IS_IN_SET(dict_modules),
#                                       
#                                       ),
#                                 
#                            table_name='up_module_base'
#                            
#                            )
#
#        return result

#    def get_modversion(self, basemoduleid):
#        db = self.db
#        result = db.basemodules[basemoduleid].version or "0.0.0"
#        return result

#    def get_modlastversion(self, objbasemodule):
#        db= self.db
#        url_modules = current.options['url_check_version'].replace("current_version", "current_module_versions.txt")
#        lastversions = urlopen(url_modules).read()
#        allversions = lastversions.split("\n")
#        for m in allversions:
#            tmpxlist = m.split("|")
#            if tmpxlist[0] == objbasemodule.modulename:
#                lastversion = tmpxlist[1]
#                break
#
#        return lastversion

#    def proccess_install_moddefinition(self, namemodule):
#        db = self.db
#        url_modules = current.options['url_check_version'].replace("current_version", "current_module_versions.txt")
#        lastversions = urlopen(url_modules).read()
#        allversions = lastversions.split("\n")
#        basemoduleid = -1
#        for m in allversions:
#            tmpxlist = m.split("|")
#            if namemodule == tmpxlist[0]:
#                #todo: instalar modulo seleccionado
#                url_yaml_data = current.options['url_check_version'].replace("current_version", "module_yaml.txt/" + namemodule) 
#                yaml_data = urlopen(url_yaml_data).read()
#                config = yaml.load(yaml_data)  # leemos del fichero yaml
#                break
#        if config:
#            #insertamos en la base de datos la definición de module_base
#            basemoduleid = db.basemodules.insert( \
#                 friendlyname=config['module_base']['friendlyname'],
#                 description=config['module_base']['description'],
#                 version=config['module_base']['version'],
#                 ispremium=config['module_base']['ispremium'],
#                 isadmin=config['module_base']['isadmin'],
#                 controller=config['module_base']['controller'],
#                 foldername=config['module_base']['foldername'],
#                 modulename=config['module_base']['modulename'],
#                 supportedfeatures=config['module_base']['supportedfeatures'],
#                 )
#
#            for obj_md in config['module_base']['moduledefinitions']:
#                try:
#                    # insertamos el/los moduledefinition/s para el basemoduleid
#                    moduledefinition = db.moduledefinitions.insert(
#                               basemoduleid=basemoduleid,
#                               friendlyname=obj_md['friendlyname'],
#                               defaultcachetime=obj_md['defaultcachetime'],
#                               table_meta=obj_md['table_meta']
#                                                                   )
#                    for k in obj_md['controls']:
#                        db.modulecontrols.insert(moduledefid=moduledefinition,
#                     controlkey=k['controlkey'],
#                     controlsrc_args=k['controlsrc_args'],
#                     controlsrc_controller=k['controlsrc_controller'],
#                     controlsrc_function=k['controlsrc_function'],
#                     controlsrc_view=k['controlsrc_function'],
#                     controltitle=k['controltitle'],
#                     controltype=k['controltype'],
#                     helpurl=k['helpurl'],
#                     iconfile=k['iconfile'],
#                     linkcssclass=k['linkcssclass'],
#                     useajax=k['useajax'],
#                     vieworder=k['vieworder'],
#                     )
#
#                    db.commit()
#
#                except Exception:
#                    break
#
#        return basemoduleid


#    def proccess_yaml_moddefinition(self, filecontent):
#        db = self.db
#        config = yaml.load(filecontent)  # leemos del fichero yaml
#        if config:
#            #insertamos en la base de datos la definición de module_base
#            basemoduleid = db.basemodules.insert( \
#                 friendlyname=config['module_base']['friendlyname'],
#                 description=config['module_base']['description'],
#                 version=config['module_base']['version'],
#                 ispremium=config['module_base']['ispremium'],
#                 isadmin=config['module_base']['isadmin'],
#                 controller=config['module_base']['controller'],
#                 foldername=config['module_base']['foldername'],
#                 modulename=config['module_base']['modulename'],
#                 supportedfeatures=config['module_base']['supportedfeatures'],
#                 )
#
#            for obj_md in config['module_base']['moduledefinitions']:
#                try:
#                    # insertamos el/los moduledefinition/s para el basemoduleid
#                    moduledefinition = db.moduledefinitions.insert(
#                               basemoduleid=basemoduleid,
#                               friendlyname=obj_md['friendlyname'],
#                               defaultcachetime=obj_md['defaultcachetime'],
#                               table_meta=obj_md['table_meta']
#                                                                   )
#                    for k in obj_md['controls']:
#                        db.modulecontrols.insert(moduledefid=moduledefinition,
#                     controlkey=k['controlkey'],
#                     controlsrc_args=k['controlsrc_args'],
#                     controlsrc_controller=k['controlsrc_controller'],
#                     controlsrc_function=k['controlsrc_function'],
#                     controlsrc_view=k['controlsrc_function'],
#                     controltitle=k['controltitle'],
#                     controltype=k['controltype'],
#                     helpurl=k['helpurl'],
#                     iconfile=k['iconfile'],
#                     linkcssclass=k['linkcssclass'],
#                     useajax=k['useajax'],
#                     vieworder=k['vieworder'],
#                     )
#
#                    db.commit()
#
#                except Exception:
#                    break
#
#        return

#    def download_yaml_moddef(self, basemoduleid):
#        """
#        Pasandole un basemoduleid genera un diccionario yaml
#        con los meta-datos en pynuke de este módulo. Se exportan los datos
#        de las tablas que se necesitan para definir un módulo, que son las
#        siguientes:
#
#            basemodules
#                module_definitions (podría haber varios)
#                    module_controls (suele haber varios)
#
#        Parametros
#        ----------
#        basemoduleid:
#            id de la table basemodules del módulo que se va a descargar
#
#        Devuelve
#        --------
#        Un diccionario con todos los metadatos del basemodule, sus controles,
#        encapsulados en un fichero YAML
#
#        """
#
#        db = self.db
#        request = self.request
#        mydata = {}
#        objbm = db.basemodules[int(basemoduleid)]
#        tmd = db.moduledefinitions
#        tmc = db.modulecontrols
#
#        mydata['module_base'] = {'friendlyname': objbm.friendlyname,
#                       'description': objbm.description,
#                       'version': objbm.version,
#                       'ispremium': objbm.ispremium,
#                       'isadmin': objbm.isadmin,
#                       'controller': objbm.controller,
#                       'foldername': objbm.foldername,
#                       'supportedfeatures': objbm.supportedfeatures,
#                       'modulename': objbm.modulename,
#                       'moduledefinitions': []
#        }
#
#        moddefinitions = db(tmd.basemoduleid == objbm.id).select()
#        controls = dict()
#        cont_md = 0
#        for md in moddefinitions:
#            cont_controls = 0
#            item = {"friendlyname": md.friendlyname,
#                    "defaultcachetime": md.defaultcachetime,
#                    "table_meta": md.table_meta,
#                    "controls": []
#                    }
#            mydata['module_base']['moduledefinitions'].insert(cont_md, item)
#            controls[md.id] = db(tmc.moduledefid == md.id).select()
#            for c in controls[md.id]:
#                item = {'controlkey': c.controlkey,
#                           'controltitle': c.controltitle,
#                           'controlsrc_controller': c.controlsrc_controller,
#                           'controlsrc_function': c.controlsrc_function,
#                           'controlsrc_args': c.controlsrc_args,
#                           'controlsrc_view': c.controlsrc_view,
#                           'iconfile': c.iconfile,
#                           'linkcssclass': c.linkcssclass,
#                           'controltype': c.controltype,
#                           'vieworder': c.vieworder,
#                           'helpurl': c.helpurl,
#                           'useajax': c.useajax,
#                          }
#                mydata['module_base']['moduledefinitions'][cont_md]['controls'].insert(int(cont_controls), item)
#                cont_controls += 1
#            cont_md += 1
#        return mydata

    def copy_pagemodule_all_pages(self, moduleid, pagemoduleid, sourcepageid,
                                  copypagesettings=True):
        """
        Copia el modulo especificado en todas las páginas, agregando registros
        en pagemodules para cada página excepto para la pagina "fuente" que es
        de donde viene el módulo

        Parametros
        ----------
        moduleid:
            id de la tabla modules

        pagemoduleid:
            id de la table pagemodules del módulo que se va a a copiar en
            todas las paginas

        sourcepageid:
            página origen donde está el modulo. Ahí no se copiará

        copypagesettings:
            True if you want to copy the page settings too

        Return
        --------
        Nothing...

        """

        db = self.db
        settings = self.settings
        obj_module_to_duplicate = db.pagemodules[pagemoduleid]
        tpages = db.pages
        pages = db((tpages.isdeleted == False) | (tpages.isdeleted == None) & 
                                        (tpages.id != sourcepageid) &
                                        (tpages.tree_id == 1) &
                                        (tpages.level > 0)).select() 
        for p in pages:
            panename_orig = db_packages.Packages().get_panename_byid(obj_module_to_duplicate.panename) 
            pane_dest = db_packages.Packages().get_idpanename_from_name_and_layout(panename_orig,  p.layoutsrc or settings.plugin_layout_default)
            new_pagemoduleid = db.pagemodules.insert(pageid=p.id,
            moduleid=moduleid,
            moduletitle=obj_module_to_duplicate.moduletitle,
            moduleorder=obj_module_to_duplicate.moduleorder,
            alignment=obj_module_to_duplicate.alignment,
            color=obj_module_to_duplicate.color,
            border=obj_module_to_duplicate.color,
            iconfile=obj_module_to_duplicate.iconfile,           
            panename = pane_dest,
            cachetime=obj_module_to_duplicate.cachetime,
            visibility=obj_module_to_duplicate.visibility,
            containersrc=obj_module_to_duplicate.containersrc,
            displaytitle=obj_module_to_duplicate.displaytitle,
            displayprint=obj_module_to_duplicate.displayprint,
            displaysyndicate=obj_module_to_duplicate.displaysyndicate,
            cachemethod=obj_module_to_duplicate.cachemethod, 
            header=obj_module_to_duplicate.header,
            footer=obj_module_to_duplicate.footer,
            culturecode=obj_module_to_duplicate.culturecode,
                            )
            #optionally copy settings ...
            if copypagesettings:
                settings_to_duplicate = db(db.modulesettings.pagemoduleid==pagemoduleid).select()
                for setting in settings_to_duplicate:
                    db.modulesettings.insert(pagemoduleid=new_pagemoduleid,
                                             settingname=setting.settingname,
                                             settingvalue=setting.settingvalue)

        return

    def add_module(self, moduledefid, titlemoduletoadd, panetoadd, pagetoadd,
                   position, alignment):
        """
            Agrega un módulo a una página

            Parametros
            ----------
            moduledefid:
                id de la table module_definitions del módulo que a agregar
            titlemoduletoadd
                Titulo del modulo
            panetoadd:
                panel
            pagetoadd:
                pageid donde se agrega el módulo
            position:
                -1 o 0 según si es arriba o abajo, respectivamente
            alignment:
                la alineación
        """
        db = self.db

        # TODO: Averiguar el orden esto es rápido para salir del paso
        if position == -1:  # bottom
            max_order = db.pagemodules.moduleorder.max()
            max_order_result = db((db.pagemodules.pageid == pagetoadd) & \
                      (db.pagemodules.panename == panetoadd)).select(max_order)
            if max_order_result[0][max_order] == None:
                moduleorder = 1
            else:
                moduleorder = max_order_result[0][max_order] + 1
        else:
            min_order = db.pagemodules.moduleorder.min()
            min_order_result = db((db.pagemodules.pageid == pagetoadd) & \
                      (db.pagemodules.panename == panetoadd)).select(min_order)
            if min_order_result[0][min_order] == None:
                moduleorder = 1
            else:
                moduleorder = min_order_result[0][min_order] - 1
        '''
        Al agregar un nuevo modulo se crea una instancia en modules y es el id
        de esta (la instancia) el que se agrega a la pagina actual
        '''
        module_id = db.modules.insert(moduledefid=moduledefid,
                                           inheritviewpermissions=True,)
        if titlemoduletoadd == None or len(titlemoduletoadd) == 0:
            titlemoduletoadd = db.moduledefinitions[moduledefid].friendlyname
        db.pagemodules.insert(pageid=pagetoadd,
                              moduleid=module_id,
                              moduleorder=moduleorder,
                              moduletitle=titlemoduletoadd,
                              panename=panetoadd,
                              alignment=alignment)
        return

    def is_module_visible_bydates(self, modulex):
        """
          Pasandole un objeto modulo, comprueba si el módulo está entre el
          intervalo de fecha_inicio y fecha_fin y por tanto ha de mostrarse.

          Si el usuario es miembro del grupo de administradores, el módulo
          se visualiza siempre, independiente de sus fechas.

        """
        db = self.db
        auth = self.auth
        settings = self.settings
        dtnow = datetime.datetime.now
        module_isvisible = False
        if db_pynuke.PyNuke.Utils().is_in_interval_of_dates(
                                dtnow, modulex.startdate, modulex.enddate):
            module_isvisible = True

        if (auth.user_id != None) and ((auth.has_membership(
                                role=settings.admin_role_name))):
            module_isvisible = True

        return module_isvisible

    def get_button_settings(self, modx, panesav, pagemoduleid, pageid,
                            moddef):
        db = self.db
        T = self.T
        settings = self.settings
        urlmsettings = URL(a='init', c='default', f='msettings',
            vars=dict(moduleid=modx.id,
                      pageid=settings.currentpage,
                      pagemoduleid=pagemoduleid),
                           ).replace('.load', '')
        li_panes = []
        for p in panesav:
            obj = LI(A(p.panename, _href=URL(c="admin", f="movemodpane",
                                             vars=dict(mip=pagemoduleid,
                                                       pane=p.id,
                                                       pageidret=pageid)
                                                       )))
            li_panes.append(obj)

        # cargar todos los modulecontrols que no sean de tipo "View"
        dbmc = db.modulecontrols
        query = (dbmc.moduledefid == moddef.id) & (dbmc.controlkey != "view")
        modctls = db(query).select()
        listcontrols = []
        for mc in modctls:
            """ 
            Si es otro control, de momento solo se carga
            si es admin, mas adelante, habrá que
            chequear permisos
            """
            if settings.currentuser_is_admin:
                urldest = URL(c=str(mc.controlsrc_controller),
                              f=str(mc.controlsrc_function),
                              vars=dict(moduleid=modx.id, pageid=pageid,
                                        pagemoduleid=pagemoduleid))
                urlfinal = urldest.replace('.load', '')
                titulomc = T(mc.controltitle)

                li_module_controls = LI(A(DIV(I(_class=mc.linkcssclass),
                                              ' ' + titulomc),
                                            _href="%s" % urlfinal))
                listcontrols.append(li_module_controls)

        link = UL(LI(
                     A("", _href="#", _class="dropdown"),
                     UL(
                        LI(
                           A(DIV(I(_class='glyphicon glyphicon-wrench'),
                     ' ' + T("Settings")), _href="%s" % urlmsettings)
                           ),
                        listcontrols,
                        LI(
                           A(I(_class='glyphicon glyphicon-fullscreen'),
                    ' ' + T("Move to..."), _href="#"),
                           UL(li_panes,
                              _class="dropdown-menu")
                           , _class="dropdown-submenu"),
                        LI(
                           A(DIV(I(_class='glyphicon glyphicon-trash'),
                    ' ' + T("Delete")), _href="javascript:void(0)",
                             _onclick="deletemodule(%s);" % pagemoduleid
                             ))
                        , _class="dropdown-menu", _role="menu")
                     , _class="dropdown active",)
                  , _class="nav nav-pills")

        return link
    