import Core
import Inline
import web

class Footnote(Core.Renderable):
    def __init__(self, number, fragments):
        self.number = number
        self.fragments = fragments

    def anchor(self):
        return 'footnote_' + str(self.number)

    def refanchor(self):
        return 'footnotelink_' + str(self.number)

    def templateName(self):
        return 'pyle_footnote'

def SpanHandler(rest, acc):
    (inner, rest) = Inline.parse(rest)

    rendercache = web.ctx.active_page.rendercache()
    if not rendercache.has_key('footnotes'):
        rendercache['footnotes'] = []

    number = len(rendercache['footnotes']) + 1
    note = Footnote(number, inner)
    rendercache['footnotes'].append(note)
    acc.append(note)
    return rest
