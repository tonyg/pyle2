import web
import Core
import cgi
import urllib

class InternalLink(Core.Renderable):
    def __init__(self, pagename, service = 'read', vistext = None, args = {}):
	if not vistext:
	    vistext = pagename

	self.pageexists = web.ctx.store.message_encoder().has_key(pagename + '.txt')
	if (not service or service == 'read') and not self.pageexists:
	    service = 'edit'
	self.pagename = pagename
	self.service = service
	self.vistext = vistext
        self.args = args

    def url(self):
        return internal_link_url(self.pagename, self.service, self.args)

    def templateName(self):
	return 'pyle_internallink'

def internal_link_url(pagename, service = 'read', args = {}):
    if service and service != 'read':
        servicePart = '/' + service
    else:
        servicePart = ''
    queryPart = urllib.urlencode(args)
    if queryPart:
        queryPart = '?' + queryPart
    return web.ctx.home + '/' + pagename + servicePart + queryPart

def internal_link(pagename, service = 'read', vistext = None, format = 'html', args = {}):
    return InternalLink(pagename, service, vistext, args).render(format)

class MediaCacheEntry(InternalLink):
    def __init__(self, pagename, path, vistext, template):
	InternalLink.__init__(self, pagename, 'mediacache/' + path, vistext)
	self.path = path
	self.template = template

    def templateName(self):
	return self.template

def media_cache(renderer, cachepath, vistext, template, mimetype, bytes):
    renderer.page.mediacache()[cachepath] = (mimetype, bytes)
    return MediaCacheEntry(renderer.page.title, cachepath, vistext, template)

escape = cgi.escape

def escapeall(lines):
    return map(escape, lines)

def escapeallpre(lines):
    return ''.join([escape(x).replace('\n', '&nbsp;<br />') for x in lines])

def aescape(s):
    s = escape(s)
    s = s.replace('"', '&quot;')
    s = s.replace("'", '&apos;')
    return s

def pquote(s):
    return urllib.quote_plus(s, ':/')

def quote(s):
    return urllib.quote(s, ':/')
