import Inline

def SpanHandler(rest, acc):
    acc.append(Inline.TagFragment('pyle_br', []))
    return Inline.discardSpan(rest)
