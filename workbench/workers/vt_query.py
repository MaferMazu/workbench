
''' VTQuery worker '''
import os
import requests
import collections
import configparser
import pprint

class VTQuery(object):
    ''' This worker query Virus Total, an apikey needs to be provided '''
    dependencies = ['meta']
    
    def __init__(self):
        ''' VTQuery Init'''

        # Grab API key from configuration file
        config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../server/config.ini')
        conf = configparser.ConfigParser()
        conf.read(config_path)
        self.apikey = conf.get('workbench', 'vt_apikey')

        # Make sure key isn't the dummy value
        if self.apikey == '123':
            raise RuntimeError('VTQuery: Invalid api_key, put your VT api key in the config.ini file.')
        
        # Change this if you want these fields
        self.exclude = ['scan_id', 'md5', 'sha1', 'sha256', 'resource', 'response_code', 'permalink',
                        'verbose_msg', 'scans']

    def execute(self, input_data):
        ''' Execute the VTQuery worker '''
        md5 = input_data['meta']['md5']
        response = requests.get('http://www.virustotal.com/vtapi/v2/file/report', 
                                params={'apikey':self.apikey,'resource':md5, 'allinfo':1})

        # Make sure we got a json blob back
        try:
            vt_output = response.json()
        except ValueError:
            return {'vt_error': 'VirusTotal Query Error, no valid response... past per min quota?'}
        
        # Just pull some of the fields
        output = {field:vt_output[field] for field in list(vt_output.keys()) if field not in self.exclude}
        
        # Check for not-found
        not_found = False if output else True        

        # Add in file_type
        output['file_type'] = input_data['meta']['file_type']
        
        # Toss back a not found
        if not_found:
            output['not_found'] = True
            return output

        # Organize the scans fields
        scan_results = collections.Counter()
        for scan in list(vt_output['scans'].values()):
            if 'result' in scan:
                if scan['result']:
                    scan_results[scan['result']] += 1
        output['scan_results'] = scan_results.most_common(5)
        return output


# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' -- vt_query.py test -- '''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Generate input for the worker
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             '../data/pdf/bad/067b3929f096768e864f6a04f04d4e54')
    md5 = workbench.store_sample(open(data_path, 'rb').read(), 'bad_pdf', 'pdf')
    input_data = workbench.work_request('meta', md5)

    # Execute the worker (unit test)
    worker = VTQuery()
    output = worker.execute(input_data)
    print('\n<<< Unit Test >>>')
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('vt_query', md5)
    print('\n<<< Server Test >>>')
    pprint.pprint(output)

if __name__ == "__main__":
    test()
