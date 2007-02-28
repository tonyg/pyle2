import Inline

def SpanHandler(rest, acc):
    (text, rest) = Inline.collectSpan(rest)
    acc.append(Inline.LiteralFragment(text))
    return rest
