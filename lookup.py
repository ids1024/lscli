#!/usr/bin/env python3

import sys
import sqlite3

key = sys.argv[1].lower()
key = key.replace('j', 'i').replace('v', 'u')

conn = sqlite3.connect("lewis.db")
c = conn.cursor()
c.execute('SELECT * FROM dictionary WHERE word=?', (key,))
for i in c:
    print(i[2], end='')
conn.close()
