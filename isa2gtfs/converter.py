import csv
import logging
import os
import yaml
import zipfile

class IsaGtfsConverter:

    def __init__(self, config_filename=None, dialect='init51'):
        self._dialect = dialect
        
        if config_filename is not None:
            with open(config_filename, 'r') as config_file:
                self._config = yaml.safe_load(config_file)
        else:
            self._config = dict()

            self._config['config'] = dict()
            self._config['config']['extract_zone_ids'] = False
            self._config['config']['extract_platform_codes'] = True
            self._config['config']['generate_feed_info'] = True
            self._config['config']['generate_feed_start_date'] = True
            self._config['config']['generate_feed_end_date'] = True
            self._config['config']['write_feed_id'] = False

            self._config['default'] = dict()
            self._config['default']['agency_url'] = 'https://gtfs.org'
            self._config['default']['agency_timezone'] = 'Europe/Berlin'
            self._config['default']['agency_lang'] = 'de-DE'
            self._config['default']['feed_info'] = dict()
            self._config['default']['feed_info']['feed_publisher_name'] = 'YourCompanyName'
            self._config['default']['feed_info']['feed_publisher_url'] = 'https://yourdomain.dev'
            self._config['default']['feed_info']['feed_contact_url'] = 'https://yourdomain.dev/contact'
            self._config['default']['feed_info']['feed_contact_email'] = 'contact@yourdomain.dev'
            self._config['default']['feed_info']['feed_version'] = '%Y%m%d%H%M%S'
            self._config['default']['feed_info']['feed_lang'] = 'de-DE'
            self._config['default']['feed_info']['default_lang'] = 'de-DE'

            self._config['mapping'] = dict()
            self._config['mapping']['feed_id'] = 'COM'
            self._config['mapping']['station_id'] = '[stationInternationalId]_Parent'
            self._config['mapping']['stop_id'] = '[stopInternationalId]'
            self._config['mapping']['service_id'] = 'service-[serviceId]'
            self._config['mapping']['agency_id'] = 'agency-[agencyId]'
            self._config['mapping']['route_id'] = '[routeInternationalId]'
            self._config['mapping']['trip_id'] = '[routeId][tripId]'

        self._txt_files = list()
        
    def convert(self, input, output):
        
        if input.endswith('.zip'):
            input_directory = os.path.dirname(input)
        else:
            input_directory = input

        if output.endswith('.zip'):
            output_directory = os.path.dirname(output)
        else:
            output_directory = output
        
        if input.endswith('.zip'):
            logging.info(f"unpacking ZIP archive {input} ...")

            with zipfile.ZipFile(input, 'r') as zip_file:
                zip_file.extractall(input_directory)

        if self._dialect == 'init51':
            from isa2gtfs.dialect import init51
            init51.convert(self, input_directory, output_directory)
        else:
            logging.error(f"unknown dialect {self._dialect}")

        if output.endswith('.zip'):
            logging.info(f"creating ZIP archive {output} ...")

            with zipfile.ZipFile(output, 'w') as zip_file:
                for txt_file in self._txt_files:
                    zip_file.write(
                        txt_file,
                        os.path.basename(txt_file),
                        compress_type=zipfile.ZIP_DEFLATED
                    )

                    os.remove(txt_file)

        if input.lower().endswith('.zip'):
            for file in os.listdir(input_directory):
                if file.lower().endswith('.asc') or file.lower().endswith('.txt'):
                    os.remove(os.path.join(input_directory, file))
    
    def _write_txt_file(self, txt_filename, txt_headers, txt_data):
        self._txt_files.append(txt_filename)
        
        with open(txt_filename, 'w', newline='', encoding='utf-8') as txt_file:
            csv_writer = csv.writer(txt_file, delimiter=',', quotechar='"')
            csv_writer.writerow(txt_headers)
            csv_writer.writerows(txt_data)
                