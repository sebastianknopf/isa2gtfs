import sys
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

ROOT: Path = Path(__file__).resolve().parents[1]
SRC: Path = ROOT / 'src'
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from isa2gtfs.dialect import ivustandard


class _FakeAscFile:
    def __init__(self, records: list[dict] | None = None) -> None:
        self.records: list[dict] = records or []

    def find_record(self, rdata: dict, primary_key: list[str], foreign_key: list[str]) -> dict | None:
        for record in self.records:
            if all(record.get(fk) == rdata.get(pk) for pk, fk in zip(primary_key, foreign_key)):
                return record
        return None


class IvuStandardHelperTests(unittest.TestCase):
    def test_daterange(self) -> None:
        days: list[date] = list(ivustandard._daterange(date(2024, 1, 1), date(2024, 1, 4)))
        self.assertEqual(days, [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)])

    def test_duration2seconds(self) -> None:
        self.assertEqual(ivustandard._duration2seconds('02:30'), 150)

    def test_datetime_add_seconds_same_day(self) -> None:
        self.assertEqual(ivustandard._datetime_add_seconds('12:00:30', 45), '12:01:15')

    def test_datetime_add_seconds_overflow(self) -> None:
        self.assertEqual(ivustandard._datetime_add_seconds('23:59:30', 90), '24:01:00')

    def test_hex2bin(self) -> None:
        self.assertEqual(ivustandard._hex2bin('0F'), '00001111')

    def test_bitwise_and(self) -> None:
        self.assertEqual(ivustandard._bitwise_and('1100', '1010'), '1000')

    def test_bitwise_and_length_mismatch_raises(self) -> None:
        with self.assertRaises(ValueError):
            ivustandard._bitwise_and('10', '101')


class IvuStandardConvertTests(unittest.TestCase):
    @mock.patch('isa2gtfs.dialect.ivustandard.logging.error')
    @mock.patch('isa2gtfs.dialect.ivustandard.read_asc_file')
    def test_convert_returns_early_on_missing_international_station_id(
        self,
        mock_read_asc_file: mock.MagicMock,
        mock_log_error: mock.MagicMock,
    ) -> None:
        converter_context: mock.MagicMock = mock.MagicMock()
        converter_context._config = {
            'config': {
                'extract_notices': False,
                'extract_platform_codes': False,
                'extract_zone_ids': False,
                'generate_feed_info': False,
                'generate_feed_start_date': False,
                'generate_feed_end_date': False,
                'generate_feed_id': False,
            },
            'default': {'feed_info': {}},
            'mapping': {
                'station_id': '[stationInternationalId]_Parent',
                'stop_id': '[stopInternationalId]',
                'service_id': 'service-[serviceId]',
                'agency_id': 'agency-[agencyId]',
                'route_id': '[routeInternationalId]',
                'trip_id': '[routeId][tripId]',
                'notice_id': '[noticeId]',
                'feed_id': 'COM',
            },
        }

        mock_read_asc_file.return_value = _FakeAscFile(
            records=[
                {
                    'InternationalStationID': '',
                    'DelivererID': 'D',
                    'ID': 1,
                    'ParentID': '',
                    'LongName': 'Name',
                    'Latitude': 1.0,
                    'Longitude': 2.0,
                }
            ]
        )

        result: None = ivustandard.convert(converter_context, 'in', 'out')

        self.assertIsNone(result)
        converter_context._write_txt_file.assert_not_called()
        mock_log_error.assert_called_once()


if __name__ == '__main__':
    unittest.main()
