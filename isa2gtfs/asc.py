import csv
import os

from isa2gtfs.ascdef import name2def

########################################################################################################################
# Helper class for reading and modifying *.asc files.
########################################################################################################################

def read_asc_file(filename):
    asc_file = AscFile()
    asc_file.read(filename)
    
    return asc_file
    
    
def create_asc_file(filename):
    asc_file = AscFile(filename)
    
    return asc_file

class AscFile:

    def __init__(self, filename=None):
        self.null_value = 'NULL'
        self.strict = False
        
        self._internal_init()

    def read(self, filename):
        self._filename = filename
        self._definition = name2def(os.path.basename(filename))
        
        if self._definition is None:
            pass
            
        if 'DIMENSIONS' in self._definition:
            self._dimensions = {
                'NUM_DIMENSIONS': 0, 
                'REPEAT_FROM': self._definition['DIMENSIONS']['REPEAT_FROM']
            }
        else:
            self._dimensions = None        
    
        with open(self._filename, newline='') as asc_file:
            asc_reader = csv.reader(asc_file, delimiter='#', quotechar='"')
            
            ptr_header = 0
            lst_record_group = None
            
            for index, asc_row in enumerate(asc_reader):
                if 'HEADER' in self._definition:
                    if index == ptr_header:
                        
                        # add last record group if available
                        if lst_record_group is not None:
                            self.records.append(lst_record_group)
                        
                        lst_record_group = list()
                        
                        # read header entry
                        entry = self._read_entry(asc_row, self._definition['HEADER'])
                        self.headers.append(entry)
                        
                        # check whether we're monitoring dimensions and update number of dimensions for the next subset
                        if self._dimensions is not None:
                            self._dimensions['NUM_DIMENSIONS'] = entry[self._definition['DIMENSIONS']['INDICATOR']]
                        
                        # set next header pointer value
                        ptr_header = ptr_header + entry[self._definition['INCREMENTOR']] + 1
                    else:
                        # add record only to record group
                        lst_record_group.append(
                            self._read_entry(asc_row, self._definition['DATA'], self._dimensions)
                        )
                else:
                    # there's no header handling, simply add the record
                    self.records.append(
                        self._read_entry(asc_row, self._definition['DATA'])
                    )
            
            # if there were headers handled, add the last remaining record group
            if lst_record_group is not None:
                self.records.append(lst_record_group)
                    
                        
    def write(self, filename=None):
        if filename == None:
            filename = self._filename
    
        with open(filename, 'w', newline='') as asc_file:
            asc_writer = csv.writer(asc_file, delimiter='#', quotechar='"', lineterminator='#\n')
            
            if len(self.headers) > 0:
                for index, header in enumerate(self.headers):                
                    asc_headers = list()
                    for header_key, header_value in header.items():
                        def_dtype = self._definition['HEADER'][list(header.keys()).index(header_key)][1]
                        def_dlen = self._definition['HEADER'][list(header.keys()).index(header_key)][2]
                        
                        asc_headers.append(self._create_value(header_value, def_dtype, def_dlen))
                    
                    asc_writer.writerow(asc_headers)
                
                    for record in self.records[index]:
                        asc_values = list()
                        for record_key, record_value in record.items():
                            if record_key == 'DIMENSIONS':
                                for dimension in record_value:
                                    for dimension_key, dimension_value in dimension.items():
                                        index = next((i for i, item in enumerate(self._definition['DATA']) if item[0] == dimension_key), -1)
                                        def_dtype = self._definition['DATA'][index][1]
                                        def_dlen = self._definition['DATA'][index][2]
                                        
                                        asc_values.append(self._create_value(dimension_value, def_dtype, def_dlen))
                            else:
                                def_dtype = self._definition['DATA'][list(record.keys()).index(record_key)][1]
                                def_dlen = self._definition['DATA'][list(record.keys()).index(record_key)][2]
                                
                                asc_values.append(self._create_value(record_value, def_dtype, def_dlen))
                        
                        asc_writer.writerow(asc_values)               
            else:
                for record in self.records:
                    asc_values = list()
                    for record_key, record_value in record.items():
                        def_dtype = self._definition['DATA'][list(record.keys()).index(record_key)][1]
                        def_dlen = self._definition['DATA'][list(record.keys()).index(record_key)][2]
                        
                        asc_values.append(self._create_value(record_value, def_dtype, def_dlen))
                    
                    asc_writer.writerow(asc_values)  
            
    def find_header(self, hdata, primary_key, foreign_key):
        header_pkfields = self._create_compare_record(hdata, primary_key)

        for index, header in enumerate(self.headers):
            compare_header = self._create_compare_record(header, foreign_key)

            if set(header_pkfields.values()) == set(compare_header.values()):
                return index, header
            
        return -1, None
    
    def find_record(self, rdata, primary_key, foreign_key):
        record_pkfields = self._create_compare_record(rdata, primary_key)
        
        for record in self.records:
            compare_record = self._create_compare_record(record, foreign_key)
            if set(record_pkfields.values()) == set(compare_record.values()):
                return record
                
        return None
    
    def add_record(self, rdata, primary_key=None):
        """record_existing = False
        record_pkfields = self._create_compare_record(rdata, primary_key)
        for i in range(len(self.records)):
            compare_record = self._create_compare_record(self.records[i], primary_key)
            
            if record_pkfields == compare_record:
                record_existing = True
                break
                
        if not record_existing:
            self.records.append(rdata)"""
            
    def remove_records(self, rdata, primary_key=None):
        """updated_records = list()
        for i in range(len(self.records)):
            compare_record = self._create_compare_record(self.records[i], primary_key)
            
            if rdata != compare_record:
                updated_records.append(self.records[i])
                
        self.records = updated_records"""
            
    def replace_foreign_keys(self, foreign_key_columns, repl_map):
        for i in range(len(self.records)):
            original_record = self.records[i]
            updated_record = dict(original_record)
            
            updated = False
            for fkc in foreign_key_columns:
                if original_record[fkc] in repl_map:
                    updated_record[fkc] = repl_map[original_record[fkc]]
                    updated = True
                    
            if updated:
                self.records[i] = updated_record
            
    def close(self):
        self._internal_init()
        
    def _internal_init(self):
        
        self._filename = None
        self._definition = None
        
        self.headers = list()
        self.records = list()
                          
            
    def _create_value(self, val, dtype=str, dlen=0):            
        if dtype == bool:
            value = '1' if val == True else '0'
        else:
            value = str(val)
        
        if not value == '':
            if dtype == int or dtype == float:
                value = value.rjust(dlen, ' ')
            else:
                value = value.ljust(dlen, ' ')
            
        return value
            

    def _read_entry(self, row_data, definition, dimensions=None):
        entry = dict()
        
        if dimensions is not None:
            dimensions_index = [i for i, k in enumerate(definition) if k[0] == dimensions['REPEAT_FROM']][0]
            dimension_size = len(definition) - dimensions_index     
        
        for index, def_obj in enumerate(definition):
                def_key = def_obj[0]
                def_dtype = def_obj[1]
                def_optional = def_obj[3]
                
                if dimensions is not None and index >= dimensions_index:
                    if 'DIMENSIONS' not in entry:
                        entry['DIMENSIONS'] = list()
                        
                    for d in range(0, dimensions['NUM_DIMENSIONS']):
                        if len(entry['DIMENSIONS']) <= d:
                            entry['DIMENSIONS'].append(dict())
                            
                        entry['DIMENSIONS'][d][def_key] = self._read_value(
                            row_data[index + dimension_size * d],
                            def_dtype,
                            def_optional
                        )
                else:
                    entry[def_key] = self._read_value(row_data[index], def_dtype, def_optional)
            
        return entry
        
    def _read_value(self, val, dtype, optional):
        val = val.strip()
        
        if dtype == str:
            if not optional and val == '':
                raise ValueError(f"column must not be empty")
            
            return val
        elif dtype == int:
            if optional and not val == '':
                return int(val)
            elif optional and val == '':
                return val
            elif not optional:
                return int(val)
        elif dtype == float:
            if optional and not val == '':
                return float(val)
            elif optional and val == '':
                return val
            elif not optional:
                return float(val)
        elif dtype == bool:
            if not optional and val == '':
                raise ValueError(f"column {def_key} must not be empty")
                
            return True if val == '1' else False

    def _create_compare_record(self, record, primary_key):
        if primary_key is not None:
            compare_record = dict(record)
            for k in record:
                if k not in primary_key:
                    del compare_record[k]
                        
            return compare_record
        else:
            return record
