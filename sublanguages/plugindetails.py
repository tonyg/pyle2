import Core
import Plugin

info = {
    "friendly_name": "Plugin Details",
    "example_spacing": "",
    "example_template": "",
    "summary": "Inserts full descriptions of and help for each plugin installed.",
    "details": """

    <p>The text you are reading now was placed here by the plugindetails plugin.</p>

    """
}

def add_default(h, key, v):
    if not h.has_key(key):
        h[key] = v
    return h

class PluginDetails(Core.Renderable):
    def plugins(self):
        result = []
        def addResult(p, c, pr, m, po):
            stanza = dict(getattr(p, 'info', {})) # dict() makes a copy
            stanza['keyword'] = p.__name__.split('.')[-1]
            add_default(stanza, 'summary', '')
            add_default(stanza, 'details', '')
            add_default(stanza, 'friendly_name', stanza['keyword'])
            add_default(stanza, 'plugin_category', c)
            add_default(stanza, 'example_prefix', pr + stanza['keyword'])
            add_default(stanza, 'example_spacing', m)
            add_default(stanza, 'example_template', '...')
            add_default(stanza, 'example_postfix', po)
            result.append(stanza)
        for p in Plugin.all_plugins('spanhandlers'):
            addResult(p, 'spanhandler', '[', ' ', ']')
        for p in Plugin.all_plugins('sublanguages'):
            addResult(p, 'sublanguage', '\n\n@', '\n  ', '\n')
        result.sort(lambda a, b: cmp(a['keyword'], b['keyword']))
        return result

    def templateName(self):
        return 'plugin_plugindetails'

def SublanguageHandler(args, doc, renderer):
    renderer.add(PluginDetails())
