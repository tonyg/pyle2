import Inline

def SpanHandler(rest, acc):
    (inner, rest) = Inline.collectSpan(rest)
    acc.append(Inline.TagFragment('pyle_code', [Inline.LiteralFragment(inner)]))
    return rest
