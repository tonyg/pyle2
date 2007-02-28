class User:
    def __init__(self, username):
        self.username = username

    def getusername(self):
        return self.username

    def is_anonymous(self):
        return False

class Anonymous:
    def getusername(self):
        return ''

    def is_anonymous(self):
        return True

anonymous = Anonymous()

def lookup(username):
    if username is None:
        return anonymous
    else:
        raise KeyError(username)
