import Inline

def SpanHandler(rest, acc):
    (inner, rest) = Inline.parse(rest)
    acc.append(Inline.TagFragment('pyle_em', inner))
    return rest
