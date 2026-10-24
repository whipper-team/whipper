"""Lookup hints and reproducibility of the published candidate table."""

from collections import defaultdict
import gzip
import hashlib
import html
import importlib.util
from pathlib import Path
import re
import unittest

from whipper.common import drive_offsets
from whipper.common import drive_offsets_data as data


ROOT = Path(__file__).resolve().parents[2]


class LookupTest(unittest.TestCase):
    def test_complete_names_and_published_conflicts(self):
        self.assertEqual(drive_offsets.known_offsets_for(
            ' plextor ', 'dvdr   px-750a'), [102, 0])
        for vendor, model in (('OTHER', 'DVDR PX-750A'),
                              ('PLEXTOR', 'PX-750A'),
                              ('PLEXTOR', 'DVDR PX-750A EXTRA'),
                              ('PLEXTOR', 'DVDR PX-750'), (None, None)):
            self.assertEqual(
                drive_offsets.known_offsets_for(vendor, model), [])

    def test_order_and_opt_out(self):
        self.assertEqual(drive_offsets.order_offsets(
            [6, 0, 102], 0, [102, 0]), [0, 102, 6])
        self.assertEqual(drive_offsets.order_offsets(
            [6, 0, 6, 102], 0, [102], prioritize=False),
            [6, 0, 102])


class SourceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / 'misc' / 'gen_drive_offsets.py'
        if not path.exists():
            raise unittest.SkipTest('source snapshot is only in the checkout')
        spec = importlib.util.spec_from_file_location('offset_generator', path)
        cls.generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.generator)

    def test_reproduction(self):
        source = gzip.decompress((ROOT / 'misc' / 'accuraterip' /
                                  'driveoffsets.html.gz').read_bytes())
        self.assertEqual(hashlib.sha256(source).hexdigest(),
                         data.SOURCE_SHA256)
        generated = self.generator.generate(source)
        self.assertEqual(generated, (ROOT / 'whipper' / 'common' /
                                     'drive_offsets_data.py').read_text())

    def test_all_records_against_independent_source_extraction(self):
        # Deliberately use row/cell extraction independent of HTMLParser,
        # so a generator regression cannot validate its own output.
        source = gzip.decompress((ROOT / 'misc' / 'accuraterip' /
                                  'driveoffsets.html.gz').read_bytes())
        rows = re.findall(r'<tr\b[^>]*>(.*?)</tr>',
                          source.decode('windows-1252'), re.I | re.S)
        expected = defaultdict(lambda: defaultdict(int))
        count = 0
        for row in rows:
            cells = re.findall(r'<td\b[^>]*>(.*?)</td>', row, re.I | re.S)
            cells = [' '.join(html.unescape(re.sub(r'<[^>]+>', '', value))
                              .split()) for value in cells]
            if len(cells) != 4 or not re.fullmatch(r'[+-]?\d+', cells[1]):
                continue
            expected[cells[0].upper()][int(cells[1])] += int(cells[2])
            count += 1
        self.assertEqual(count, data.SOURCE_ROWS)
        self.assertEqual(set(expected), set(data.MODEL_OFFSETS))
        for name, offsets in expected.items():
            self.assertEqual(data.MODEL_OFFSETS[name], tuple(sorted(
                offsets.items(), key=lambda item: (-item[1], item[0]))))

    def test_duplicate_counts_and_deterministic_ties(self):
        rows = [('V - MODEL', 30, 2), ('V - MODEL', 6, 4),
                (' v - model ', 30, 2), ('V - MODEL', 0, 1)]
        source = ('<table>' + ''.join(
            '<tr><td>{}</td><td>{}</td><td>{}</td><td>100%</td></tr>'
            .format(*row) for row in rows) + '</table>').encode()
        generated = {}
        exec(self.generator.generate(source), generated)
        self.assertEqual(generated['MODEL_OFFSETS'], {
            'V - MODEL': ((6, 4), (30, 4), (0, 1))})
        with self.assertRaises(ValueError):
            self.generator.generate(b'<html>not a drive table</html>')
