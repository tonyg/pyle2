import Utils
import Block
import re

colspecre = re.compile(r"\s*\(([^)]+)\)\s*")

def lenient_int(s):
    try:
        return int(s)
    except:
        return None

def parse_colspan(spec):
    bits = map(lenient_int, spec.split('-'))
    if len(bits) == 1:
        return (bits[0], bits[0])
    else:
        return (bits[0], bits[1])

def collect_colspecs(args):
    acc = []
    prefix = ''
    haveFirstMatch = 0
    while 1:
        match = colspecre.search(args)
        if match:
            (xspec, yspec, attrs) = match.group(1).split(',', 2)
            acc.append((parse_colspan(xspec), parse_colspan(yspec), attrs))
            if not haveFirstMatch:
                haveFirstMatch = 1
                prefix = args[:match.start()].strip()
            args = args[match.end():]
        else:
            break
    return (acc, prefix)

def in_range(c, spec):
    (lo, hi) = spec
    if lo == None:
        if hi == None:
            return 1
        else:
            return c <= hi
    else:
        if hi == None:
            return c >= lo
        else:
            return (c >= lo) and (c <= hi)

def attrs_for(x, y, colspecs):
    acc = [attrs
           for (xspec, yspec, attrs) in colspecs
           if in_range(x, xspec) and in_range(y, yspec)]
    return ' '.join(acc)

def finish_row(rows, subparas):
    if subparas:
        rows.append(map(Block.parselines, subparas))
    return []

def group_columns(para):
    rows = []
    subparas = []
    for line in para.lines:
        if line.strip() == '':
            subparas = finish_row(rows, subparas)
        else:
            sublines = line.split('||')
            while len(subparas) < len(sublines):
                subparas.append([])
            index = 0
            for subline in sublines:
                subparas[index].append(subline.rstrip())
                index = index + 1
    subparas = finish_row(rows, subparas)
    return rows

def SublanguageHandler(args, doc, renderer):
    (colspecs, prefix) = collect_colspecs(args)
    rows = group_columns(doc.reconstruct_child_text())

    if not prefix:
        prefix = 'class="wikimarkup"'
    renderer.appendHtml('<table %s cellspacing="0" cellpadding="0" border="0">' % prefix)
    
    rownum = 0
    for cols in rows:
        rownum = rownum + 1
        if rownum % 2:
            rowclass = 'oddrow'
        else:
            rowclass = 'evenrow'
        renderer.appendHtml('<tr class="%s">' % rowclass)
        colnum = 0
        for celldoc in cols:
            colnum = colnum + 1
            renderer.appendHtml('<td ' + attrs_for(colnum, rownum, colspecs) + '>')
            Block.BasicWikiMarkup(renderer).visit(celldoc.children)
            # renderer.appendHtml('<pre>')
            # renderer.appendPlain(celldoc.reconstruct_text().as_string())
            # renderer.appendHtml('</pre>')
            renderer.appendHtml('</td>')
        renderer.appendHtml('</tr>')
    renderer.appendHtml('</table>')
