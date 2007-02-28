import Utils
import Config
import string

def footnote_pp(renderer):
    if renderer.footnotes:
        renderer.appendHtml('<hr><dl class="footnotes">')
        counter = 1
        for note in renderer.footnotes:
            renderer.appendHtml('<dt>Footnote <a name="footnote_' + str(counter) + '"></a>' +
                                '<a href="#footnotelink_' + str(counter) + '">' +
                                str(counter) + '</a>:\n' +
                                '<dd>' + ''.join(note) + '\n')
            counter = counter + 1
        renderer.appendHtml('</dl>')

def SpanHandler(rest, renderer, acc):
    if not hasattr(renderer, 'footnotes'):
        renderer.footnotes = []
        renderer.addPostProcessor(200, footnote_pp)

    noteHtml = []
    nextnote = len(renderer.footnotes) + 1
    renderer.footnotes.append(noteHtml)

    rest = renderer.appendMarkup(rest, noteHtml)

    acc.append('<a name="footnotelink_' + str(nextnote) + '"></a>' + \
               '<a class="footnoteref" href="#footnote_' + str(nextnote) + '">' + \
               str(nextnote) + '</a>')
    return rest
