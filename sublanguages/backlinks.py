import Core

info = {
    "friendly_name": "Backlinks",
    "example_spacing": "",
    "example_template": "",
    "summary": "Displays a list of pages that link to the current page.",
}

class BackLinks(Core.Renderable):
    def __init__(self, page):
        self.page = page

    def prerender(self, format):
        self.backlinks = self.page.backlinks()

    def templateName(self):
        return 'pyle_backlinks'

def SublanguageHandler(args, doc, renderer):
    renderer.add(BackLinks(renderer.page))
