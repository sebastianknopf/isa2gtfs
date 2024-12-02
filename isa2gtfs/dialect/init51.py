import logging
import os

from datetime import datetime, date, timedelta

from isa2gtfs.asc import read_asc_file

_stop_id_map = dict()
_agency_id_map = dict()
_route_id_map = dict()

_version_map = dict()

_service_list = list()

def convert(converter_context, input_directory, output_directory):

    # load general attributes
    if converter_context._config['config']['extract_platform_codes']:
        logging.info('loading ATTRIBUT.ASC')
        asc_attribut = read_asc_file(os.path.join(input_directory, 'ATTRIBUT.ASC'))

        platform_code_attribute_id = asc_attribut.find_record({'ShortName': 'GLEIS'}, ['ShortName'],  ['ShortName'])
        if platform_code_attribute_id is not None:
            platform_code_attribute_id = platform_code_attribute_id['ID']
        else:
            logging.warning('could not determine platform_code attribute ID')

        logging.info('loading HSTATTRI.ASC ...')
        asc_hstattri = read_asc_file(os.path.join(input_directory, 'HSTATTRI.ASC'))
    else:
        platform_code_attribute_id = None

    # create stops.txt
    logging.info('loading HALTESTE.ASC ...')
    asc_halteste = read_asc_file(os.path.join(input_directory, 'HALTESTE.ASC'))  

    if converter_context._config['config']['extract_zone_ids']:
        logging.info('loading TARIF.ASC ...')
        asc_tarif = read_asc_file(os.path.join(input_directory, 'TARIF.ASC'))

    logging.info(f"found {len(asc_halteste.records)} stations - converting now ...")
    
    txt_stops = list()
    for station in asc_halteste.records:
        if station['InternationalStationID'] == '':
            logging.error(f"station {station['DelivererID']}-{station['ID']} has not assigned a international ID")
            return
    
        if station['ParentID'] == '': # we have a parent station here
            stop_id = converter_context._config['mapping']['station_id']
            stop_id = stop_id.replace('[stationInternationalId]', station['InternationalStationID'])
            
            stop_name = station['LongName']
            stop_lat = station['Latitude']
            stop_lon = station['Longitude']
            
            location_type = '1'
            parent_station = ''
            zone_id = ''
            platform_code = ''
            
            # create and register dataset
            txt_stops.append([
                stop_id,
                stop_name,
                stop_lat,
                stop_lon,
                location_type,
                parent_station,
                zone_id,
                platform_code
            ])
            
            _stop_id_map[station['ID']] = stop_id
            
        else: # we have a stop point with parent location here ...
            
            # find parent station at first
            parent = asc_halteste.find_record(station, ['ParentID', 'ParentDelivererID'], ['ID', 'DelivererID'])
            if parent is None:
                logging.error('could not find parent station')

            # find stop attribute for platform_code
            if platform_code_attribute_id is not None:
                platform_code_attribute = asc_hstattri.find_record({'ID': station['ID'], 'DelivererID': station['DelivererID'], 'AttributeID': platform_code_attribute_id}, ['ID', 'DelivererID', 'AttributeID'], ['ID', 'DelivererID', 'AttributeID'])
                
                if platform_code_attribute is not None:
                    platform_code = platform_code_attribute['AttributeValue']
                else:
                    platform_code = ''
            else:
                platform_code = ''
            
            stop_id = converter_context._config['mapping']['stop_id']
            stop_id = stop_id.replace('[stopInternationalId]', station['InternationalStationID'])
            
            stop_name = station['LongName']
            stop_lat = station['Latitude']
            stop_lon = station['Longitude']
            
            location_type = ''
            parent_station = converter_context._config['mapping']['station_id']
            parent_station = parent_station.replace('[stationInternationalId]', parent['InternationalStationID'])
            
            if converter_context._config['config']['extract_zone_ids']:
                zone_id_record = asc_tarif.find_record(station, ['ID', 'DelivererID'], ['StationID', 'DelivererID'])
                if zone_id_record is not None:
                    zone_id = zone_id_record['Area']
                else:
                    zone_id = ''
            else:
                zone_id = ''

            # create and register dataset
            txt_stops.append([
                stop_id,
                stop_name,
                stop_lat,
                stop_lon,
                location_type,
                parent_station,
                zone_id,
                platform_code
            ])
            
            _stop_id_map[station['ID']] = stop_id
            
    logging.info('creating stops.txt ...')
    converter_context._write_txt_file(
        os.path.join(output_directory, 'stops.txt'),
        ['stop_id', 'stop_name', 'stop_lat', 'stop_lon', 'location_type', 'parent_station', 'zone_id', 'platform_code'],
        txt_stops
    )

    # create agency.txt
    logging.info('loading BETRIEBSTEILE.ASC ...')
    asc_betriebsteile = read_asc_file(os.path.join(input_directory, 'BETRIEBSTEILE.ASC'))
    
    logging.info('loading BETRIEBE.ASC ...')
    asc_betriebe = read_asc_file(os.path.join(input_directory, 'BETRIEBE.ASC'))
    logging.info(f"found {len(asc_betriebsteile.records)} operator organisations and {len(asc_betriebe.records)} operators - converting now ...")
    
    txt_agencies = list()
    for operator_organisation in asc_betriebsteile.records:
        operator = asc_betriebe.find_record(operator_organisation, ['OperatorID'], ['ID'])

        agency_id = converter_context._config['mapping']['agency_id']
        agency_id = agency_id.replace('[agencyId]', str(operator['ID']))
        
        agency_name = operator['Name']
        agency_url = converter_context._config['default']['agency_url']
        agency_timezone = converter_context._config['default']['agency_timezone']
        agency_lang = converter_context._config['default']['agency_lang']
            
        txt_agencies.append([
            agency_id,
            agency_name,
            agency_url,
            agency_timezone,
            agency_lang
        ])
        
        _agency_id_map[operator_organisation['ID']] = agency_id
        
    logging.info('creating agency.txt ...')
    converter_context._write_txt_file(
        os.path.join(output_directory, 'agency.txt'),
        ['agency_id', 'agency_name', 'agency_url', 'agency_timezone', 'agency_lang'],
        txt_agencies
    )
    
    # create routes.txt
    logging.info('loading LINIEN.ASC ...')
    asc_linien = read_asc_file(os.path.join(input_directory, 'LINIEN.ASC'))
    logging.info(f"found {len(asc_linien.records)} routes - converting now ...")
    
    txt_routes = list()

    processed_lines = list()
    for route in asc_linien.records:

        # check whether this line number has already been processed - INIT writes the same line for each line version ...
        line_identifier = f"{route['OperatorOrganisationID']}-{route['LineNumber']}"
        if line_identifier in processed_lines:
            continue

        if route['InternationalLineID'] == '':
            logging.error(f"route {route['OperatorOrganisationID']}-{route['LineNumber']} has not assigned an international ID")
            return
            
        route_id = converter_context._config['mapping']['route_id']
        route_id = route_id.replace('[routeInternationalId]', route['InternationalLineID'])

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
            logging.warning(f"route type {route['VehicleTypeGroup']} not supported by GTFS - route type set to 0 (TRAM) for {route_id}")
            route_type = '0'
            
        txt_routes.append([
            route_id,
            agency_id,
            route_short_name,
            route_type
        ])
        
        _route_id_map[route['LineNumber']] = route_id

        # mark line as processed 
        processed_lines.append(line_identifier)
        
    logging.info('creating routes.txt ...')
    converter_context._write_txt_file(
        os.path.join(output_directory, 'routes.txt'),
        ['route_id', 'agency_id', 'route_short_name', 'route_type'],
        txt_routes
    )

    # create calendar_dates.txt, trips.txt and stop_times.txt
    logging.info('loading VERSIONE.ASC ...')
    asc_versione = read_asc_file(os.path.join(input_directory, 'VERSIONE.ASC'))

    for version in asc_versione.records:
        _version_map[version['ID']] = (
            datetime.strptime(version['StartDate'], '%d.%m.%Y'),
            datetime.strptime(version['EndDate'], '%d.%m.%Y'),
            version['BitfieldID']
        )

        if version['BitfieldID'] is None or version['BitfieldID'] == '':
            base_version_start_date = datetime.strptime(version['StartDate'], '%d.%m.%Y')
            base_version_end_date = datetime.strptime(version['EndDate'], '%d.%m.%Y')
    
    logging.info(f"base version starts at {base_version_start_date.strftime('%Y-%m-%d')} and ends at {base_version_end_date.strftime('%Y-%m-%d')}")
    
    logging.info('loading BITFELD.ASC ...')
    asc_bitfeld = read_asc_file(os.path.join(input_directory, 'BITFELD.ASC'))

    txt_trips = list()
    txt_stop_times = list()
    
    processed_lines = list()
    for route in asc_linien.records:

        # check whether this line number has already been processed - INIT writes the same line for each line version ...
        line_identifier = f"{route['OperatorOrganisationID']}-{route['LineNumber']}"
        if line_identifier in processed_lines:
            continue

        # beginn processing
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

            # extract bitfield of line version
            line_version_bitfield_id = _version_map[ldxxxxxx_header['LineVersionNumber']][2]
            if line_version_bitfield_id is not None and not line_version_bitfield_id == '':
                line_version_bitfield = asc_bitfeld.find_record({'ID': line_version_bitfield_id}, ['ID'], ['ID'])
                line_version_bitfield = _hex2bin(line_version_bitfield['Bitfield'])
            else:
                line_version_bitfield = _hex2bin('F' * 250)

            # extract basic trip data 
            for trip in asc_fdxxxxxx.records[sub_line_index]:
                route_id = _route_id_map[route['LineNumber']]

                # extract trip bitfield
                trip_bitfield = asc_bitfeld.find_record({'ID': trip['BitfieldID']}, ['ID'], ['ID'])
                trip_bitfield = _hex2bin(trip_bitfield['Bitfield'])

                # determine service bitfield out of line version bitfield and trip bitfield
                service_bitfield = _bitwise_and(line_version_bitfield, trip_bitfield)

                # line versioning can result in bitfields with zero days active - consider a trip only travelling a certain weekday and line version only valid for three other weekdays
                # if we have such a trip ... skip it
                if service_bitfield == _hex2bin('0' * 250):
                    continue

                if service_bitfield not in _service_list:
                    _service_list.append(service_bitfield)

                service_id = converter_context._config['mapping']['service_id']
                service_id = service_id.replace('[serviceId]', str(_service_list.index(service_bitfield)))
                
                trip_id = converter_context._config['mapping']['trip_id']
                trip_id = trip_id.replace('[tripRouteId]', route_id)
                trip_id = trip_id.replace('[tripId]', trip['ID'])
                trip_id = trip_id.replace('[tripInternationalId]', trip['InternationalTripID'])

                trip_headsign = ''
                trip_short_name = trip['ExternalTripNumber']

                direction_id = str(int(sub_line['DirectionID']) - 1)

                # empty default values
                block_id = ''
                shape_id = ''
                wheelchair_accessible = ''
                bikes_allowed = ''

                # extract travel times from corresponding ldxxxxxx
                time_demand_type_index = trip['TimeDemandType']
                time_demand_type_index = int(time_demand_type_index) - 1
                
                last_departure_time = trip['StartTime'].replace('.', ':')
                last_stop_id = None
                
                for sub_line_item in ldxxxxxx_records:
                    
                    time_demand_type = sub_line_item['DIMENSIONS'][time_demand_type_index]

                    travel_duration_seconds = _duration2seconds(time_demand_type['TravelTime'])
                    waiting_duration_seconds = _duration2seconds(time_demand_type['WaitingTime'])

                    arrival_time = last_departure_time
                    departure_time = _datetime_add_seconds(arrival_time, waiting_duration_seconds)

                    stop_id = _stop_id_map[sub_line_item['StopID']]
                    stop_sequence = sub_line_item['ConsecutiveNumber']

                    if time_demand_type['NoEntry']:
                        pickup_type = '1'
                    elif time_demand_type['DemandStop']:
                        pickup_type = '3'
                    else:
                        pickup_type = '0'

                    if time_demand_type['NoExit']:
                        drop_off_type = '1'
                    elif time_demand_type['DemandStop']:
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

        # mark line as processed 
        processed_lines.append(line_identifier)

    logging.info('creating trips.txt ...')
    converter_context._write_txt_file(
        os.path.join(output_directory, 'trips.txt'),
        ['route_id', 'service_id', 'trip_id', 'trip_headsign', 'trip_short_name', 'direction_id', 'block_id', 'shape_id', 'wheelchair_accessible', 'bikes_allowed'],
        txt_trips
    )

    logging.info('creating stop_times.txt ...')
    converter_context._write_txt_file(
        os.path.join(output_directory, 'stop_times.txt'),
        ['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence', 'pickup_type', 'drop_off_type', 'shape_dist_travelled'],
        txt_stop_times
    )

    # finally, create calendar_dates.txt out of bitfields
    txt_calendar_dates = list()
    for i, bitfield in enumerate(_service_list):
        service_id = converter_context._config['mapping']['service_id']
        service_id = service_id.replace('[serviceId]', str(i))
                   
        for c, day in enumerate(_daterange(base_version_start_date, base_version_end_date)):                
            if bitfield[c] == '1':
                
                exception_type = '1'
            
                txt_calendar_dates.append([
                    service_id,
                    day.strftime('%Y%m%d'),
                    exception_type
                ])

    logging.info('creating calendar_dates.txt ...')
    converter_context._write_txt_file(
        os.path.join(output_directory, 'calendar_dates.txt'),
        ['service_id', 'date', 'exception_type'],
        txt_calendar_dates
    )
        
def _daterange(start_date: date, end_date: date):
    days = int((end_date - start_date).days)
    for n in range(days):
        yield start_date + timedelta(n)

def _duration2seconds(input_string: str):
    minutes, seconds = input_string.split(':')
    minutes = int(minutes)
    seconds = int(seconds)

    return seconds + (minutes * 60)

def _datetime_add_seconds(input_datetime, add_seconds):
    input_datetime = input_datetime.replace('.', ':')
    hours, minutes, seconds = input_datetime.split(':')

    timestamp = timedelta(hours=int(hours)) + datetime.strptime(f"{minutes}:{seconds}", "%M:%S")
    timestamp = timestamp + timedelta(seconds=add_seconds)

    total_seconds = int(int(hours) * 3600 + int(minutes) * 60 + int(seconds) + add_seconds)
    if total_seconds >= (24 * 60 * 60):
        hours = int(total_seconds / 3600)
        return f"{hours}:{timestamp.strftime('%M:%S')}"
    else:
        return timestamp.strftime('%H:%M:%S')

def _hex2bin(hexrepr):
    byterepr = bytes.fromhex(hexrepr)
    bitrepr = ''
    for irepr in byterepr:
        bitrepr = bitrepr + f'{irepr:08b}'
        
    return bitrepr

def _bitwise_and(bitfield_a, bitfield_b):
    if not len(bitfield_a) == len(bitfield_b):
        raise ValueError(f"bitfield A and bitfield B must have exactly the same length")
    
    bitfield_r = ''
    for i in range(0, len(bitfield_a)):
        if bitfield_a[i] == '1' and bitfield_b[i] == '1':
            bitfield_r = bitfield_r + '1'
        else:
            bitfield_r = bitfield_r + '0'

    return bitfield_r