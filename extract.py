#!/usr/bin/env python3

import lxml.etree
import json
import os
import sqlite3

import beta_to_unicode

RESET = "\033[0m"
BOLD = "\033[1m"
ITALIC = "\033[3m"

parser = lxml.etree.XMLParser(no_network=False)
root = lxml.etree.parse("lat.ls.perseus-eng1.xml", parser=parser)

betacode_replacer = beta_to_unicode.Replacer()

def xml2str(xml, level=0):
    if xml.tag == "sense":
        level = int(xml.get("level"))
    contents = (xml.text or '') + ''.join(xml2str(i, level) for i in xml)
    tail = xml.tail or ''

    if xml.tag == "orth":
        return BOLD + contents + RESET + tail
    elif xml.tag == "gen":
        return ITALIC + contents + RESET + tail
    elif xml.tag == "sense":
        return '\n' + level*'  ' + BOLD + xml.get('n') + ('. ' if xml.get('n')[-1] != ')' else ' ') + RESET + contents.strip('— ') + tail
    elif xml.tag == "hi" and xml.get("rend") == "ital":
        return ITALIC + contents + RESET + tail
    elif xml.tag == "foreign" and xml.get("lang") == "greek":
        return betacode_replacer.beta_code(contents.upper()) + tail
    elif xml.tag == "cit":
        return "\n" + (level+1) * '  ' + contents + tail.strip(": ")
    elif xml.tag == "quote":
        return '“' + contents + "”" + tail
    else:
        return contents + tail


def create_db(dictionary):
    if os.path.exists("lewis.db"):
        os.remove("lewis.db")

    entries = [(word, desc) for word, v in dictionary.items() for desc in v]

    conn = sqlite3.connect("lewis.db")
    c = conn.cursor()
    c.execute("CREATE TABLE dictionary (word text, description text)")
    c.executemany("INSERT INTO dictionary (word, description) VALUES (?, ?)", entries)
    conn.commit()
    conn.close()


dictionary = {}
for entry in root.iterfind("//entryFree"):
    key = entry.get("key").lower().strip("0123456789")
    key = key.replace('j', 'i').replace('v', 'u')

    assert entry.text is None # May as well assert instead of just assuming this
    value = ''.join(map(xml2str, entry)) + (entry.tail or '')
    value = value.replace(" ...", "…")

    if key in dictionary:
        dictionary[key].append(value)
    else:
        dictionary[key] = [value]

create_db(dictionary)
