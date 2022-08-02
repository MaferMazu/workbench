''' view_pcap worker '''
import zerorpc
import pprint
import os

class ViewPcap(object):
    ''' ViewPcap: Generates a view for a pcap sample (depends on Bro)'''
    dependencies = ['pcap_bro']

    def __init__(self):
        self.workbench = zerorpc.Client(timeout=300, heartbeat=60)
        self.workbench.connect("tcp://127.0.0.1:4242")

    def execute(self, input_data):
        ''' Execute '''
        view = {}

        # Grab logs from Bro
        view['bro_logs'] = {key: input_data['pcap_bro'][key] for key in list(input_data['pcap_bro'].keys()) if '_log' in key}

        # Grab logs from Bro
        view['extracted_files'] = input_data['pcap_bro']['extracted_files']

        return view

    def __del__(self):
        ''' Class Cleanup '''
        # Close zeroRPC client
        self.workbench.close()

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' view_pcap.py: Unit test'''

    # This worker test requires a local server running
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../data/pcap/winmediaplayer.pcap')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'winmedia.pcap', 'pcap')
    input_data = workbench.work_request('pcap_bro', md5)

    # Execute the worker (unit test)
    worker = ViewPcap()
    output = worker.execute(input_data)
    print('\n<<< Unit Test >>>')
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('view_pcap', md5)
    print('\n<<< Server Test >>>')
    pprint.pprint(output)

if __name__ == "__main__":
    test()
