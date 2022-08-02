''' view_customer worker '''

class ViewCustomer(object):
    ''' ViewCustomer: Generates a customer usage view. '''
    dependencies = ['meta']

    def execute(self, input_data):
        ''' Execute Method '''

        # View on all the meta data files in the sample
        fields = ['filename', 'md5', 'length', 'customer', 'import_time', 'type_tag']
        view = {key:input_data['meta'][key] for key in fields}
        return view

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' view_customer.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../data/pe/bad/033d91aae8ad29ed9fbb858179271232')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad_pe', 'exe')
    input_data = workbench.work_request('meta', md5)

    # Execute the worker (unit test)
    worker = ViewCustomer()
    output = worker.execute(input_data)
    print('\n<<< Unit Test >>>')
    import pprint
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('view_customer', md5)
    print('\n<<< Server Test >>>')
    pprint.pprint(output)

if __name__ == "__main__":
    test()
