"""PEFeaturesDF worker puts the output of pe_features into a dictionary of dataframes"""

import os
import hashlib
import pandas as pd
import zerorpc

class PEFeaturesDF(object):
    """This worker puts the output of pe_features into a dictionary of dataframes"""
    dependencies = ['sample']
    sample_set_input = True

    def __init__(self):
        """Initialization"""
        self.workbench = zerorpc.Client(timeout=300, heartbeat=60)
        self.workbench.connect("tcp://127.0.0.1:4242")
        self.samples = []

    def execute(self, input_data):
        """This worker puts the output of pe_features into a dictionary of dataframes"""
        if 'sample' in input_data:
            print('Warning: PEFeaturesDF is supposed to be called on a sample_set')
            self.samples.append(input_data['sample']['md5'])
        else:
            self.samples = input_data['sample_set']['md5_list']

        # Make a sample set
        sample_set = self.workbench.store_sample_set(self.samples)

        # Dense Features               
        dense_features = self.workbench.set_work_request('pe_features', sample_set, ['md5', 'tags', 'dense_features'])

        # Fixme: There's probably a nicer/better way to do this
        flat_features = []
        for feat in dense_features:
            feat['dense_features'].update({'md5': feat['md5'], 'tags': feat['tags']})
            flat_features.append(feat['dense_features'])
        dense_df = pd.DataFrame(flat_features)
        df_packed = dense_df.to_msgpack()
        dense_df_md5 = self.workbench.store_sample(df_packed, 'pe_features_dense_df', 'dataframe')
        
        # Sparse Features
        sparse_features = self.workbench.set_work_request('pe_features', sample_set, ['md5', 'tags', 'sparse_features'])

        # Fixme: There's probably a nicer/better way to do this
        flat_features = []
        for feat in sparse_features:
            feat['sparse_features'].update({'md5': feat['md5'], 'tags': feat['tags']})
            flat_features.append(feat['sparse_features'])
        sparse_df = pd.DataFrame(flat_features)
        df_packed = sparse_df.to_msgpack()
        sparse_df_md5 = self.workbench.store_sample(df_packed, 'pe_features_sparse_df', 'dataframe')

        # Return the dataframes
        return {'dense_features': dense_df_md5, 'sparse_features': sparse_df_md5}

# Helper method for test
def all_files_in_directory(path):
    """ Recursively ist all files under a directory """
    file_list = []
    for dirname, dirnames, filenames in os.walk(path):
        for filename in filenames:
            file_list.append(os.path.join(dirname, filename))
    return file_list

# Unit test: Create the class, the proper input and run the execute() method for a test
import pytest
@pytest.mark.xfail
def test():
    ''' pe_features_df.py: Unit test'''
    import pprint

    # This worker test requires a local server running
    import zerorpc
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect("tcp://127.0.0.1:4242")


    # Grab all the filenames from the pe/bad data directory
    import os
    data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/pe/bad')
    file_list = all_files_in_directory(data_dir)

    # Upload the files into workbench
    md5_list = []
    for path in file_list:

        # Skip OS generated files
        if '.DS_Store' in path: 
            continue

        with open(path,'rb') as f:
            filename = os.path.basename(path)

            # Here we're going to save network traffic by asking
            # Workbench if it already has this md5
            raw_bytes = f.read()
            md5 = hashlib.md5(raw_bytes).hexdigest()
            md5_list.append(md5)
            if workbench.has_sample(md5):
                print('Workbench already has this sample %s' % md5)
            else:
                # Store the sample into workbench
                md5 = workbench.store_sample(raw_bytes, filename, 'unknown')
                print('Filename %s uploaded: type_tag %s, md5 %s' % (filename, 'unknown', md5))

    # Store the sample_set
    set_md5 = workbench.store_sample_set(md5_list)

    # Execute the worker (unit test)
    worker = PEFeaturesDF()
    output = worker.execute({'sample_set': {'md5_list': workbench.get_sample_set(set_md5)}})
    print('\n<<< Unit Test >>>')
    pprint.pprint(output)

    # Execute the worker (server test)
    output = workbench.work_request('pe_features_df', set_md5)['pe_features_df']
    print('\n<<< Server Test >>>')
    pprint.pprint(output)

if __name__ == "__main__":
    test()
