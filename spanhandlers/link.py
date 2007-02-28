import Inline

def SpanHandler(rest, acc):
    (text, rest) = Inline.collectSpan(rest)
    textparts = text.split('|', 1)
    if len(textparts) > 1:
        target = textparts[0]
        vistext = textparts[1]
    else:
        target = text
        vistext = target
    acc.append(Inline.ExternalLink(target, vistext))
    return rest
