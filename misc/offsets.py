# -*- Mode: Python -*-
# vi:si:et:sw=4:sts=4:ts=4

# show all possible offsets, in order of popularity, from a download of
# http://www.accuraterip.com/driveoffsets.htm

import sys

import BeautifulSoup

handle = open(sys.argv[1])

doc = handle.read()

soup = BeautifulSoup.BeautifulSoup(doc)

offsets = {} # offset -> total count

rows = soup.findAll('tr')
for row in rows:
    columns = row.findAll('td')
    if len(columns) == 4:
        first, second, third, fourth = columns
        name = first.find(text=True)
        offset = second.find(text=True)
        count = third.find(text=True)

        # only use sensible offsets
        try:
            int(offset)
        except:
            continue

        if offset not in offsets.keys():
            offsets[offset] = 0
        # first line is text, so int will fail with ValueError
        # purged entries will have None as count, so TypeError
        try:
            offsets[offset] += int(count)
        except (ValueError, TypeError):
            pass

# now sort offsets by count
counts = []
for offset, count in offsets.items():
    counts.append((count, offset))

counts.sort()
counts.reverse()

offsets = []
for count, offset in counts:
    offsets.append(offset)

# now format it for code inclusion
lines = []
line = 'OFFSETS = "'

for offset in offsets:
    line += offset + ", "
    if len(line) > 60:
        line += "\" + \\"
        lines.append(line)
        line = '          "'

# get last line too, trimming the comma and adding the quote
if len(line) > 11:
    line = line[:-2] + '"'
    lines.append(line)

print "\n".join(lines)
