import Config
import web
import cgi
import Block
import os
import Cheetah.Template
import exceptions
import traceback
import sys
import time
import rfc822
import User
import re

def skinfile(file):
    return os.path.join(Config.skin, file)

class Renderable:
    def render(self, format):
        self.prerender(format)
	import RenderUtils
	templatename = skinfile(self.templateName() + '.' + format)
        extra = web.storage({
            'Config': Config,
            'ctx': web.ctx,
            'skinfile': skinfile,
            })
	return Cheetah.Template.Template(file = templatename,
					 searchList = (self, RenderUtils, extra))

    def prerender(self, format):
        pass

    def notify_parent(self, newparent):
        pass

    def anchor(self):
        return str(self.uuid())

    def uuid(self):
        try:
            return self.uuid
        except exceptions.AttributeError:
            import uuid
            self.uuid = uuid.uuid4()
            return self.uuid

class Paragraph(Renderable):
    def __init__(self, blockPara):
	import Inline
	self.fragments = []
	Inline.parse(blockPara.as_string(), self.fragments)

    def templateName(self):
	return 'pyle_paragraph'

class ListItem(Paragraph):
    def templateName(self):
	return 'pyle_listitem'

class Container(Renderable):
    def __init__(self, klass = ''):
	self.klass = klass
	self.container_items = []

    def addItem(self, item):
	self.container_items.append(item)
        item.notify_parent(self)

    def templateName(self):
	return 'pyle_container'

class List(Container):
    def __init__(self, is_ordered):
        Container.__init__(self)
	self.is_ordered = is_ordered

    def templateName(self):
	return 'pyle_list'

class Section(Container):
    def __init__(self, rank, title):
	Container.__init__(self)
	self.rank = rank
        self.tocpath = []
        self.subsectioncount = 0
	self.title = title

    def subsections(self):
        return [x for x in self.container_items if isinstance(x, Section)]

    def notify_parent(self, newparent):
        self.tocpath = newparent.alloc_toc_entry()

    def alloc_toc_entry(self):
        self.subsectioncount = self.subsectioncount + 1
        entry = self.tocpath[:]
        entry.append(self.subsectioncount)
        return entry

    def anchor(self):
        return 'section_' + '_'.join([str(part) for part in self.tocpath])

    def templateName(self):
	return 'pyle_section'

class Separator(Renderable):
    def templateName(self):
	return 'pyle_separator'

def find_plugin(category, name, entrypoint):
    try:
	mod = __import__(category + '.' + name)
	if hasattr(mod, name):
	    mod = getattr(mod, name)
	    if hasattr(mod, entrypoint):
		return (None, getattr(mod, entrypoint))
	    else:
		return ('Plugin ' + category + '.' + name + \
			' missing entrypoint ' + entrypoint, None)
	else:
	    return ('Plugin ' + category + '.' + name + \
		    ' did not load correctly', None)
    except exceptions.ImportError:
	return ('Could not find plugin ' + category + '.' + name, None)
    except:
	return ('Error loading plugin ' + category + '.' + name + ':\n<tt>' +
		cgi.escape(''.join(traceback.format_exception(*sys.exc_info()))) +
		'</tt>', None)

class PyleBlockParser(Block.BasicWikiMarkup):
    def __init__(self, page):
	Block.BasicWikiMarkup.__init__(self, self)
	self.page = page
	self.accumulator = page
	self.stack = []

    def current_rank(self):
	if isinstance(self.accumulator, Section):
	    return self.accumulator.rank
	else:
	    return 0

    def push_acc(self, acc):
	self.accumulator.addItem(acc)
	self.stack.append(self.accumulator)
	self.accumulator = acc
	return acc

    def add(self, item):
	self.accumulator.addItem(item)

    def pop_acc(self):
	self.accumulator = self.stack.pop()

    def push_visit_pop(self, container, kids):
	self.push_acc(container)
	self.visit(kids)
	self.pop_acc()

    def begin_list(self, is_ordered):
	self.push_acc(List(is_ordered))

    def visit_item(self, para):
	self.add(ListItem(para))

    def end_list(self, is_ordered):
	self.pop_acc()

    def visit_section(self, rank, titleline, doc):
	while self.current_rank() >= rank:
	    self.pop_acc()
#	while self.current_rank() < rank - 1:
#	    self.push_acc(Section(self.current_rank() + 1, None))
	self.push_acc(Section(rank, titleline))

    def visit_separator(self):
	self.add(Separator())

    def visit_sublanguage(self, commandline, doc):
	commandparts = commandline.split(' ', 1)
	command = commandparts[0]
	if len(commandparts) > 1:
	    args = commandparts[1]
	else:
	    args = ''
	(err, plugin) = find_plugin('sublanguages', command, 'SublanguageHandler')
	if plugin:
	    plugin(args, doc, self)
	else:
	    import Inline
	    self.add(Inline.MarkupError(True, 'missingsublanguage', err))

    def visit_normal(self, para):
	self.add(Paragraph(para))

class DefaultPageContent(Renderable):
    def __init__(self, title):
        self.title = title

    def templateName(self):
        return 'default_page_content'

class PageChangeEmail(Renderable):
    def __init__(self, page):
        self.page = page

    def templateName(self):
        return 'page_change'

def send_emails(users, message_including_headers):
    if users:
        import smtplib
        s = smtplib.SMTP(Config.smtp_hostname, Config.smtp_portnumber)
        s.sendmail(Config.daemon_email_address, [u.email for u in users],
                   normalize_newlines(message_including_headers).replace('\n', '\r\n'))
        s.quit()

def normalize_newlines(s):
    s = s.replace('\r\n', '\n')
    s = s.replace('\r', '\n')
    return s

def log_change(d, when = None):
    if not when:
        when = time.time()
    oldchanges = web.ctx.cache.getpickle('changes', 'changelog', [])
    d['when'] = when
    oldchanges.append(d)
    web.ctx.cache.setpickle('changes', 'changelog', oldchanges)

class Attachment:
    def __init__(self, pagetitle, name, version):
        self.pagetitle = pagetitle
        self.name = name
        self.version = version
        self._load()

    def _key(self, kind):
        return self.pagetitle + '.attach' + kind + '.' + self.name

    def _load(self):
        props = web.ctx.attachments.getpickle(self._key('meta'), None, {}, self.version)
        self.mimetype = props.get('mimetype', 'application/octet-stream')
        self.creator = props.get('creator', '')
        self.bodylen = props.get('bodylen', None)
        self._body = None

    def exists(self):
        return web.ctx.attachments.has_key(self._key('meta'))

    def save(self):
        props = {
            'mimetype': self.mimetype,
            'creator': self.creator,
            'bodylen': self.bodylen,
            }
        web.ctx.attachments.setpickle(self._key('meta'), None, props)
        web.ctx.attachments.setitem(self._key('file'), None, self.body(), is_binary = True)

    def delete(self):
        web.ctx.attachments.delitem(self._key('meta'), None)
        web.ctx.attachments.delitem(self._key('file'), None)

    def history(self):
        entries = web.ctx.attachments.gethistory(self._key('file'), None)
        for entry in entries:
            meta = web.ctx.attachments.getpickle(self._key('meta'), None, {}, entry.version_id)
            entry.who = meta.get('creator', '') or Config.anonymous_user
        return entries

    def body(self):
        if not self._body:
            self._body = web.ctx.attachments.getitem(self._key('file'), None, '', self.version,
                                                     is_binary = True)
            self.bodylen = len(self._body)
        return self._body

    def setbody(self, newbody):
        self._body = newbody
        self.bodylen = len(self._body)

    def url(self):
        return web.ctx.home + '/' + self.pagetitle + '/attach/' + self.name

class Page(Section):
    def __init__(self, title, version = None):
        Section.__init__(self, 0, title)
	self.store = web.ctx.store
	self.cache = web.ctx.cache
        self.version = version
        self.notify_required = False
	self.load_()

    def load_(self):
        self.meta = self.store.getpickle(self.title, 'meta', {}, self.version)
        self._text = None
        self.container_items = None
        self._mediacache = None

    def text(self):
        if self._text is None:
            self._text = self.store.getitem(self.title, 'txt', None, self.version)
            if self._text is None:
                self._text = str(DefaultPageContent(self.title).render('txt'))
        return self._text

    def newest_stored_version(self):
        return self.store.current_version_id(self.title, 'txt')

    def history(self):
        entries = self.store.gethistory(self.title, 'txt')
        for entry in entries:
            meta = self.store.getpickle(self.title, 'meta', {}, entry.version_id)
            entry.who = meta.get('Modifier', '') or Config.anonymous_user
        return entries

    def friendly_version(self):
        if self.version:
            e = self.store.gethistoryentry(self.title, 'txt', self.version)
            if e: return e.friendly_id
        return self.version

    def exists(self):
        return self.store.has_key(self.title)

    def getmeta(self, name, defaultValue = ''):
        return self.meta.get(name, defaultValue)

    def setmeta(self, name, value):
        self.meta[name] = value

    def getmetadate(self, name, defaultValue = None):
        s = self.getmeta(name, None)
        if s:
            return time.mktime(rfc822.parsedate(s))
        else:
            return defaultValue

    def setmetadate(self, name, t):
        self.setmeta(name, rfc822.formatdate(t))

    def _preprocess(self, s):
        return normalize_newlines(s)

    def setText(self, newtext):
        newtext = self._preprocess(newtext)
        self.notify_required = self.notify_required or (self._text != newtext)
	self._text = newtext
        self.reset_cache()

    def prerender(self, format):
        if not self.version:
            self.container_items = self.cache.getpickle(self.title, 'tree', None)
            self._mediacache = self.cache.getpickle(self.title, 'mediacache', {})
            if self.container_items is not None:
                return

        self.container_items = []
        self._mediacache = {}

        web.ctx.active_page = self
	doc = Block.parsestring(self.text())
	PyleBlockParser(self).visit(doc.children)
        web.ctx.active_page = None

        if not self.version:
            self.cache.setpickle(self.title, 'tree', self.container_items)
            self.cache.setpickle(self.title, 'mediacache', self._mediacache)

    def mediacache(self):
        if self._mediacache is None:
            self.prerender('html')
        return self._mediacache

    def save(self, user):
        savetime = time.time()
        self.setmetadate('Date', savetime)
        self.setmeta('Modifier', user.getusername())
        self.inner_save()
        self.log_change('saved', user, savetime)
        self.notify_subscribers(user)

    def inner_save(self):
        self.store.setpickle(self.title, 'meta', self.meta)
	self.store.setitem(self.title, 'txt', self._text)

    def reset_cache(self):
        self.cache.delitem(self.title, 'tree')
        self.cache.delitem(self.title, 'mediacache')

    def delete(self, user):
        self.reset_cache()
        self.store.delitem(self.title, 'meta')
        self.store.delitem(self.title, 'txt')
        for name in self.attachment_names():
            Attachment(self.title, name, None).delete()
        self.log_change('deleted', user)

    def attachment_names(self):
        prefix = self.title + '.attachmeta.'
        prefixlen = len(prefix)
        return [f[prefixlen:] for f in web.ctx.attachments.keys_glob(prefix + '*')]

    def get_attachments(self):
        return [Attachment(self.title, name, None) for name in self.attachment_names()]

    def get_attachment(self, name, version):
        return Attachment(self.title, name, version)

    def backlinks(self):
        result = []
        r = re.compile(r'\b' + re.escape(self.title) + r'\b')
        for otherpage in self.store.keys():
            othertext = self.store.getitem(otherpage, 'txt', '')
            if r.search(othertext):
                result.append(otherpage)
        return result

    def subscribers(self):
        result = []
        for username in Config.user_data_store.keys():
            user = User.User(username)
            if user.is_subscribed_to(self.title):
                result.append(user)
        return result

    def notify_subscribers(self, currentuser):
        if self.notify_required and Config.smtp_hostname:
            users = [s for s in self.subscribers() if s != currentuser]
            if users:
                notification = str(PageChangeEmail(self).render('email'))
                send_emails(users, notification)
            self.notify_required = False

    def log_change(self, event, user, when = None):
        log_change({'page': self.title,
                    'what': event,
                    'who': user.username}, when)

    def readable_for(self, user):
        return not user.is_anonymous() or Config.allow_anonymous_view

    def writable_for(self, user):
        return not user.is_anonymous() or Config.allow_anonymous_edit

    def templateName(self):
	return 'pyle_page'

app_initialised = 0
def init_pyle():
    global app_initialised
    if not app_initialised:
        Config.user_data_store.set_basic_kind('user')
        Config.attachment_store.set_basic_kind(None)
        app_initialised = 1
