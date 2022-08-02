
''' Test: This worker tests for robustly handling timeout situations '''
import gevent

class Test_Timeout(object):
    ''' Test: This worker tests for robustly handling timeout situations '''
    dependencies = []

    def __init__(self):
        ''' Initialization '''
        self.sleep_time = 35

    def execute(self, input_data):
        ''' Test: This worker tests for robustly handling timeout situations '''
        gevent.sleep(self.sleep_time)
        return {'timeout':self.sleep_time}

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' test_timeout.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Execute the worker (unit test)
    print('\n<<< Unit Test >>>')
    worker = Test_Timeout()
    output = worker.execute(None)
    import pprint
    pprint.pprint(output)

    # Execute the worker (server test)
    print('\n<<< Server Test >>>')

    # Execute the worker (server test) (note no unit test as the test is testing server timeouts)
    try:
        workbench.work_request('test_timeout','123')
        raise RuntimeError('Timeout did not fail... unexpected, investigate!')
    except zerorpc.exceptions.TimeoutExpired:
        print('Timeout failed as expected.. so success!')

if __name__ == "__main__":
    test()
