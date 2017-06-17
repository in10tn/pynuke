# -*- coding: utf-8 -*-

'''
Created on 29/07/2012

@author: javier
'''

from gluon import *
import db_pynuke, db_eventlog
import os
import yaml
import urllib
from gluon.fileutils import up, fix_newlines, abspath, recursive_unlink
from gluon.fileutils import read_file, write_file, parse_version
from urllib import urlopen
import zipfile


class Packages(object):
    def __init__(self):
        from gluon.globals import current
        self.db = current.db
        self.T = current.T
        self.auth = current.auth
        self.options = current.options
        self.request = current.request
        self.clEventLog = db_eventlog.EventLog()

    def define_tables(self):
        T = self.T
        db = self.db
        signature = db_pynuke.PyNuke().def_fields_signature()

        db.define_table(
            'packagetypes',
            Field('packagetype', 'string', label=T('Name of package type')),
            Field('description', 'text'),
            Field('securityaccesslevel', 'integer'),
            Field('editorcontrolsrc', 'string'),
            format='%(packagetype)s',
            plural='package types',
            singular='package type',
            )

        db.define_table(
            'packages',
            Field('name', 'string', length=255, unique=True),
            Field('friendlyname','string'),
            Field('description','text'),
            Field('packagetype',db.packagetypes,label=T('Package type')),
            Field('version','string'),
            Field('license','text'),
            Field('manifest','text'),
            Field('owner','string'),
            Field('organization','string'),
            Field('url','string'),
            Field('email','string'),
            Field('releasenotes','text'),
            Field('issystempackage','boolean'),
            signature,
            format='%(friendlyname)s',
            plural='packages',
            singular = 'package',
            )

        db.define_table(
            'layoutspackages',
            Field('packageid', db.packages),
            Field('layoutname', 'string'),
            Field('layouttype', 'string'),
            signature,
            format='%(layoutname)s',
            plural='layoutspackages',
            singular='layoutspackage',
            )

        db.define_table(
            'layouts',
            Field('layoutspackagesid', db.layoutspackages),
            Field('layoutsrc', 'string'),
            format='%(layoutsrc)s',
            plural='layouts',
            singular='layout',
            )

        db.define_table(
            'layouts_panes',
            Field('layout', db.layouts),
            Field('panename', 'string'),
            format='%(panename)s',
            plural='layouts_panes',
            singular='layout_pane',
            )

        return

    def insert_initial_records(self):
        db = self.db
        if db(db.packagetypes.id > 0).count() == 0:
            db.packagetypes.insert(packagetype='Layout',
                                  description='Layout',
                                  securityaccesslevel=3)
            db.packagetypes.insert(packagetype='Container',
                                    description='Container',
                                    securityaccesslevel=3)
            idmtype = db.packagetypes.insert(packagetype='Module',
                                             description='Module',
                                             securityaccesslevel=3)

            Packages.WebForms().proccess_package_in_folder("plugin_layout_bs3",1, issystempackage=True)
            Packages.WebForms().proccess_package_in_folder("plugin_containers_bs3",2, issystempackage=True)


#             # Bootstrap Layout
#             idpackage = db.packages.insert(name='Bootstrap 3 Layout',
#                                            friendlyname='Bootstrap 3 Layout',
#                                            description='Bootstrap 3 Layout',
#                                            packagetype=idptype,
#                                            version='0.0.1',
#                                            owner='pynuke',
#                                            organization='pynuke',
#                                            issystempackage=True)
#             idlayoutpackage = db.layoutspackages.insert(packageid=idpackage,
#                                                         layoutname='Bootstrap 3 Layout',
#                                                         layouttype='layout')
#             idlayout_base = db.layouts.insert(layoutspackagesid=idlayoutpackage,
#                                               layoutsrc='plugin_layout_bs3/layout.html')
# 
#             self.insert_original_panes(idlayout_base)

            # Bootstrap Containers

#             idpackagecont1 = db.packages.insert(name='Bootstrap Containers',
#                                                 description='Bootstrap containers',
#                                                 packagetype=idtypecont,
#                                                 version='0.0.1',
#                                                 owner = 'pynuke',
#                                                 organization = 'pynuke',
#                                                 issystempackage=True)
# 
#             idlayout_package_container = db.layoutspackages.insert(packageid=idpackagecont1,
#                                            layoutname='Bootstrap Containers',
#                                            layouttype='container')
# 
#             db.layouts.insert(layoutspackagesid=idlayout_package_container,
#                      layoutsrc='plugin_containers_bootstrap/containerh1.html')
#             db.layouts.insert(layoutspackagesid=idlayout_package_container,
#                      layoutsrc='plugin_containers_bootstrap/containerh2.html')
#             db.layouts.insert(layoutspackagesid=idlayout_package_container,
#                      layoutsrc='plugin_containers_bootstrap/containerh3.html')
#             db.layouts.insert(layoutspackagesid=idlayout_package_container,
#                      layoutsrc='plugin_containers_bootstrap/containerh4.html')
#             db.layouts.insert(layoutspackagesid=idlayout_package_container,
#                      layoutsrc='plugin_containers_bootstrap/containerh5.html')
#             db.layouts.insert(layoutspackagesid=idlayout_package_container,
#                      layoutsrc='plugin_containers_bootstrap/containerh6.html')

            
        return

    def insert_original_panes(self, idlayout):
        db = self.db

#         db.layouts_panes.insert(layout=idlayout,panename="toppane") #1
#         db.layouts_panes.insert(layout=idlayout,panename="leftpane") #2
#         db.layouts_panes.insert(layout=idlayout,panename="contentpane") #3
#         db.layouts_panes.insert(layout=idlayout,panename="rightpane") #4
#         db.layouts_panes.insert(layout=idlayout,panename="bottompane") #5
#         db.layouts_panes.insert(layout=idlayout,panename="middleleftpane_a") #5
#         db.layouts_panes.insert(layout=idlayout,panename="middlecontentpane_a") #5
#         db.layouts_panes.insert(layout=idlayout,panename="middleleftpane_b") #5
#         db.layouts_panes.insert(layout=idlayout,panename="middlecontentpane_b") #5
#         db.layouts_panes.insert(layout=idlayout,panename="showpaneup_1") #5
#         db.layouts_panes.insert(layout=idlayout,panename="showpaneup_2") #5
#         db.layouts_panes.insert(layout=idlayout,panename="showpaneup_3") #5
#         db.layouts_panes.insert(layout=idlayout,panename="showpaneup_4") #5
#         db.layouts_panes.insert(layout=idlayout,panename="upleftpane") #5
#         db.layouts_panes.insert(layout=idlayout,panename="upcontentpane") #5
#         db.layouts_panes.insert(layout=idlayout,panename="uprightpane") #5
#         db.layouts_panes.insert(layout=idlayout,panename="doublepane_1") #5
#         db.layouts_panes.insert(layout=idlayout,panename="doublepane_2") #5
#         db.layouts_panes.insert(layout=idlayout,panename="showpanedown_1") #5
#         db.layouts_panes.insert(layout=idlayout,panename="showpanedown_2") #5
#         db.layouts_panes.insert(layout=idlayout,panename="showpanedown_3") #5
#         db.layouts_panes.insert(layout=idlayout,panename="showpanedown_4") #5
#         db.layouts_panes.insert(layout=idlayout,panename="middleleftdownpane_a") #5
#         db.layouts_panes.insert(layout=idlayout,panename="middlecontentdownpane_a") #5
#         db.layouts_panes.insert(layout=idlayout,panename="middleleftdownpane_b") #5
#         db.layouts_panes.insert(layout=idlayout,panename="middlecontentdownpane_b") #5
#         db.layouts_panes.insert(layout=idlayout,panename="leftdownpane") #5
#         db.layouts_panes.insert(layout=idlayout,panename="contentdownpane") #5
#         db.layouts_panes.insert(layout=idlayout,panename="rightdownpane") #5
#         db.layouts_panes.insert(layout=idlayout,panename="downleftpane") #5
#         db.layouts_panes.insert(layout=idlayout,panename="downcontentpane") #5
#         db.layouts_panes.insert(layout=idlayout,panename="downrightpane") #5
        db.commit()

    def get_src_layout_by_layoutid(self, layoutid):
        db = self.db
        if layoutid != None:
            objlay = db.layouts[layoutid]
            return objlay.layoutsrc
        else:
            return None

    def get_id_layout_by_layoutsrc(self, layoutsrc):
        db = self.db
        query = (db.layouts.layoutsrc == layoutsrc)
        objlay = db(query).select().first()

        return objlay.id

    def get_panename_byid(self, layouts_panes_id):
        db = self.db
        result = "contentpane"
        if layouts_panes_id > 0:
            objpane = db.layouts_panes[layouts_panes_id]
            if objpane != None:
                result = objpane.panename

        return result

    def get_panesfromlayoutid(self, layouts_id, as_list=False):
 
        ''' Pasandole un id de layout devuelve un objeto rows con los paneles 
        de ese layout. Opcionalmente puede devolver una lista de paneles e ids
         '''
        db = self.db
        query = (db.layouts_panes.layout == layouts_id)
        orderby = db.layouts_panes.panename
        result = db(query).select(db.layouts_panes.id,
                                  db.layouts_panes.panename,
                                  orderby=orderby)
        if as_list:
            result = result.as_list()
        return result

    def get_panes_from_layout_file(self, layouts_id, as_list=False):
 
        # Find the panes used in a layout file.
        request = self.request
        layoutsrc = self.get_src_layout_by_layoutid(layouts_id)
        rutabase = request.folder[:len(request.folder) -1] + "/views/"
        panes = self.WebForms().read_panes_from_file(rutabase + layoutsrc)

        return panes


    def existe_panename(self,panename,layout_id): 
        # devuelve True o False en funcion de si encuentra un panel con el nombre
        # especificado en el layout id especificado
        db = self.db
        query_pane = db((db.layouts_panes.layout==layout_id) & (db.layouts_panes.panename==panename)).select()        
        
        if len(query_pane)>0:
            retorno = True
        else:
            retorno = False
        
        return retorno

    def get_idpanename_from_name_and_layout(self,panename,layout):

        db = self.db
        query_pane = db((db.layouts_panes.layout==layout) & (db.layouts_panes.panename==panename)).select().first()
        if query_pane:
            retorno = query_pane['id']
        else:
            retorno = -1
        
        return retorno

    def get_typepackage_fromid(self, idtype):
        db = self.db
        rec = db(db.packagetypes.packagetype == idtype).select().first()
        return rec.packagetype

    def get_packages_by_type(self, type):
        #obtener la lista de packages del tipo pasado en type
        db = self.db
        dbp = db.packages
        xpacks = db(dbp.packagetype == type).select()
        return xpacks    

    def get_layouts_available(self, type=1):
        '''
            Obtiene los layouts o containers disponibles, los valores de type
            se crean en la instalacion

            Type = 1 --> layouts
            Type = 2 --> containers

        '''
        db = self.db
        packages = self.get_packages_by_type(type)
        result = {}
        for p in packages:
            xlayoutspackages = db(db.layoutspackages.packageid == p.id).select()
            for layout_package in xlayoutspackages:
                xlayouts = db(db.layouts.layoutspackagesid == layout_package).select()
                for layout in xlayouts:
                    result[layout.id] = layout.layoutsrc

        return result

    def get_layouts_by_packageid(self, packageid):
        db = self.db
        layouts = db(db.layouts.layoutspackagesid == packageid).select()
        return layouts

    def get_packagelastversion(self, objpackage):
        db= self.db
        url_packages = current.options['url_check_version'].replace("current_version", "current_package_versions.txt")
        lastversions = urlopen(url_packages).read()
        allversions = lastversions.split("\n")
        lastversion = ''
        for m in allversions:
            tmpxlist = m.split("|")
            if tmpxlist[0] == objpackage.name:
                lastversion = tmpxlist[1]
                break

        return lastversion

    def get_packageversion(self, packageid):
            db = self.db
            result = db.packages[packageid].version or "0.0.0"
            return result

    def download_yaml_package(self, packageid):
        """
        Pasandole un packageid genera un diccionario yaml
        con los meta-datos en pynuke de este paquete. Se exportan los datos
        de las tablas que se necesitan para definir un módulo, que son las
        siguientes:

        Packages
            basemodules (podría haber varios)
                module_definitions (podría haber varios)
                    module_controls (suele haber varios)

        Parametros
        ----------
        packageid:
            id de la table packages del módulo que se va a descargar

        Devuelve
        --------
        Un diccionario con todos los metadatos de basemodules, sus controles,
        encapsulados en un fichero YAML

        """

        db = self.db
        request = self.request
        mydata = {}
        objpackage = db.packages[int(packageid)]
        tbm = db.basemodules
        tmd = db.moduledefinitions
        tmc = db.modulecontrols

        mydata['package'] = {'name': objpackage.name,
                       'friendlyname': objpackage.friendlyname,
                       'description': objpackage.description,
                       'packagetype': db.packagetypes[objpackage.packagetype].packagetype,
                       'version': objpackage.version,
                       'license': objpackage.license,
                       'manifest': objpackage.manifest,
                       'owner': objpackage.owner,
                       'organization': objpackage.organization,
                       'url': objpackage.url,
                       'email': objpackage.email,
                       'releasenotes': objpackage.releasenotes,
                       'basemodules': []
        }

        basemodules = db(tbm.packageid == objpackage.id).select()
        cont_bm = 0
        for bm in basemodules:
            basemodule = dict()
            item = {"friendlyname": bm.friendlyname,
                    "description": bm.description,
                    "version": bm.version,
                    "ispremium": bm.ispremium,
                    "isadmin": bm.isadmin,
                    "controller": bm.controller,
                    "foldername": bm.foldername,
                    "modulename": bm.modulename,
                    "supportedfeatures": bm.supportedfeatures,
                    "moduledefinitions": []
                    }
            mydata['package']['basemodules'].insert(cont_bm, item)
            moddefinitions = db(tmd.basemoduleid == bm.id).select()
            controls = dict()
            cont_md = 0
            for md in moddefinitions:
                cont_controls = 0
                item = {"friendlyname": md.friendlyname,
                        "defaultcachetime": md.defaultcachetime,
                        "table_meta": md.table_meta,
                        "controls": []
                        }
                mydata['package']['basemodules'][cont_bm]['moduledefinitions'].insert(cont_md, item)
                controls[md.id] = db(tmc.moduledefid == md.id).select()
                for c in controls[md.id]:
                    item = {'controlkey': c.controlkey,
                               'controltitle': c.controltitle,
                               'controlsrc_controller': c.controlsrc_controller,
                               'controlsrc_function': c.controlsrc_function,
                               'controlsrc_args': c.controlsrc_args,
                               'controlsrc_view': c.controlsrc_view,
                               'iconfile': c.iconfile,
                               'linkcssclass': c.linkcssclass,
                               'controltype': c.controltype,
                               'vieworder': c.vieworder,
                               'helpurl': c.helpurl,
                               'useajax': c.useajax,
                              }
                    mydata['package']['basemodules'][cont_bm]['moduledefinitions'][cont_md]['controls'].insert(cont_controls, item)
                    cont_controls += 1
                cont_md += 1
            cont_bm += 1
        return mydata

    class WebForms(object):
        """
            En la clase WebForms se agrupan aquellas funciones relacionadas con
            la presentación HTML de formularios.
        """
        def __init__(self):
            self.db = current.db
            self.T = current.T
            self.auth = current.auth        
            self.settings = current.settings
            self.options = current.options
            self.request = current.request


        def ver_packages(self, type=1):
            '''
                Returns Packages grid 
                type: Package type: 1 layout
                                    2 container
                                    3 module
            '''
            db = self.db
            T = self.T
            settings = self.settings
            query = (db.packages.packagetype == type)
            fields = [db.packages.id,
                      db.packages.friendlyname,
                      db.packages.description,
                      db.packages.version,
                      ]
            maxtextlengths = {'packages.id': 8,
                              'packages.friendlyname': 90,
                              'packages.description': 80,
                              'packages.version': 80,
                              }
            if type == 3:  # Module

                links = [lambda row: A(I(_class=settings['cssclass_icon_edit']),
                                       SPAN(T('')),
                                        _href="%s" % URL('admin',
                                            'edit_packagem',
                                            args=[row.id]),
                                            _title=T('Edit'), 
                                            _class=settings['cssclass_button_small']),
                         ]
            else:
                links = [lambda row: A(I(_class=settings['cssclass_icon_edit']),
                                       SPAN(T('')),
                                        _href="%s" % URL('admin',
                                            'edit_package',
                                            args=[row.id]),
                                            _title=T('Edit'), 
                                            _class=settings['cssclass_button_small']),
                        ]
            
            table = SQLFORM.grid(query,
                            fields=fields,
                            maxtextlengths=maxtextlengths,
                            csv=False,
                            links=links,
                            searchable=False,
                            create=False,
                            editable=False,
                            details=False,
                            deletable=False,
                            user_signature=True,
                            )          
            if type == 3:
                button_upload = A(I(_class='glyphicon glyphicon-arrow-up'),SPAN(' ' + T('Upload')),_href="%s" % URL('admin','upload_def'), _class="btn btn-sm btn-default")
            else:
                button_upload = A(I(_class='glyphicon glyphicon-arrow-up'),SPAN(' ' + T('Upload')),_href="%s" % URL('admin','upload_pac',args=type), _class="btn btn-sm btn-default")

            table.element('div[class=web2py_console').insert(0, button_upload + ' ')

            return table

        def proccess_package_in_folder(self, folder, type, issystempackage=False):
            '''
                procesar la carpeta especificada, buscando las vistas html y paneles
            '''
            db = self.db
            T = self.T
            request = self.request
            result = False
            
            if int(type) == 1:
                url_return = URL(c="admin", f="layouts")
                layouttype = "layout"
            elif int(type) == 2:
                url_return = URL(c="admin", f="containers")
                layouttype = "container"

            #creariamos un nuevo package
            packageid = db.packages.insert(name=folder,
                 packagetype=int(type),
                 friendlyname=folder,
                 description=T("This package is created automatically by Pynuke"),
                 version="Version 0.0.1",
                 license='',
                 manifest='',
                 owner='',
                 url='',
                 email='',
                 releasenotes='',
                 issystempackage=issystempackage,
                 )

            newlayoutpackage = db.layoutspackages.insert(packageid=packageid,
                                                    layoutname=folder,
                                                         layouttype=layouttype,
                                                         )

            rutabase = request.folder[:len(request.folder) -1] + "/views/" + folder
            # sorting the list to avoid conflicts with different files systems
            for filex in sorted(os.listdir(rutabase)):
                if filex.endswith(".html"):
                    filename = rutabase + "/" + filex
                    idlay = db.layouts.insert(layoutspackagesid=newlayoutpackage,
                                              layoutsrc=folder+"/" + filex)
                    panes = self.read_panes_from_file(filename)

                    for namepane in panes:
                        db.layouts_panes.insert(layout=idlay,
                                                panename=namepane)
            return

        def read_panes_from_file(self, filex):
            result = []
            const = "{{db_pynuke.PyNuke().render_modules_in_pane('"
            ilc = len(const)

            with open(filex, "r") as skinsrc:
                for line in skinsrc:
                    if const in line:
                        result1 = line.find(const)
                        result2 = line[result1 + ilc:].find("'")
                        substr = line[result1 + ilc:]
                        namepane = substr[:result2]
                        result.append(namepane)
            return result

        def editar_package(self, packageid):
            '''
                devuelve un formulario para editar un package
            '''
            db = self.db
            db.packages.packagetype.writable = False
            record = db.packages[packageid]
            deletable = self.package_isdeletable(packageid)
            result = SQLFORM(db.packages, record, showid=False,
                             deletable=deletable)
            return result

        def editar_layoutpackage(self, layoutpackageid):
            '''
                devuelve un formulario para editar un package
            '''
            db = self.db
            record = db.layoutspackages[layoutpackageid]
            deletable = self.package_isdeletable(record.packageid)
            result = SQLFORM(db.layoutspackages, record, showid=False,
                             deletable=deletable)
            return result


        def get_icons_ver_layouts(self, row):
            T = self.T
            enlace = A(SPAN(_class='icon edit'),
                               SPAN(T('')),
                                _href="%s" % URL(a="init",
                                                 c="admin",
                                                 f='edit_layout',
                                                 args=str(row.id),
                                                 ),
                                _title=T('Editar'),
                                _class='w2p_trap button16'
                  )
            return enlace

        def grid_layouts(self, layoutpackageid=-1, limit_records=-1, searchable=True,
                        sortable=True, paginate=10, args=[]):

            db = self.db
            T = self.T
            query = (db.layouts.layoutspackagesid == layoutpackageid)
            fields = [db.layouts.id,
                           db.layouts.layoutsrc,
                            ]
            headers = {'layouts.id': 'id',
                       'layouts.layoutsrc': 'SRC',
                        }
            maxtextlengths = {'layouts.id': 8,
                              'layouts.layoutsrc': 90,
                              }
            links = [lambda row: A(I(_class='icon-edit'),
                               SPAN(T('')),
                                _href="%s" % URL(c='admin',
                                                 f='edit_layout',
                                                 args=[row.id]),
                                _title=T('Edit'), 
                                _class="btn btn-mini")]

            table = SQLFORM.grid(query,
                            fields=fields,
                            links=links,
                            orderby=~db.layouts.id,
                            csv=False,
                            maxtextlengths=maxtextlengths,
                            searchable=searchable,
                            args=args,
                            create=False,
                            editable=False,
                            details=False,
                            deletable=False,
                            sortable=sortable,
                            paginate=paginate,
                            user_signature=False,
                            headers=headers
                            )
            
            return table

        def grid_layoutspackages(self, packageid=-1, limit_records=-1, searchable=True,
                        sortable=True, paginate=10, args=[]):

            db = self.db
            T = self.T
            query = (db.layoutspackages.packageid == packageid)
            fields = [db.layoutspackages.id,
                           db.layoutspackages.layoutname,
                            ]
#            headers = {'layouts.id': 'id',
#                       'layouts.layoutsrc': 'SRC',
#                        }
#            maxtextlengths = {'layouts.id': 8,
#                              'layouts.layoutsrc': 90,
#                              }
            links = [lambda row: A(I(_class='icon-edit'),
                               SPAN(T('')),
                                _href="%s" % URL(c='admin',
                                                 f='edit_layoutpackage',
                                                 args=[row.id]),
                                _title=T('Edit'), 
                                _class="btn btn-mini")]

            table = SQLFORM.grid(query,
                            fields=fields,
                            links=links,
                            orderby=~db.layoutspackages.id,
                            csv=False,
                            #maxtextlengths=maxtextlengths,
                            searchable=searchable,
                            args=args,
                            create=False,
                            editable=False,
                            details=False,
                            deletable=False,
                            sortable=sortable,
                            paginate=paginate,
                            user_signature=False,
                            #headers=headers
                            )
            return table


        def package_isdeletable(self, idpackage):
            '''
                solo se puede borrar si no está asignado al sitio,
                a alguna página o a algún módulo
            '''
            db = self.db
            result = True
            if idpackage != 1:  # Es del sistema, se crea al instalar
                #TODO: Para que un paquete se pueda borrar, todos sus
                #layouts se han de poder borrar.
                tbllp = db.layoutspackages
                tbl = db.layouts
                for layoutpackage in db(tbllp.packageid == idpackage).select():
                    for layout in db(tbl.layoutspackagesid == layoutpackage.id).select():
                        if not self.layout_isdeletable(layout.id):
                            result = False
                            break
                    if not result:
                        break
            return result

        def layout_isdeletable(self, idlayout):
            settings = self.settings
            db = self.db
            result = True
            if idlayout == 1:
                result = False
            else:
                if settings.plugin_layout_default == idlayout or settings.plugin_container_default == idlayout: 
                    result = False
                query = (db.pages.layoutsrc == idlayout) | (db.pages.containersrc == idlayout)
                recs = db(query).select()
                if len(recs) > 0:
                    result = False
                recs = db(db.pagemodules.containersrc == idlayout).select()
                if len(recs) > 0:
                    result = False

            return result

        def editar_layout(self, id):
            '''
                devuelve un formulario para editar un layout
            '''
            db = self.db
            record = db.layouts[id]
            deletable = True
            result = SQLFORM(db.layouts, record, showid=False,
                             deletable=deletable)
            return result

        def ver_panes(self,packageid,layoutid):
            '''
                Devuelve un grid de panes asociados al layout id que se pasa
            '''
            db = self.db
            T = self.T
            query = (db.layouts_panes.layout == layoutid)

            fields = [db.layouts_panes.id,
                          db.layouts_panes.panename,
                         ]
            maxtextlengths = {'layouts_panes.id': 8,
                              'layouts_panes.panename': 90,
                              }

            links = [lambda row: A(I(_class='icon-edit'),
                                   SPAN(T('')),
                                    _href="%s" % URL('admin',
                                        'edit_pane',
                                        args=[row.id,packageid,layoutid]),
                                        _title=T('Edit'), 
                                        _class="btn btn-mini"),
                    ]
            table = SQLFORM.grid(query,
                            fields=fields,
                            maxtextlengths=maxtextlengths,
                            csv=True,
                            links=links,
                            searchable=True,
                            paginate=None,
                            create=False,
                            editable=False,
                            details=False,
                            deletable=False,
                            user_signature=False,
                            )
            return table

        def ver_basemodules(self, packageid):
            '''
                Devuelve un grid de basemodules asociados al package id
            '''
            db = self.db
            T = self.T
            query = (db.basemodules.packageid == packageid)

            fields = [db.basemodules.friendlyname,
                          db.basemodules.controller,
                          db.basemodules.description,
                         ]
            maxtextlengths = {'basemodules.friendlyname': 90,
                              'basemodules.controller': 90,
                              'basemodules.description': 200,
                              }

            links = [lambda row: self.get_enlaces_verbasemodules(row)]

            table = SQLFORM.grid(query,
                            fields=fields,
                            maxtextlengths=maxtextlengths,
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

        def get_enlaces_verbasemodules(self,row):
            T = self.T
            enlaces = A(I(_class='icon-edit'),
                                   SPAN(T('')),
                                    _href="%s" % URL('admin',
                                        'editar_basemodules',
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


    class yaml_utils(object):
        def __init__(self):
            self.db = current.db
            self.T = current.T
            self.auth = current.auth
            self.request = current.request

        def download_yaml_package(self, packageid):
            """
            Pasandole un packageid genera un diccionario yaml
            con los meta-datos en pynuke de este diseño. Se exportan los datos
            de las tablas que se necesitan para definir un módulo, que son las
            siguientes:

                packages
                    layouts
                        panes

            Parametros
            ----------
            packageid:
                id de la table packages del package de diseño que se va a 
                descargar

            Devuelve
            --------
            Un diccionario con todos los metadatos del package y sus componentes,
            encapsulados en un fichero YAML

            """

            db = self.db
            request = self.request
            mydata = {}
            objpa = db.packages[int(request.args(0))]
            tlay = db.layouts
            tpan = db.layouts_panes
            tlaypack = db.layoutspackages
            reclaypack = db(tlaypack.packageid==objpa.id).select().first()
            reclayouts = db(tlay.layoutspackagesid == reclaypack.id).select()
            lays = dict()
            cont_lay = 0
            for lay in reclayouts:
                cont_panels = 0
                cont_lay += 1
                panes = db(tpan.layout == lay.id).select()
                dictpanes = {}
                for p in panes:
                    cont_panels += 1
                    dictpanes['pane_' + str(cont_panels)] = p.panename

                lays['layout_' + str(cont_lay)] = {'src': lay.layoutsrc,
                                                   'panes': dictpanes}

            mydata['package'] = {'name': objpa.name,
                                 'packagetype': objpa.packagetype.packagetype.lower(),
                               'friendlyname': objpa.friendlyname,
                               'description': objpa.description,
                               'version': objpa.version,
                               'license': objpa.license,
                               'manifest': objpa.manifest,
                               'owner': objpa.owner,
                               'organization': objpa.organization,
                               'url': objpa.url,
                               'email': objpa.email,
                               'releasenotes': objpa.email,
                               'layouts': lays}

            return mydata

        def form_upload_package(self, type_default):
            ''' Devuelve un formulario html que permite subir un fichero 
            yaml con la definicion del modulo
            '''
            T = self.T
            request = self.request
            upload_folder = os.path.join(request.folder, 'py_tmp')

            result = SQLFORM.factory(Field('YAML_File', 'upload',
                               uploadfolder=upload_folder,
                               label=T('YAML File:')),
             Field('register_layout', "string",
                   label=T('Existent folder with layout(s)')),
             Field('Type', "string", requires=IS_IN_SET((('1', '2')),
                                                        [T('Layout'),
                                                         T('Container')]),
                   default=type_default,
                   label=T('Select layout type'),
                   ),

            table_name='up_module_base')

            return result

        def get_packages_for_install(self):
            '''
                Obtener la lista de módulos que pueden instalarse...
            '''
            db= self.db
            result = {}
            url_modules = current.options['url_check_version'].replace("current_version", "current_package_versions.txt")
            lastversions = urlopen(url_modules).read()
            allversions = lastversions.split("\n")
            for p in allversions:
                tmpxlist = p.split("|")
                if tmpxlist[0] !='':
                    if db(db.packages.name == tmpxlist[0]).count() == 0:
                        result[tmpxlist[0]] = tmpxlist[0]
            return result

        def proccess_yaml_packdefinitionmod(self, filecontent):
            db = self.db
            config = yaml.load(filecontent)  # leemos del fichero yaml
            if config:
                #insertamos en la base de datos la definición del package
                packagetype = db(db.packagetypes.packagetype == config['package']['packagetype']).select().first().id
                packageid = db.packages.insert(name=config['package']['name'],
                     friendlyname=config['package']['friendlyname'],
                     description=config['package']['description'],
                     packagetype=packagetype,
                     version=config['package']['version'],
                     license=config['package']['license'],
                     manifest=config['package']['manifest'],
                     owner=config['package']['owner'],
                     organization=config['package']['organization'],
                     url=config['package']['url'],
                     email=config['package']['email'],
                     releasenotes=config['package']['releasenotes'],
                     )
                contmod = 0
                for obj_mb in config['package']['basemodules']:
                    #insertamos en la base de datos la definición de module_base
                    basemoduleid = db.basemodules.insert( \
                         packageid=packageid,
                         friendlyname=config['package']['basemodules'][contmod]['friendlyname'],
                         description=config['package']['basemodules'][contmod]['description'],
                         version=config['package']['basemodules'][contmod]['version'],
                         ispremium=config['package']['basemodules'][contmod]['ispremium'],
                         isadmin=config['package']['basemodules'][contmod]['isadmin'],
                         controller=config['package']['basemodules'][contmod]['controller'],
                         foldername=config['package']['basemodules'][contmod]['foldername'],
                         modulename=config['package']['basemodules'][contmod]['modulename'],
                         supportedfeatures=config['package']['basemodules'][contmod]['supportedfeatures'],
                         )

                    for obj_md in config['package']['basemodules'][contmod]['moduledefinitions']:
                        try:
                            # insertamos el/los moduledefinition/s para el basemoduleid
                            moduledefinition = db.moduledefinitions.insert(
                                       basemoduleid=basemoduleid,
                                       friendlyname=obj_md['friendlyname'],
                                       defaultcachetime=obj_md['defaultcachetime'],
                                       table_meta=obj_md['table_meta']
                                                                           )
                            for k in obj_md['controls']:
                                db.modulecontrols.insert(moduledefid=moduledefinition,
                             controlkey=k['controlkey'],
                             controlsrc_args=k['controlsrc_args'],
                             controlsrc_controller=k['controlsrc_controller'],
                             controlsrc_function=k['controlsrc_function'],
                             controlsrc_view=k['controlsrc_function'],
                             controltitle=k['controltitle'],
                             controltype=k['controltype'],
                             helpurl=k['helpurl'],
                             iconfile=k['iconfile'],
                             linkcssclass=k['linkcssclass'],
                             useajax=k['useajax'],
                             vieworder=k['vieworder'],
                             )

                            db.commit()
                        except Exception:
                            break

                    contmod += 1

            return

        def proccess_install_packdefinition(self, namepack):
            db = self.db
            request = self.request
            url_packs = current.options['url_check_version'].replace("current_version", "current_package_versions.txt")
            lastversions = urlopen(url_packs).read()
            allversions = lastversions.split("\n")
            basemoduleid = -1
            cldbpnu = db_pynuke.PyNuke.Upgrades()
            for m in allversions:
                tmpxlist = m.split("|")
                if namepack == tmpxlist[0]:
                    #todo: instalar modulo seleccionado
                    url_yaml_data = current.options['url_check_version'].replace("current_version", "package_yaml.txt/" + namepack) 
                    yaml_data = urlopen(url_yaml_data).read()
                    config = yaml.load(yaml_data)  # leemos del fichero yaml
                    break
            if config:
                #insertamos en la base de datos la definición del package
                packagetype = db(db.packagetypes.packagetype == config['package']['packagetype']).select().first().id
                packageid = db.packages.insert(name=config['package']['name'],
                     friendlyname=config['package']['friendlyname'],
                     description=config['package']['description'],
                     packagetype=packagetype,
                     version=config['package']['version'],
                     license=config['package']['license'],
                     manifest=config['package']['manifest'],
                     owner=config['package']['owner'],
                     organization=config['package']['organization'],
                     url=config['package']['url'],
                     email=config['package']['email'],
                     releasenotes=config['package']['releasenotes'],
                     )
                contmod = 0
                for obj_mb in config['package']['basemodules']:
                    #insertamos en la base de datos la definición de module_base
                    basemoduleid = db.basemodules.insert( \
                         packageid=packageid,
                         friendlyname=config['package']['basemodules'][contmod]['friendlyname'],
                         description=config['package']['basemodules'][contmod]['description'],
                         version=config['package']['basemodules'][contmod]['version'],
                         ispremium=config['package']['basemodules'][contmod]['ispremium'],
                         isadmin=config['package']['basemodules'][contmod]['isadmin'],
                         controller=config['package']['basemodules'][contmod]['controller'],
                         foldername=config['package']['basemodules'][contmod]['foldername'],
                         modulename=config['package']['basemodules'][contmod]['modulename'],
                         supportedfeatures=config['package']['basemodules'][contmod]['supportedfeatures'],
                         )

                    for obj_md in config['package']['basemodules'][contmod]['moduledefinitions']:
                        try:
                            # insertamos el/los moduledefinition/s para el basemoduleid
                            moduledefinition = db.moduledefinitions.insert(
                                       basemoduleid=basemoduleid,
                                       friendlyname=obj_md['friendlyname'],
                                       defaultcachetime=obj_md['defaultcachetime'],
                                       table_meta=obj_md['table_meta']
                                                                           )
                            for k in obj_md['controls']:
                                db.modulecontrols.insert(moduledefid=moduledefinition,
                             controlkey=k['controlkey'],
                             controlsrc_args=k['controlsrc_args'],
                             controlsrc_controller=k['controlsrc_controller'],
                             controlsrc_function=k['controlsrc_function'],
                             controlsrc_view=k['controlsrc_function'],
                             controltitle=k['controltitle'],
                             controltype=k['controltype'],
                             helpurl=k['helpurl'],
                             iconfile=k['iconfile'],
                             linkcssclass=k['linkcssclass'],
                             useajax=k['useajax'],
                             vieworder=k['vieworder'],
                             )

                            db.commit()
                        except Exception:
                            break

                    contmod += 1

                #TODO: descargar fichero source y descomprimir
                gluon_parent = request.env.gluon_parent
                obj_package = db.packages[packageid]
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
                    destination = gluon_parent + "/applications/init"
                    subfolder = 'pynukedev-' + obj_package.name + '-' + obj_package.version.split(";")[1]

                #https://bitbucket.org/pynukedev/pynuke/get/fef75d9c0931.zip
                full_url = "https://bitbucket.org/pynukedev/" + obj_package.name + "/get/" + '%s.zip' % obj_package.version.split(";")[1]
                filename = abspath(obj_package.name + '_%s_downloaded.zip' % version_type)
                file = None 
                try:
                    write_file(filename, urllib.urlopen(full_url).read(), 'wb')
                except Exception, e:
                    return False, e
                try:
                    clEventLog = db_eventlog.EventLog()
                    version = obj_package.version
                    listnames = cldbpnu.unzip(filename, destination, version, subfolder, obj_package.name)
                    clEventLog.eventlog("HOST_ALERT", locals(),[('Package Installed', obj_package.name),
                                                                ('Version', version),
                                                                ('Files installed', listnames)
                                                                ])
                except Exception, e:
                    return False, e

            return packageid

#         def unzip(self, filename, dir, version, subfolder='', modulename=""):
#             """
#             Unzips filename into dir (.zip only, no .gz etc)
#             if subfolder!='' it unzip only files in subfolder
#             """
#             listnames = []
#             filename = abspath(filename)
#             if not zipfile.is_zipfile(filename):
#                 raise RuntimeError('Not a valid zipfile')
#             zf = zipfile.ZipFile(filename)
#             if not subfolder.endswith('/'):
#                 subfolder = subfolder + '/'
#             n = len(subfolder)
#             for name in sorted(zf.namelist()):
#                 if not name.startswith(subfolder):
#                     continue
#                 print name[n:]
#                 if name.endswith('/'):
#                     folder = os.path.join(dir, name)
#                     if not os.path.exists(folder):
#                         os.mkdir(folder)
#                 else:
#                     if modulename == "":
#                         namesave = name.replace("pynukedev-pynuke-" + version.split(";")[1] + "/", "")
#                     else:
#                         namesave = name.replace("pynukedev-" + modulename + "-" + version.split(";")[1] + "/", "")
#         
#                     listnames.append(namesave)
# 
#                     if not namesave.startswith("."):
#                         folder = namesave.replace(os.path.basename(namesave),"")
#                         if not os.path.exists(os.path.join(dir,folder)):
#                             os.makedirs(os.path.join(dir,folder))
#                         write_file(os.path.join(dir, namesave), zf.read(name), 'wb')
# 
#             return listnames

        def form_upload_packagemod(self):
            ''' Returns the form to install a new module
            '''
            T = self.T
            request = self.request

            dict_modules = self.get_packages_for_install()

            upload_folder = os.path.join(request.folder, 'py_tmp')
            result = SQLFORM.factory(Field('YAML_File', 'upload',
                                           uploadfolder=upload_folder,
                                           label=T('YAML File:')),
                         Field('download', label='Download',
                               requires=IS_EMPTY_OR(IS_IN_SET(dict_modules))),
                        table_name='up_module_base')

            return result

        def get_type_package_from_yaml_loaded(self,yaml_loaded):
            typepackage = 1 #Por defecto layout
            if yaml_loaded['package'].has_key('packagetype'):
                if yaml_loaded['package']['packagetype'] == 'container':
                    typepackage = 2

            return typepackage

        def proccess_yaml_packdefinition(self, filecontent):
            db = self.db
            config = yaml.load(filecontent)  # leemos del fichero yaml
            typepackage = self.get_type_package_from_yaml_loaded(config)
            packageid = db.packages.insert(name=config['package']['name'],
                 packagetype=typepackage,
                 friendlyname=config['package']['friendlyname'],
                 description=config['package']['description'],
                 version=config['package']['version'],
                 license=config['package']['license'],
                 manifest=config['package']['manifest'],
                 owner=config['package']['owner'],
                 url=config['package']['url'],
                 email=config['package']['email'],
                 releasenotes=config['package']['releasenotes'],
                 issystempackage=False,
                 )

            newlayoutpackage = db.layoutspackages.insert(packageid=packageid,
                                                         layoutname=config['package']['name'],
                                                         layouttype="layout",
                                                         )

            cont_layouts = len(config['package']['layouts'].items())

            while cont_layouts >= 1:

                    obj_lay = config['package']['layouts']['layout_' + str(cont_layouts)]
                    newlayoutid = db.layouts.insert(layoutspackagesid=newlayoutpackage,
                                                    layoutsrc=obj_lay['src'])
                    panes = obj_lay['panes']
                    for p in panes.values():
                        db.layouts_panes.insert(layout=newlayoutid,
                                                panename=p)
                    cont_layouts -= 1
            db.commit()

            return typepackage
