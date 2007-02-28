import Inline

def SublanguageHandler(args, doc, renderer):
    renderer.add(Inline.HtmlFragment(doc.reconstruct_child_text().as_string()))
