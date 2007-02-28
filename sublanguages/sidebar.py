import Utils
import Block

def SublanguageHandler(args, doc, renderer):
    renderer.appendHtml('<div class="sidebar">\n')
    Block.BasicWikiMarkup(renderer).visit(doc.children)
    renderer.appendHtml('</div>\n')
