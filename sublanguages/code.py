import Config
import Inline
import Core
import os
import re

import warnings
import exceptions
warnings.filterwarnings('ignore',
                        r'.*tmpnam is a potential security risk to your program$',
                        exceptions.RuntimeWarning,
                        r'.*sublanguages\.code$',
                        20)

enscriptre = re.compile('.*<PRE>(.*)</PRE>.*', re.S)

def SublanguageHandler(args, doc, renderer):
    code = doc.reconstruct_child_text().as_string()
    literalfragment = Inline.LiteralFragment(code)
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
        renderer.add(HighlightedCode(Inline.HtmlFragment(enscriptre.sub(r'\1', result)),
                                     literalfragment))
    else:
	renderer.add(HighlightedCode(literalfragment, literalfragment))

class HighlightedCode(Core.Renderable):
    def __init__(self, highlightedFragment, plainFragment):
        self.highlightedFragment = highlightedFragment
        self.plainFragment = plainFragment

    def templateName(self):
        return 'pyle_highlightedcode'
