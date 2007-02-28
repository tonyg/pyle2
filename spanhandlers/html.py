import Inline

def SpanHandler(rest, acc):
    (inner, rest) = Inline.collectSpan(rest)
    acc.append(Inline.HtmlFragment(inner))
    return rest
