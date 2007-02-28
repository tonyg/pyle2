import Core

def SublanguageHandler(args, doc, renderer):
    renderer.push_visit_pop(Core.Container('sidebar'), doc.children)
