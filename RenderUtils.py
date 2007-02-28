import web
import Core
import cgi
import urllib

class InternalLink(Core.Renderable):
    def __init__(self, pagename, service = 'read', vistext = None):
	if not vistext:
	    vistext = pagename

	self.pageexists = web.ctx.store.has_key(pagename)
	if (not service or service == 'read') and not self.pageexists:
	    service = 'edit'
	self.pagename = pagename
	self.service = service
	self.vistext = vistext

    def url(self):
	if self.service and self.service != 'read':
	    servicePart = '/' + self.service
	else:
	    servicePart = ''
	return web.ctx.home + '/' + self.pagename + servicePart

    def templateName(self):
	return 'pyle_internallink'

def internal_link(pagename, service = 'read', vistext = None, format = 'html'):
    return InternalLink(pagename, service, vistext).render(format)

class MediaCacheEntry(InternalLink):
    def __init__(self, pagename, path, vistext, template):
	InternalLink.__init__(self, pagename, 'mediacache/' + path, vistext)
	self.path = path
	self.template = template

    def templateName(self):
	return self.template

def media_cache(renderer, cachepath, vistext, template, mimetype, bytes):
    renderer.page.mediacache[cachepath] = (mimetype, bytes)
    return MediaCacheEntry(renderer.page.title, cachepath, vistext, template)

escape = cgi.escape

def aescape(s):
    s = escape(s)
    s = s.replace('"', '&quot;')
    s = s.replace("'", '&apos;')
    return s

def pquote(s):
    return urllib.quote_plus(s, ':/')

def quote(s):
    return urllib.quote(s, ':/')
