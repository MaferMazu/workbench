''' view_pcap_deep worker '''
import zerorpc
import pprint
import os


class ViewPcapDeep(object):
    ''' ViewPcapDeep: Generates a view for a pcap sample (depends on Bro)'''
    dependencies = ['view_pcap']

    def __init__(self):
        ''' Initialization of ViewPcapDeep '''
        self.workbench = zerorpc.Client(timeout=300, heartbeat=60)
        self.workbench.connect("tcp://127.0.0.1:4242")

    def execute(self, input_data):
        ''' ViewPcapDeep execute method '''

        # Copy info from input
        view = input_data['view_pcap']

        # Grab a couple of handles
        extracted_files = input_data['view_pcap']['extracted_files']

        # Dump a couple of fields
        del view['extracted_files']        

        # Grab additional info about the extracted files
        view['extracted_files'] = [self.workbench.work_request('meta_deep', md5, 
            ['md5', 'sha256', 'entropy', 'ssdeep', 'file_size', 'file_type']) for md5 in extracted_files]

        return view

    def __del__(self):
        ''' Class Cleanup '''
        # Close zeroRPC client
        self.workbench.close()


# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' view_pcap_deep.py: Unit test'''

    # This worker test requires a local server running
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../data/pcap/winmediaplayer.pcap')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'winmedia.pcap', 'pcap')
    input_data = workbench.work_request('view_pcap', md5)

    # Execute the worker (unit test)
    worker = ViewPcapDeep()
    output = worker.execute(input_data)
    print('\n<<< Unit Test >>>')
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('view_pcap_deep', md5)
    print('\n<<< Server Test >>>')
    pprint.pprint(output)

if __name__ == "__main__":
    test()
