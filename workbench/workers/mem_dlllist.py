
''' Memory Image DllList worker. This worker utilizes the Rekall Memory Forensic Framework.
    See Google Github: http://github.com/google/rekall
    All credit for good stuff goes to them, all credit for bad stuff goes to us. :)
'''
import os
import hashlib
import collections
import pprint
from .rekall_adapter.rekall_adapter import RekallAdapter

class MemoryImageDllList(object):
    ''' This worker computes dlllist for memory image files. '''
    dependencies = ['sample']

    def __init__(self):
        ''' Initialization '''
        self.plugin_name = 'dlllist'
        self.current_table_name = 'dlllist'
        self.output = {'tables': collections.defaultdict(list)}
        self.column_map = {}

    @staticmethod
    def safe_key(key):
        return key.replace('.','_')

    def parse_base(self, base_data):
        """Parse the Base object we get from some rekall output"""
        base = base_data['Base']['target']
        return {'Base': base}

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
                if line['data']['name']:
                    self.current_table_name = str(line['data']['name'][1].v())
            elif line['type'] == 't': # New Table Headers (column names)
                self.column_map = {item['cname']: item['name'] if 'name' in item else item['cname'] for item in line['data']}
            elif line['type'] == 'r': # Row

                # Add the row to our current table
                row = RekallAdapter.process_row(line['data'], self.column_map)
                self.output['tables'][self.current_table_name].append(row)

                # Process Base entries
                if 'Base' in row:
                    base_info = self.parse_base(row)
                    row.update(base_info)
            else:
                print('Got unknown line %s: %s' % (line['type'], line['data']))

        # All done
        return self.output

# Unit test: Create the class, the proper input and run the execute() method for a test
import pytest
#pylint: disable=no-member
@pytest.mark.xfail
#pylint: enable=no-member
def test():
    ''' mem_dlllist.py: Test '''

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
    worker = MemoryImageDllList()
    output = worker.execute({'sample':{'raw_bytes':raw_bytes}})
    print('\n<<< Unit Test >>>')
    print('Meta: %s' % output['meta'])
    for name, table in output['tables'].items():
        print('\nTable: %s' % name)
        pprint.pprint(table)
    assert 'Error' not in output

    # Execute the worker (server test)
    output = workbench.work_request('mem_dlllist', md5)['mem_dlllist']
    print('\n<<< Server Test >>>')
    print('Meta: %s' % output['meta'])
    for name, table in output['tables'].items():
        print('\nTable: %s' % name)
        pprint.pprint(table)
    assert 'Error' not in output


if __name__ == "__main__":
    test()
