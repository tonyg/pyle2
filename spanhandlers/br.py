import Inline

def SpanHandler(rest, acc):
    acc.append(Inline.TagFragment('br', []))
    return Inline.discardSpan(rest)
