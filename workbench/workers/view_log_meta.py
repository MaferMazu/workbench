
''' view_log_meta worker '''
import pprint

class ViewLogMeta(object):
    ''' ViewLogMeta: Generates a view for meta data on the sample '''
    dependencies = ['log_meta']

    def execute(self, input_data):
        ''' Execute the ViewLogMeta worker '''

        # Deprecation unless something more interesting happens with this class
        return input_data['log_meta']

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' view_log_meta.py: Unit test'''
    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/log/system.log')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'system.log', 'log')
    input_data = workbench.work_request('log_meta', md5)

    # Execute the worker (unit test)
    worker = ViewLogMeta()
    output = worker.execute(input_data)
    print('\n<<< Unit Test >>>')
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('view_log_meta', md5)
    print('\n<<< Server Test >>>')
    pprint.pprint(output)

if __name__ == "__main__":
    test()
