
''' Yara worker '''
import os
from . import yara
import pprint
import collections

# We want to load this once per module load
def get_rules_from_disk():
    ''' Recursively traverse the yara/rules directory for rules '''

    # Try to find the yara rules directory relative to the worker
    my_dir = os.path.dirname(os.path.realpath(__file__))
    yara_rule_path = os.path.join(my_dir, 'yara/rules')
    if not os.path.exists(yara_rule_path):
        raise RuntimeError('yara could not find yara rules directory under: %s' % my_dir)

    # Okay load in all the rules under the yara rule path
    rules = yara.load_rules(rules_rootpath=yara_rule_path, fast_match=True)

    return rules

YARA_RULES = get_rules_from_disk()

class YaraSigs(object):
    ''' This worker check for matches against yara sigs. 
        Output keys: [matches:list of matches] '''
    dependencies = ['sample']

    def __init__(self):
        self.rules = YARA_RULES

    def execute(self, input_data):
        ''' yara worker execute method '''
        raw_bytes = input_data['sample']['raw_bytes']
        matches = self.rules.match_data(raw_bytes)

        # The matches data is organized in the following way
        # {'filename1': [match_list], 'filename2': [match_list]}
        # match_list = list of match
        # match = {'meta':{'description':'blah}, tags=[], matches:True,
        #           strings:[string_list]}
        # string = {'flags':blah, 'identifier':'$', 'data': FindWindow, 'offset'}
        # 
        # So we're going to flatten a bit (shrug)
        # {filename_match_meta_description: string_list}
        flat_data = collections.defaultdict(list)
        for filename, match_list in matches.items():
            for match in match_list:
                if 'description' in match['meta']:
                    new_tag = filename+'_'+match['meta']['description']
                else:
                    new_tag = filename+'_'+match['rule']
                for match in match['strings']:
                    flat_data[new_tag].append(match['data'])
                # Remove duplicates
                flat_data[new_tag] = list(set(flat_data[new_tag]))

        return {'matches': flat_data}


# Unit test: Create the class, the proper input and run the execute() method for a test
def test():
    ''' yara_sigs.py: Unit test'''

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")

    # Test a file with known yara sigs
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../data/pe/bad/auriga.exe')

    with open(data_path,'rb') as pe_file:
        base_name = os.path.basename(data_path)
        md5 = workbench.store_sample(pe_file.read(), base_name, 'exe')

    # Grab the sample from workbench
    input_data = workbench.get_sample(md5)

    # Execute the worker (unit test)
    worker = YaraSigs()
    output = worker.execute(input_data)
    print('\n<<< Unit Test >>>')
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('yara_sigs', md5)
    print('\n<<< Server Test >>>')
    pprint.pprint(output)

if __name__ == "__main__":
    test()
