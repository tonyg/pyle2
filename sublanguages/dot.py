from __future__ import nested_scopes

import RenderUtils
import Config
import os

def SublanguageHandler(args, doc, renderer):
    command = Config.dot_command + ' -Tpng'
    (child_stdin, child_stdout) = os.popen2(command)
    child_stdin.write(doc.reconstruct_child_text().as_string())
    child_stdin.close()
    pngdata = child_stdout.read()
    child_stdout.close()

    if not renderer.page.mediacache.has_key('__dot_counter'):
	renderer.page.mediacache['__dot_counter'] = 0
    index = renderer.page.mediacache['__dot_counter']
    name = 'dot' + str(index)
    renderer.page.mediacache['__dot_counter'] = index + 1

    cachepath = 'dot/' + name + '.png'
    renderer.add(RenderUtils.media_cache(renderer,
					 cachepath,
					 '[Dot figure ' + name + ']',
					 'pyle_mediacache_image',
					 'image/png',
					 pngdata))
