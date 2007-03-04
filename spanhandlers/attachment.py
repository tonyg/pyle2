import Inline
import Core
import web

def SpanHandler(rest, acc):
    (text, rest) = Inline.collectSpan(rest)

    parts = text.split('/', 1)
    name = parts[0]
    pagename = ''

    if name.find(':') != -1:
        (pagename, name) = name.split(':', 1)
    if not pagename:
        pagename = web.ctx.active_page.title

    if len(parts) > 1:
        alt = parts[1]
    else:
        alt = '[Attachment ' + pagename + ':' + name + ']'

    a = Core.Attachment(pagename, name, None)
    acc.append(AttachmentReference(a, alt))
    return rest

class AttachmentReference(Core.Renderable):
    def __init__(self, attachment, alt):
        self.attachment = attachment
        self.alt = alt

    def templateName(self):
        return 'pyle_attachmentreference'
