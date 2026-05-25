#!/usr/bin/env python3

# reg, sic

import lxml.etree
import json
import os
import sys
import sqlite3

XML_PATH = "lexica/CTS_XML_TEI/perseus/pdllex/lat/ls/lat.ls.perseus-eng2.xml"
LAT_GRK = dict(zip("abgdez", "αβγδεζ"))

if len(sys.argv) > 1 and sys.argv[1] == "--android":
    DBNAME = "lewis-android.db"

    BOLD = '<b>'
    ITALIC = '<i>'
    UNBOLD = "</b>"
    UNITALIC = "</i>"
    NL = "<br/>"
    SPACE = '&nbsp;' * 2
else:
    DBNAME = "lewis.db"

    BOLD = "\033[1m"
    ITALIC = "\033[3m"
    UNBOLD = UNITALIC = "\033[0m"
    NL = '\n'
    SPACE = '  '

def xml2str(xml, level=0):
    if xml.tag == "sense":
        level = int(xml.get("level"))
    contents = (xml.text or '') + ''.join(xml2str(i, level) for i in xml)
    tail = xml.tail or ''

    if xml.tag == "orth":
        return BOLD + contents + UNBOLD + tail
    elif xml.tag == "gen":
        return ITALIC + contents + UNITALIC + tail
    elif xml.tag == "sense":
        n = xml.get('n')
        if level == 5:
            n = ''.join(LAT_GRK[i] if i.isalpha() else i for i in n)
        n += '. ' if n[-1] != ')' else ' '
        return NL + level*SPACE + BOLD + n + UNBOLD + contents.strip('— ') + tail
    elif xml.tag == "hi" and xml.get("rend") == "ital":
        return ITALIC + contents + UNITALIC + tail
    elif xml.tag == "foreign" and xml.get("lang") == "greek":
        return contents.upper() + tail
    elif xml.tag == "cit":
        if tail.endswith(': '):
            tail = tail.rstrip(': ')
        return NL + (level+1) * SPACE + contents + tail
    elif xml.tag == "quote":
        return '“' + contents + "”" + tail
    else:
        return contents + tail

def orth2str(xml):
    contents = (xml.text or '') + ''.join(orth2str(i) for i in xml)
    tail = xml.tail or ''

    if xml.tag in ("orth", "reg", "sic", "corr"):
        return contents + tail
    else:
        sys.exit(f"Unexpected tag '{xml.tag}' in orth");

if os.path.exists(DBNAME):
    os.remove(DBNAME)

with sqlite3.connect(DBNAME) as conn:
    c = conn.cursor()
    c.execute("CREATE TABLE dictionary (_id INTEGER PRIMARY KEY, key TEXT, word TEXT, description TEXT)")

    print("Reading from " + XML_PATH)

    context = lxml.etree.iterparse(XML_PATH, no_network=False, events=("end",), tag="entryFree")
    for i, (_, entry) in enumerate(context):
        print("\rProcessing entry ", i, sep='', end='')

        key = entry.get("key").lower().strip("0123456789")
        key = key.replace('j', 'i').replace('v', 'u')

        assert entry[0].tag == "orth"
        word = orth2str(entry[0]).replace('-', '')

        assert entry.text is None # May as well assert instead of just assuming this
        value = ''.join(map(xml2str, entry)) + (entry.tail or '')
        value = value.replace(" ...", "…")

        # XXX: Render proper diacritics: https://github.com/PerseusDL/lexica/issues/41
        word = word.replace("^", "")
        value = value.replace("^", "")

        c.execute("INSERT INTO dictionary (key, word, description) VALUES (?, ?, ?)", (key, word, value))
        entry.clear() # Free memory
    print()

    print("Creating index")
    c.execute("CREATE INDEX dictionary_key_idx ON dictionary (key)")

print("Finished generating " + DBNAME)
