
''' EvelKnievelKey worker '''
import hashlib
import magic
import pprint

class EvelKnievelKey(object):
    """This worker pseudo-randomly throws a KeyError Exception. The
       pseudo-random part is that the logic is deterministic given a pile
       of md5s about 8% will fail but it will always be the same ones"""
    dependencies = ['meta']

    def __init__(self):
        ''' Initialization '''
        self.meta = {}

    def execute(self, input_data):
        ''' This worker pseudo-randomly throws a KeyError Exception. '''
        md5 = input_data['meta']['md5']
        if not (int(md5,16) % 13):
            foo = input_data['nonsense_key']
            return {'Evel': 'fail'}

        return {'Evel':'success'}


# Unit test: Create the class, the proper input and run the execute() method for a test
import pytest
#pylint: disable=no-member
@pytest.mark.xfail
#pylint: enable=no-member
def test():
    ''' meta.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate the input data for this worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../data/pe/bad/033d91aae8ad29ed9fbb858179271232')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad_pe', 'exe')
    input_data = workbench.work_request('meta', md5)

    # Execute the worker (unit test)
    worker = EvelKnievelKey()
    output = worker.execute(input_data)
    print('\n<<< Unit Test >>>')
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('evel_knievel_key', md5)
    print('\n<<< Server Test >>>')
    pprint.pprint(output)

if __name__ == "__main__":
    test()
