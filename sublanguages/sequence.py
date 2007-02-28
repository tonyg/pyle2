from __future__ import nested_scopes

import RenderUtils
import Config
import os

def runpipe(command, input):
    (child_stdin, child_stdout) = os.popen2(command)
    child_stdin.write(input)
    child_stdin.close()
    output = child_stdout.read()
    child_stdout.close()
    return output

def SublanguageHandler(args, doc, renderer):
    args = args.split(' ')
    name = args[0]

    input = '.PS'
    if len(args) > 1:
	input = input + ' ' + args[1]
    input = input + '\ncopy "./sublanguages/sequence.pic";\n' \
	+ doc.reconstruct_child_text().as_string() \
	+ '\n\n.PE\n'
    #input = runpipe('/usr/bin/pic2plot -T fig', input)
    #output = runpipe('/usr/bin/fig2dev -L png', input)
    output = runpipe('./sublanguages/sequence-helper.sh', input)

    cachepath = 'sequence/' + name + '.png'
    renderer.add(RenderUtils.media_cache(renderer,
					 cachepath,
					 '[Sequence diagram ' + name + ']',
					 'pyle_mediacache_image',
					 'image/png',
					 output))
