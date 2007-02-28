#!/usr/bin/env python2.5
# -*- python -*-
from __future__ import generators
import web
import Core
import RenderUtils
import Config
import base64
import md5
import pickle

urls = (
    '/([^/]*)', 'read',
    '/([^/]*)/edit', 'edit',
    '/([^/]*)/delete', 'delete',
    '/([^/]*)/mediacache/(.*)', 'mediacache',
    '/([^/]*)/static/style.css', 'style',
    )

def mac(str):
    return md5.new(str + Config.session_passphrase).hexdigest()

def newSession():
    return {
        'user': None,
        }

class Action(Core.Renderable):
    def __init__(self):
        self.loadCookies_()
        self.recoverSession_()
        self.input = web.input(**self.defaultInputs())
        self.ctx = web.ctx
        self.ctx.store = Core.FileStore(Config.filestore_dir)
        self.ctx.cache = Core.FileStore(Config.cache_dir)

    def defaultInputs(self):
        return {
            'format': 'html'
            }

    def loadCookies_(self):
        self.cookies = web.cookies(pyle_session = '')

    def recoverSession_(self):
        self.session = None
        try:
            if self.cookies.pyle_session:
                (cookiehash, sessionpickle64) = self.cookies.pyle_session.split('::', 1)
                sessionpickle = base64.decodestring(sessionpickle64)
                computedhash = mac(sessionpickle)
                if computedhash == cookiehash:
                    self.session = pickle.loads(sessionpickle)
        except:
            pass
        if not self.session:
            self.session = newSession()

    def render(self, format):
        self.saveSession_()
        self.ctx.store.commit()
        return Core.Renderable.render(self, format)

    def saveSession_(self):
        sessionpickle = pickle.dumps(self.session)
        computedhash = mac(sessionpickle)
        web.setcookie('pyle_session',
                      computedhash + '::' + base64.encodestring(sessionpickle).strip())

class PageAction(Action):
    def init_page(self, pagename):
        if not pagename:
            pagename = Config.frontpage
        self.pagename = pagename
        self.page = Core.Page(self.ctx.store, self.ctx.cache, pagename)

    def GET(self, pagename):
        self.init_page(pagename)
        if self.input.format == 'html':
            web.header('Content-Type','text/html; charset=utf-8', unique=True)
        web.output(self.render(self.input.format))

class read(PageAction):
    def templateName(self):
        return 'action_read'

class mediacache(PageAction):
    def GET(self, pagename, cachepath):
        self.init_page(pagename)
        (mimetype, bytes) = self.page.mediacache[cachepath]
        web.header('Content-Type', mimetype)
        web.output(bytes)

class edit(PageAction):
    def POST(self, pagename):
        self.init_page(pagename)
        self.page.setText(self.input.body)
        self.page.save()
	web.seeother(RenderUtils.InternalLink(self.page.title).url())

    def templateName(self):
        return 'action_edit'

class style:
    def GET(self, pagename):
	web.header('Content-Type', 'text/css')
	f = open('static/style.css', 'rb')
	web.output(f.read())
	f.close()

if __name__ == '__main__': web.run(urls, globals())
