###########################################################################
# Configuration of the Wiki
###########################################################################

# Session signing passphrase (erk)
session_passphrase = 'changeit'

# Name of default page
frontpage = 'FrontPage'

# Internal-link pattern - be careful when changing this
linkpattern = r'\b([A-Z]+[a-z0-9]+){2,}'

# Location of stored files
filestore_dir = './pyledb'
cache_dir = './pyledb_cache'

# Use "enscript" to format @code blocks? Set to None to disable.
code_enscript_command = '/usr/bin/enscript'
# code_enscript_command = None

# Where may "dot" be found, to render graph figures?
dot_command = '/usr/local/bin/dot'
