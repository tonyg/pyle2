import Config
import urllib
import re

class User:
    def __init__(self, username):
        self.username = username
        self.load_properties()

    def getusername(self):
        return self.username

    def is_anonymous(self):
        return False

    def email_address_editable(self):
        return True

    def load_properties(self):
        props = Config.user_data_store.getpickle(self.username, 'user',
                                                 Config.default_user_properties)
        self.email = props.get('email', None)
        self.subscriptions = props.get('subscriptions', [])
        self.superuser_flag = props.get('superuser_flag', False)

    def save_properties(self):
        props = {
            'email': self.email,
            'subscriptions': self.subscriptions,
            'superuser_flag': self.superuser_flag,
            }
        Config.user_data_store.setpickle(self.username, 'user', props)

class Anonymous(User):
    def __init__(self):
        User.__init__(self, '')

    def is_anonymous(self):
        return True

    def load_properties(self):
        self.email = None
        self.subscriptions = []
        self.superuser_flag = False

    def save_properties(self):
        pass

class Authenticator:
    def authenticate(self, user, password):
        subClassResponsibility()

    def lookup_user(self, username):
        subClassResponsibility()

class BugzillaUser(User):
    def email_address_editable(self):
        return False

    def load_properties(self):
        User.load_properties(self)
        self.email = self.username

    def save_properties(self):
        self.email = self.username
        User.save_properties(self)

class BugzillaAuthenticator(Authenticator):
    def __init__(self,
                 url = None,
                 success_regex = None,
                 default_email_suffix = None,
                 login_input = 'Bugzilla_login',
                 password_input = 'Bugzilla_password',
                 other_inputs = [('GoAheadAndLogIn', '1')]):
        self.url = url
        self.success_regex = re.compile(success_regex)
        self.default_email_suffix = default_email_suffix
        self.login_input = login_input
        self.password_input = password_input
        self.other_inputs = other_inputs

    def authenticate(self, user, password):
        if user.is_anonymous():
            return False

        inputs = [(self.login_input, user.getusername()),
                  (self.password_input, password)] + self.other_inputs
        data = urllib.urlencode(inputs)
        resulthandle = urllib.urlopen(self.url, data)
        result = resulthandle.read()
        resulthandle.close()

        if self.success_regex.search(result):
            return True
        else:
            return False

    def lookup_user(self, username):
        if username.find('@') == -1 and self.default_email_suffix:
            username = username + '@' + self.default_email_suffix
        return BugzillaUser(username)

###########################################################################

anonymous = Anonymous()

def lookup(username):
    if username is None:
        return anonymous
    else:
        return Config.user_authenticator.lookup_user(username)
