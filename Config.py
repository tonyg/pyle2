###########################################################################
# Configuration of the Wiki
###########################################################################
import User
import Store

# Session signing passphrase (erk)
session_passphrase = 'changeit'

# Name of default page
frontpage = 'FrontPage'

# Internal-link pattern - be careful when changing this
linkpattern = r'\b([A-Z]+[a-z0-9]+){2,}'

# Location of stored files
file_store = Store.FileStore('./pyledb')
cache_store = Store.FileStore('./pyledb_cache')

# Use "enscript" to format @code blocks? Set to None to disable.
code_enscript_command = '/usr/bin/env enscript'
# code_enscript_command = None

# Where may "dot" be found, to render graph figures?
dot_command = '/usr/bin/env dot'

# How should Pyle authenticate users?
user_authenticator = \
        User.BugzillaAuthenticator(url = 'https://extra.lshift.net/bugzilla/relogin.cgi',
                                   default_email_suffix = 'lshift.net',
                                   success_regex = '<h1>Logged Out</h1>')

# How should Pyle store user properties?
user_data_store = Store.FileStore('./pyledb_users')

# URL of web-based user creation service; None to disable
user_creation_service = 'https://extra.lshift.net/bugzilla/createaccount.cgi'

# URL of web-based password change service; None to disable
password_change_service = 'https://extra.lshift.net/bugzilla/userprefs.cgi'

# What defaults should Pyle use for user properties?
default_user_properties = {}

# Name of anonymous users
anonymous_user = "Anonymous"

# Allow anonymous editing of pages?
allow_anonymous_edit = True

# Allow anonymous viewing of pages?
allow_anonymous_view = True

# When running a standalone FTP frontend to pyle, if running as root,
# setuid to this user first:
ftp_server_user = 'www-data'
