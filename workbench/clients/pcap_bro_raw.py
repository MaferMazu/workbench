"""This client gets the raw bro logs from PCAP files."""

import zerorpc
import os
from . import client_helper

def run():
    """This client gets the raw bro logs from PCAP files."""
    
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

        with open(filename,'rb') as f:
            base_name = os.path.basename(filename)
            md5 = workbench.store_sample(f.read(), base_name, 'pcap')
            results = workbench.work_request('pcap_bro', md5)

            # Results is just a dictionary of Bro log file names and their MD5s in workbench
            for log_name, md5 in results['pcap_bro'].items():

                # Just want the logs
                if log_name.endswith('_log'):
                    bro_log = workbench.get_sample(md5)['sample']['raw_bytes']
                    print('\n\n<<< Bro log: %s >>>\n %s' % (log_name, str(bro_log)[:500]))

def test():
    """Executes pcap_bro_raw test."""
    run()

if __name__ == '__main__':
    run()

