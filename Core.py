import web
import cgi
import pickle
import Block
import os
import Cheetah.Template
import exceptions
import traceback
import sys
import rfc822
import MimeWriter
import StringIO
import time

class Renderable:
    def render(self, format):
	import RenderUtils
	templatename = os.path.join('templates', self.templateName() + '.' + format)
	return Cheetah.Template.Template(file = templatename,
					 searchList = (self, RenderUtils))

class Store:
    def probe_kind(self):
	return 'txt'

    def has_key(self, title):
	subClassResponsibility()

    def getitem(self, title, kind, defaultvalue):
	subClassResponsibility()

    def setitem(self, title, kind, value):
	subClassResponsibility()

    def getpickle(self, title, kind, defaultvalue):
	p = self.getitem(title, kind, None)
	if p:
	    return pickle.loads(p)
	else:
	    return defaultvalue

    def setpickle(self, title, kind, value):
	self.setitem(title, kind, pickle.dumps(value))

    def getrfc822(self, title, kind, defaultheaders, defaultbody):
        p = self.getitem(title, kind, None)
        if p:
            fp = StringIO.StringIO(p)
            headers = rfc822.Message(fp)
            body = fp.read()
            return (headers, body)
        else:
            return (defaultheaders, defaultbody)

    def setrfc822(self, title, kind, headers, body):
        fp = StringIO.StringIO()
        w = MimeWriter.MimeWriter(fp)
        for (key, value) in headers.items():
            w.addheader(key, value)
        w.startbody('text/x-pylewiki-store').write(body)
        self.setitem(title, kind, fp.getvalue())

    def page(self, title, createIfAbsent = False):
	if has_key(self, title) or createIfAbsent:
	    return Page(self, title)
	else:
	    raise KeyError(title)

    def __get__(self, title):
	return self.page(title)

class FileStore(Store):
    def __init__(self, dirname):
	self.dirname = dirname

    def path_(self, title, kind):
	p = os.path.join(self.dirname, title)
	if kind is not None:
	    p = p + '.' + kind
	return p

    def has_key(self, title):
	return os.path.exists(self.path_(title, self.probe_kind()))

    def getitem(self, title, kind, defaultvalue):
	try:
	    f = open(self.path_(title, kind), 'rb')
	    content = f.read()
	    f.close()
	    return content
	except IOError:
	    return defaultvalue

    def setitem(self, title, kind, value):
	f = open(self.path_(title, kind), 'wb')
	f.write(value)
	f.close()

    def commit(self):
	pass

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

class List(Renderable):
    def __init__(self, is_ordered):
	self.is_ordered = is_ordered
	self.list_items = []

    def addItem(self, item):
	self.list_items.append(item)

    def templateName(self):
	return 'pyle_list'

class Container(Renderable):
    def __init__(self, klass = ''):
	self.klass = klass
	self.container_items = []

    def addItem(self, item):
	self.container_items.append(item)

    def templateName(self):
	return 'pyle_container'

class Section(Container):
    def __init__(self, rank, titleline, doc):
	Container.__init__(self)
	self.rank = rank
	self.titleline = titleline

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
	while self.current_rank() < rank - 1:
	    self.push_acc(Section(self.current_rank() + 1, None, None))
	self.push_acc(Section(rank, titleline, doc))

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

class Page(Renderable):
    def __init__(self, store, cache, title):
	self.store = store
	self.cache = cache
	self.title = title
	self.load_()

    def load_(self):
	(self.meta, self.text) = self.store.getrfc822(self.title, 'txt', {}, '')
	self.tree = self.cache.getpickle(self.title, 'tree', None)
	self.mediacache = self.cache.getpickle(self.title, 'mediacache', {})
	if self.tree is None:
	    self.renderTree()

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

    def setText(self, newtext):
	self.text = newtext
	self.renderTree()

    def renderTree(self):
	self.tree = []
	self.mediacache = {}
	doc = Block.parsestring(self.text)
	PyleBlockParser(self).visit(doc.children)
	self.saveTree()

    def saveTree(self):
	self.cache.setpickle(self.title, 'tree', self.tree)
	self.cache.setpickle(self.title, 'mediacache', self.mediacache)

    def addItem(self, item):
	self.tree.append(item)

    def save(self, user):
        self.setmetadate('Date', time.time())
        self.setmeta('Modifier', user.getusername())
	self.store.setrfc822(self.title, 'txt', self.meta, self.text)

    def templateName(self):
	return 'page'
