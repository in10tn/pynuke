# -*- coding: utf-8 -*-
#!/usr/bin/env python

from gluon import *
import datetime
import db_pynuke


class PNSecurity(object):
    def __init__(self):
        from gluon.globals import current
        self.db = current.db
        self.T = current.T
        self.auth = current.auth
        self.settings = current.settings        

    def define_tables(self):
        """
            Esta funcion no define las tablas, realmente amplía la definición
            de auth_users con los campos especificados en los dos diccionarios
            que retorna.

            Devuelve
            ---------
            2 diccionarios users_extra_fields y groups_extra_fields

            Notas
            ------
            Aquí no utilizamos la función signature de pynuke ya que ésta
            hace uso precisamente de estas tablas.

        """

        T = self.T
        auth = current.auth

        users_extra_fields = [
            Field('superuser','boolean', default='False',readable=False,writable=False),
            Field('affiliateid','integer',readable=False,writable=False),
            Field('displayname',readable=False,writable=False),
            Field('updatepassword','boolean', default='False',readable=False,writable=False),
            Field('lastipaddress',readable=False,writable=False),
            Field('isdeleted','boolean', default='False',readable=False,writable=False),
            Field('createdbyuserid','reference auth_user',default=auth.user_id,readable=False,writable=False,label=T('Created by')),
            Field('createdon','datetime',default=datetime.datetime.now(),readable=True,writable=False,label=T('Created On')),
            Field('lastmodifiedbyuserid','reference auth_user',update=auth.user_id,readable=False,writable=False,label=T('Last modified by')),
            Field('lastmodifiedondate', 'datetime',update=datetime.datetime.now(),readable=True,writable=False,label=T('Last modified on')),
                ]
        groups_extra_fields = [
            Field('ServiceFee', 'double', readable=False, writable=False),
            Field('BillingFrequency', readable=False, writable=False),
            Field('TrialPeriod','integer',readable=False,writable=False),    
            Field('TrialFrequency',readable=False,writable=False),
            Field('BillingPeriod','integer',readable=False,writable=False),
            Field('TrialFee','double',readable=False,writable=False),
            Field('IsPublic','boolean', default='False',readable=False,writable=False),    
            Field('AutoAssignment','boolean', default='False',readable=False,writable=False),    
            Field('RSVPCode',readable=False,writable=False),
            Field('IconFile',readable=False,writable=False),        
            Field('createdbyuserid','reference auth_user',default=auth.user_id,writable=False,label=T('Created by')),
            Field('createdon','datetime',default=datetime.datetime.now(),writable=False,label=T('Created On')),
            Field('lastmodifiedbyuserid','reference auth_user',update=auth.user_id,writable=False,label=T('Last modified by')),
            Field('lastmodifiedondate', 'datetime',update=datetime.datetime.now(),writable=False,label=T('Last modified on')),
          ]

        return users_extra_fields, groups_extra_fields

#     def view_users(self):
#          users list
#         T = self.T
#         db = self.db
# 
#         query = (db.auth_user.id > 0) 
#         
#         fields = [db.auth_user.id,
#                       db.auth_user.first_name,
#                       db.auth_user.last_name,
#                       db.auth_user.email,
#                       db.auth_user.superuser,
#                       db.auth_user.affiliateid,
#                       db.auth_user.displayname,
#                       db.auth_user.lastipaddress,
#                      ]
#         links = [lambda row: A(I(_class='icon-edit'),
#                                SPAN(' '),
#                                 _href="%s" % URL('admin',
#                                     'user_edit' ,
#                                     args=[row.id],user_signature=True),
#                                     _title=T('Edit'), _class="btn btn-mini")
#                 ]
#         table = SQLFORM.grid(query,
#                         fields=fields,
#                         orderby=db.auth_user.id,
#                         csv=True,
#                         searchable=True,
#                         create=False,
#                         editable=False,
#                         details=False,
#                         links=links,
#                         deletable=False,
#                         user_signature=True,
#                         )
#         return table

    def view_groups(self):

        # users list
        
        db = self.db
        T = self.T
        settings = self.settings
        query = (db.auth_group.id > 0)
        
        fields = [db.auth_group.id,
                      db.auth_group.role,
                      db.auth_group.description,
                      db.auth_group.BillingFrequency,    
                      db.auth_group.TrialPeriod,
                      db.auth_group.TrialFrequency,
                      db.auth_group.BillingPeriod,
                      db.auth_group.TrialFee,
                      db.auth_group.IsPublic,
                                  
                     ]                                 
        links = [lambda row: A(I(_class=settings['cssclass_icon_edit']),
                               SPAN(' '),
                                _href="%s" % URL('admin',
                                    'rol_edit' ,
                                    args=[row.id],user_signature=True),
                                    _title=T('Edit'), _class="btn btn-mini")
                ]
        table = SQLFORM.grid(query,
                        fields=fields,
                        orderby=db.auth_group.id,
                        csv=True,
                        searchable=True,
                        create=True,
                        editable=False,
                        details=False,
                        links=links,
                        deletable=False,
                        user_signature=True,                 
                        )
        return table    

    def editar(self, option_id):
        '''
            devuelve un formulario para editar una opción
        '''        
        sepuedeborrar = False #TODO: que no se pueda borrar de momento pero sería con get_deletable
        db = self.db
        record = db.options[option_id]
        # TODO:creo que esto siempre se puede borrar  
        deletable = False
        result = SQLFORM(db.options, record,
                         deletable=deletable)

        return result

        #TODO: Opción BCC todos los mensajes que enviaría copia de todos los correos de gestion a una dirección especificada en la config
        #TODO: Parametrizar los dias antes de generar el pedido de renovación para servicios 

    def user_edit(self, user_id):
        '''Devuelve un formulario para editar un usuario'''
        db = self.db
        record = db.auth_user[user_id]

        deletable = self.user_can_be_deleted(user_id)

        result = SQLFORM(db.auth_user, record, deletable=deletable)

        return result

    def user_can_be_deleted (self, userid):
        '''
            El usuario no se puede borrar a si mismo

            El usuario no se puede borrar si está puesto como
            "administrador del portal"

        '''

        settings = current.settings
        auth = self.auth
        result = True
        if auth.user_id == userid:
            result = False
        if settings.portal_admin == userid:
            result = False

        return result

    def rol_edit(self, rol_id):
        '''
            devuelve un formulario para editar un group
        '''

        db = self.db
        record = db.auth_group[rol_id]
        deletable = self.rol_isdeletable(rol_id)
        result = SQLFORM(db.auth_group, record,
                         deletable=deletable)
        return result

    def rol_isdeletable(self, rolid):
        # Un grupo solo se puede borrar cuando se cumplan todas las condiciones:
        #
        #  * Ser mayor del grupo 3 (administradores,registrados, no verificados 
        # creados en la instalacion), es decir que no sea de sistema...
        #  * No tener ningun usuario asignado en las relaciones
        db = self.db
        result = False

        if rolid > 3:
            records = db(db.auth_membership.group_id == rolid).select()
            if len(records) == 0:
                result = True

        return result

    def membership_isdeletable(self, userid, roleid):
        # No se puede borrar de usuarios registrados
        # No se puede borrar la relación si se cumple algo de lo siguiente:
        # * userid = administrador del sitio y roleid = "Administradores"

        db = self.db
        deletable = True
        settings = self.settings
        auth = self.auth

        if (userid == int(settings.portal_admin) and (roleid == 1)) or (userid == auth.user_id and (roleid == 1)):
            deletable = False

        if roleid == 2 or roleid == 3:
            deletable = False

        rec_group = db.auth_group[roleid]
        if rec_group.role == 'user_' + str(userid):
            deletable = False

        return deletable

    def user_has_membership(self, userid, rolid):
        db = self.db
        query = (db.auth_membership.group_id == rolid)
        query = query & (db.auth_membership.user_id == userid)
        records = db(query).select()
        value = False
        if len(records) > 0:
            return True
        return value

    def getnameuser(self, iduser):
        """ Autor Name"""
        db = self.db
        name = 'No name'
        users = db(db.auth_user.id == iduser).select()
        if users:
            user = users[0]
            name = user.displayname
        return name

    def create_firsts_records_auth(self, options):
        ''' Creamos un grupo "administradores", un usuario admin y
            lo hacemos miembro.
            Creamos
            Devuelve los ids de usuario, grupo y no 
            verificados
        '''
        db = self.db
        T = self.T
        settings = current.settings
        auth = current.auth
        idg = -1
        idu = -1
        idru = -1
        if db(db.auth_group.id > 0).count() == 0:
            idu = 0
            if db(db.auth_user.id > 0).count() == 0:
                emailx = options['admin_email']
                first_namex = options['admin_first_name']
                last_namex = options['admin_last_name']
                user_namex = "admin"
                passwordx = db.auth_user.password.validate(
                                           options['admin_initial_password'])
                idu = db.auth_user.insert(first_name=first_namex,
                                          last_name=last_namex,
                                          email=emailx,
                                          password=passwordx[0],
                                          username=user_namex)

            idg = db.auth_group.insert(role=T("Administrators"),
                                       description=T("Administrators"),
                                       createdbyuserid=idu)
            idru = db.auth_group.insert(role=T("Registered users"),
                                        description=T("Registered users"),
                                        createdbyuserid=idu)
            idunv = db.auth_group.insert(role=T("Unverified users"),
                                        description=T("Unverified users"),
                                        createdbyuserid=idu)

            if idg and idu:
                auth.add_membership(idg, idu)
                auth.add_membership(idru, idu)

        return idg, idu, idru, idunv

    def delete_unique_rol(self, userid):
        ''' Pasandole un userid borra el rol que tiene asignado de forma unica
        ese userid '''
        db = self.db
        rol_name = "user_" + str(userid)
        db(db.auth_group.role == rol_name).delete()
        return None

    def get_roles_from_user(self,userid):
        ''' devuelve los roles de un usuario '''
        db = self.db
        tgroup = db.auth_group
        tmship = db.auth_membership
        xjoin = tgroup.on(db.auth_membership.group_id == tgroup.id)
        rolesasignados = db(tmship.user_id == userid).select(tgroup.id,
                                                            tgroup.role,
                                                            join=xjoin)

        return rolesasignados

    def get_users_from_role(self, roleid):
        ''' Devuelve los usuarios que pertenecen a un rol '''
        db = self.db
        tuser = db.auth_user
        tmship = db.auth_membership
        xjoin = tuser.on(db.auth_membership.user_id == tuser.id)
        #TODO: Comprobar si en la tabla existe el campo username para hacer
        # el order y el select, si no existe, no cogerlos...
        if "username" in tuser.fields():
            order = tuser.username
        else:
            order = tuser.id

        usersasignados = db(tmship.group_id == roleid).select(tuser.ALL,
                                                               join=xjoin,
                                                               orderby=order)
        return usersasignados

    def add_user_to_role(self, userid, roleid, notification=False):
        ''' agrega un usuario a un rol y opcionalmente le notifica
            (Pendiente acabar tema notificaciones)
        '''
        db = self.db
        tmship = db.auth_membership
        if userid + roleid > 0:
            #comprobamos que no existe en el rol...
            query = (tmship.user_id == userid) & (tmship.group_id == roleid)
            recs = db(query).select()
            if len(recs) == 0:
                tmship.insert(user_id=userid, group_id=roleid)
                db.commit()
                if notification == True:
                    #TODO: Enviar mensaje de correo electrónico
                    objuser = db.auth_user[userid]
                    destinatario = objuser.email
                    context = dict(destinatario=destinatario)
                    #enviar correo
    #                db.queue_smtp.insert(destinatario = destinatario,
    #                         asunto = T('Account Verified'),                         
    #                         texto=response.render('default/emailcuenta_verificada.txt',context),
    #                         html =response.render('default/emailcuenta_verificada.html',context),        
    #                         notas = "Puesto en cola al agregar un usuario al cliente " + str(datetime.datetime.now())                                 
    #                         )

    def remove_user_from_role(self, userid, roleid):
        ''' Elimina un usuario de un grupo '''
        db = self.db
        tmship = db.auth_membership
        query = (tmship.user_id == userid) & (tmship.group_id == roleid)
        db(query).delete()
        db.commit()

    def user_is_admin(self, userid):
        settings = current.settings
        auth = self.auth
        arn = settings.admin_role_name
        valor = False
        if (auth.user_id != None) and ((auth.has_membership(role=arn))):
            valor = True

        return valor

    def get_name_role_admin(self):
        '''
            Esta funcion se utiliza en la construccion de settings en memoria
            lo que sucede es que se llama en cada petición y la primera vez,
            el count va a dar 0, ya que no existen los registros, por tanto,
            vamos a crearlos.
        '''
        db = self.db
        options = current.options
        T = self.T
        if db(db.auth_group.id > 0).count() == 0:
            idg, idu, idru, idunv = self.create_firsts_records_auth(options)
            result = str(T("Administrators"))
        else:
            result = str(db.auth_group[1].role)

        return result

    def get_id_role_from_name(self, name_role):
        db = self.db
        tgroup = db.auth_group
        result = db(tgroup.role == name_role).select(id).first()[id]
        return result
