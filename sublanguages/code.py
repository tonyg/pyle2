import Config
import Inline
import os
import re

import warnings
import exceptions
warnings.filterwarnings('ignore',
                        r'.*tmpnam is a potential security risk to your program$',
                        exceptions.RuntimeWarning,
                        r'.*sublanguages\.code$',
                        19)

enscriptre = re.compile('.*<PRE>(.*)</PRE>.*', re.S)

def SublanguageHandler(args, doc, renderer):
    code = doc.reconstruct_child_text().as_string()
    if Config.code_enscript_command:
	filename = os.tmpnam()
	file = open(filename, 'w+')
	file.write(code)
	file.close()
	command = Config.code_enscript_command + ' -B -p - --language=html --color -E' + \
	    args + ' ' + filename + ' 2>/dev/null'
	child_stdout = os.popen(command)
	result = child_stdout.read()
	child_stdout.close()
	os.unlink(filename)
        renderer.add(Inline.TagFragment('pre',
					[Inline.HtmlFragment(enscriptre.sub(r'\1', result))],
					'enscript'))
    else:
	renderer.add(Inline.TagFragment('pre', [Inline.LiteralFragment(code)], 'enscript'))
