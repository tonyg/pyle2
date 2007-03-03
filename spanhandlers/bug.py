import Config
import Inline

def SpanHandler(rest, acc):
    (text, rest) = Inline.collectSpan(rest)
    text = text.strip()
    acc.append(Inline.ExternalLink(Config.bug_url_template % text, "bug %s" % text))
    return rest
