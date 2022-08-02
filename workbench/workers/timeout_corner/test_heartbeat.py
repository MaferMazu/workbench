
''' Test: This worker tests for robustly handling heartbeat timeout situations '''
import time

class Test_Heartbeat(object):
    ''' Test: This worker tests for robustly handling heartbeat timeout situations '''
    dependencies = []

    def __init__(self):
        ''' Initialization '''
        self.loop_time = 20
        self.start_time = time.time()

    def execute(self, input_data):
        ''' Test: This worker tests for robustly handling heartbeat timeout situations '''
        busy_loop = True
        while busy_loop:
            if (time.time() - self.start_time) > self.loop_time:
                busy_loop = False
        return {'heartbeat timeout': self.loop_time}

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' test_heartbeat.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")
    
    # Execute the worker (unit test)
    print('\n<<< Unit Test >>>')
    worker = Test_Heartbeat()
    output = worker.execute(None)
    import pprint
    pprint.pprint(output)

    # Execute the worker (server test)
    print('\n<<< Server Test >>>')
    try:
        output = workbench.work_request('test_heartbeat','123')
        raise RuntimeError('Heartbeat did not fail... unexpected, investigate!')
    except zerorpc.exceptions.LostRemote:
        print('Heartbeat failed as expected.. so success!')

if __name__ == "__main__":
    test()
