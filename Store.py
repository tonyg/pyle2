import re
import pickle
import os
import glob
import exceptions

class Store:
    def keys(self):
        subClassResponsibility

    def has_key(self, title):
	subClassResponsibility()

    def getitem(self, title, kind, defaultvalue, is_binary = False):
	subClassResponsibility()

    def setitem(self, title, kind, value, is_binary = False):
	subClassResponsibility()

    def delitem(self, title, kind):
        subClassResponsibility

    def getpickle(self, title, kind, defaultvalue):
	p = self.getitem(title, kind, None, True)
	if p:
	    return pickle.loads(p)
	else:
	    return defaultvalue

    def setpickle(self, title, kind, value):
	self.setitem(title, kind, pickle.dumps(value), True)

    def page(self, title, createIfAbsent = False):
	if has_key(self, title) or createIfAbsent:
	    return Page(self, title)
	else:
	    raise KeyError(title)

    def __get__(self, title):
	return self.page(title)

    def search(self, keywords):
        regexes = [re.compile(re.escape(k), re.IGNORECASE) for k in keywords]
        return self.search_regexes(regexes)

    def search_regexes(self, regexes):
        subClassResponsibility()

class FileStore(Store):
    def __init__(self, dirname):
	self.dirname = dirname
        self.probe_kind = 'txt'

    def set_probe_kind(self, new_probe_kind):
        self.probe_kind = new_probe_kind

    def path_(self, title, kind):
	p = os.path.join(self.dirname, title)
	if kind is not None:
	    p = p + '.' + kind
	return p

    def keys(self):
        globpattern = self.path_('*', self.probe_kind)
        suffixlen = len(self.probe_kind) + 1
        prefixlen = len(globpattern) - suffixlen - 1
        return [filename[prefixlen:-suffixlen] for filename in glob.iglob(globpattern)]

    def has_key(self, title):
	return os.path.exists(self.path_(title, self.probe_kind))

    def file_open_mode_(self, base, is_binary):
        if is_binary:
            return base + 'b'
        else:
            return base

    def getitem(self, title, kind, defaultvalue, is_binary = False):
	try:
	    f = open(self.path_(title, kind), self.file_open_mode_('r', is_binary))
	    content = f.read()
	    f.close()
	    return content
	except IOError:
	    return defaultvalue

    def setitem(self, title, kind, value, is_binary = False):
	f = open(self.path_(title, kind), self.file_open_mode_('w', is_binary))
	f.write(value)
	f.close()

    def delitem(self, title, kind, ignore_missing = False):
        try:
            os.unlink(self.path_(title, kind))
        except exceptions.OSError:
            if ignore_missing:
                pass
            else:
                raise exceptions.KeyError((title, kind))

    def search_regexes(self, regexes):
        result = []
        for key in self.keys():
            text = self.getitem(key, 'txt', '')
            score = 0
            for r in regexes:
                score = score + len(r.findall(text)) + len(r.findall(key))
            if score:
                result.append((score, key))
        result.sort(None, lambda r: r[0], True)
        return result

    def commit(self):
	pass
