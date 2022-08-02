"""This client shows workbench extacting files from a zip file."""

import zerorpc
import os
import pprint
from . import client_helper

def run():
    """This client shows workbench extacting files from a zip file."""
    
    # Grab server args
    args = client_helper.grab_server_args()

    # Start up workbench connection
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect('tcp://'+args['server']+':'+args['port'])

    # Test out zip data
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/zip')
    file_list = [os.path.join(data_path, child) for child in os.listdir(data_path)]
    for filename in file_list:
        with open(filename,'rb') as f:
            base_name = os.path.basename(filename)
            md5 = workbench.store_sample(f.read(), base_name, 'zip')
            results = workbench.work_request('view', md5)
            print('Filename: %s ' % (base_name))
            pprint.pprint(results)

            # The unzip worker gives you a list of md5s back
            # Run meta on all the unzipped files.
            results = workbench.work_request('unzip', md5)
            print('\n*** Filename: %s ***' % (base_name))
            for child_md5 in results['unzip']['payload_md5s']:
                pprint.pprint(workbench.work_request('meta', child_md5))

def test():
    """Executes simple_client_helper test."""
    run()

if __name__ == '__main__':
    run()

