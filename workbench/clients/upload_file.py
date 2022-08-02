"""This client pushes a file into Workbench."""

import zerorpc
import os
import pprint
from . import client_helper

def run():
    """This client pushes a file into Workbench."""
    
    # Grab server args
    args = client_helper.grab_server_args()

    # Start up workbench connection
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect('tcp://'+args['server']+':'+args['port'])

    # Upload the file into workbench
    my_file = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                           '../data/pe/bad/033d91aae8ad29ed9fbb858179271232')
    with open(my_file,'rb') as f:

        # Throw file into workbench
        filename = os.path.basename(my_file)
        raw_bytes = f.read()
        md5 = workbench.store_sample(raw_bytes, filename, 'exe')
        results = workbench.work_request('view', md5)
        print('Filename: %s' % filename)
        pprint.pprint(results)

def test():
    """Executes file_upload test."""
    run()

if __name__ == '__main__':
    run()

