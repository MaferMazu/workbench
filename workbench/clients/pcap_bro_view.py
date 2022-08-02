"""This client pulls PCAP 'views' (view summarize what's in a sample)."""

import zerorpc
import os
import pprint
from . import client_helper

def run():
    """This client pulls PCAP 'views' (view summarize what's in a sample)."""
    
    # Grab server args
    args = client_helper.grab_server_args()

    # Start up workbench connection
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect('tcp://'+args['server']+':'+args['port'])

    # Test out getting the raw Bro logs from a PCAP file
    # Note: you can get a super nice 'generator' python list of dict by using
    #       'stream_sample' instead of 'get_sample'.
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/pcap')
    file_list = [os.path.join(data_path, child) for child in os.listdir(data_path)]
    for filename in file_list:

        # Skip OS generated files
        if '.DS_Store' in filename: continue

        # Process the pcap file
        with open(filename,'rb') as f:
            base_name = os.path.basename(filename)
            md5 = workbench.store_sample(f.read(), base_name, 'pcap')
            results = workbench.work_request('view_pcap', md5)
            print('\n<<< %s >>>' % base_name)
            pprint.pprint(results)

def test():
    ''' pcap_bro_view test '''
    run()

if __name__ == '__main__':
    run()

