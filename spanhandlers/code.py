import Inline

def SpanHandler(rest, acc):
    (inner, rest) = Inline.collectSpan(rest)
    acc.append(Inline.TagFragment('code', [Inline.LiteralFragment(inner)]))
    return rest
