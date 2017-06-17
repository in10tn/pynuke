# -*- coding: utf-8 -*-
'''
@author: javier
'''

from gluon import *
import db_options
import db_pages
import db_packages
import db_pynuke
import uuid


class PageModules(object):

    def __init__(self):
        from gluon.globals import current
        self.db = current.db
        self.T = current.T
        self.auth = current.auth
        self.response = current.response
        self.clPyPages = db_pynuke.PyNuke.Pages()

    def define_tables(self):
        T = self.T
        db = self.db
        signature = db_pynuke.PyNuke().def_fields_signature()
        querypages = (db.pages.tree_id == 1) & (db.pages.id > 1)
        dict_containers = db_packages.Packages().get_layouts_available(2)

        db.define_table(
            'pagemodules',
            Field('moduleid',db.modules,label=T('module'),readable=False,writable=False),
            Field('moduletitle','string',label=T('Module title'), comment=T("Title for the module")),
            Field('moduleorder','integer',label=T('order')),
            Field('alignment',requires =IS_EMPTY_OR(IS_IN_SET([T('Left'),T('Center'),T('Right')]))),
            Field('pageid',db.pages,requires=IS_IN_DB(db(querypages),db.pages.id,'%(name)s'),label=T('Page'),represent=lambda id, row: A(db.pages(id).name,_href='%s' % db_pages.Pages.Navigation().friendly_url_to_page(id))),
            #Field('pageid',db.pages,requires=IS_IN_SET(db_pages.Pages.WebForms().get_pages_hierarchical()) ,label=T('Page')),
            Field('color','string',label=T('color')),
            Field('border','string',label=T('border')),
            Field('iconfile','upload',label=T('Icon File')),
            Field('panename',db.layouts_panes,label=T('Pane')),
            Field('cachetime','integer',readable=False,writable=False,label=T('Cache time')),
            Field('visibility','integer',readable=False,writable=False,label=T('Visibility')),
            Field('containersrc',db.layouts,requires=IS_EMPTY_OR(IS_IN_SET(dict_containers)),label=T('container')),
            Field('displaytitle','boolean',default=True,label=T('Display Title')),
            Field('displayprint','boolean',default=False,readable=False,writable=False,label=T('Display Print')),
            Field('displaysyndicate','boolean',default=False,readable=False,writable=False,label=T('Display Syndicate')),
            Field('iswebslice','boolean',default=False,readable=False,writable=False,label=T('Is Web Slice')),
            Field('webslicetitle','string',readable=False,writable=False,label=T('Web Slice Title')),
            Field('websliceexpirydate','datetime',readable=False,writable=False,label=T('Web Slice expiry date')),
            Field('webslicettl','integer',readable=False,writable=False,label=T('Web Slice ttl')),
            Field('isdeleted','boolean',label=T('Is Deleted'),readable=False,writable=False),
            Field('cachemethod','string',readable=False,writable=False,label=T('Cache Method')),           
            Field('header','text',label=T('Module header')),
            Field('footer','text',label=T('Module footer')),            
            Field('culturecode','string',label=T('Culture code'),readable=False,writable=False),
            Field('uniqueid',length=64,default=lambda:str(uuid.uuid4()),notnull=True,readable=False,writable=False),
            Field('versionguid',length=64,default=lambda:str(uuid.uuid4()),notnull=True,readable=False,writable=False),
            Field('defaultlanguageguid',length=64,default=lambda:str(uuid.uuid4()),notnull=True,readable=False,writable=False),
            Field('localizedversionguid',length=64,default=lambda:str(uuid.uuid4()),notnull=True,readable=False,writable=False),
            signature,
            format='%(moduletitle)s',
            plural='pagemodules',
            singular = 'pagemodule',  
            )
        
        db.define_table(
            'modulesettings',
            Field('pagemoduleid',db.pagemodules,label=T('pagemoduleid'),readable=False,writable=False),
            Field('settingname','string',label=T('Setting Name'),writable=False),
            Field('settingvalue','string',label=T('Setting Value')),
            signature,
            format='%(settingname)s',
            plural='Setting',
            singular = 'Settings',              
            
            )

        return;

    def get_pagepermissionsbypageid(self,pageid):
        '''
            Devuelve los permisos que tiene un page
            se usa para construir el menu
        '''
              
        db = self.db
        result = db(db.pagepermissions.page == pageid).select()                       
        
        return result       

    def user_canviewpage(self,pageid,userid):
            
        #devuelve True o False en funcion de si puede ver o no un page
        
        db = self.db
        result = False        
        page_permissionsx = self.get_pagepermissionsbypageid(pageid)
        roles_user = db(db.auth_membership.user_id==userid).select()
        
        for tp in page_permissionsx:
            rol_aut = tp.groupid
            for ru in roles_user:
                if ru.group_id == rol_aut:
                    result = True
        
        return result

    def get_pagemodules(self, pageid):
        db = self.db
        dbpm = db.pagemodules
        orderby = db.pagemodules.panename, db.pagemodules.moduleorder
        query_pagemodules = (dbpm.pageid == pageid) & (
            (dbpm.isdeleted == False) | (dbpm.isdeleted == None))
        records_page_modules = db(query_pagemodules).select(orderby=orderby)
        return records_page_modules

    def get_pagemoduletitle(self,pagemoduleid):
        
        db=self.db
        query = (db.pagemodules.id == pagemoduleid) 
        modulerecord = db(query).select().first()
        if modulerecord<>None:            
            module_title = modulerecord['moduletitle']
            displaytitle = modulerecord['displaytitle']
        else:
            module_title = ''            
            displaytitle =False

        return module_title,displaytitle

    def edit_pagemodule(self, pagemoduleid):

        """ Editar pagemodule a partir del pagemoduleid"""

        db = self.db
        clPyPages = self.clPyPages
        deletable = False
        pagemodulerecord = db.pagemodules[pagemoduleid]

        #Filtrar los paneles según el layout que tiene la pagina        
        obj_page = db.pages[pagemodulerecord.pageid]
        layouts_id_default = int(db_options.Options().get_option('plugin_layout_default'))
        container_id_default = int(db_options.Options().get_option('plugin_container_default'))

        try:
            layouts_id = obj_page.layoutsrc
        except:
            layouts_id = layouts_id_default

        if layouts_id == None:
            layouts_id = layouts_id_default

        panes = db_packages.Packages().get_panesfromlayoutid(layouts_id,True)        
        #limitar la lista de paneles para que solo se muestren los correspondientes al layout que está usando
        isinset_list = []
        for p in panes:
            item_panes = ((p['id']),p['panename'])
            isinset_list.append(item_panes)

        db.pagemodules.panename.requires = IS_IN_SET(isinset_list)

        db.pagemodules.pageid.requires = IS_IN_SET(clPyPages.get_pages_hierarchical())

        form = SQLFORM(db.pagemodules,
                       pagemoduleid,
                       showid=True,
                       deletable=deletable
                       )
        return form

    def get_all_modulesettings(self, pagemoduleid, dict_defaultvalues):

        db = self.db
        query = (db.modulesettings.pagemoduleid == pagemoduleid)
        options = dict()
        for row in db(query).select(db.modulesettings.ALL):
            if row.settingvalue == 'on':
                row.settingvalue = 'True'
            elif row.settingvalue == 'F':
                row.settingvalue = 'False'
            options[row.settingname] = row.settingvalue
        for item in dict_defaultvalues:
            try:
                value = options[item]
                dict_defaultvalues[item] = value
            except:
                pass
        return dict_defaultvalues

    def view_pagemodules_deleted(self):
        # pages deleted list
        
        db = self.db
        
        query = (db.pagemodules.isdeleted == True)
        
        fields = [db.pagemodules.id,
                      db.pagemodules.moduletitle,
                      db.pagemodules.pageid,                      
                     ]                                 
        
        gridlinks = [lambda row: self.get_icons_view_pagemodulesdeleted(row)]      
                      
        table = SQLFORM.grid(query,
                        fields=fields,
                        orderby=db.pagemodules.pageid,
                        user_signature=True,
                        create=False,
                        searchable=False,
                        deletable = False, #TODO: poner el boton borrar en get_icons y controlar el borrado para borrar tambien de tabla modules
                        editable=False,
                        csv=False,
                        details = False,
                        links=gridlinks                                         
                        )
        return table        

    def get_icons_view_pagemodulesdeleted(self,row):
        
        T=self.T
        db = self.db
#        objpageid = db.pages[row.pageid]        
#        enlace = A(I(_class='icon icon-eye-open'),
#                                    SPAN(T('')),_href="%s" % URL('default',
#                                        'page',
#                                        args=[objpageid.slug]),                                        
#                                        _title=T('Ver'), _class='btn btn-mini')
        
        enlace=(A(SPAN(_class='icon icon-backward'),
                           SPAN(T('')),
                            _href="%s" % URL('admin',
                                'restore_pagemodule',
                                vars = {'pagemoduleid': str(row.id)},
                                ),_title=T('Restore'), _class='btn btn-mini'                
                  )
                )                  

        enlace.append(A(SPAN(_class='icon icon-remove'),
                           SPAN(T('')),
                            _href="%s" % URL('admin',
                                'delete_pagemodule',
                                vars = {'pagemoduleid': str(row.id)},
                                ),_title=T('Delete'), _class='btn btn-mini'                
                  )
                )                  


        return enlace

    def get_pagemoduleid_from_page_and_moduleid(self, pageid, moduleid):

        db=self.db
        query = (db.pagemodules.pageid==pageid) & (db.pagemodules.moduleid==moduleid)
        record = db(query).select().first()
        return record.id

    def empty_recyclebin(self):
        db = self.db
        tpm = db.pagemodules
        tp = db.pages
        query = (tpm.isdeleted == True)
        recspm = db(query).select()
        for r in recspm:
            self.delete_pagemodule(r.id)
        self.delete_orphanmodules()
        query = (tp.isdeleted == True)
        db(query).delete()
        return

    def delete_orphanmodules(self):
        '''
            if are modules in table modules without entrys in pagemodules, 
            these modules are orphans, there is, not are added to any page and  
            then we can delete
        '''
        db = self.db
        orphanmodules = db(~db.modules.id.belongs(db()._select(db.pagemodules.moduleid))).delete()
        return

    def delete_pagemodule(self, pagemoduleid):
        '''
        Delete permanently a module. no lo marca como borrado. Esto se usa
        desde la papelera de reciclaje, para borrar definitivamente un módulo.

        Miramos en modules el moduleid que presente el objeto pagemodules
        a borrar.

        Si en Pagemodules ya no hay mas registros con este moduleid,
        borramos el module también

        '''
        db = self.db
        tpm = db.pagemodules
        objpagemodule = tpm[pagemoduleid]
        objmoduletosearch = objpagemodule.moduleid
        db(tpm.id == pagemoduleid).delete()
        db.commit()
        otherpagemodules = db(tpm.moduleid == objmoduletosearch).select()
        if len(otherpagemodules) == 0:
            db(db.modules.id == objmoduletosearch).delete()
            db.commit()

        return

    def proccess_form_settings(self, dict_values, pagemoduleid):
        '''
            Realiza el guardado en la base de datos de los formularios de
            settings de cualquier módulo.

            Parameters
            ----------
            dict_values:
                un diccionario, que normalmente será una copia del request.vars
                del formulario
            pagemoduleid:
                El valor se guarda en la tabla relacionado con el pagemoduleid
                indicado en el segundo parametro.
        '''

        db = self.db
        db_pynuke.PyNuke.Utils().clean_form_vars(dict_values)
        dbms = db.modulesettings
        for v in dict_values:
            try:
                if dict_values[v][0] == 'on':
                    dict_values[v] = 'True'
                elif dict_values[v][0] == 'F':
                    dict_values[v] = 'False'
            except:
                pass

            ''' En método update_or_insert especificamos la "query clave" que
            controla si existe el registro o ha de crearse nuevo'''
            query = (dbms.pagemoduleid == pagemoduleid) & (
                                                        dbms.settingname == v)
            dbms.update_or_insert(query, pagemoduleid=pagemoduleid,
                                                settingname=v,
                                                settingvalue=dict_values[v])
            db.commit()
        return

    def get_icons_gridpagemodules(self, row, moduleid, pageid, pagemoduleid):
        T = self.T
        db = self.db
#        objpageid = db.pages[row.pageid]        
#        enlace = A(I(_class='icon icon-eye-open'),
#                                    SPAN(T('')),_href="%s" % URL('default',
#                                        'page',
#                                        args=[objpageid.slug]),                                        
#                                        _title=T('Ver'), _class='btn btn-mini')
        enlace=(A(SPAN(_class='icon icon-wrench'),
                           SPAN(T('')),
                            _href="%s" % URL('default',
                                'msettings',
                                vars = {'pagemoduleid': str(row.id),
                                        'moduleid': str(row.moduleid),
                                        'pageid': str(row.pageid),
                                        },
                                ),_title=T('Settings'), _class='btn btn-mini'                
                  )
                )

#        https://127.0.0.1:8000/msettings?moduleid=94&pageid=48&pagemoduleid=392

        enlace.append(A(SPAN(_class='icon icon-trash'),
                           SPAN(T('')),
                            _href="%s" % URL('default',
                                'pagemodule_deletex',
                                vars = {'delpagemoduleid': str(row.id),
                                        'moduleid': str(moduleid),
                                        'pageid': str(pageid),
                                        'pagemoduleid':str(pagemoduleid),
                                        },

                                ),_title=T('Delete'), _class='btn btn-mini'                
                  )
                )


        return enlace

    def grid_pagemodules(self, moduleid, pageid, pagemoduleid):
        """ when a module is added to many pages, this grid show the pages"""

        T = self.T
        db = self.db
        objtable = db.pagemodules
        fields = [objtable.id,
                  objtable.moduleid,
                  objtable.pageid,
                  objtable.moduletitle
                     ]

        gridlinks = [lambda row: self.get_icons_gridpagemodules(row, moduleid,
                                                                pageid,
                                                                pagemoduleid)]

        query = ((db.pagemodules.moduleid == moduleid) & (db.pagemodules.pageid <> pageid))
        query = query & ((db.pagemodules.isdeleted == False) | (db.pagemodules.isdeleted == None))
        grid = SQLFORM.grid(query,
                            fields=fields,
                            links=gridlinks,
                            user_signature=False,
                            csv=False,
                            searchable=False,
                            create=False,
                            editable=False,
                            details=False,
                            deletable=False,
                            paginate=None,
                            args=[moduleid, pageid, pagemoduleid],
                            )
#        icon_add = SPAN(_class='icon plus icon-plus')
#        text_add = SPAN(T('Add'), _class='buttontext button')
#        button_add = A(icon_add + text_add, _href=addlink,
#                       _class='w2p_trap button btn')
#
#        grid.element('div[class=web2py_console').insert(0, XML('<br/>'))
#        grid.element('div[class=web2py_console').insert(0, button_add + ' ')

        return grid
