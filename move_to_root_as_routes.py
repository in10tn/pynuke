# encoding: utf-8
'''
https://groups.google.com/forum/?fromgroups=#!topic/web2py/uQ-wjGwTCqQ
https://snipt.net/rochacbruno/routesconf/
https://snipt.net/rochacbruno/routespy/
'''

logging = 'debug'
default_application = 'init'    # ordinarily set in base routes.py
default_controller = 'default'  # ordinarily set in app-specific routes.py
default_function = 'page'      # ordinarily set in app-specific routes.py

# Así evitamos distribuir el routes.conf, creelo si es necesario...
config = "127.0.0.1 /init/default"
##try:
##    config = open('routes.conf', 'r').read()
##except:
##    config = ''


def auto_in(apps):
    routes = [
        ('/static/$anything', '/init/static/$anything'),
        ('/init/static/$anything', '/init/static/$anything'),
        ('/robots.txt', '/init/static/robots.txt'),
        ('/favicon.ico', '/init/static/favicon.ico'),
        ('/admin/$anything', '/admin/$anything'),
        ('/sitemap.xml', '/init/default/sitemap.xml'),
        ('/page/$anything', '/init/default/page/$anything'),
        ('/user$anything', '/init/default/user$anything'),
        ('/init/appadmin$anything', '/init/appadmin$anything'),
        ('/init/admin/$anything', '/init/admin/$anything'),
        ('/msettings$anything', '/init/default/msettings$anything'),
        ('/init$anything', '/init$anything'),
        ('/init/controlpanel$anything', '/init/controlpanel$anything'),
        ('/download/$anything', '/init/default/download/$anything'),
        ('/init/plugin$anything', '/init/plugin$anything'),
        ('/init/default/current_version$anything', '/init/default/current_version/$anything'),
        ('/$anything', '/init/default/page/$anything'),
        ]
    for domain, path in [x.strip().split() for x in apps.split('\n')
                        if x.strip() and not x.strip().startswith('#')]:
        if not path.startswith('/'):
            path = '/' + path
        if path.endswith('/'):
            path = path[:-1]
        app = path.split('/')[1]
        routes += [
           ('.*:https?://(.*\.)?%s:$method /' % domain, '%s' % path),
            ('.*:https?://(.*\.)?%s:$method /static/$anything' % domain,
                                            '/%s/static/$anything' % app),
            ('.*:https?://(.*\.)?%s:$method /$anything' % domain,
                                            '%s/$anything' % path),
            ('.*:https?://(.*\.)?%s:$method /page/$anything' % domain,
                                            '/%s/default/page$anything' % app)
            ]
    return routes


def auto_out(apps):
    routes = []
    for a, b in [x.strip().split() for x in apps.split('\n')
                if x.strip() and not x.strip().startswith('#')]:
        if not b.startswith('/'):
            b = '/' + b
        if b.endswith('/'):
            b = b[:-1]
        app = b.split('/')[1]
        routes += [
            ('/%s/static/$anything' % app, '/static/$anything'),
            ('/%s/init/appadmin/$anything' % app, '/appadmin/$anything'),
            ('/%s/default/page/$anything' % app, '/$anything'),
            ('/%s/default/current_version' % app, '/current_version'),
            ('%s/$anything' % b, '/$anything'),
            ]

    return routes

routes_in = auto_in(config)
routes_out = auto_out(config)
routes_onerror = [
                  ('init/*', '/init/default/handle_error')
                  ]