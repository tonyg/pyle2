import re
import pickle
import os
import glob
import exceptions
import sets
import time

class Store:
    def __init__(self, basic_kind):
        self.basic_kind = basic_kind

    def keys(self):
        subClassResponsibility

    def has_key(self, title):
	subClassResponsibility()

    def gethistory(self, title, kind):
        subClassResponsibility()

    def current_version_id(self, title, kind):
        subClassResponsibility()

    def getitem(self, title, kind, defaultvalue, version = None, is_binary = False):
	subClassResponsibility()

    def setitem(self, title, kind, value, is_binary = False):
	subClassResponsibility()

    def delitem(self, title, kind):
        subClassResponsibility

    def set_basic_kind(self, new_basic_kind):
        self.basic_kind = new_basic_kind

    def getpickle(self, title, kind, defaultvalue, version = None):
	p = self.getitem(title, kind, None, version, True)
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

    def items_for_search(self):
        for key in self.keys():
            yield (key, self.getitem(key, self.basic_kind, ''))

    def search(self, keywords):
        regexes = [re.compile(re.escape(k), re.IGNORECASE) for k in keywords]
        return self.search_regexes(regexes)

    def search_regexes(self, regexes):
        result = []
        for key, text in self.items_for_search():
            score = 0
            for r in regexes:
                score = score + len(r.findall(text)) + len(r.findall(key))
            if score:
                result.append((score, key))
        result.sort(None, lambda r: r[0], True)
        return result

class HistoryEntry:
    def __init__(self, version_id, timestamp):
        self.version_id = version_id
        self.timestamp = timestamp

class FileStore(Store):
    def __init__(self, dirname):
        Store.__init__(self, 'txt')
	self.dirname = dirname

    def shell_quoted_file_(self, title, kind):
        return '"' + self.file_(title, kind).replace('\\', '\\\\').replace('"', '\\"') + '"'

    def file_(self, title, kind):
        if kind is None:
            return title
        else:
            return title + '.' + kind

    def path_(self, title, kind):
	return os.path.join(self.dirname, self.file_(title, kind))

    def keys(self):
        globpattern = self.path_('*', self.basic_kind)
        suffixlen = len(self.basic_kind) + 1
        prefixlen = len(globpattern) - suffixlen - 1
        return [filename[prefixlen:-suffixlen] for filename in glob.iglob(globpattern)]

    def has_key(self, title):
	return os.path.exists(self.path_(title, self.basic_kind))

    def file_open_mode_(self, base, is_binary):
        if is_binary:
            return base + 'b'
        else:
            return base

    def gethistory(self, title, kind):
        return [HistoryEntry("N/A", os.stat(self.path_(title, kind)).st_mtime)]

    def current_version_id(self, title, kind):
        return None

    def getitem(self, title, kind, defaultvalue, version = None, is_binary = False):
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

    def delitem(self, title, kind):
        try:
            os.unlink(self.path_(title, kind))
        except exceptions.OSError:
            pass

    def process_transaction(self, changed, deleted):
        for (title, kind), (value, is_binary) in changed.items():
            self.setitem(title, kind, value, is_binary)
        for (title, kind) in deleted:
            self.delitem(title, kind)

class CvsStore(FileStore):
    def __init__(self, dirname):
        FileStore.__init__(self, dirname)
        self.history = {}

    def ensure_history_for(self, title, kind):
        key = (title, kind)
        if not self.history.has_key(key):
            f = os.popen('cd ' + self.dirname + \
                         ' && cvs log ' + self.file_(title, kind) + \
                         ' 2>/dev/null', 'r')
            lines = [x.strip() for x in f.readlines()]
            f.close()

            entries = []
            versionmap = {}

            i = 0
            while i < len(lines):
                if lines[i] == '----------------------------':
                    revision = lines[i+1].split(' ')[1]
                    fields = [[k.strip() for k in f.strip().split(':', 1)]
                              for f in lines[i+2].split(';')]
                    fmap = dict([f for f in fields if len(f) == 2])
                    if fmap.has_key('commitid'):
                        versionid = fmap['commitid']
                    else:
                        versionid = revision

                    m = re.match('(\d+)[/-](\d+)[/-](\d+) +(\d+):(\d+):(\d+)( +([^ ]+))?',
                                 fmap['date'])
                    if m:
                        parts = map(int, m.groups()[:6])
                        zone = m.group(8)
                        # Timezone processing and CVS are independently horrible.
                        # Brought together, they're impossible.
                        timestamp = time.mktime(parts + [-1, -1, -1])
                    else:
                        timestamp = 0

                    versionmap[versionid] = revision
                    entries.append(HistoryEntry(versionid, timestamp))
                    i = i + 2
                i = i + 1

            self.history[key] = (versionmap, entries)
        return self.history[key]

    def gethistory(self, title, kind):
        (versionmap, entries) = self.ensure_history_for(title, kind)
        return entries

    def current_version_id(self, title, kind):
        try:
            f = os.popen('cd ' + self.dirname + \
                         ' && cvs status ' + self.shell_quoted_file_(title, kind) + \
                         ' 2>/dev/null', 'r')
        except:
            return None
        lines = f.readlines()
        f.close()
        revision = None
        commitid = None
        for line in lines:
            m = re.search(r'Working revision:\s+([0-9.]+)', line)
            if m: revision = m.group(1)
            m = re.search(r'Commit Identifier:\s+(\S+)', line)
            if m: commitid = m.group(1)
        if commitid: return commitid
        if revision: return revision
        return None

    def getitem(self, title, kind, defaultvalue, version = None, is_binary = False):
        if version:
            (versionmap, entries) = self.ensure_history_for(title, kind)
            revision = versionmap[version]
            try:
                f = os.popen('cd ' + self.dirname + \
                             ' && cvs update -r ' + revision + \
                             ' -p ' + self.file_(title, kind) + \
                             ' 2>/dev/null', 'r')
            except:
                raise KeyError(version)
            result = f.read()
            f.close()
            return result
        else:
            return FileStore.getitem(self, title, kind, defaultvalue, version, is_binary)

    def setitem(self, title, kind, value, is_binary = False):
        self.history.pop((title, kind), None)
        FileStore.setitem(self, title, kind, value, is_binary)

    def delitem(self, title, kind):
        self.history.pop((title, kind), None)
        FileStore.delitem(self, title, kind)

    def process_transaction(self, changed, deleted):
        FileStore.process_transaction(self, changed, deleted)
        cmd = '( cd ' + self.dirname + ' && ('
        touched = []
        if deleted:
            cmd = cmd + ' cvs remove'
            for (title, kind) in deleted:
                f = self.shell_quoted_file_(title, kind)
                touched.append(f)
                cmd = cmd + ' ' + f
            cmd = cmd + ' ;'
        if changed:
            cmd = cmd + ' cvs add -kb'
            for (title, kind), (value, is_binary) in changed.items():
                f = self.shell_quoted_file_(title, kind)
                touched.append(f)
                cmd = cmd + ' ' + f
            cmd = cmd + ' ;'
        if touched:
            cmd = cmd + ' cvs commit -m "CvsStore" ' + ' '.join(touched)
            cmd = cmd + ' )) >/dev/null 2>&1'
            os.system(cmd)

# Really only a pseudo-transaction, as it doesn't provide ACID
class Transaction(Store):
    def __init__(self, backing):
        Store.__init__(self, None)
        self.basic_kind = backing.basic_kind
        self.backing = backing
        self.reset()

    def set_basic_kind(self, new_basic_kind):
        Store.set_basic_kind(self, new_basic_kind)
        self.backing.set_basic_kind(new_basic_kind)

    def reset(self):
        self.changed = {}
        self.deleted = sets.Set()

    def keys(self):
        result = self.backing.keys()
        result.extend([k[0] for k in self.changed.keys() if k[1] == self.basic_kind])
        return result

    def has_key(self, title):
        return (self.backing.has_key(title) and (title, self.basic_kind) not in self.deleted) or \
               (title, self.basic_kind) in self.changed

    def gethistory(self, title, kind):
        return self.backing.gethistory(title, kind)

    def current_version_id(self, title, kind):
        return self.backing.current_version_id(title, kind)

    def getitem(self, title, kind, defaultvalue, version = None, is_binary = False):
        if version is None:
            key = (title, kind)
            if key in self.changed:
                return self.changed[key]
            elif key in self.deleted:
                return defaultvalue
            else:
                pass
        return self.backing.getitem(title, kind, defaultvalue, version, is_binary)

    def setitem(self, title, kind, value, is_binary = False):
        key = (title, kind)
        self.deleted.discard(key)
        self.changed[key] = (value, is_binary)

    def delitem(self, title, kind):
        key = (title, kind)
        self.changed.pop(key, None)
        self.deleted.add(key)

    def commit(self):
        self.backing.process_transaction(self.changed, self.deleted)
        self.reset()
