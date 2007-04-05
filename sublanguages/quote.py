import Core

def SublanguageHandler(args, doc, renderer):
    renderer.push_visit_pop(Core.Container('quote'), doc.children)
