import Core

def SublanguageHandler(args, doc, renderer):
    renderer.push_and_visit(Core.Division('sidebar'), doc.children)
