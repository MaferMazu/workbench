
''' MetaDeep worker '''
import hashlib
import ssdeep as ssd
import pprint

class MetaDeepData(object):
    ''' This worker computes deeper meta-data '''
    dependencies = ['sample', 'meta']

    def __init__(self):
        ''' Initialization '''
        self.meta = {}

    def execute(self, input_data):
        raw_bytes = input_data['sample']['raw_bytes']
        self.meta['sha1'] = hashlib.sha1(raw_bytes).hexdigest()
        self.meta['sha256'] = hashlib.sha256(raw_bytes).hexdigest()
        self.meta['ssdeep'] = ssd.hash(raw_bytes)
        self.meta['entropy'] = self._entropy(raw_bytes)
        self.meta.update(input_data['meta'])
        return self.meta

    def _entropy(self, s):
        # Grabbed this snippet from Rosetta Code (rosettacode.org)
        import math
        from collections import Counter
        p, lns = Counter(s), float(len(s))
        return -sum( count/lns * math.log(count/lns, 2) for count in list(p.values()))

# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' meta_deep.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    import os
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/log/system.log')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'system.log', 'log')
    input_data = workbench.get_sample(md5)
    input_data.update(workbench.work_request('meta', md5))

    # Execute the worker (unit test)
    worker = MetaDeepData()
    output = worker.execute(input_data)
    print('\n<<< Unit Test >>>')
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('meta_deep', md5)
    print('\n<<< Server Test >>>')
    pprint.pprint(output)

if __name__ == "__main__":
    test()
