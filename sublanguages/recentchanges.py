import web
import time
import Core

info = {
    "friendly_name": "Recent Changes List",
    "example_template": "changecount",
    "summary": "Inserts a description of recent Wiki activity.",
    "details": """

    <p>If 'changecount' is omitted, all changes recorded since the
    current server was started are printed; otherwise, the list is
    limited to just the most recent 'changecount' changes.</p>

    """
}

class RecentChanges(Core.Renderable):
    def __init__(self, count):
        self.count = count

    def prerender(self, format):
        self.changes = web.ctx.cache.getpickle('changes', [])
        if self.count is not None:
            self.changes = self.changes[-self.count:]

    def filter_duplicates(self, group):
        previous = None
        result = []
        for change in group:
            if previous and previous.get('page', '?') != change.get('page', '?'):
                result.append(previous)
            previous = change
        if previous:
            result.append(previous)
        return result

    def changes_by_day(self):
        result = []
        group = []
        previoustime = time.gmtime(0)
        def pushgroup():
            if group:
                group.sort(None, lambda c: c.get('page', 0))
                filteredgroup = self.filter_duplicates(group)
                result.append((previoustime, filteredgroup))
        for change in self.changes:
            when = change.get('when', 0)
            eventtime = time.gmtime(when)
            if previoustime[:3] != eventtime[:3]:
                pushgroup()
                group = []
            previoustime = eventtime
            group.append(change)
        pushgroup()
        return result

    def changes_by_day_newest_first(self):
        result = self.changes_by_day()
        result.reverse()
        return result

    def templateName(self):
        return 'pyle_recentchanges'

def SublanguageHandler(args, doc, renderer):
    if args.strip():
        count = int(args.strip())
    else:
        count = None
    renderer.add(RecentChanges(count))
