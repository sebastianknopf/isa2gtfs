import csv
import logging

class IsaGtfsConverter:

    def __init__(self, dialect='init51'):
        self._dialect = dialect
        
    def convert(self, input_directory, output_directory):
        if self._dialect == 'init51':
            from isa2gtfs.dialect import init51
            init51.convert(self, input_directory, output_directory)
        else:
            logging.error(f"unknown dialect {self._dialect}")
    
    def write_txt_file(self, txt_filename, txt_headers, txt_data):
        with open(txt_filename, 'w', newline='', encoding='utf-8') as txt_file:
            csv_writer = csv.writer(txt_file, delimiter=',', quotechar='"')
            csv_writer.writerow(txt_headers)
            csv_writer.writerows(txt_data)
                