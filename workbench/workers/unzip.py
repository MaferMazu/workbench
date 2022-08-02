
''' Unzip worker '''
import zipfile
import zerorpc
import pprint
import os
try:
    from io import StringIO
except ImportError:
    from io import StringIO

class Unzip(object):
    ''' This worker unzips a zipped file '''
    dependencies = ['sample']

    def __init__(self):
        self.workbench = zerorpc.Client(timeout=300, heartbeat=60)
        self.workbench.connect("tcp://127.0.0.1:4242")

    def execute(self, input_data):
        ''' Execute the Unzip worker '''
        raw_bytes = input_data['sample']['raw_bytes']
        zipfile_output = zipfile.ZipFile(StringIO(raw_bytes))
        payload_md5s = []
        for name in zipfile_output.namelist():
            filename = os.path.basename(name)
            payload_md5s.append(self.workbench.store_sample(zipfile_output.read(name), name, 'unknown'))
        return {'payload_md5s': payload_md5s}

    def __del__(self):
        ''' Class Cleanup '''
        # Close zeroRPC client
        self.workbench.close()

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' unzip.py: Unit test'''

    # This worker test requires a local server running
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/zip/bad.zip')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad.zip', 'zip')
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/zip/good.zip')
    md5_2 = workbench.store_sample(open(data_path, 'rb').read(), 'good.zip', 'zip')
    input_data = workbench.get_sample(md5)
    input_data_2 = workbench.get_sample(md5_2)    

    # Execute the worker (unit test)
    worker = Unzip()
    output = worker.execute(input_data)
    print('\n<<< Unit Test >>>')
    pprint.pprint(output)

    # For coverage
    output = worker.execute(input_data_2)

    # Execute the worker (server test)
    output = workbench.work_request('unzip', md5)
    print('\n<<< Server Test >>>')
    pprint.pprint(output)

if __name__ == "__main__":
    test()
