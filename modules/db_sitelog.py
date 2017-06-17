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

class SiteLog(object):

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
        db.define_table('sitelog',
            Field('logdatetime','datetime',default=datetime.datetime.now(), 
                  required=True, writable=False,),
            Field('userid', db.auth_user, label=T('User'), default=auth.user_id),
            Field('referrer', label=T('Referrer'), requires=IS_URL()),
            Field('url', label=T('URL'), requires=IS_URL()),
            Field('useragent', label=T('User agent'),),
            Field('userhostaddress', label=T('User host address'),
                  requires=IS_IPV4()),
            Field('userhostname', label=T('User Host Name'),),
            Field('pageid',db.pages, label=T('Page')),
            format='%(url)s',
            plural='Logs',
            singular='Log'
                    )
        return

    def grid_log(self, reporttype, startdate, enddate, pag=1):
        """ Grid Log """
        db = self.db
        T = self.T
        result = ""
        self.currentpage = pag  # Id de pag a ver del modulo blog (paginador)
        self.mindate = startdate
        self.maxdate = enddate
        self.max_results_x_page = 15
        self.reporttype = reporttype
        query = (db.sitelog.id > 0)
        query = query & (db.sitelog.logdatetime >= startdate) & (db.sitelog.logdatetime <= (enddate))

        if reporttype == "detailed":
#            query = (db.sitelog.id > 0)
#            query = query & (db.sitelog.logdatetime >= startdate) & (db.sitelog.logdatetime <= (enddate))
            recordscount = db(query).count()
            self.recordscount = recordscount
            orderby = ~db.sitelog.id
            limit_inf = (self.max_results_x_page * pag) - self.max_results_x_page
            limit_sup = limit_inf + self.max_results_x_page
            recs = db(query).select(limitby=(limit_inf, limit_sup),
                                   orderby=orderby)
            if len(recs) > 0:
                rows = [THEAD(TR(TH(T("Date time")),
                                 TH(T("User name")),
                                 TH(T("Referrer")),
                                 TH(T("URL")),
                                 TH(T("User agent")),
                                 TH(T("User host address")),
                                 TH(T("Page name")),
                                 )
                              )
                        ]
                xtbody = TBODY()
                for r in recs:
                    if r.userid != None:
                        usernamex = db.auth_user[r.userid].first_name + ' ' + db.auth_user[r.userid].last_name
                    else:
                        usernamex = T("Anonymous")
                    xobject = TR(TD(r.logdatetime),
                                 TD(usernamex),
                                 TD(r.referrer),
                                 TD(r.url),
                                 TD(r.useragent),
                                 TD(r.userhostaddress),
                                 TD(db.pages[r.pageid].name))
                    xtbody.append(xobject)
                rows.append(xtbody)
                xtable = TABLE(*rows, _border="0", _align="left", _class="table table-hover table-condensed table-striped table-bordered")
                result = xtable
                result += self.render_pagination()
        elif reporttype == "referrals":
            count = db.sitelog.id.count()
            query = query & (db.sitelog.referrer != None) & (db.sitelog.referrer != "")
            recs = db(query).select(db.sitelog.referrer, count, groupby = db.sitelog.referrer, orderby=~count)
            if len(recs) > 0:
                rows = [THEAD(TR(TH(T("Referrer")),
                     TH(T("Hits")),
                     )
                  )
            ]
                xtbody = TBODY()
                for r in recs:
                    xobject = TR(TD(r.sitelog.referrer),
                                 TD(r['COUNT(sitelog.id)']))
                    xtbody.append(xobject)

                rows.append(xtbody)

                xtable = TABLE(*rows, _border="0", _align="left", _class="table table-hover table-condensed table-striped table-bordered")
                result = xtable

        elif reporttype == "popularity":
            count = db.sitelog.id.count()
            recs = db(query).select(db.sitelog.url,db.sitelog.pageid, count, groupby = db.sitelog.pageid, orderby=~count)
            if len(recs) > 0:
                rows = [THEAD(TR(TH(T("URL")),
                     TH(T("Page id")),
                     TH(T("Page name")),
                     TH(T("Views")),
                     )
                  )
            ]
                xtbody = TBODY()
                for r in recs:
                    xobject = TR(TD(r.sitelog.url),
                                 TD(r.sitelog.pageid),
                                 TD(db.pages[r.sitelog.pageid].name),
                                 TD(r['COUNT(sitelog.id)']))
                    xtbody.append(xobject)

                rows.append(xtbody)

                xtable = TABLE(*rows, _border="0", _align="left", _class="table table-hover table-condensed table-striped table-bordered")
                result = xtable

        elif reporttype == "byday":
            count = db.sitelog.id.count()
            recs = db(query).select(db.sitelog.logdatetime, count, groupby = db.sitelog.logdatetime.day(), orderby=~count)
            if len(recs) > 0:
                rows = [THEAD(TR(TH(T("Date")),
                     TH(T("Page Views")),
                     )
                  )
            ]
                xtbody = TBODY()
                for r in recs:
                    xobject = TR(TD(r.sitelog.logdatetime.strftime(str(T("%Y-%m-%d")))),
                                 TD(r['COUNT(sitelog.id)']))
                    xtbody.append(xobject)

                rows.append(xtbody)

                xtable = TABLE(*rows, _border="0", _align="left", _class="table table-hover table-condensed table-striped table-bordered")
                result = xtable

        elif reporttype == "byhour":
            count = db.sitelog.id.count()
            recs = db(query).select(db.sitelog.logdatetime, count, groupby = db.sitelog.logdatetime.hour(), orderby=~count)
            if len(recs) > 0:
                rows = [THEAD(TR(TH(T("Hour")),
                     TH(T("Page Views")),
                     )
                  )
            ]
                xtbody = TBODY()
                for r in recs:
                    xobject = TR(TD(r.sitelog.logdatetime.strftime(str(T("%Y-%m-%d %H")))),
                                 TD(r['COUNT(sitelog.id)']))
                    xtbody.append(xobject)

                rows.append(xtbody)

                xtable = TABLE(*rows, _border="0", _align="left", _class="table table-hover table-condensed table-striped table-bordered")
                result = xtable

        elif reporttype == "bymonth":
            count = db.sitelog.id.count()
            recs = db(query).select(db.sitelog.logdatetime, count, groupby = db.sitelog.logdatetime.month(), orderby=~count)
            if len(recs) > 0:
                rows = [THEAD(TR(TH(T("Month")),
                     TH(T("Page Views")),
                     )
                  )
            ]
                xtbody = TBODY()
                for r in recs:
                    xobject = TR(TD(r.sitelog.logdatetime.strftime(str(T("%m")))),
                                 TD(r['COUNT(sitelog.id)']))
                    xtbody.append(xobject)

                rows.append(xtbody)

                xtable = TABLE(*rows, _border="0", _align="left", _class="table table-hover table-condensed table-striped table-bordered")
                result = xtable


        return result

    def form_getlog(self, startdate, enddate, reporttype=""):
        """ form Log """
        T = self.T
        semana = datetime.timedelta(days=7)
        dia = datetime.timedelta(days=1)
        if startdate is None:
            date_startdate = datetime.date.today() - semana
        elif isinstance(startdate, basestring): 
            date_startdate = db_pynuke.PyNuke.Utils().localized_str_to_date(startdate)

        formlog = SQLFORM.factory(Field('startdate', 'date',
                            label=T('Start date'),
                            default=date_startdate,
                            requires=IS_DATE(format=T('%Y-%m-%d')),
                            required=True
                            ),
                                  Field('enddate',
                                        'date',
                                        label=T('End date'),
                                        default=(datetime.date.today() + dia),
                                        required=True,
                                        requires=IS_DATE(format=T('%Y-%m-%d'))
                                        ),
                                  Field('reporttype',
                                        'string',
                                        label=T('Report type'),
                                        default = reporttype,
                                        requires=IS_IN_SET([('referrals',T('Referrals')),
                                ('detailed',T('Detailed Site Log')),
                                ('popularity',T('Page Popularity')),
                                ('byday',T('Page Views By Day')),
                                ('byhour',T('Page Views By Hour')),
                                ('bymonth',T('Page Views By Month')),
                                                            ])
                                        )
                                  )
        return formlog

    def render_pagination(self, controller='admin', function='sitelog'):
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

    def render_pages(self, controller='default', function='sitelog'):
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
                last_page = first_page + self.max_display_pages

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
        rq_vars['startdate'] = self.mindate
        rq_vars['enddate'] = self.maxdate
        rq_vars['reporttype'] = self.reporttype

        result = URL(controller, function, args=[self.currentpageslug], \
                                                vars=rq_vars)
        return result

