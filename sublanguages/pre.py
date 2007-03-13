import Inline

def SublanguageHandler(args, doc, renderer):
    text = doc.reconstruct_child_text().as_string()
    renderer.add(Inline.TagFragment('pre', [Inline.LiteralFragment(text)], 'pre'))
