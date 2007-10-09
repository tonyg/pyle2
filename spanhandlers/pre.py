import Inline

def SpanHandler(rest, acc):
    (fragments, rest) = Inline.parse(rest)
    acc.append(Inline.TagFragment('tt', fragments))
    return rest
