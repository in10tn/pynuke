#!/usr/bin/env python
# encoding: utf-8
# Requiere instalar http://pyyaml.org/wiki/PyYAML
from gluon import *
import datetime
import db_pages
import db_pynuke
import math
import os
import urllib
import uuid
import yaml
from gluon.sanitizer import sanitize

class EventLog(object):

    def __init__(self):
        from gluon.globals import current
        self.db = current.db
        self.T = current.T
        self.settings = current.settings
        self.auth = current.auth
        self.recordscount = 0
        self.currentpage = 1
        self.max_results_x_page = -1
        self.max_display_pages = 10
        self.render_url_page = lambda page, controller, function: \
                    self.default_url_page(page, controller, function)
        self.request_vars = {}
        self.currentpageslug = self.settings.currentpageslug
        self.reporttype = ""

    def define_tables(self):
        T = self.T
        db = self.db
        auth = self.auth
        db.define_table('eventtypes',
            Field('logtypekey',required=True,),
            Field('friendlyname',required=True,),
            Field('description'),
            Field('cssclass'),
            format='%(friendlyname)s',
            plural='Event types',
            singular='Event type'
                        )

        db.define_table('eventlogconfig',
            Field('logtypekey',db.eventtypes,required=True,),
            Field('loggingisactive','boolean'),
            Field('keepmostrecent','integer',),
            Field('emailnotificationisactive','boolean',),
            Field('notificationthreshold','integer',),
            Field('notificationthresholdtimetype','integer',),
            Field('mailfromaddress',requires=IS_EMPTY_OR(IS_EMAIL())),
            Field('mailtoaddress',requires=IS_EMPTY_OR(IS_EMAIL())),
            )

        db.define_table('eventlog',
            Field('guid',length=64,
                  default=lambda:str(uuid.uuid4()),
                  notnull=True,writable=False,readable=True),
            Field('typekey',db.eventtypes),
            Field('configid',db.eventlogconfig,),
            Field('userid', db.auth_user, default=auth.user_id,
                  writable=False, label=T('User ID')),
            Field('username', label=T('User name')),
            Field('portalname', label=T('Portal name')),
            Field('createdate', 'datetime', default=datetime.datetime.now(), label=T('Created by')),
            Field('servername', label=T('Server name')),
            Field('properties', "text", label=T('Properties')),
            Field('notificationpending', 'boolean', label=T('Notification pending')),
            )
        self.insert_default_eventtypes()
        self.insert_default_eventlogconfigs()
        return

    def insert_default_eventtypes(self):
        db = self.db
        if db(db.eventtypes.id > 0).count() == 0:
            fname = os.path.join(current.request.folder, "modules", "options.yaml")
            config = yaml.load(file(fname, 'r'))
            if config:
                for event in config['eventtypes']:
                    db.eventtypes.insert(logtypekey=event['logtypekey'],
                                      friendlyname=event['friendlyname'],
                                      description=event['description'],
                                      cssclass=event['cssclass'],
                                      )
                db.commit()
        return

    def insert_default_eventlogconfigs(self):
        db = self.db
        if db(db.eventlogconfig.id > 0).count() == 0:
            fname = os.path.join(current.request.folder, "modules", "options.yaml")
            configs = yaml.load(file(fname, 'r'))
            if configs:
                for event in configs['eventconfigs']:
                    logtypekey = event['logtypekey']
                    eventtype = db(db.eventtypes.logtypekey == logtypekey).select(
                                                  db.eventtypes.friendlyname,
                                                  db.eventtypes.id).first()
                    loggingisactive = db_pynuke.PyNuke.Utils().str2bool(event['loggingisactive'])

                    db.eventlogconfig.insert(logtypekey=eventtype.id,
                                      loggingisactive=loggingisactive,
                                      keepmostrecent=int(event['keepmostrecent']),
                                      )
                db.commit()
        return

    def render_pagination(self, controller='admin', function='eventlog'):
        T = current.T
        firstresult = self.currentpage * self.max_results_x_page - self.max_results_x_page
        lastresult = self.currentpage * self.max_results_x_page
        recordscount = self.recordscount

        if lastresult > recordscount:
            lastresult = recordscount

        if recordscount < self.max_results_x_page:
            return ""
        title = '''%(displaying)s %(firstresult)s %(to)s %(lastresult)s %(of)s %(recordscount)s ''' % \
                {'displaying': T('Displaying'),
                'to': T('to'),
                'of': T('of'),
                'firstresult': firstresult + 1,
                'lastresult': lastresult,
                'recordscount': recordscount}
        divtitle = DIV(title,)
        cleardiv = DIV(_style='clear: both')
        pagination = DIV(divtitle, self.render_pages(controller, function),
                         cleardiv, _class='pagination')
        return XML(pagination)

    def render_pages(self, controller='default', function='page'):
        """ Render pages """

        T = current.T
        rendered = []
        if self.recordscount > self.max_results_x_page:
            total_pages = self.recordscount // self.max_results_x_page
            if (self.recordscount % self.max_results_x_page)>0:
                total_pages += 1
            first_page = int(math.ceil(self.currentpage / self.max_display_pages)) * self.max_display_pages

            if first_page < 1:
                first_page = 1
                if total_pages < self.max_display_pages:
                    last_page = total_pages
                else:
                    last_page = self.max_display_pages
            else:
                last_page = total_pages
                if total_pages > first_page - last_page: 
                    last_page = first_page + self.max_display_pages
                if last_page > total_pages:
                    last_page = total_pages

            backward = A(T('Prior'), _href=self.render_url_page(self.currentpage-1,controller,function))
            forward = A(T('Next'), _href=self.render_url_page(self.currentpage+1, controller, function))
            first = A(T('First'), _href=self.render_url_page(1, controller, function))
            last = A(T('Last'), _href=self.render_url_page(last_page, controller, function))

            listpages = []
            listpages.append(first)

            if self.currentpage > 1:
                listpages.append(LI(backward))

            #TODO: revisar que solo se activen los links que correspondan
            #http://twitter.github.com/bootstrap/components.html#pagination
            #Disabled and active states
            for page in range(first_page, last_page + 1):
                page_a = A(str(page), _href=self.render_url_page(page, controller, function))
                if page <= total_pages:
                    if page == self.currentpage:
                        class_current = 'active'
                    else:
                        class_current = ''

                    listpages.append(LI(page_a, _class=class_current))

            if total_pages > self.currentpage:
                listpages.append(LI(forward))

            listpages.append(last)

            if listpages != []:
                rendered = DIV(UL(listpages), _class='pages')

        if rendered == []:
            rendered = ''

        return rendered

    def default_url_page(self, page, controller, function):
        """ Generate the url to a page """
        rq_vars = self.request_vars.copy()
        rq_vars['pag'] = page
        result = URL(controller, function, args=[self.currentpageslug], \
                                                vars=rq_vars)
        return result

    def grid_eventlog(self, pag=1):
        """ Grid Log """
        db = self.db
        T = self.T
        settings = self.settings
        result = ""
        self.currentpage = pag  # Id de pag a ver del modulo blog (paginador)
        self.max_results_x_page = 15

        limit_inf = (self.max_results_x_page * pag) - self.max_results_x_page
        limit_sup = self.max_results_x_page
        limit_sup = limit_inf + self.max_results_x_page
#        query = """ select  eventlog.id,eventlog.createdate,eventlog.properties,eventlog.portalname,eventlog.userid from eventlog
#union
#select auth_event.id, auth_event.time_stamp,auth_event.description, auth_event.client_ip,auth_event.user_id  from auth_event order by auth_event.time_stamp desc  limit %s,%s
#        """ % (limit_inf, limit_sup)

        recs = db(db.eventlog).select(orderby=~db.eventlog.id,
                                      limitby=(limit_inf, limit_sup))
        recordscount1 = db(db.eventlog.id > 0).count()
#        recordscount2 = db(db.auth_event.id > 0).count()
        self.recordscount = recordscount1 #+ recordscount2
        '''Para evitar que se pueda venir con un pagid que no existe,
        como 34543, si no existe ese num. de pagina generamos un error '''
        maxpagid = self.recordscount / self.max_results_x_page + 1
        if pag > maxpagid:
            raise HTTP(404)

        if len(recs) > 0:
            rows = [THEAD(TR(TH(T("Date")),
                             TH(T("User name")),
                             TH(T("Event type")),
                             TH(T("Properties")),
                             )
                          )
                    ]
            xtbody = TBODY()
            for r in recs:
                idrec = r.id
                createdate = r.createdate
                typekeyname = ""
                properties = r.properties
                #clientip = r[3]
                userid = r.userid
                username = T("Anonymous")
                if userid != None:
                    if settings.use_mail_as_username:
                        objuser = db.auth_user[userid]
                        if objuser != None:
                            username = db.auth_user[userid].email
                    else:
                        username = db.auth_user[userid].username

                event = db.eventlog[idrec]
                idtypeevent = event.typekey

                if idtypeevent > 0:
                    eventtype = db.eventtypes[idtypeevent]
                    typekeyx = eventtype.friendlyname

                #.success     Indicates a successful or positive action.
                #.error     Indicates a dangerous or potentially negative action.
                #.warning     Indicates a warning that might need attention.
                #.info     Used as an alternative to the default styles.

                cssclass = ""

                if eventtype.cssclass == "AdminAlert":
                    cssclass = "warning"
                elif eventtype.cssclass == "GeneralAdminOperation":
                    cssclass = "success"
                elif eventtype.cssclass == "Exception":
                    cssclass = "error"
                elif eventtype.cssclass == "HostAlert":
                    cssclass = "warning"
                elif eventtype.cssclass == "OperationFailure":
                    cssclass = "warning"
                elif eventtype.cssclass == "OperationSuccess":
                    cssclass = "success"
                elif eventtype.cssclass == "ItemCreated":
                    cssclass = "info"
                elif eventtype.cssclass == "ItemDeleted":
                    cssclass = "warning"
                elif eventtype.cssclass == "ItemUpdated":
                    cssclass = "success"

                xobject = TR(TD(createdate),
                             TD(username),
                             TD(typekeyx),
                             TD(self.clean_resume_log(properties)[0:60],
                                _width="35%")
                                , _class=cssclass, _style="cursor:pointer;", _onclick="ShowSubTable(this)")
                #http://jsfiddle.net/BuyPN/ pure javascript collapse
                xobjectcollapse = TR(TD(P(XML(properties)), _colspan=4,),_style="display: none;")
                xtbody.append(xobject)
                xtbody.append(xobjectcollapse)

            rows.append(xtbody)
            xtable = TABLE(*rows, _border="0", _align="left", _class="table table-hover table-condensed table-striped table-bordered")
            result = xtable
            result += self.render_pagination(controller="admin", function="eventlog")
        return result

    def clean_resume_log(self, properties):
        resprop = properties
        tmpresprop = resprop.replace("<p>", " ")
        tmpresprop = tmpresprop.replace("<strong>", "")
        tmpresprop = tmpresprop.replace("</strong>", "")
        tmpresprop = tmpresprop.replace("</p>", "")
        tmpresprop = tmpresprop.replace("<br />", " ")
        return XML(tmpresprop)

    def eventlog(self, logtypekey, varlocals={}, logvars=[]):
        settings = self.settings
        db = self.db
        auth = self.auth
        T = self.T
        request = current.request
        if auth.user_id != None:
            if settings.use_mail_as_username:
                username = auth.user.email
            else:
                username = auth.user.username
        else:
            username = T("Anonymous")

        if logtypekey == "LOGOUT_SUCCESS":
            if db(db.eventtypes.logtypekey=="LOGOUT_SUCCESS").count() == 0:
                idlogtypekey = db.eventtypes.insert(logtypekey="LOGOUT_SUCCESS",
                                                  friendlyname="Logout Success",
                                                  cssclass="OperationSuccess"
                                                  )
                db.eventlogconfig.insert(logtypekey=idlogtypekey,
                                         loggingisactive=True,
                                         keepmostrecent=10,
                                         )
                #db.commit()

        eventtype = db(db.eventtypes.logtypekey == logtypekey).select(
                                                  db.eventtypes.friendlyname,
                                                  db.eventtypes.id).first()

        eventlogconfig = db(db.eventlogconfig.logtypekey == eventtype.id).select().first()

        if eventlogconfig.loggingisactive:
            if eventlogconfig.keepmostrecent > 0:
                currentcount = db(db.eventlog.typekey == eventtype.id).count()
                if currentcount >= eventlogconfig.keepmostrecent:
                    idlastevent = db(db.eventlog.typekey == eventtype.id).select(orderby=db.eventlog.createdate).first().id
                    db(db.eventlog.id == idlastevent).delete()

            general_properties = [('IP',request.env.remote_addr),
                  ('Time',db_pynuke.PyNuke.Utils().localized_datetimenow())]
            especific_properties = logvars
            errproperties = []
            if logtypekey=="PAGE_LOAD_EXCEPTION":
                errproperties = [('Pynuke', settings.shortcurrentversion),
                                 ('URL IN', varlocals['url_in']),
                                 ('Referrer', request.env.http_referer),
                                 ('User agent', request.env.http_user_agent),
                                 ]
            elif logtypekey=="PAGE_UPDATED":
                errproperties = [('Page id', varlocals['id_page']),
                                 ('Page name', varlocals['reqvars']['name']),
                                 ]

            properties = general_properties + errproperties + especific_properties

            db.eventlog.insert(userid=auth.user_id or None,
                       username=username or None,
                       typekey=eventtype.id,
                               properties=self.prepare_properties(properties)
                                )
            db.commit()
        return

    def prepare_properties(self, properties):
        formatted_properties = None
        for p in properties:
            if formatted_properties is None:
                formatted_properties = STRONG(p[0]) + ": " + p[1] + BR()
            else:
                formatted_properties += STRONG(p[0]) + ": " + p[1] + BR()

        return formatted_properties

    def get_eventtype_id_from_key(self,logtypekey):
        db = self.db
        query = db.eventtypes.logtypekey == logtypekey
        event = db(query).select().first()
        return event.id

    def get_active_eventtypes(self):
        db = self.db
        xjoin = [db.eventtypes.on(db.eventlogconfig.logtypekey==db.eventtypes.id)]
        activeevents = db(db.eventlogconfig.loggingisactive == True).select(db.eventtypes.id,db.eventtypes.friendlyname, 
                                                                            join=xjoin)
        result = {}
        for ae in activeevents:
            typeeventid = str(ae['id'])
            result[typeeventid] = ae['friendlyname']
        return result

    def form_eventlog(self):
        T = self.T
        dict_types = self.get_active_eventtypes()
        formlog = SQLFORM.factory(Field('eventtype', 'string',
                                        label=T('Event type'),
                                        requires=IS_IN_SET(dict_types)
                                ))

        return formlog
    