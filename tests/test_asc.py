import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from isa2gtfs.asc import AscFile, create_asc_file, read_asc_file


class AscTests(unittest.TestCase):
    def test_read_asc_file_for_attributes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            asc_path = os.path.join(tmp_dir, 'ATTRIBUT.ASC')
            with open(asc_path, 'w', encoding='ISO-8859-1') as handle:
                handle.write('ID1#GLEIS#1\n')

            asc_file = read_asc_file(asc_path)

            self.assertEqual(len(asc_file.records), 1)
            self.assertEqual(asc_file.records[0]['ID'], 'ID1')
            self.assertEqual(asc_file.records[0]['ShortName'], 'GLEIS')
            self.assertTrue(asc_file.records[0]['IsMetaAttribute'])

    def test_create_asc_file_sets_filename(self) -> None:
        asc_file = create_asc_file('ATTRIBUT.ASC')
        self.assertIsNone(asc_file._filename)
        self.assertEqual(asc_file.null_value, 'NULL')

    def test_write_raises_value_error_with_current_csv_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source = os.path.join(tmp_dir, 'ATTRIBUT.ASC')
            with open(source, 'w', encoding='ISO-8859-1') as handle:
                handle.write('ID1#GLEIS#1\n')

            asc_file = read_asc_file(source)

            out_dir = os.path.join(tmp_dir, 'out')
            os.makedirs(out_dir)
            target = os.path.join(out_dir, 'ATTRIBUT.ASC')

            with self.assertRaises(ValueError):
                asc_file.write(target)

    def test_find_header_and_find_record(self) -> None:
        asc_file = AscFile()
        asc_file.headers = [{'HID': '1'}]
        asc_file.records = [[{'RID': '1', 'Value': 'A'}]]

        index, header = asc_file.find_header({'HID': '1'}, ['HID'], ['HID'])
        self.assertEqual(index, 0)
        self.assertEqual(header, {'HID': '1'})

        asc_records = AscFile()
        asc_records.records = [
            {'ID': '1', 'Name': 'foo'},
            {'ID': '2', 'Name': 'bar'},
        ]
        record = asc_records.find_record({'ID': '2'}, ['ID'], ['ID'])
        self.assertEqual(record, {'ID': '2', 'Name': 'bar'})

    def test_replace_foreign_keys(self) -> None:
        asc_file = AscFile()
        asc_file.records = [
            {'FK': 'A', 'Name': 'n1'},
            {'FK': 'B', 'Name': 'n2'},
        ]

        asc_file.replace_foreign_keys(['FK'], {'A': 'X'})

        self.assertEqual(asc_file.records[0]['FK'], 'X')
        self.assertEqual(asc_file.records[1]['FK'], 'B')

    def test_create_value_formats(self) -> None:
        asc_file = AscFile()

        self.assertEqual(asc_file._create_value(True, bool, 1), '1')
        self.assertEqual(asc_file._create_value(5, int, 3), '  5')
        self.assertEqual(asc_file._create_value('x', str, 3), 'x  ')

    def test_read_value_str_int_float(self) -> None:
        asc_file = AscFile()

        self.assertEqual(asc_file._read_value(' abc ', str, True), 'abc')
        self.assertEqual(asc_file._read_value(' 42 ', int, False), 42)
        self.assertEqual(asc_file._read_value(' 3.5 ', float, False), 3.5)
        self.assertEqual(asc_file._read_value('1', bool, True), True)

    def test_create_compare_record(self) -> None:
        asc_file = AscFile()
        record = {'A': 1, 'B': 2, 'C': 3}

        filtered = asc_file._create_compare_record(record, ['A', 'C'])
        self.assertEqual(filtered, {'A': 1, 'C': 3})

        all_fields = asc_file._create_compare_record(record, None)
        self.assertEqual(all_fields, record)


if __name__ == '__main__':
    unittest.main()
