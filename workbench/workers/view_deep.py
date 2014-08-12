
''' view_deep worker '''
import zerorpc

class ViewDeep(object):
    ''' ViewDeep: Generates a view_deep for any file type '''
    dependencies = ['meta']

    def __init__(self):
        self.workbench = zerorpc.Client(timeout=300, heartbeat=60)
        self.workbench.connect("tcp://127.0.0.1:4242")

    def execute(self, input_data):

        # Grab the tag from the input and switch view types
        md5 = input_data['meta']['md5']
        tag = input_data['meta']['type_tag']
        if tag == 'exe':
            result = self.workbench.work_request('view_pe_deep', md5)['view_pe_deep']
        elif tag == 'pdf':
            result = self.workbench.work_request('view_pdf_deep', md5)['view_pdf_deep']
        elif tag == 'zip':
            result = self.workbench.work_request('view_zip_deep', md5)['view_zip_deep']
        elif tag == 'pcap':
            result = self.workbench.work_request('view_pcap_deep', md5)['view_pcap_deep']
        elif tag == 'swf':
            result = self.workbench.work_request('view_swf_deep', md5)['view_swf_deep']
        elif tag == 'mem':
            result = self.workbench.work_request('view_memory_deep', md5)['view_memory_deep']
        else:
            # In the case of an unsupported MIME type just return the meta data
            result = input_data

        return result

    def __del__(self):
        ''' Class Cleanup '''
        # Close zeroRPC client
        self.workbench.close()

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' view_deep.py: Unit test'''
    import pprint

    # This worker test requires a local server running
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate the input data for this worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../data/pdf/bad/067b3929f096768e864f6a04f04d4e54')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad_pdf', 'pdf')
    input_data = workbench.work_request('meta', md5)

    # Execute the worker
    worker = ViewDeep()
    output = worker.execute(input_data)
    print '\nViewDeep: '
    pprint.pprint(output)

    # Generate the input data for this worker
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../data/pe/bad/033d91aae8ad29ed9fbb858179271232')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad_pe', 'exe')
    input_data = workbench.work_request('meta', md5)

    # Execute the worker
    output = worker.execute(input_data)
    print '\nViewDeep: '
    pprint.pprint(output)

    # Generate the input data for this worker
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../data/zip/good.zip')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'good.zip', 'zip')
    input_data = workbench.work_request('meta', md5)

    # Execute the worker
    output = worker.execute(input_data)
    print '\nViewDeep: '
    pprint.pprint(output)

if __name__ == "__main__":
    test()
