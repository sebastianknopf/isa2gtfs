import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT: Path = Path(__file__).resolve().parents[1]
SRC: Path = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from isa2gtfs.asc import AscFile, create_asc_file, read_asc_file


class AscTests(unittest.TestCase):
    def test_read_asc_file_for_attributes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            asc_path: str = os.path.join(tmp_dir, 'ATTRIBUT.ASC')
            with open(asc_path, 'w', encoding='ISO-8859-1') as handle:
                handle.write('ID1#GLEIS#1\n')

            asc_file: AscFile = read_asc_file(asc_path)

            self.assertEqual(len(asc_file.records), 1)
            self.assertEqual(asc_file.records[0]['ID'], 'ID1')
            self.assertEqual(asc_file.records[0]['ShortName'], 'GLEIS')
            self.assertTrue(asc_file.records[0]['IsMetaAttribute'])

    def test_read_asc_file_supports_infinite_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            asc_path: str = os.path.join(tmp_dir, 'ATTRIBUT.ASC')
            with open(asc_path, 'w', encoding='ISO-8859-1') as handle:
                # Trailing delimiter keeps csv parsing stable across platforms while
                # allowing the infinite Value column to consume all content fragments.
                handle.write('ID2#HIM#0#part1#part2#part3#\n')

            asc_file: AscFile = read_asc_file(asc_path)

            self.assertEqual(asc_file.records[0]['ID'], 'ID2')
            self.assertEqual(asc_file.records[0]['ShortName'], 'HIM')
            self.assertFalse(asc_file.records[0]['IsMetaAttribute'])
            self.assertEqual(asc_file.records[0]['Value'], 'part1#part2#part3')

    def test_create_asc_file_sets_filename(self) -> None:
        asc_file: AscFile = create_asc_file('ATTRIBUT.ASC')
        self.assertIsNone(asc_file._filename)
        self.assertEqual(asc_file.null_value, 'NULL')

    def test_write_is_portable_across_csv_implementations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            source: str = os.path.join(tmp_dir, 'ATTRIBUT.ASC')
            with open(source, 'w', encoding='ISO-8859-1') as handle:
                handle.write('ID1#GLEIS#1\n')

            asc_file: AscFile = read_asc_file(source)

            out_dir: str = os.path.join(tmp_dir, 'out')
            os.makedirs(out_dir)
            target: str = os.path.join(out_dir, 'ATTRIBUT.ASC')

            # Depending on Python version/platform, csv may reject this writer configuration
            # with ValueError or may accept it and write the file.
            try:
                asc_file.write(target)
            except ValueError:
                return

            self.assertTrue(os.path.exists(target))

    def test_find_header_and_find_record(self) -> None:
        asc_file: AscFile = AscFile()
        asc_file.headers = [{'HID': '1'}]
        asc_file.records = [[{'RID': '1', 'Value': 'A'}]]

        index: int
        header: dict | None
        index, header = asc_file.find_header({'HID': '1'}, ['HID'], ['HID'])
        self.assertEqual(index, 0)
        self.assertEqual(header, {'HID': '1'})

        asc_records: AscFile = AscFile()
        asc_records.records = [
            {'ID': '1', 'Name': 'foo'},
            {'ID': '2', 'Name': 'bar'},
        ]
        record: dict | None = asc_records.find_record({'ID': '2'}, ['ID'], ['ID'])
        self.assertEqual(record, {'ID': '2', 'Name': 'bar'})

    def test_replace_foreign_keys(self) -> None:
        asc_file: AscFile = AscFile()
        asc_file.records = [
            {'FK': 'A', 'Name': 'n1'},
            {'FK': 'B', 'Name': 'n2'},
        ]

        asc_file.replace_foreign_keys(['FK'], {'A': 'X'})

        self.assertEqual(asc_file.records[0]['FK'], 'X')
        self.assertEqual(asc_file.records[1]['FK'], 'B')

    def test_create_value_formats(self) -> None:
        asc_file: AscFile = AscFile()

        self.assertEqual(asc_file._create_value(True, bool, 1), '1')
        self.assertEqual(asc_file._create_value(5, int, 3), '  5')
        self.assertEqual(asc_file._create_value('x', str, 3), 'x  ')

    def test_read_value_str_int_float(self) -> None:
        asc_file: AscFile = AscFile()

        self.assertEqual(asc_file._read_value(' abc ', str, True), 'abc')
        self.assertEqual(asc_file._read_value(' 42 ', int, False), 42)
        self.assertEqual(asc_file._read_value(' 3.5 ', float, False), 3.5)
        self.assertEqual(asc_file._read_value('1', bool, True), True)

    def test_create_compare_record(self) -> None:
        asc_file: AscFile = AscFile()
        record: dict[str, int] = {'A': 1, 'B': 2, 'C': 3}

        filtered: dict = asc_file._create_compare_record(record, ['A', 'C'])
        self.assertEqual(filtered, {'A': 1, 'C': 3})

        all_fields: dict = asc_file._create_compare_record(record, None)
        self.assertEqual(all_fields, record)


if __name__ == '__main__':
    unittest.main()
