import csv
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT: Path = Path(__file__).resolve().parents[1]
SRC: Path = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from isa2gtfs.converter import IsaGtfsConverter


class ConverterTests(unittest.TestCase):
    def test_default_config_matches_expected_values(self) -> None:
        converter: IsaGtfsConverter = IsaGtfsConverter()

        self.assertFalse(converter._config['config']['extract_zone_ids'])
        self.assertTrue(converter._config['config']['extract_platform_codes'])
        self.assertFalse(converter._config['config']['extract_notices'])
        self.assertTrue(converter._config['config']['generate_feed_info'])
        self.assertTrue(converter._config['config']['generate_feed_start_date'])
        self.assertTrue(converter._config['config']['generate_feed_end_date'])
        self.assertFalse(converter._config['config']['generate_feed_id'])

        self.assertEqual(converter._config['default']['agency_url'], 'https://gtfs.org')
        self.assertEqual(converter._config['default']['agency_timezone'], 'Europe/Berlin')
        self.assertEqual(converter._config['default']['agency_lang'], 'de-DE')

        self.assertEqual(converter._config['mapping']['feed_id'], 'COM')
        self.assertEqual(converter._config['mapping']['trip_id'], '[routeId][tripId]')
        self.assertEqual(converter._config['mapping']['notice_id'], '[noticeId]')

    def test_write_txt_file_writes_csv(self) -> None:
        converter: IsaGtfsConverter = IsaGtfsConverter()
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file: str = os.path.join(tmp_dir, 'out.txt')

            converter._write_txt_file(
                output_file,
                ['col1', 'col2'],
                [['a', 'b'], ['c', 'd']],
            )

            with open(output_file, newline='', encoding='utf-8') as handle:
                rows: list[list[str]] = list(csv.reader(handle))

            self.assertEqual(rows[0], ['col1', 'col2'])
            self.assertEqual(rows[1], ['a', 'b'])
            self.assertEqual(rows[2], ['c', 'd'])

    @mock.patch('isa2gtfs.converter.os.remove')
    @mock.patch('isa2gtfs.converter.os.listdir')
    @mock.patch('isa2gtfs.dialect.ivustandard.convert')
    @mock.patch('isa2gtfs.converter.zipfile.ZipFile')
    def test_convert_zip_paths_calls_dialect_and_cleanup(
        self,
        mock_zip_file: mock.MagicMock,
        mock_ivustandard_convert: mock.MagicMock,
        mock_listdir: mock.MagicMock,
        mock_remove: mock.MagicMock,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            input_directory: str = os.path.join(tmp_dir, 'input')
            output_directory: str = os.path.join(tmp_dir, 'output')
            os.makedirs(input_directory)
            os.makedirs(output_directory)

            input_zip: str = os.path.join(input_directory, 'input.zip')
            output_zip: str = os.path.join(output_directory, 'output.zip')

            in_ctx: mock.MagicMock = mock.MagicMock()
            in_zip: mock.MagicMock = mock.MagicMock()
            in_ctx.__enter__.return_value = in_zip

            out_ctx: mock.MagicMock = mock.MagicMock()
            out_zip: mock.MagicMock = mock.MagicMock()
            out_ctx.__enter__.return_value = out_zip

            mock_zip_file.side_effect = [in_ctx, out_ctx]
            mock_listdir.return_value = ['A.ASC', 'B.txt', 'ignore.bin']

            converter: IsaGtfsConverter = IsaGtfsConverter()
            generated_1: str = os.path.join(output_directory, 'a.txt')
            generated_2: str = os.path.join(output_directory, 'b.txt')
            converter._txt_files = [generated_1, generated_2]

            converter.convert(input_zip, output_zip)

            in_zip.extractall.assert_called_once_with(input_directory)
            mock_ivustandard_convert.assert_called_once_with(converter, input_directory, output_directory)

            out_zip.write.assert_any_call(generated_1, 'a.txt', compress_type=mock.ANY)
            out_zip.write.assert_any_call(generated_2, 'b.txt', compress_type=mock.ANY)

            mock_remove.assert_any_call(generated_1)
            mock_remove.assert_any_call(generated_2)
            mock_remove.assert_any_call(os.path.join(input_directory, 'A.ASC'))
            mock_remove.assert_any_call(os.path.join(input_directory, 'B.txt'))

    @mock.patch('isa2gtfs.converter.logging.error')
    def test_convert_with_unknown_dialect_logs_error(self, mock_log_error: mock.MagicMock) -> None:
        converter: IsaGtfsConverter = IsaGtfsConverter(dialect='unknown')
        converter.convert('input_dir', 'output_dir')

        mock_log_error.assert_called_once_with('unknown dialect unknown')


if __name__ == '__main__':
    unittest.main()
