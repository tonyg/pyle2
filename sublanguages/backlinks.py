import web
import time
import Core

class BackLinks(Core.Renderable):
    def __init__(self, page):
        self.page = page

    def prerender(self, format):
        self.backlinks = self.page.backlinks()

    def templateName(self):
        return 'pyle_backlinks'

def SublanguageHandler(args, doc, renderer):
    renderer.add(BackLinks(renderer.page))
