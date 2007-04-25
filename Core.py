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
import Group
import re
import Store

def skinfile(file):
    p = file
    for dir in Config.skin:
        p = os.path.join(dir, file)
        if os.path.exists(p):
            return p
    # None exist. Return the last in the list for error-reporting purposes.
    return p

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
    if users and Config.smtp_hostname:
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
    oldchanges = web.ctx.cache.getpickle('changes', [])
    d['when'] = when
    oldchanges.append(d)
    web.ctx.cache.setpickle('changes', oldchanges)

class Attachment(Store.Item):
    def __init__(self, pagetitle, name, version):
        Store.Item.__init__(self,
                            web.ctx.attachments,
                            pagetitle + '.attach.' + name,
                            version)
        self.pagetitle = pagetitle
        self.name = name

    default_properties = {
        'mimetype': 'application/octet-stream',
        'author': '',
        'bodylen': '0',
        }

    def body(self):
        if not self._body:
            Store.Item.body(self)
            self.bodylen = str(len(self._body))
        return self._body

    def setbody(self, newbody):
        self._body = newbody
        self.bodylen = str(len(self._body))

    def save(self):
        self.primitive_save()

    def delete(self):
        self.primitive_delete()

    def url(self):
        return web.ctx.home + '/' + self.pagetitle + '/attach/' + self.name

class Page(Section, Store.Item):
    def __init__(self, title, version = None):
        Store.Item.__init__(self, web.ctx.store, title + '.txt', version)
        Section.__init__(self, 0, title)
	self.cache = web.ctx.cache
        self.notify_required = False
        self.container_items = None
        self._mediacache = None
        self._rendercache = None

    default_properties = {
        'timestamp': rfc822.formatdate(0),
        'author': '',
        'owner': None,
        'viewgroup': None,
        'editgroup': None,
        }

    def __getstate__(self):
        return {'title': self.title, 'version': self.version}

    def __setstate__(self, state):
        self.__init__(state['title'], state['version'])

    def body(self):
        if self._body is None:
            if self.exists():
                return Store.Item.body(self)
            else:
                self._body = str(DefaultPageContent(self.title).render('txt'))
        return self._body

    def timestamp_epoch(self):
        return time.mktime(rfc822.parsedate(self.timestamp))

    def _preprocess(self, s):
        return normalize_newlines(s)

    def setbody(self, newtext):
        newtext = self._preprocess(newtext)
        self.notify_required = self.notify_required or (self._body != newtext)
	self._body = newtext
        self.reset_cache()

    def prerender(self, format):
        if not self.version:
            self.container_items = self.cache.getpickle(self.title + '.tree', None)
            self._mediacache = self.cache.getpickle(self.title + '.mediacache', {})
            self._rendercache = self.cache.getpickle(self.title + '.rendercache', {})
            if self.container_items is not None:
                return

        self.container_items = []
        self._mediacache = {}
        self._rendercache = {}

        web.ctx.active_page = self
	doc = Block.parsestring(self.body())
	PyleBlockParser(self).visit(doc.children)
        web.ctx.active_page = None

        if not self.version:
            self.cache.setpickle(self.title + '.tree', self.container_items)
            self.cache.setpickle(self.title + '.mediacache', self._mediacache)
            self.cache.setpickle(self.title + '.rendercache', self._rendercache)

    def mediacache(self):
        if self._mediacache is None:
            self.prerender('html')
        return self._mediacache

    def rendercache(self):
        return self._rendercache

    def save(self, user):
        savetime = time.time()
        self.timestamp = rfc822.formatdate(savetime)
        if not self.exists():
            self.set_creation_properties()
        self.author = user.getusername()
        self.primitive_save()
        self.log_change('saved', user, savetime)
        self.notify_subscribers(user)

    def set_creation_properties(self):
        if not user.is_anonymous():
            self.owner = user.getusername()
            self.viewgroup = user.getdefaultgroup()
            self.editgroup = user.getdefaultgroup()

    def reset_cache(self):
        self.cache.delete(self.title + '.tree')
        self.cache.delete(self.title + '.mediacache')
        self.cache.delete(self.title + '.rendercache')

    def delete(self, user):
        self.reset_cache()
        self.primitive_delete()
        for name in self.attachment_names():
            Attachment(self.title, name, None).delete()
        self.log_change('deleted', user)

    def attachment_names(self):
        prefix = self.title + '.attach.'
        prefixlen = len(prefix)
        return [f[prefixlen:]
                for f in web.ctx.attachments.message_encoder().keys_glob(prefix + '*')]

    def get_attachments(self):
        return [Attachment(self.title, name, None) for name in self.attachment_names()]

    def get_attachment(self, name, version):
        return Attachment(self.title, name, version)

    def backlinks(self):
        result = []
        r = re.compile(r'\b' + re.escape(self.title) + r'\b')
        for otherpage in self.msgenc.keys_glob('*.txt'):
            othertext = self.msgenc.getbody(otherpage, None)
            if r.search(othertext):
                result.append(otherpage[:-4]) # chop off the '.txt'
        return result

    def subscribers(self):
        result = []
        for username in Config.user_data_store.keys():
            user = User.User(username)
            if user.is_subscribed_to(self.title):
                result.append(user)
        return result

    def notify_subscribers(self, currentuser):
        if self.notify_required:
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
        return user in Group.lookup(self.viewgroup or Config.default_view_group)

    def writable_for(self, user):
        return user in Group.lookup(self.editgroup or Config.default_edit_group)

    def templateName(self):
	return 'pyle_page'

app_initialised = 0
def init_pyle():
    global app_initialised
    if not app_initialised:
        pass
