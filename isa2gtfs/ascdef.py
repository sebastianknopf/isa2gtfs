import os

########################################################################################################################
# Definition of header and data lines in *.asc files.
########################################################################################################################

def name2def(filename):
    filename = os.path.basename(filename)
    filename = filename.split('.')[0]
    
    if filename == 'VERSIONE':
        return VERSIONS        
    elif filename == 'BITFELD':
        return BITFIELD
    elif filename == 'HALTESTE':
        return STATIONS
    elif filename == 'TARIF':
        return FARES
    elif filename == 'BETRIEBE':
        return OPERATORS
    elif filename == 'BETRIEBSTEILE':
        return OPERATOR_ORGANISATIONS
    elif filename == 'LINIEN':
        return LINES
    elif filename == 'LVATTRIB':
        return LINE_VERSION_ATTRIBUTES
    elif filename.startswith('LD'):
        return LDXXXXXX
    elif filename.startswith('LF'):
        return LFXXXXXX
    elif filename == 'FAHRTATT':
        return TRIP_ATTRIBUTES
    elif filename.startswith('FD'):
        return FDXXXXXX
    elif filename == 'FPLTAB':
        return TIMETABLE
    elif filename == 'VERKEHRM':
        return VEHICLE_TYPES
    else:
        return None


VERSIONS = {
    'DATA': [
        ('ID', int, 10, False),
        ('Name', str, 60, False),
        ('StartDate', str, 10, False),
        ('EndDate', str, 10, False),
        ('BitfieldID', int, 10, True),
    ],
    'PRIMARY': {
        'DATA': [
            'ID'
        ]
    }
}

BITFIELD = {
    'DATA': [
        ('ID', int, 10, False),
        ('Bitfield', str, 255, False)
    ],
    'PRIMARY': {
        'DATA': [
            'ID'
        ]
    }
}

STATIONS = {
    'DATA': [
        ('ID', int, 10, False),
        ('DelivererID', str, 10, False),
        ('ParentID', int, 10, True),
        ('ParentDelivererID', str, 10, True),
        ('StationType', str, 2, True),
        ('Code', str, 8, True),
        ('Longitude', float, 10, True),
        ('Latitude', float, 10, True),
        ('MunicipalCode', str, 11, True),
        ('WheelchairAccessible', str, 1, True),
        ('LongName', str, 60, True),
        ('HeadsignText', str, 60, True),
        ('TimetableInformationName', str, 60, True),
        ('PrintingName', str, 60, True),
        ('KilometerInfo', int, 6, True),
        ('InterchangePriority', int, 2, True),
        ('ExportFlag', str, 2, True),
        ('ItcsNumber', int, 10, True),
        ('LocationType', str, 1, True),
        ('InternationalStationID', str, 60, True)
    ],
    'PRIMARY': {
        'DATA': [
            'ID',
            'DelivererID'
        ]
    }
}

FARES = {
    'DATA': [
        ('StationID', int, 10, False),
        ('DelivererID', str, 10, False),
        ('Area', str, 10, True)
    ],
    'PRIMARY': {
        'DATA': [
            'StationID',
            'DelivererID',
            'Area'
        ]
    }
}

OPERATORS = {
    'DATA': [
        ('ID', int, 10, False),
        ('OperatorNumber', int, 10, True),
        ('Code', str, 8, False),
        ('Name', str, 60, False),
        ('AdditionalName', str, 255, True),
        ('AddressID', int, 10, True),
        ('ShortName', str, 3, True),
        ('Logo', str, 255, True)
    ],
    'PRIMARY': {
        'DATA': [
            'ID'
        ]
    }
}

OPERATOR_ORGANISATIONS = {
    'DATA': [
        ('Code', str, 8, False),
        ('Name', str, 60, False),
        ('ID', str, 6, False),
        ('VehicleTypeGroup', str, 32, False),
        ('DelivererID', str, 10, False),
        ('OperatorID', int, 10, True),
        ('AddressID', int, 10, True),
        ('OrganisationNumber', int, 8, False)
    ],
    'PRIMARY': {
        'DATA': [
            'ID'
        ]
    }
}

LINES = {
    'DATA': [
        ('OperatorOrganisationID', str, 6, False),
        ('LineNumber', str, 32, False),
        ('Name', str, 32, True),
        ('Type', str, 3, True),
        ('VehicleTypeGroup', str, 32, True),
        ('InternationalLineID', str, 50, True),
        ('PseudoFlag', bool, 1, True),
        ('ExportNameFlag', bool, 1, True),
        ('TextColor', str, 6, True),
        ('BackgroundColor', str, 6, True),
        ('HafasLogo', str, 255, True),
        ('Comment', str, 255, True)        
    ],
    'PRIMARY': {
        'DATA': [
            'OperatorOrganisationID',
            'LineNumber'
        ]
    }
}

LINE_VERSION_ATTRIBUTES = {
    'DATA': [
        ('OperatorOrganisationID', str, 6, False),
        ('LineNumber', str, 8, False),
        ('LineVersionNumber', int, 10, False),
        ('AttributeID', str, 10, False),
        ('Value', str, 511, True),
        ('BitfieldID', int, 10, True),
        ('CalendarID', str, 4, True)     
    ],
    'PRIMARY': {
        'DATA': [
        ]
    }
}

LDXXXXXX = {
    'HEADER': [
        ('LineNumber', str, 32, False),
        ('LineVersionNumber', int, 10, False),
        ('LineVersionPriority', int, 3, False),
        ('OperatorOrganisationID', str, 6, False),
        ('SubLineNumber', int, 8, False),
        ('DirectionID', str, 2, False),
        ('NumStops', int, 3, False),
        ('NumTimeDemandTypes', int, 3, False),
        ('VehicleTypeID', str, 10, False),
        ('BitfieldID', int, 10, True)
    ],
    'DATA': [
        ('ConsecutiveNumber', int, 4, False),
        ('StopCode', str, 8, True),
        ('StopID', int, 10, False),
        ('Kilometers', int, 7, True),
        ('PositionSequenceArrivalTime', int, 4, True),
        ('PositionSequenceDepartureTime', int, 4, True),
        ('TravelTime', str, 6, False),
        ('WaitingTime', str, 6, False),
        ('NoEntry', bool, 1, True),
        ('NoExit', bool, 1, True),
        ('DemandStop', bool, 1, True)
    ],
    'PRIMARY': {
        'HEADER': [
            'LineNumber',
            'LineVersionNumber',
            'OperatorOrganisationID',
            'SubLineNumber',
            'DirectionID'
        ],
        'DATA': [
            'ConsecutiveNumber'
        ]
    },
    'INCREMENTOR': 'NumStops',
    'DIMENSIONS': {
        'INDICATOR': 'NumTimeDemandTypes',
        'REPEAT_FROM': 'TravelTime'
    }
}

LFXXXXXX = {
    'HEADER': [
        ('OperatorOrganisationID', str, 6, False),
        ('LineNumber', str, 32, False),
        ('DirectionID', str, 2, False),
        ('LineVersionNumber', int, 10, False),
        ('NumStops', int, 3, False)
    ],
    'DATA': [
        ('StopID', int, 10, False),
        ('ConsecutiveNumber', int, 4, False),
        ('DisplayBoldFlag', bool, 1, True),
        ('DisplayCursiveFlag', bool, 1, True),
        ('DisplayPostedTimetableFlag', bool, 1, True),
        ('DisplayGuidlineFlag', bool, 1, True),
        ('DisplayTimetableFlag', bool, 1, True),
        ('DisplayArrivalFlag', bool, 1, True),
        ('DisplayDepartureFlag', bool, 1, True),
        ('DisplayStopName', str, 60, True)
    ],
    'PRIMARY': {
        'HEADER': [
            'OperatorOrganisationID',
            'LineNumber',
            'DirectionID',
            'LineVersionNumber'
        ],
        'DATA': [
            'ConsecutiveNumber'
        ]
    },
    'INCREMENTOR': 'NumStops'
}

TRIP_ATTRIBUTES = {
    'DATA': [
        ('OperatorOrganisationID', str, 6, False),
        ('LineNumber', str, 8, False),
        ('DirectionID', str, 2, False),
        ('VersionNumber', int, 10, False),
        ('InternalTripNumber', str, 10, True),
        ('PositionSequenceFrom', int, 4, True),
        ('PositionSequenceTo', int, 4, True),      
        ('AttributeID', str, 10, False),      
        ('Value', str, 511, True),
        ('BitfieldID', int, 10, True),
        ('CalendarCode', str, 4, True)       
    ],
    'PRIMARY': {
        'DATA': [
        ]
    }
}

FDXXXXXX = {
    'HEADER': [
        ('LineNumber', str, 8, False),
        ('LineVersionNumber', int, 10, False),
        ('OperatorOrganisationID', str, 6, False),
        ('DirectionID', str, 2, False),
        ('SubLineNumber', int, 8, False),
        ('NumTrips', int, 10, False)
    ],
    'DATA': [
        ('PositionSequenceStartStop', int, 4, False),
        ('StartStopID', int, 10, False),
        ('StartTime', str, 8, False),
        ('PositionSequenceDestinationStop', int, 4, False),
        ('DestinationStopID', int, 10, False),
        ('ArrivalTime', str, 6, True),
        ('VehicleTypeID', str, 10, True),
        ('TimeDemandType', int, 3, False),
        ('ExternalTripNumber', str, 10, True),
        ('CalendarDayTypesTimetable', str, 7, True),
        ('NumFollowingTrips', int, 5, False),
        ('TimeSpanFollowingTrips', str, 7, False),
        ('BitfieldID', int, 10, True),
        ('ID', str, 10, True),
        ('Type', str, 3, True),
        ('InternationalTripID', str, 255, True),
        ('CalendarCode', str, 4, True)
    ],
    'PRIMARY': {
        'HEADER': [
            'LineNumber',
            'LineVersionNumber',
            'OperatorOrganisationID',
            'DirectionID',
            'SubLineNumber'
        ],
        'DATA': [
        ]
    },
    'INCREMENTOR': 'NumTrips'
}

TIMETABLE = {
    'DATA': [
        ('ID', int, 10, False),
        ('DelivererID', str, 10, False),
        ('VersionNumber', int, 10, False),
        ('LineNumberText', str, 32, False),
        ('LineCourseText', str, 1000, False),
        ('LineDirectionCode', str, 1, False),
        ('OperatorOrganisationID', str, 6, False),      
        ('LineNumber', str, 10, False),      
        ('DirectionID', str, 2, False),
        ('LineVersionNumber', int, 10, False)  
    ],
    'PRIMARY': {
        'DATA': [
            'ID',
            'LineDirectionCode'
        ]
    }
}

VEHICLE_TYPES = {
    'DATA': [
        ('ID', str, 10, False),
        ('VehicleTypeGroup', str, 32, True),
        ('VehicleTypeName', str, 50, True) 
    ],
    'PRIMARY': {
        'DATA': [
            'ID'
        ]
    }
}
