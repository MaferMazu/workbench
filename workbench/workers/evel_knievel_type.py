
''' EvelKnievelType worker '''
import hashlib
import magic
import pprint

class EvelKnievelType(object):
    """This worker pseudo-randomly throws a TypeError Exception. The
       pseudo-random part is that the logic is deterministic given a pile
       of md5s about 7% will fail but it will always be the same ones"""
    dependencies = ['meta']

    def __init__(self):
        ''' Initialization '''
        self.meta = {}

    def execute(self, input_data):
        ''' This worker pseudo-randomly throws a TypeError Exception. '''
        md5 = input_data['meta']['md5']
        if not (int(md5,16) % 15):
            print('%d' % md5)
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
                             '../data/pe/bad/0e8b030fb6ae48ffd29e520fc16b5641')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad_pe', 'exe')
    input_data = workbench.work_request('meta', md5)

    # Execute the worker (unit test)
    worker = EvelKnievelType()
    output = worker.execute(input_data)
    print('\n<<< Unit Test >>>')
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('evel_knievel_type', md5)
    print('\n<<< Server Test >>>')
    pprint.pprint(output)

if __name__ == "__main__":
    test()
