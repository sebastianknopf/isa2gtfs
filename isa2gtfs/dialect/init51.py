import logging
import os

from datetime import datetime, date, timedelta

from isa2gtfs.asc import read_asc_file

_stop_id_map = dict()
_agency_id_map = dict()
_route_id_map = dict()

_service_id_map = dict()

def convert(converter_context, input_directory, output_directory):
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
            
            _stop_id_map[station['ID']] = stop_id
            
        else: # we have a stop point with parent location here ...
            
            # find parent station at first
            parent = asc_halteste.find_record(station, ['ParentID', 'ParentDelivererID'], ['ID', 'DelivererID'])
            if parent is None:
                logging.error('could not find parent station')
            
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
            
            _stop_id_map[station['ID']] = stop_id
            
    logging.info('creating stops.txt ...')
    converter_context.write_txt_file(
        os.path.join(output_directory, 'stops.txt'),
        ['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'location_type', 'parent_station'],
        txt_stops
    )

    # create agency.txt
    logging.info('loading BETRIEBSTEILE.ASC ...')
    asc_betriebsteile = read_asc_file(os.path.join(input_directory, 'BETRIEBSTEILE.ASC'))
    asc_betriebe = read_asc_file(os.path.join(input_directory, 'BETRIEBE.ASC'))
    logging.info(f"found {len(asc_betriebsteile.records)} operator organisations and {len(asc_betriebe.records)} operators - converting now ...")
    
    txt_agencies = list()
    for operator_organisation in asc_betriebsteile.records:
        operator = asc_betriebe.find_record(operator_organisation, ['OperatorID'], ['ID'])

        agency_id = operator['ID']
        agency_id = f"vpe-{agency_id}"
        
        agency_name = operator['Name']
        agency_url = 'https://www.vpe.de'
        agency_timezone = 'Europe/Berlin'
            
        txt_agencies.append([
            agency_id,
            agency_name,
            agency_url,
            agency_timezone
        ])
        
        _agency_id_map[operator_organisation['ID']] = agency_id
        
    logging.info('creating agency.txt ...')
    converter_context.write_txt_file(
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
        agency_id = _agency_id_map[route['OperatorOrganisationID']]
        route_short_name = route['Name']
        
        if route['VehicleTypeGroup'] == 'Bus':
            route_type = '3'
        elif route['VehicleTypeGroup'] == 'U-Bahn':
            route_type = '1'
        elif route['VehicleTypeGroup'] == 'S-Bahn':
            route_type = '2'
        elif route['VehicleTypeGroup'] == 'R-Bahn':
            route_type = '2'
        elif route['VehicleTypeGroup'] == 'Tram':
            route_type = '0'
        elif route['VehicleTypeGroup'] == 'Zug':
            route_type = '2'
        elif route['VehicleTypeGroup'] == 'Fähre':
            route_type = '4'
        elif route['VehicleTypeGroup'] == 'Seilbahn':
            route_type = '6'
        else:
            logging.warn(f"route type {route['VehicleTypeGroup']} not supported by GTFS - route type set to 0 (TRAM) for {route_id}")
            route_type = '0'
            
        txt_routes.append([
            route_id,
            agency_id,
            route_short_name,
            route_type
        ])
        
        _route_id_map[route['LineNumber']] = route_id
        
    logging.info('creating routes.txt ...')
    converter_context.write_txt_file(
        os.path.join(output_directory, 'routes.txt'),
        ['route_id', 'agency_id', 'route_short_name', 'route_type'],
        txt_routes
    )

    # create trips.txt and stop_times.txt

    txt_trips = list()
    txt_stop_times = list()
    for route in asc_linien.records:

        logging.info(f"loading FD{route['LineNumber']}.ASC ...")
        asc_fdxxxxxx = read_asc_file(os.path.join(input_directory, f"FD{route['LineNumber']}.ASC"))

        logging.info(f"loading LD{route['LineNumber']}.ASC ...")
        asc_ldxxxxxx = read_asc_file(os.path.join(input_directory, f"LD{route['LineNumber']}.ASC"))

        # process each trip of this line
        for sub_line_index, sub_line in enumerate(asc_fdxxxxxx.headers):

            logging.info(f"found LineNumber-LineVersionNumber-SubLineNumber-DirectionID ({sub_line['LineNumber']}-{sub_line['LineVersionNumber']}-{sub_line['SubLineNumber']}-{sub_line['DirectionID']}) - converting {sub_line['NumTrips']} trips now ...")
        
            ldxxxxxx_index, ldxxxxxx_header = asc_ldxxxxxx.find_header(
                sub_line, 
                ['LineNumber', 'LineVersionNumber', 'OperatorOrganisationID', 'DirectionID', 'SubLineNumber'],
                ['LineNumber', 'LineVersionNumber', 'OperatorOrganisationID', 'DirectionID', 'SubLineNumber']
            )

            ldxxxxxx_records = asc_ldxxxxxx.records[ldxxxxxx_index]

            # extract basic trip data 
            for trip in asc_fdxxxxxx.records[sub_line_index]:
                route_id = _route_id_map[route['LineNumber']]
                service_id = 'NONE'
                
                if trip['InternationalTripID'] is not None and not trip['InternationalTripID'] == '':
                    trip_id = trip['InternationalTripID']
                else:
                    trip_id = f"de:vpe:{trip['ID']}"

                trip_headsign = ''
                trip_short_name = trip['ExternalTripNumber']
                direction_id = sub_line['DirectionID']

                # empty default values
                block_id = ''
                shape_id = ''
                wheelchair_accessible = ''
                bikes_allowed = ''

                # extract travel times from corresponding ldxxxxxx
                time_demand_type_index = trip['TimeDemandType']
                time_demand_type_index = int(time_demand_type_index) - 1
                
                last_departure_time = trip['StartTime']
                last_stop_id = None
                
                for sub_line_item in ldxxxxxx_records:
                    
                    time_demand_type = sub_line_item['DIMENSIONS'][time_demand_type_index]

                    travel_duration_seconds = _duration2seconds(time_demand_type['TravelTime'])
                    waiting_duration_seconds = _duration2seconds(time_demand_type['WaitingTime'])

                    arrival_time = last_departure_time
                    departure_time = _datetime_add_seconds(arrival_time, waiting_duration_seconds)

                    stop_id = _stop_id_map[sub_line_item['StopID']]
                    stop_sequence = sub_line_item['ConsecutiveNumber']

                    if time_demand_type['NoEntry'] == '1':
                        pickup_type = '1'
                    elif time_demand_type['DemandStop'] == '1':
                        pickup_type = '3'
                    else:
                        pickup_type = '0'

                    if time_demand_type['NoExit'] == '1':
                        drop_off_type = '1'
                    elif time_demand_type['DemandStop'] == '1':
                        drop_off_type = '3'
                    else:
                        drop_off_type = '0'

                    # empty default values
                    shape_dist_travelled = '0'

                    txt_stop_times.append([
                        trip_id,
                        arrival_time,
                        departure_time,
                        stop_id,
                        stop_sequence,
                        pickup_type,
                        drop_off_type,
                        shape_dist_travelled
                    ])

                    # set next travel time
                    last_departure_time = _datetime_add_seconds(departure_time, travel_duration_seconds)
                    last_stop_id = sub_line_item['StopID']

                # add trip dataset after generating stop times
                trip_headsign_stop = asc_halteste.find_record({'ID': last_stop_id}, ['ID'], ['ID'])
                if trip_headsign_stop is not None:
                    trip_headsign_station = asc_halteste.find_record(trip_headsign_stop, ['ParentID', 'ParentDelivererID'], ['ID', 'DelivererID'])
                    if trip_headsign_station is not None:
                        trip_headsign = trip_headsign_station['LongName']

                txt_trips.append([
                    route_id,
                    service_id,
                    trip_id,
                    trip_headsign,
                    trip_short_name,
                    direction_id,
                    block_id,
                    shape_id,
                    wheelchair_accessible,
                    bikes_allowed
                ])

    logging.info('creating trips.txt ...')
    converter_context.write_txt_file(
        os.path.join(output_directory, 'trips.txt'),
        ['route_id', 'service_id', 'trip_id', 'trip_headsign', 'trip_short_name', 'direction_id', 'block_id', 'shape_id', 'wheelchair_accessible', 'bikes_allowed'],
        txt_trips
    )

    logging.info('creating stop_times.txt ...')
    converter_context.write_txt_file(
        os.path.join(output_directory, 'stop_times.txt'),
        ['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence', 'pickup_type', 'drop_off_type', 'shape_dist_travelled'],
        txt_stop_times
    )

    
    """# create calendar_dates.txt
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
        
        bitfield_data = _hex2bin(bitfield['BitField'])            
        for index, day in enumerate(_daterange(version_start_date, version_end_date)):                
            if bitfield_data[index] == '1':
                
                exception_type = '1'
            
                txt_calendar_dates.append([
                    service_id,
                    day.strftime('%Y%m%d'),
                    exception_type
                ])
                
        _service_id_map[bitfield['ID']] = service_id
        
    logging.info('creating calendar_dates.txt ...')
    converter_context.write_txt_file(
        os.path.join(output_directory, 'calendar_dates.txt'),
        ['service_id', 'date', 'exception_type'],
        txt_calendar_dates
    )""" 
        
def _daterange(start_date: date, end_date: date):
    days = int((end_date - start_date).days)
    for n in range(days):
        yield start_date + timedelta(n)

def _duration2seconds(input_string: str):
    minutes, seconds = input_string.split(':')
    minutes = int(minutes)
    seconds = int(seconds)

    return seconds + (minutes * 60)

def _datetime_add_seconds(input_datetime, seconds):
    input_datetime = input_datetime.replace('.', ':')
    hours, rest = input_datetime.split(':', 1)

    timestamp = timedelta(hours=int(hours)) + datetime.strptime(rest, "%M:%S")
    timestamp = timestamp + timedelta(seconds=seconds)

    remainder = int(int(hours) + (seconds / 60 / 60))
    if remainder > 23:
        return f"{remainder}:{timestamp.strftime('%M:%S')}"
    else:
        return timestamp.strftime('%H:%M:%S')

def _hex2bin(hexrepr):
    byterepr = bytes.fromhex(hexrepr)
    bitrepr = ''
    for irepr in byterepr:
        bitrepr = bitrepr + f'{irepr:08b}'
        
    return bitrepr