import csv
import logging
import re
import os

from datetime import datetime, date, timedelta

from isa2gtfs.asc import read_asc_file

class IsaGtfsConverter:

    def __init__(self, dialect='init'):
        self._dialect = dialect
        
        self._stop_id_map = dict()
        self._service_id_map = dict()
        self._agency_id_map = dict()
        self._route_id_map = dict()
        
    def convert(self, input_directory, output_directory):
        
        if self._dialect == 'init':
            self._convert_init(input_directory, output_directory)
        else:
            logging.error(f"unknown dialect {self._dialect}")
            
    def _convert_init(self, input_directory, output_directory):
        
        # create stops.txt
        logging.info('loading HALTESTE.ASC ...')
        asc_halteste = read_asc_file(os.path.join(input_directory, 'HALTESTE.ASC'))        
        logging.info(f"found {len(asc_halteste.records)} stations - converting now ...")
        
        txt_stops = list()
        for station in asc_halteste.records:
            if station['GlobalID'] == '':
                logging.error(f"station {station['DelivererID']}-{station['ID']} has not assigned a international ID")
                return
        
            if station['ParentID'] == '': # we have a parent station here 
                stop_id = station['GlobalID']
                stop_id = f"{stop_id}_Parent"
                
                stop_name = station['LongName']
                stop_lat = station['Latitude']
                stop_lon = station['Longitude']
                
                location_type = '1'
                parent_station = ''
                
                # create and register dataset
                txt_stops.append([
                    stop_id,
                    stop_name,
                    stop_lat,
                    stop_lon,
                    location_type,
                    parent_station
                ])
                
                self._stop_id_map[station['ID']] = stop_id
                
            else: # we have a stop point with parent location here ...
                
                # find parent station at first
                parent = asc_halteste.find_record(station, ['ParentID', 'ParentDelivererID'], ['ID', 'DelivererID'])
                if parent is None:
                    logging.error('could not find parent')
                
                stop_id = station['GlobalID']
                
                stop_name = parent['LongName']
                stop_lat = station['Latitude']
                stop_lon = station['Longitude']
                
                location_type = ''
                parent_station = parent['GlobalID']
                parent_station = f"{parent_station}_Parent"
                
                # create and register dataset
                txt_stops.append([
                    stop_id,
                    stop_name,
                    stop_lat,
                    stop_lon,
                    location_type,
                    parent_station
                ])
                
                self._stop_id_map[station['ID']] = stop_id
                
        logging.info('creating stops.txt ...')
        self._write_txt_file(
            os.path.join(output_directory, 'stops.txt'),
            ['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'location_type', 'parent_station'],
            txt_stops
        )
        
        # create calendar_dates.txt
        logging.info('loading VERSIONE.ASC ...')
        asc_versione = read_asc_file(os.path.join(input_directory, 'VERSIONE.ASC'))
        
        if len(asc_versione.records) > 1:
            logging.error('multiple versions found')
        
        version_start_date = datetime.strptime(asc_versione.records[0]['StartDate'], '%d.%m.%Y')
        version_end_date = datetime.strptime(asc_versione.records[0]['EndDate'], '%d.%m.%Y')
        
        logging.info(f"version starts at {version_start_date.strftime('%Y-%m-%d')} and ends at {version_end_date.strftime('%Y-%m-%d')}")
        
        logging.info('loading BITFELD.ASC ...')
        asc_bitfeld = read_asc_file(os.path.join(input_directory, 'BITFELD.ASC'))
        logging.info(f"found {len(asc_bitfeld.records)} bitfields - converting now ...")
        
        txt_calendar_dates = list()
        for bitfield in asc_bitfeld.records:
            service_id = f"vpe-{bitfield['ID']}"
            
            bitfield_data = self._hex2bin(bitfield['BitField'])            
            for index, day in enumerate(self._daterange(version_start_date, version_end_date)):                
                if bitfield_data[index] == '1':
                    
                    exception_type = '1'
                
                    txt_calendar_dates.append([
                        service_id,
                        day.strftime('%Y%m%d'),
                        exception_type
                    ])
                    
            self._service_id_map[bitfield['ID']] = service_id
            
        logging.info('creating calendar_dates.txt ...')
        self._write_txt_file(
            os.path.join(output_directory, 'calendar_dates.txt'),
            ['service_id', 'date', 'exception_type'],
            txt_calendar_dates
        )
        
        # create agency.txt
        logging.info('loading BETRIEBSTEILE.ASC ...')
        asc_betriebsteile = read_asc_file(os.path.join(input_directory, 'BETRIEBSTEILE.ASC'))
        logging.info(f"found {len(asc_betriebsteile.records)} operator organisations - converting now ...")
        
        txt_agencies = list()
        for operator_organisation in asc_betriebsteile.records:
            agency_id = operator_organisation['ID']
            agency_id = f"vpe-{agency_id}"
            
            agency_name = operator_organisation['Name']
            agency_url = 'https://www.vpe.de'
            agency_timezone = 'Europe/Berlin'
                
            txt_agencies.append([
                agency_id,
                agency_name,
                agency_url,
                agency_timezone
            ])
            
            self._agency_id_map[operator_organisation['ID']] = agency_id
            
        logging.info('creating agency.txt ...')
        self._write_txt_file(
            os.path.join(output_directory, 'agency.txt'),
            ['agency_id', 'agency_name', 'agency_url', 'agency_timezone'],
            txt_agencies
        )
        
        # create routes.txt
        logging.info('loading LINIEN.ASC ...')
        asc_linien = read_asc_file(os.path.join(input_directory, 'LINIEN.ASC'))
        logging.info(f"found {len(asc_linien.records)} routes - converting now ...")
        
        txt_routes = list()
        for route in asc_linien.records:
            if route['InternationalID'] == '':
                logging.error(f"route {route['OperatorOrganisationID']}-{route['LineNumber']} has not assigned an international ID")
                return
                
            route_id = route['InternationalID']
            agency_id = self._agency_id_map[route['OperatorOrganisationID']]
            route_short_name = route['Name']
            
            if route['VehicleTypeGroup'] == 'Bus':
                route_type = '3'
                
            txt_routes.append([
                route_id,
                agency_id,
                route_short_name,
                route_type
            ])
            
            self._route_id_map[route['LineNumber']] = route_id
            
        logging.info('creating routes.txt ...')
        self._write_txt_file(
            os.path.join(output_directory, 'routes.txt'),
            ['route_id', 'agency_id', 'route_short_name', 'route_type'],
            txt_routes
        ) 
        
    def _daterange(self, start_date: date, end_date: date):
        days = int((end_date - start_date).days)
        for n in range(days):
            yield start_date + timedelta(n)
            
    def _hex2bin(self, hexrepr):
        byterepr = bytes.fromhex(hexrepr)
        bitrepr = ''
        for irepr in byterepr:
            bitrepr = bitrepr + f'{irepr:08b}'
            
        return bitrepr
    
    def _write_txt_file(self, txt_filename, txt_headers, txt_data):
        with open(txt_filename, 'w', newline='', encoding='utf-8') as txt_file:
            csv_writer = csv.writer(txt_file, delimiter=',', quotechar='"')
            csv_writer.writerow(txt_headers)
            csv_writer.writerows(txt_data)
                