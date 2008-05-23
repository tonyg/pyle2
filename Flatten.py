import Config
import Inline
import re
import sets

def flatten_wiki(chosen_root = None, dump_tree = False):
    """
    Flattens the graph of wiki pages into a tree (as contained within
    Config.file_store), using a pagerank-like algorithm to decide how
    to break the DAG into a tree, and bottom-up tree construction to
    decide how best to represent cyclic (parent-to-child) paths.

    Returns a triple:
     [0] = the name of the root page
     [1] = the tree rooted at that page
     [2] = dictionary of orphans (orphan name -> tree rooted there)

    If chosen_root is supplied, and not None, then it will be used as
    the main root of the main tree ('actual_root'). Otherwise, the
    most 'popular' page in the entire wiki is used as the root.

    Local variables:
     - outbound_links: maps page title to list of page titles
     - inbound_links: maps page title to list of page titles
     - bestparent: maps page title to page title
     - parent: maps page title to page title (or None, for orphans)
     - children: maps page title to list of page titles
     - roots: list of page titles
     - actual_root: page title

    Each entry in both of outbound_links and inbound_links is
    eventually sorted so that the first title in the list is the page
    with the most inbound links of all the candidates. Essentially,
    this is a sorting based on a rough approximation to page
    popularity or authoritativeness, similar to what Google are doing.

    'bestparent' is the parent that each individual page would 'like'
    to have: the highest-ranked of all the pages it links to, if such
    a page exists; otherwise the highest-ranked page linking to it;
    otherwise None.

    The 'parent' map takes 'bestparent' into account in selecting the
    final parent of a particular page, but has parent-child cycles
    broken, forming for the first time a proper tree. Less popular
    nodes are inserted into 'parent' first, so that more popular nodes
    will end up closer to the root of the final tree.

    The tree is then re-rooted at actual_root, and the final
    representation is constructed and returned.
    """
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
    """
    Prints a representation of a tree-of-dictionaries. Useful for
    debugging flatten_wiki.
    """
    for (childname, childnode) in node.items():
        print '%s- %s' % ('        ' * indent, childname)
        dump(childnode, indent + 1)

if __name__ == '__main__':
    flatten_wiki(None, dump_tree = True)
