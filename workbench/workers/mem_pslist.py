
''' Memory Image PSList worker. This worker utilizes the Rekall Memory Forensic Framework.
    See Google Github: http://github.com/google/rekall
    All credit for good stuff goes to them, all credit for bad stuff goes to us. :)
'''
import os
import hashlib
import collections
import pprint
from .rekall_adapter.rekall_adapter import RekallAdapter


class MemoryImagePSList(object):
    ''' This worker computes pslist-data for memory image files. '''
    dependencies = ['sample']

    def __init__(self):
        ''' Initialization '''
        self.plugin_name = 'pslist'
        self.current_table_name = 'pslist'
        self.output = {'tables': collections.defaultdict(list)}
        self.column_map = {}

    def parse_eprocess(self, eprocess_data):
        """Parse the EProcess object we get from some rekall output"""
        Name = eprocess_data['_EPROCESS']['Cybox']['Name']
        PID = eprocess_data['_EPROCESS']['Cybox']['PID']
        PPID = eprocess_data['_EPROCESS']['Cybox']['Parent_PID']
        return {'Name': Name, 'PID': PID, 'PPID': PPID}

    def execute(self, input_data):
        ''' Execute method '''

        # Spin up the rekall adapter
        adapter = RekallAdapter()
        adapter.set_plugin_name(self.plugin_name)
        rekall_output = adapter.execute(input_data)

        # Process the output data
        for line in rekall_output:

            if line['type'] == 'm':  # Meta
                self.output['meta'] = line['data']
            elif line['type'] == 's': # New Session (Table)
                self.current_table_name = line['data']['name'][1]
            elif line['type'] == 't': # New Table Headers (column names)
                self.column_map = {item['cname']: item['name'] if 'name' in item else item['cname'] for item in line['data']}
            elif line['type'] == 'r': # Row

                # Standard processing on the rekall row data
                row = RekallAdapter.process_row(line['data'], self.column_map)

                # Process _EPROCESS entries
                if '_EPROCESS' in row:
                    eprocess_info = self.parse_eprocess(row)
                    row.update(eprocess_info)
                    del row['_EPROCESS']

                # Add the row to our current table
                self.output['tables'][self.current_table_name].append(row)

        # All done
        return self.output

# Unit test: Create the class, the proper input and run the execute() method for a test
import pytest
#pylint: disable=no-member
@pytest.mark.xfail
#pylint: enable=no-member
def test():
    ''' mem_pslist.py: Test '''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Store the sample
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/memory_images/exemplar4.vmem')
    with open(data_path, 'rb') as mem_file:
        raw_bytes = mem_file.read()
        md5 = hashlib.md5(raw_bytes).hexdigest()
        if not workbench.has_sample(md5):
            md5 = workbench.store_sample(open(data_path, 'rb').read(), 'exemplar4.vmem', 'mem')

    # Execute the worker (unit test)
    worker = MemoryImagePSList()
    output = worker.execute({'sample':{'raw_bytes':raw_bytes}})
    print('\n<<< Unit Test >>>')
    print('Meta: %s' % output['meta'])
    for name, table in output['tables'].items():
        print('\nTable: %s' % name)
        pprint.pprint(table)
    assert 'Error' not in output

    # Execute the worker (server test)
    output = workbench.work_request('mem_pslist', md5)['mem_pslist']
    print('\n<<< Server Test >>>')
    print('Meta: %s' % output['meta'])
    for name, table in output['tables'].items():
        print('\nTable: %s' % name)
        pprint.pprint(table)
    assert 'Error' not in output


if __name__ == "__main__":
    test()
