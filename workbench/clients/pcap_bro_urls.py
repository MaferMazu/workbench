"""This client gets extracts URLs from PCAP files (via Bro logs)."""

import zerorpc
import os
import pprint
from . import client_helper

def run():
    """This client gets extracts URLs from PCAP files (via Bro logs)."""
    
    # Grab server args
    args = client_helper.grab_server_args()

    # Start up workbench connection
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect('tcp://'+args['server']+':'+args['port'])

    # Loop through all the pcaps and collect a set of urls(hosts) from the http_log files
    urls = set()
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/pcap')
    file_list = [os.path.join(data_path, child) for child in os.listdir(data_path)]
    for filename in file_list:

        # Skip OS generated files
        if '.DS_Store' in filename: continue

        with open(filename,'rb') as f:
            base_name = os.path.basename(filename)
            pcap_md5 = workbench.store_sample(f.read(), base_name, 'pcap')
            results = workbench.work_request('pcap_bro', pcap_md5)

            # Just grab the http log
            if 'http_log' in results['pcap_bro']:
                log_md5 = results['pcap_bro']['http_log']
                http_data = workbench.stream_sample(log_md5)  # None Means all data
                urls = set( row['host'] for row in http_data)
                print('<<< %s >>>' % filename)
                pprint.pprint(list(urls))
                print()


def test():
    """Exexutes pcap_bro_urls test."""
    run()

if __name__ == '__main__':
    run()

