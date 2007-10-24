import Inline

def SublanguageHandler(args, doc, renderer):
    text = doc.reconstruct_child_text().as_string()
    (fragments, rest) = Inline.parse(text)
    renderer.add(Inline.TagFragment('pyle_pre', fragments, 'pre'))
