import re

class Group:
    def __init__(self):
        pass

    def __contains__(self, user):
        self.subClassResponsibility()

    def __and__(self, other): return And(self, other)
    def __or__(self, other): return Or(self, other)
    def __sub__(self, other): return Sub(self, other)
    def __not__(self): return Not(self)

class EmptyGroup(Group):
    def __contains__(self, user):
        return False

class Public(Group):
    def __contains__(self, user):
        return True

class Anonymous(Group):
    def __contains__(self, user):
        return user.is_anonymous()

class List(Group):
    def __init__(self, initial_members = []):
        Group.__init__(self)
        self.members = frozenset(initial_members)

    def __contains__(self, user):
        return user in self.members

class Regex(Group):
    def __init__(self, username_pattern, flags = 0):
        Group.__init__(self)
        self.pattern = re.compile('^' + username_pattern + '$')

    def __contains__(self, user):
        return bool(self.pattern.match(user.getusername()))

class EmailDomain(Regex):
    def __init__(self, email_domain):
        Regex.__init__(self, '.*@' + re.escape(email_domain), re.IGNORECASE)

class Not(Group):
    def __init__(self, g):
        Group.__init__(self)
        self.inner_group = g

    def __contains__(self, user):
        return g not in self.inner_group

class BinaryGroup(Group):
    def __init__(self, g1, g2):
        Group.__init__(self)
        self.group1 = g1
        self.group2 = g2

class And(BinaryGroup):
    def __contains__(self, user):
        return (user in self.group1) and (user in self.group2)

class Or(BinaryGroup):
    def __contains__(self, user):
        return (user in self.group1) or (user in self.group2)

class Sub(BinaryGroup):
    def __contains__(self, user):
        return (user in self.group1) and (user not in self.group2)

def lookup(groupname, default_value = None):
    import Groups
    g = Groups.__dict__.get(groupname, None)
    if isinstance(g, Group):
        return g
    if default_value:
        return default_value
    raise 'No such group', groupname
