import Inline

def SpanHandler(rest, acc):
    (fragments, rest) = Inline.parse(rest)
    acc.append(Inline.TagFragment('pyle_tt', fragments))
    return rest
