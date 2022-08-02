''' SWFMeta worker: This is a stub the real class (under the experimental 
                    directory has too many dependencies)
'''
import pprint

class SWFMeta(object):
    ''' This worker computes a bunch of meta-data about a SWF file '''
    dependencies = ['sample', 'meta']

    def execute(self, input_data):
        ''' Execute the SWFMeta worker '''

        # Add the meta data to the output
        output = input_data['meta']
        return output

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' swf_meta.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/swf/unknown.swf')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'unknown.swf', 'swf')
    input_data = workbench.get_sample(md5)
    input_data.update(workbench.work_request('meta', md5))

    # Execute the worker (unit test)
    worker = SWFMeta()
    output = worker.execute(input_data)
    print('\n<<< Unit Test >>>')
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('swf_meta', md5)
    print('\n<<< Server Test >>>')
    pprint.pprint(output)


if __name__ == "__main__":
    test()
