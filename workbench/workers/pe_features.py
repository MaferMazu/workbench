''' PE Features worker. This class pulls static features
    out of a PE file using the python pefile module.
'''
import pefile
import pprint


class PEFileWorker(object):
    ''' Create instance of PEFileWorker class. This class pulls static
        features out of a PE file using the python pefile module.
    '''
    dependencies = ['sample', 'tags']

    def __init__(self, verbose=False):
        ''' Init method '''

        # Dense feature list: this only functions to ensure that all of these
        #               features get extracted with a sanity check at the end.
        self._dense_feature_list = None
        self._dense_features = None

        # Okay now the sparse fields
        self._sparse_feature_list = None
        self._sparse_features = None

        # Verbose
        self._verbose = verbose

        # Warnings handle
        self._warnings = []

        # Set the features that I'm expected PE File to extract, note this is just
        # for sanity checking, meaning that if you don't get some of these features
        # the processing will spit out warnings for each feature not extracted.
        self.set_dense_features(['check_sum', 'generated_check_sum', 'compile_date', 'debug_size', 'export_size',
                                 'iat_rva', 'major_version', 'minor_version', 'number_of_bound_import_symbols',
                                 'number_of_bound_imports', 'number_of_export_symbols', 'number_of_import_symbols',
                                 'number_of_imports', 'number_of_rva_and_sizes', 'number_of_sections', 'pe_warnings',
                                 'std_section_names', 'total_size_pe', 'virtual_address', 'virtual_size',
                                 'virtual_size_2', 'datadir_IMAGE_DIRECTORY_ENTRY_BASERELOC_size',
                                 'datadir_IMAGE_DIRECTORY_ENTRY_RESOURCE_size',
                                 'datadir_IMAGE_DIRECTORY_ENTRY_IAT_size', 'datadir_IMAGE_DIRECTORY_ENTRY_IMPORT_size',
                                 'pe_char', 'pe_dll', 'pe_driver', 'pe_exe', 'pe_i386', 'pe_majorlink', 
                                 'pe_minorlink', 'sec_entropy_data', 'sec_entropy_rdata',
                                 'sec_entropy_reloc', 'sec_entropy_text', 'sec_entropy_rsrc', 'sec_rawptr_rsrc',
                                 'sec_rawsize_rsrc', 'sec_vasize_rsrc', 'sec_raw_execsize', 'sec_rawptr_data',
                                 'sec_rawptr_text', 'sec_rawsize_data', 'sec_rawsize_text', 'sec_va_execsize',
                                 'sec_vasize_data', 'sec_vasize_text', 'size_code', 'size_image', 'size_initdata',
                                 'size_uninit'])

        self.set_sparse_features(['imported_symbols', 'section_names', 'pe_warning_strings'])

    def execute(self, input_data):

        ''' Process the input bytes with pefile '''
        raw_bytes = input_data['sample']['raw_bytes']

        # Have the PE File module process the file
        pefile_handle, error_str = self.open_using_pefile('unknown', raw_bytes)
        if not pefile_handle:
            return {'error': error_str, 'dense_features': [], 'sparse_features': []}

        # Now extract the various features using pefile
        dense_features, sparse_features = self.extract_features_using_pefile(pefile_handle)

        # Okay set my response
        return {'dense_features': dense_features, 'sparse_features': sparse_features, 'tags': input_data['tags']['tags']}

    def set_dense_features(self, dense_feature_list):
        ''' Set the dense feature list that the Python pefile module should extract.
            This is really just sanity check functionality, meaning that these
            are the features you are expecting to get, and a warning will spit
            out if you don't get some of these. '''
        self._dense_feature_list = dense_feature_list

    def get_dense_features(self):
        ''' Set the dense feature list that the Python pefile module should extract. '''
        return self._dense_features

    def set_sparse_features(self, sparse_feature_list):
        ''' Set the sparse feature list that the Python pefile module should extract.
            This is really just sanity check functionality, meaning that these
            are the features you are expecting to get, and a warning will spit
            out if you don't get some of these. '''
        self._sparse_feature_list = sparse_feature_list

    def get_sparse_features(self):
        ''' Set the sparse feature list that the Python pefile module should extract. '''
        return self._sparse_features

    # Make sure pe can parse this file
    @staticmethod
    def open_using_pefile(input_name, input_bytes):
        ''' Open the PE File using the Python pefile module. '''
        try:
            pef = pefile.PE(data=input_bytes, fast_load=False)
        except (AttributeError, pefile.PEFormatError) as error:
            print('warning: pe_fail (with exception from pefile module) on file: %s' % input_name)
            error_str = '(Exception):, %s' % (str(error))
            return None, error_str

        # Now test to see if the features are there/extractable if not return FAIL flag
        if pef.PE_TYPE is None or pef.OPTIONAL_HEADER is None or len(pef.OPTIONAL_HEADER.DATA_DIRECTORY) < 7:
            print('warning: pe_fail on file: %s' % input_name)
            error_str = 'warning: pe_fail on file: %s' % input_name
            return None, error_str

        # Success
        return pef, None

    # Extract various set of features using PEfile module
    def extract_features_using_pefile(self, pef):
        ''' Process the PE File using the Python pefile module. '''

        # Store all extracted features into feature lists
        extracted_dense = {}
        extracted_sparse = {}

        # Now slog through the info and extract the features
        feature_not_found_flag = -99
        feature_default_value = 0
        self._warnings = []

        # Set all the dense features and sparse features to 'feature not found'
        # value and then check later to see if it was found
        for feature in self._dense_feature_list:
            extracted_dense[feature] = feature_not_found_flag
        for feature in self._sparse_feature_list:
            extracted_sparse[feature] = feature_not_found_flag

        # Check to make sure all the section names are standard
        std_sections = ['.text', '.bss', '.rdata', '.data', '.rsrc', '.edata', '.idata',
                        '.pdata', '.debug', '.reloc', '.stab', '.stabstr', '.tls',
                        '.crt', '.gnu_deb', '.eh_fram', '.exptbl', '.rodata']
        for i in range(200):
            std_sections.append('/'+str(i))
        std_section_names = 1
        extracted_sparse['section_names'] = []
        for section in pef.sections:
            name = convert_to_ascii_null_term(section.Name).lower()
            extracted_sparse['section_names'].append(name)
            if name not in std_sections:
                std_section_names = 0

        extracted_dense['std_section_names'] = std_section_names
        extracted_dense['debug_size'] = pef.OPTIONAL_HEADER.DATA_DIRECTORY[6].Size
        extracted_dense['major_version'] = pef.OPTIONAL_HEADER.MajorImageVersion
        extracted_dense['minor_version'] = pef.OPTIONAL_HEADER.MinorImageVersion
        extracted_dense['iat_rva']	 = pef.OPTIONAL_HEADER.DATA_DIRECTORY[1].VirtualAddress
        extracted_dense['export_size'] = pef.OPTIONAL_HEADER.DATA_DIRECTORY[0].Size
        extracted_dense['check_sum'] = pef.OPTIONAL_HEADER.CheckSum
        try:
            extracted_dense['generated_check_sum'] = pef.generate_checksum()
        except ValueError:
            extracted_dense['generated_check_sum'] = 0
        if len(pef.sections) > 0:
            extracted_dense['virtual_address'] = pef.sections[0].VirtualAddress
            extracted_dense['virtual_size'] = pef.sections[0].Misc_VirtualSize
        extracted_dense['number_of_sections'] = pef.FILE_HEADER.NumberOfSections
        extracted_dense['compile_date'] = pef.FILE_HEADER.TimeDateStamp
        extracted_dense['number_of_rva_and_sizes'] = pef.OPTIONAL_HEADER.NumberOfRvaAndSizes
        extracted_dense['total_size_pe'] = len(pef.__data__)

        # Number of import and exports
        if hasattr(pef, 'DIRECTORY_ENTRY_IMPORT'):
            extracted_dense['number_of_imports'] = len(pef.DIRECTORY_ENTRY_IMPORT)
            num_imported_symbols = 0
            for module in pef.DIRECTORY_ENTRY_IMPORT:
                num_imported_symbols += len(module.imports)
            extracted_dense['number_of_import_symbols'] = num_imported_symbols

        if hasattr(pef, 'DIRECTORY_ENTRY_BOUND_IMPORT'):
            extracted_dense['number_of_bound_imports'] = len(pef.DIRECTORY_ENTRY_BOUND_IMPORT)
            num_imported_symbols = 0
            for module in pef.DIRECTORY_ENTRY_BOUND_IMPORT:
                num_imported_symbols += len(module.entries)
            extracted_dense['number_of_bound_import_symbols'] = num_imported_symbols

        if hasattr(pef, 'DIRECTORY_ENTRY_EXPORT'):
            try:
                extracted_dense['number_of_export_symbols'] = len(pef.DIRECTORY_ENTRY_EXPORT.symbols)
                symbol_set = set()
                for symbol in pef.DIRECTORY_ENTRY_EXPORT.symbols:
                    symbol_info = 'unknown'
                    if not symbol.name:
                        symbol_info = 'ordinal=' + str(symbol.ordinal)
                    else:
                        symbol_info = 'name=' + symbol.name
                    symbol_set.add(convert_to_utf8('%s' % (symbol_info)).lower())

                # Now convert set to list and add to features
                extracted_sparse['ExportedSymbols'] = list(symbol_set)

            except AttributeError:
                extracted_sparse['ExportedSymbols'] = ['AttributeError']

        # Specific Import info (Note this will be a sparse field woo hoo!)
        if hasattr(pef, 'DIRECTORY_ENTRY_IMPORT'):
            symbol_set = set()
            for module in pef.DIRECTORY_ENTRY_IMPORT:
                for symbol in module.imports:
                    symbol_info = 'unknown'
                    if symbol.import_by_ordinal is True:
                        symbol_info = 'ordinal=' + str(symbol.ordinal)
                    else:
                        symbol_info = 'name=' + symbol.name
                        # symbol_info['hint'] = symbol.hint
                    if symbol.bound:
                        symbol_info += ' bound=' + str(symbol.bound)

                    symbol_set.add(convert_to_utf8('%s:%s' % (module.dll, symbol_info)).lower())

            # Now convert set to list and add to features
            extracted_sparse['imported_symbols'] = list(symbol_set)

        # Do we have a second section
        if len(pef.sections) >= 2:
            extracted_dense['virtual_size_2'] = pef.sections[1].Misc_VirtualSize

        extracted_dense['size_image'] = pef.OPTIONAL_HEADER.SizeOfImage
        extracted_dense['size_code'] = pef.OPTIONAL_HEADER.SizeOfCode
        extracted_dense['size_initdata'] = pef.OPTIONAL_HEADER.SizeOfInitializedData
        extracted_dense['size_uninit'] = pef.OPTIONAL_HEADER.SizeOfUninitializedData
        extracted_dense['pe_majorlink'] = pef.OPTIONAL_HEADER.MajorLinkerVersion
        extracted_dense['pe_minorlink'] = pef.OPTIONAL_HEADER.MinorLinkerVersion
        extracted_dense['pe_driver'] = 1 if pef.is_driver() else 0
        extracted_dense['pe_exe'] = 1 if pef.is_exe() else 0
        extracted_dense['pe_dll'] = 1 if pef.is_dll() else 0
        extracted_dense['pe_i386'] = 1
        if pef.FILE_HEADER.Machine != 0x014c:
            extracted_dense['pe_i386'] = 0
        extracted_dense['pe_char'] = pef.FILE_HEADER.Characteristics

        # Data directory features!!
        datadirs = { 
            0: 'IMAGE_DIRECTORY_ENTRY_EXPORT', 1: 'IMAGE_DIRECTORY_ENTRY_IMPORT', 
            2: 'IMAGE_DIRECTORY_ENTRY_RESOURCE', 5: 'IMAGE_DIRECTORY_ENTRY_BASERELOC', 
            12: 'IMAGE_DIRECTORY_ENTRY_IAT'}
        for idx, datadir in list(datadirs.items()):
            datadir = pefile.DIRECTORY_ENTRY[idx]
            if len(pef.OPTIONAL_HEADER.DATA_DIRECTORY) <= idx:
                continue

            directory = pef.OPTIONAL_HEADER.DATA_DIRECTORY[idx]
            extracted_dense['datadir_%s_size' % datadir] = directory.Size

        # Section features
        section_flags = ['IMAGE_SCN_MEM_EXECUTE', 'IMAGE_SCN_CNT_CODE', 'IMAGE_SCN_MEM_WRITE', 'IMAGE_SCN_MEM_READ']
        rawexecsize = 0
        vaexecsize = 0
        for sec in pef.sections:
            if not sec:
                continue

            for char in section_flags:
                # does the section have one of our attribs?
                if hasattr(sec, char):
                    rawexecsize += sec.SizeOfRawData
                    vaexecsize += sec.Misc_VirtualSize
                    break

            # Take out any weird characters in section names
            secname = convert_to_ascii_null_term(sec.Name).lower()
            secname = secname.replace('.', '')
            if secname in std_sections:
                extracted_dense['sec_entropy_%s' % secname] = sec.get_entropy()
                extracted_dense['sec_rawptr_%s' % secname] = sec.PointerToRawData
                extracted_dense['sec_rawsize_%s' % secname] = sec.SizeOfRawData
                extracted_dense['sec_vasize_%s' % secname] = sec.Misc_VirtualSize

        extracted_dense['sec_va_execsize'] = vaexecsize
        extracted_dense['sec_raw_execsize'] = rawexecsize

        # Imphash (implemented in pefile 1.2.10-139 or later)
        try:
            extracted_sparse['imp_hash'] = pef.get_imphash()
        except AttributeError:
            extracted_sparse['imp_hash'] = 'Not found: Install pefile 1.2.10-139 or later'

        # Register if there were any pe warnings
        warnings = pef.get_warnings()
        if warnings:
            extracted_dense['pe_warnings'] = 1
            extracted_sparse['pe_warning_strings'] = warnings
        else:
            extracted_dense['pe_warnings'] = 0

        # Issue a warning if the feature isn't found
        for feature in self._dense_feature_list:
            if extracted_dense[feature] == feature_not_found_flag:
                extracted_dense[feature] = feature_default_value
                if (self._verbose):
                    print('info: Feature: %s not found! Setting to %d' % (feature, feature_default_value))

        # Issue a warning if the feature isn't found
        for feature in self._sparse_feature_list:
            if extracted_sparse[feature] == feature_not_found_flag:
                extracted_sparse[feature] = []  # For sparse data probably best default
                if (self._verbose):
                    print('info: Feature: %s not found! Setting to %d' % (feature, feature_default_value))

        # Set the features for the class var
        self._dense_features = extracted_dense
        self._sparse_features = extracted_sparse

        return self.get_dense_features(), self.get_sparse_features()

# Helper functions
def convert_to_utf8(string):
    ''' Convert string to UTF8 '''
    if (isinstance(string, str)):
        return string.encode('utf-8')
    try:
        u = str(string, 'utf-8')
    except TypeError:
        return str(string)
    utf8 = u.encode('utf-8')
    return utf8

def convert_to_ascii_null_term(string):
    ''' Convert string to Null terminated ascii '''
    string = string.split('\x00', 1)[0]
    return string.decode('ascii', 'ignore')


# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' pe_features.py: Test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect('tcp://127.0.0.1:4242')

    # Generate 3 different inputs for the worker (better coverage)
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../data/pe/bad/033d91aae8ad29ed9fbb858179271232')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad_pe', 'exe')
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../data/pe/good/4be7ec02133544cde7a580875e130208')
    md5_2 = workbench.store_sample(open(data_path, 'rb').read(), 'good_pe', 'exe')
    input_data = workbench.get_sample(md5)
    input_data.update(workbench.work_request('tags', md5))
    input_data_2 = workbench.get_sample(md5_2)
    input_data_2.update(workbench.work_request('tags', md5_2))
    input_data_3 = {'sample': {'raw_bytes': 'invalid pe file to hit exception code'}}

    # Execute the worker (unit test)
    worker = PEFileWorker()
    output = worker.execute(input_data)
    print('\n<<< Unit Test >>>')
    pprint.pprint(output)    

    # For code coverage
    output = worker.execute(input_data_2)
    output = worker.execute(input_data_3)

    # Execute the worker (server test)
    output = workbench.work_request('pe_features', md5)
    print('\n<<< Server Test >>>')
    pprint.pprint(output)


if __name__ == "__main__":
    test()
