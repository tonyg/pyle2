import Config
import Inline
import re
import sets

def flatten_wiki(chosen_root = None, dump_tree = False):
    msgenc = Config.file_store.message_encoder()

    outbound_links = {}
    inbound_links = {}

    for filename in msgenc.keys_glob('*.txt'):
        pagename = filename[:-4] # chop off the '.txt'
        body = msgenc.getbody(filename, None)
        links = sets.Set([x[0]
                          for x in Inline.intlinkre.findall(body)
                          if msgenc.has_key(x[0] + '.txt')])
        outbound_links[pagename] = links
        for target in links:
            if not inbound_links.has_key(target):
                inbound_links[target] = sets.Set()
            inbound_links[target].add(pagename)

    if len(outbound_links) == 0:
        return None

    def sort_by_inbound_links(x, reverse = True):
        x.sort(key = lambda page: len(inbound_links.get(page, [])), reverse = reverse)

    def sort_table_by_inbound_links(t):
        for page in t.keys():
            targets = list(t[page])
            sort_by_inbound_links(targets)
            t[page] = targets

    sort_table_by_inbound_links(outbound_links)
    sort_table_by_inbound_links(inbound_links)

    def best_parent_from(selections, page):
        for selection in selections:
            if selection != page:
                return selection
        return None

    bestparent = {}
    for (page, targets) in outbound_links.items():
        p = best_parent_from(targets, page)
        if not p: p = best_parent_from(inbound_links.get(page, []), page)
        bestparent[page] = p

    pages_by_inbound_link_count = bestparent.keys()
    sort_by_inbound_links(pages_by_inbound_link_count, reverse = False)

    parent = {}
    roots = sets.Set()

    def path_from_to(a, b):
        node = a
        while node:
            p = parent.get(node, None)
            if p == b:
                return True
            node = p
        return False

    for page in pages_by_inbound_link_count:
        if path_from_to(bestparent[page], page):
            roots.add(page)
        else:
            parent[page] = bestparent[page]

    def reroot_at(page):
        node = page
        newparent = None
        while node:
            oldparent = parent.get(node, None)
            parent[node] = newparent
            newparent = node
            node = oldparent
        roots.remove(newparent)
        roots.add(page)

    actual_root = chosen_root or pages_by_inbound_link_count[-1]
    reroot_at(actual_root)

    children = {}
    for (c, p) in parent.items():
        if not children.has_key(p): children[p] = []
        children[p].append(c)

    def construct_tree(root):
        return dict((child, construct_tree(child)) for child in children.get(root, []))

    result = ( actual_root,
               construct_tree(actual_root),
               dict((root, construct_tree(root))
                    for root in roots
                    if root != actual_root) )
    if dump_tree:
        dump({ result[0]: result[1],
               "(Orphans)": result[2] }, 0)

    return result

def dump(node, indent):
    for (childname, childnode) in node.items():
        print '%s- %s' % ('        ' * indent, childname)
        dump(childnode, indent + 1)

if __name__ == '__main__':
    flatten_wiki(None, dump_tree = True)
