"""This client generates a similarity graph from features in PE Files."""

import zerorpc
import os
from . import client_helper

def add_it(workbench, file_list, labels):
    """Add the given file_list to workbench as samples, also add them as nodes.

    Args:
        workbench: Instance of Workbench Client.
        file_list: list of files.
        labels: labels for the nodes.

    Returns:
        A list of md5s.

    """
    md5s = []
    for filename in file_list:
        if filename != '.DS_Store':
            with open(filename, 'rb') as pe_file:
                base_name = os.path.basename(filename)
                md5 = workbench.store_sample(pe_file.read(), base_name, 'exe')
                workbench.add_node(md5, md5[:6], labels)
                md5s.append(md5)
    return md5s


def jaccard_sims(feature_list):
    """Compute Jaccard similarities between all the observations in the feature list.

    Args:
        feature_list: a list of dictionaries, each having structure as
                      { 'md5' : String, 'features': list of Strings }

    Returns:
        list of dictionaries with structure as 
        {'source': md5 String, 'target': md5 String, 'sim': Jaccard similarity Number}
    """

    sim_info_list = []
    for feature_info in feature_list:
        md5_source = feature_info['md5']
        features_source = feature_info['features']
        for feature_info in feature_list:
            md5_target = feature_info['md5']
            features_target = feature_info['features']
            if md5_source == md5_target: 
                continue
            sim = jaccard_sim(features_source, features_target)
            if sim > .5:
                sim_info_list.append({'source': md5_source, 'target': md5_target, 'sim': sim})

    return sim_info_list


def jaccard_sim(features1, features2):
    """Compute similarity between two sets using Jaccard similarity.

    Args:
        features1: list of PE Symbols.
        features2: list of PE Symbols. 

    Returns:
        Returns an int.
    """
    set1 = set(features1)
    set2 = set(features2)
    try:
        return len(set1.intersection(set2))/float(max(len(set1), len(set2)))
    except ZeroDivisionError:
        return 0


def run():
    """This client generates a similarity graph from features in PE Files."""

    # Grab server args
    args = client_helper.grab_server_args()

    # Start up workbench connection
    workbench = zerorpc.Client(timeout=300, heartbeat=60)
    workbench.connect('tcp://'+args['server']+':'+args['port'])

    # Test out PEFile -> pe_deep_sim -> pe_jaccard_sim -> graph
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/pe/bad')
    bad_files = [os.path.join(data_path, child) for child in os.listdir(data_path)][:5]
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../data/pe/good')
    good_files = [os.path.join(data_path, child) for child in os.listdir(data_path)][:5]

    # Clear any graph in the Neo4j database
    workbench.clear_graph_db()

    # First throw them into workbench and add them as nodes into the graph
    all_md5s = add_it(workbench, bad_files, ['exe', 'bad']) + add_it(workbench, good_files, ['exe', 'good'])

    # Make a sample set
    sample_set = workbench.store_sample_set(all_md5s)

    # Compute pe_features on all files of type pe, just pull back the sparse features
    import_gen = workbench.set_work_request('pe_features', sample_set, ['md5', 'sparse_features.imported_symbols'])
    imports = [{'md5': r['md5'], 'features': r['imported_symbols']} for r in import_gen]

    # Compute pe_features on all files of type pe, just pull back the sparse features
    warning_gen = workbench.set_work_request('pe_features', sample_set, ['md5', 'sparse_features.pe_warning_strings'])
    warnings = [{'md5': r['md5'], 'features': r['pe_warning_strings']} for r in warning_gen]

    # Compute strings on all files of type pe, just pull back the string_list
    string_gen = workbench.set_work_request('strings', sample_set, ['md5', 'string_list'])
    strings = [{'md5': r['md5'], 'features': r['string_list']} for r in string_gen]

    # Compute pe_peid on all files of type pe, just pull back the match_list
    # Fixme: commenting this out until we figure out why peid is SO slow
    '''
    peid_gen = workbench.set_work_request('pe_peid', sample_set, ['md5', 'match_list']})
    peids = [{'md5': r['md5'], 'features': r['match_list']} for r in peid_gen]
    '''

    # Compute the Jaccard Index between imported systems and store as relationships
    sims = jaccard_sims(imports)
    for sim_info in sims:
        workbench.add_rel(sim_info['source'], sim_info['target'], 'imports')

    # Compute the Jaccard Index between warnings and store as relationships
    sims = jaccard_sims(warnings)
    for sim_info in sims:
        workbench.add_rel(sim_info['source'], sim_info['target'], 'warnings')

    # Compute the Jaccard Index between strings and store as relationships
    sims = jaccard_sims(strings)
    for sim_info in sims:
        workbench.add_rel(sim_info['source'], sim_info['target'], 'strings')

    # Compute the Jaccard Index between peids and store as relationships
    # Fixme: commenting this out until we figure out why peid is SO slow
    '''
    sims = jaccard_sims(peids)
    for sim_info in sims:
        workbench.add_rel(sim_info['source'], sim_info['target'], 'peids')
    '''

    # Compute pe_deep_sim on all files of type pe
    results = workbench.set_work_request('pe_deep_sim', sample_set)

    # Store the ssdeep sims as relationships
    for result in list(results):
        for sim_info in result['sim_list']:
            workbench.add_rel(result['md5'], sim_info['md5'], 'ssdeep')

    # Let them know where they can get there graph
    print('All done: go to http://localhost:7474/browser and execute this query: "%s"' % \
        ('match (n)-[r]-() return n,r'))

import pytest
#pylint: disable=no-member
@pytest.mark.xfail
#pylint: enable=no-member
def test():
    """Executes pe_sim_graph test."""
    run()

if __name__ == '__main__':
    run()
