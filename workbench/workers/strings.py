
''' Strings worker '''
import re
import pprint

class Strings(object):
    ''' This worker extracts all the strings from any type of file '''
    dependencies = ['sample']

    def __init__(self):
        ''' Initialize the Strings worker '''
        self.find_strings = re.compile(r'[^\x00-\x1F\x7F-\xFF]{4,}', re.MULTILINE)

    def execute(self, input_data):
        ''' Execute the Strings worker '''
        raw_bytes = input_data['sample']['raw_bytes']
        strings = self.find_strings.findall(raw_bytes)
        return {'string_list': strings}

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' strings.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../data/pe/bad/033d91aae8ad29ed9fbb858179271232')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad_pe', 'exe')
    input_data = workbench.get_sample(md5)

    # Execute the worker (unit test)
    worker = Strings()
    output = worker.execute(input_data)
    print('\n<<< Unit Test >>>')
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('strings', md5)
    print('\n<<< Server Test >>>')
    pprint.pprint(output)

if __name__ == "__main__":
    test()
