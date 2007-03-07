#!/usr/bin/env python2.5
# -*- python -*-
from __future__ import generators
import web
import Core
import Store
import RenderUtils
import Config
import base64
import pickle
import User
import hmac
import urllib
import os
import re

urls = (
    '/([^/]*)', 'read',
    '/([^/]*)/print', 'printmode',
    '/([^/]*)/history', 'history',
    '/([^/]*)/diff', 'diff',
    '/([^/]*)/backlinks', 'backlinks',
    '/([^/]*)/subscribe', 'subscribe',
    '/([^/]*)/edit', 'edit',
    '/([^/]*)/save', 'save',
    '/([^/]*)/delete', 'delete',
    '/([^/]*)/mediacache/(.*)', 'mediacache',
    '/([^/]*)/attach/(.*)', 'getattach',
    '/([^/]*)/attach', 'editattach',
    '/([^/]*)/updateattach', 'updateattach',
    '/([^/]*)/delattach', 'delattach',
    '/_/static/([^/]+)', 'static',
    '/_/settings', 'settings',
    '/_/follow_backlink', 'follow_backlink',
    '/_/logout', 'logout',
    '/_/search', 'search',
    )

def mac(str):
    return hmac.new(Config.session_passphrase, str).hexdigest()

def newSession():
    return web.storage({
        'username': None,
        })

class LoginPage(Core.Renderable):
    def __init__(self, action, login_failed):
        self.action = action
        self.login_failed = login_failed

    def templateName(self):
        return 'action_loginpage'

class Action(Core.Renderable):
    def __init__(self):
        self.loadCookies_()
        self.recoverSession_()
        self.input = web.input(**self.defaultInputs())
        self.ctx = web.ctx
        self.ctx.store = Store.Transaction(Config.file_store)
        self.ctx.cache = Store.Transaction(Config.cache_store)
        self.ctx.attachments = Store.Transaction(Config.attachment_store)
        self.ctx.printmode = False
        if Config.use_canonical_base_url:
            self.ctx.home = Config.canonical_base_url

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
        self._user = None

    def user(self):
        if not self._user:
            self._user = User.lookup(self.session.username)
        return self._user

    def ensure_login(self):
        if not self.user().is_anonymous():
            return True

        self._user = None

        login_failed = 0
        if self.input.has_key('Pyle_username'):
            username = self.input.Pyle_username
            password = self.input.Pyle_password
            user = User.lookup(username)
            if Config.user_authenticator.authenticate(user, password):
                self.session.username = username
                self._user = user
                return True
            login_failed = 1

        web.header('Content-Type','text/html; charset=utf-8', unique=True)
        web.output(LoginPage(self, login_failed).render('html'))
        return False

    def ensure_login_if_required(self):
        if self.login_required():
            return self.ensure_login()
        else:
            return True

    def login_required(self):
        return False

    def commit(self):
        self.saveSession_()
        self.ctx.store.commit()
        self.ctx.cache.commit()
        self.ctx.attachments.commit()

    def render(self, format):
        self.commit()
        return Core.Renderable.render(self, format)

    def saveSession_(self):
        sessionpickle = pickle.dumps(self.session)
        computedhash = mac(sessionpickle)
        web.setcookie('pyle_session',
                      computedhash + '::' + base64.encodestring(sessionpickle).strip())

    def GET(self, *args):
        if self.ensure_login_if_required():
            self.handle_request(*args)
            self.commit()

    def POST(self, *args):
        return self.GET(*args)

    def handle_request(self, *args):
        if self.input.format == 'html':
            web.header('Content-Type','text/html; charset=utf-8', unique=True)
        web.output(self.render(self.input.format))

class PageAction(Action):
    def init_page(self, pagename):
        if not hasattr(self, 'page') or not self.page:
            if not pagename:
                pagename = Config.frontpage
            self.pagename = pagename
            if self.input.has_key('version'):
                version = self.input.version
            else:
                version = None
            self.page = Core.Page(pagename, version)

    def login_required(self):
        return not Config.allow_anonymous_view

    def handle_request(self, pagename):
        self.init_page(pagename)
        Action.handle_request(self)

class EditPageAction(PageAction):
    def login_required(self):
        return not Config.allow_anonymous_edit

class read(PageAction):
    def templateName(self):
        return 'action_read'

class printmode(PageAction):
    def prerender(self, format):
        self.ctx.printmode = True

    def templateName(self):
        return 'action_read'

class history(PageAction):
    def templateName(self):
        return 'action_history'

class diff(Action):
    def login_required(self):
        return not Config.allow_anonymous_view

    def handle_request(self, pagename):
        key = pagename + '.txt'
        msgenc = self.ctx.store.message_encoder()
        self.v1 = msgenc.gethistoryentry(key, self.input.v1)
        self.v2 = msgenc.gethistoryentry(key, self.input.v2)
        self.diff = msgenc.diff(key, self.input.v1, self.input.v2)
	self.pagetitle = pagename
        Action.handle_request(self)

    def templateName(self):
        return 'action_diff'

class backlinks(PageAction):
    def prerender(self, format):
        self.backlinks = self.page.backlinks()

    def templateName(self):
        return 'action_backlinks'

class mediacache(PageAction):
    def handle_request(self, pagename, cachepath):
        self.init_page(pagename)
        (mimetype, bytes) = self.page.mediacache()[cachepath]
        web.header('Content-Type', mimetype)
        web.output(bytes)

class subscribe(PageAction):
    def login_required(self):
        return True

    def handle_request(self, pagename):
        self.init_page(pagename)
        self.subscription_status = not self.user().is_subscribed_to(pagename)
        self.user().set_subscription(pagename, self.subscription_status)
        self.user().save_properties()
        PageAction.handle_request(self, pagename)

    def templateName(self):
        return 'action_subscribe'

class edit(EditPageAction):
    def templateName(self):
        return 'action_edit'

class save(EditPageAction):
    def handle_request(self, pagename):
        self.init_page(pagename)
        self.page.setbody(self.input.body)
        self.page.save(self.user())
        web.seeother(RenderUtils.internal_link_url(self.page.title))

class delete(EditPageAction):
    def handle_request(self, pagename):
        if self.input.get('delete_confirmed', ''):
            self.init_page(pagename)
            self.page.delete(self.user())
            web.seeother(RenderUtils.internal_link_url(self.page.title))
        else:
            PageAction.handle_request(self, pagename)

    def templateName(self):
        return 'action_delete'

class getattach(PageAction):
    def handle_request(self, pagename, attachname):
        self.init_page(pagename)
        a = self.page.get_attachment(attachname, self.input.get('version', None))
        web.header('Content-Type', a.mimetype)
        web.header('Content-Length', len(a.body()))
        web.output(a.body())

class editattach(EditPageAction):
    def templateName(self):
        return 'action_editattach'

class updateattach(EditPageAction):
    def handle_request(self, pagename):
        self.init_page(pagename)

        attachname = self.input.name
        content = self.input.content
        if content and not attachname:
            attachname = os.path.basename(web.input(content = {}).content.filename)

        a = self.page.get_attachment(attachname, None)
        a.mimetype = self.input.mimetype
        a.creator = self.user().getusername()
        if content:
            a.setbody(content)
        a.save()
        self.page.reset_cache()
        web.seeother(RenderUtils.internal_link_url(pagename, 'attach'))

class delattach(EditPageAction):
    def handle_request(self, pagename):
        self.attachname = self.input.name
        if self.input.get('delete_confirmed', ''):
            self.init_page(pagename)
            a = self.page.get_attachment(self.attachname, None)
            a.delete()
            self.page.reset_cache()
            web.seeother(RenderUtils.internal_link_url(pagename, 'attach'))
        else:
            PageAction.handle_request(self, pagename)

    def templateName(self):
        return 'action_delattach'

class static:
    def GET(self, filename):
        if filename in ['.', '..', '']:
            web.ctx.status = '403 Forbidden'
        else:
            f = open(os.path.join('static', filename), 'rb')
            web.output(f.read())
            f.close()

class settings(Action):
    def login_required(self):
        return True

    def handle_request(self):
        self.changes_saved = False
        if self.input.has_key('action'):
            if self.input.action == 'save_settings':
                i = web.input(email = self.user().email,
                              unsubscribe = [])
                self.user().email = i.email
                self.user().subscriptions = [s for s in self.user().subscriptions
                                             if s not in i.unsubscribe]
                self.user().save_properties()
                self.changes_saved = True
        Action.handle_request(self)

    def templateName(self):
        return 'action_settings'

class follow_backlink(Action):
    def handle_request(self):
        web.seeother(RenderUtils.internal_link_url(self.input.page))

class logout(Action):
    def handle_request(self):
        self.session.username = None
        self._user = None
        Action.handle_request(self)

    def templateName(self):
        return 'action_logout'

class search(Action):
    def handle_request(self):
        self.keywords = [k for k in self.input.get('q', '').split(' ') if k]
        if self.keywords:
            self.ran_search = True
            self.results = self.run_search()
        else:
            self.ran_search = False
            self.results = []
        Action.handle_request(self)

    def run_search(self):
        regexes = [re.compile(re.escape(k), re.IGNORECASE) for k in self.keywords]
        result = []
        msgenc = self.ctx.store.message_encoder()
        for key in msgenc.keys_glob('*.txt'):
            pagetitle = key[:-4] # chop off '.txt'
            text = msgenc.getbody(key, None)
            if text is not None:
                score = 0
                headerscore = 0
                for r in regexes:
                    headerscore = len(r.findall(pagetitle))
                    score = score + len(r.findall(text)) + headerscore
                if score:
                    result.append((score, bool(headerscore), pagetitle))
        result.sort(None, lambda r: r[0], True)
        return result

    def templateName(self):
        return 'action_search'

if __name__ == '__main__':
    Core.init_pyle()
    web.run(urls, globals())
