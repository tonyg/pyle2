import re
import pickle
import os
import glob
import exceptions
import sets
import time
import Diff

import warnings
import exceptions
warnings.filterwarnings('ignore',
                        r'.*tmpnam is a potential security risk to your program$',
                        exceptions.RuntimeWarning,
                        r'.*Store$',
                        98)

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

    def gethistoryentry(self, title, kind, version):
        entries = self.gethistory(title, kind)
        for entry in entries:
            if entry.version_id == version:
                return entry
        for entry in entries:
            if entry.friendly_id == version:
                return entry
        return HistoryEntry(version, version, 0)

    def diff(self, title, kind, v1, v2):
        text1 = self.getitem(title, kind, '', v1)
        text2 = self.getitem(title, kind, '', v2)
        f1 = tempfilewith(text1)
        f2 = tempfilewith(text2)
        command = 'diff -u3 %s %s' % (f1, f2)
        f = os.popen(command)
        result = f.readlines()
        f.close()
        os.unlink(f1)
        os.unlink(f2)
        return Diff.Diff(title, v1, v2, result)

def tempfilewith(text):
    name = os.tmpnam()
    f = open(name, 'w+')
    f.write(text)
    f.close()
    return name

class HistoryEntry:
    def __init__(self, version_id, friendly_id, timestamp):
        self.version_id = version_id
        self.friendly_id = friendly_id
        self.timestamp = timestamp
        self.previous = None
        self.next = None

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
        return [HistoryEntry("N/A", "N/A", os.stat(self.path_(title, kind)).st_mtime)]

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

def parse_cvs_timestamp(s):
    m = re.match('(\d+)[/-](\d+)[/-](\d+) +(\d+):(\d+):(\d+)( +([^ ]+))?', s)
    if m:
        parts = map(int, m.groups()[:6])
        zone = m.group(8)
        # Timezone processing and CVS are independently horrible.
        # Brought together, they're impossible.
        timestamp = time.mktime(parts + [-1, -1, -1])
    else:
        timestamp = 0
    return timestamp

class SimpleShellStoreBase(FileStore):
    def __init__(self, dirname):
        FileStore.__init__(self, dirname)
        self.history_cache = {}

    def ensure_history_for(self, title, kind):
        key = (title, kind)
        if not self.history_cache.has_key(key):
            self.history_cache[key] = self.compute_history_for(title, kind)
        return self.history_cache[key]

    def pipe(self, text):
        try:
            return os.popen(self.shell_command(text), 'r')
        except:
            return None

    def pipe_lines(self, text, nostrip = False):
        f = self.pipe(text)
        if not f:
            return []
        if nostrip:
            result = f.readlines()
        else:
            result = [x.strip() for x in f.readlines()]
        f.close()
        return result

    def pipe_all(self, text):
        f = self.pipe(text)
        if not f:
            return ''
        result = f.read()
        f.close()
        return result

    def setitem(self, title, kind, value, is_binary = False):
        self.history_cache.pop((title, kind), None)
        FileStore.setitem(self, title, kind, value, is_binary)

    def delitem(self, title, kind):
        self.history_cache.pop((title, kind), None)
        FileStore.delitem(self, title, kind)

class CvsStore(SimpleShellStoreBase):
    def shell_command(self, text):
        return 'cd ' + self.dirname + ' && cvs ' + text + ' 2>/dev/null'

    def compute_history_for(self, title, kind):
        lines = self.pipe_lines('log ' + self.file_(title, kind))
        entries = []
        versionmap = {}
        i = 0
        nextentry = None
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
                timestamp = parse_cvs_timestamp(fmap['date'])

                versionmap[versionid] = revision
                entry = HistoryEntry(versionid, revision, timestamp)
                if nextentry:
                    nextentry.previous = entry
                    entry.next = nextentry
                nextentry = entry
                entries.append(entry)
                i = i + 2
            i = i + 1
        return (versionmap, entries)

    def gethistory(self, title, kind):
        (versionmap, entries) = self.ensure_history_for(title, kind)
        return entries

    def current_version_id(self, title, kind):
        revision = None
        commitid = None
        for line in self.pipe_lines('status ' + self.shell_quoted_file_(title, kind)):
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
            if versionmap.has_key(version):
                revision = versionmap[version]
                return self.pipe_all('update -r ' + revision + ' -p ' + self.file_(title, kind))
            else:
                return defaultvalue
        else:
            return FileStore.getitem(self, title, kind, defaultvalue, version, is_binary)

    def diff(self, title, kind, v1, v2):
        (versionmap, entries) = self.ensure_history_for(title, kind)
        r1 = versionmap.get(v1, v1)
        r2 = versionmap.get(v2, v2)
        return Diff.Diff(title, v1, v2,
                         self.pipe_lines('diff -u3 -r %s -r %s %s' % \
                                         (r1, r2, self.shell_quoted_file_(title, kind)),
                                         True))

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

class SvnStore(SimpleShellStoreBase):
    def __init__(self, dirname):
        SimpleShellStoreBase.__init__(self, dirname)
        self.load_repository_properties()

    def shell_command(self, text):
        return 'cd ' + self.dirname + ' && svn ' + text + ' 2>/dev/null'

    def load_repository_properties(self):
        self.repository_properties = self.svn_info('')

    def svn_info(self, f):
        result = {}
        for line in self.pipe_lines('info ' + f):
            parts = [part.strip() for part in line.split(':', 1)]
            if len(parts) == 2:
                result[parts[0]] = parts[1]
        return result

    def gethistory(self, title, kind):
        return self.ensure_history_for(title, kind)

    def compute_history_for(self, title, kind):
        lines = self.pipe_lines('log ' + self.file_(title, kind))
        entries = []
        i = 0
        nextentry = None
        while i + 1 < len(lines):
            if lines[i] == \
                   '------------------------------------------------------------------------':
                fields = [f.strip() for f in lines[i+1].split('|')]
                if len(fields) > 1:
                    versionid = fields[0][1:]
                    timestamp = parse_cvs_timestamp(fields[2])
                    entry = HistoryEntry(versionid, versionid, timestamp)
                    if nextentry:
                        nextentry.previous = entry
                        entry.next = nextentry
                    nextentry = entry
                    entries.append(entry)
            i = i + 1
        return entries

    def current_version_id(self, title, kind):
        i = self.svn_info(self.shell_quoted_file_(title, kind))
        return i['Last Changed Rev']

    def getitem(self, title, kind, defaultvalue, version = None, is_binary = False):
        if version:
            return self.pipe_all('cat -r ' + version + ' ' + self.file_(title, kind))
        else:
            return FileStore.getitem(self, title, kind, defaultvalue, version, is_binary)

    def diff(self, title, kind, v1, v2):
        return Diff.Diff(title, v1, v2,
                         self.pipe_lines('diff -r %s:%s %s' % \
                                         (v1, v2, self.shell_quoted_file_(title, kind)),
                                         True))

    def process_transaction(self, changed, deleted):
        FileStore.process_transaction(self, changed, deleted)
        cmd = '( cd ' + self.dirname + ' && ('
        touched = []
        if deleted:
            cmd = cmd + ' svn delete'
            for (title, kind) in deleted:
                f = self.shell_quoted_file_(title, kind)
                touched.append(f)
                cmd = cmd + ' ' + f
            cmd = cmd + ' ;'
        if changed:
            cmd = cmd + ' svn add'
            for (title, kind), (value, is_binary) in changed.items():
                f = self.shell_quoted_file_(title, kind)
                touched.append(f)
                cmd = cmd + ' ' + f
            cmd = cmd + ' ;'
        if touched:
            cmd = cmd + ' svn commit -m "CvsStore" ' + ' '.join(touched)
            cmd = cmd + ' ; svn update )) >/dev/null 2>&1'
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

    def diff(self, title, kind, v1, v2):
        return self.backing.diff(title, kind, v1, v2)

    def commit(self):
        self.backing.process_transaction(self.changed, self.deleted)
        self.reset()
