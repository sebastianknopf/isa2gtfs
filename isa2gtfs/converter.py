import csv
import logging
import yaml

class IsaGtfsConverter:

    def __init__(self, config_filename=None, dialect='init51'):
        self._dialect = dialect
        
        if config_filename is not None:
            with open(config_filename, 'r') as config_file:
                self._config = yaml.safe_load(config_file)
        else:
            self._config = dict()

            self._config['default'] = dict()
            self._config['default']['agency_url'] = 'https://gtfs.org'
            self._config['default']['agency_timezone'] = 'Europe/Berlin'

            self._config['mapping'] = dict()
            self._config['mapping']['station_id'] = '[stationInternationalId]_Parent'
            self._config['mapping']['stop_id'] = '[stopInternationalId]'
            self._config['mapping']['service_id'] = 'service-[serviceId]'
            self._config['mapping']['agency_id'] = 'agency-[agencyId]'
            self._config['mapping']['route_id'] = '[routeInternationalId]'
            self._config['mapping']['trip_id'] = '[routeId][tripId]'
        
    def convert(self, input_directory, output_directory):
        if self._dialect == 'init51':
            from isa2gtfs.dialect import init51
            init51.convert(self, input_directory, output_directory)
        else:
            logging.error(f"unknown dialect {self._dialect}")
    
    def _write_txt_file(self, txt_filename, txt_headers, txt_data):
        with open(txt_filename, 'w', newline='', encoding='utf-8') as txt_file:
            csv_writer = csv.writer(txt_file, delimiter=',', quotechar='"')
            csv_writer.writerow(txt_headers)
            csv_writer.writerows(txt_data)
                