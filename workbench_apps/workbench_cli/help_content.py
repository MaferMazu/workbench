"""Workbench Interactive Shell Help Content"""

import inspect
from IPython.utils.coloransi import TermColors as color
#pylint: disable=no-member

class WorkbenchShellHelp(object):
    """Workbench CLI Help"""

    def __init__(self):
        ''' Workbench CLI Initialization '''

    def help_cli(self):
        """ Help on Workbench CLI """
        help = '%sWelcome to Workbench CLI Help:%s' % (color.Yellow, color.Normal)
        help += '\n\t%s> help cli_basic %s for getting started help' % (color.Green, color.LightBlue)
        help += '\n\t%s> help workers %s for help on available workers' % (color.Green, color.LightBlue)
        help += '\n\t%s> help search %s for help on searching samples' % (color.Green, color.LightBlue)
        help += '\n\t%s> help dataframe %s for help on making dataframes' % (color.Green, color.LightBlue)
        help += '\n\t%s> help commands %s for help on workbench commands' % (color.Green, color.LightBlue)
        help += '\n\t%s> help topic %s where topic can be a help, command or worker' % (color.Green, color.LightBlue)
        help += '\n\n%sNote: cli commands are transformed into python calls' % (color.Yellow)
        help += '\n\t%s> help cli_basic --> help("cli_basic")%s' % (color.Green, color.Normal)
        return help

    def help_cli_basic(self):
        """ Help for Workbench CLI Basics """
        help =  '%sWorkbench: Getting started...' % (color.Yellow)
        help += '\n%sLoad in a sample:'  % (color.Green)
        help += '\n\t%s> load_sample /path/to/file' % (color.LightBlue)
        help += '\n\n%sNotice the prompt now shows the md5 of the sample...'% (color.Yellow)
        help += '\n%sRun workers on the sample:'  % (color.Green)
        help += '\n\t%s> view' % (color.LightBlue)
        help += '\n%sType the \'help workers\' or the first part of the worker <tab>...'  % (color.Green)
        help += '\n\t%s> help workers (lists all possible workers)' % (color.LightBlue)
        help += '\n\t%s> pe_<tab> (will give you pe_classifier, pe_deep_sim, pe_features, pe_indicators, pe_peid)%s' % (color.LightBlue, color.Normal)
        return help

    def help_cli_search(self):
        """ Help for Workbench CLI Search """
        help =  '%sSearch: %s returns sample_sets, a sample_set is a set/list of md5s.' % (color.Yellow, color.Green)
        help += '\n\n\t%sSearch for all samples in the database that are known bad pe files,'  % (color.Green)
        help += '\n\t%sthis command returns the sample_set containing the matching items'% (color.Green)
        help += '\n\t%s> my_bad_exes = search([\'bad\', \'exe\'])' % (color.LightBlue)
        help += '\n\n\t%sRun workers on this sample_set:'  % (color.Green)
        help += '\n\t%s> pe_outputs = pe_features(my_bad_exes) %s' % (color.LightBlue, color.Normal)
        help += '\n\n\t%sLoop on the generator (or make a DataFrame see >help dataframe)'  % (color.Green)
        help += '\n\t%s> for output in pe_outputs: %s' % (color.LightBlue, color.Normal)
        help += '\n\t\t%s print output %s' % (color.LightBlue, color.Normal)
        return help

    def help_dataframe(self):
        """ Help for making a DataFrame with Workbench CLI """
        help =  '%sMaking a DataFrame: %s how to make a dataframe from raw data (pcap, memory, pe files)' % (color.Yellow, color.Green)
        help += '\n\t%sNote: for memory_image and pe_files see > help dataframe_memory or dataframe_pe'  % (color.Green)
        help += '\n\n%sPCAP Example:'  % (color.Green)
        help += '\n\t%s> load_sample /path/to/pcap/gold_xxx.pcap [\'bad\', \'threatglass\']' % (color.LightBlue)
        help += '\n\t%s> view     # view is your friend use it often' % (color.LightBlue)
        help += '\n\n%sGrab the http_log from the pcap (also play around with other logs):'  % (color.Green)
        help += '\n\t%s> http_log_md5 = view()[\'view\'][\'bro_logs\'][\'http_log\']' % (color.LightBlue)
        help += '\n\t%s> http_log_md5 (returns the md5 of the http_log)' % (color.LightBlue)
        help += '\n\n%sStream back the ^contents^ of the http_log:'  % (color.Green)
        help += '\n\t%s> http_log = stream_sample(http_log_md5)' % (color.LightBlue)     
        help += '\n\n%sPut the http_log into a dataframe:'  % (color.Green)
        help += '\n\t%s> http_df = pd.DataFrame(http_log)' % (color.LightBlue)
        help += '\n\t%s> http_df.head()' % (color.LightBlue)
        help += '\n\t%s> http_df.groupby([\'host\',\'id.resp_h\',\'resp_mime_types\'])[[\'response_body_len\']].sum()' % (color.LightBlue)
        help += '\n\t%s> http_df.describe() %s' % (color.LightBlue, color.Normal)
        return help

    def help_dataframe_memory(self):
        """ Help for making a DataFrame with Workbench CLI """
        help =  '%sMaking a DataFrame: %s how to make a dataframe from memory_forensics sample' % (color.Yellow, color.Green)
        help += '\n\n%sMemory Images Example:'  % (color.Green)
        help += '\n\t%s> load_sample /path/to/pcap/exemplar4.vmem [\'bad\', \'aptz13\']' % (color.LightBlue)
        help += '\n\t%s> view # view is your friend use it often' % (color.LightBlue)
        help += '\n\t%s> <<< TODO :) >>> %s' % (color.LightBlue, color.Normal)
        return help

    def help_dataframe_pe(self):
        """ Help for making a DataFrame with Workbench CLI """
        help =  '%sMaking a DataFrame: %s how to make a dataframe from pe files' % (color.Yellow, color.Green)
        help += '\n\n%sPE Files Example (loading a directory):'  % (color.Green)
        help += '\n\t%s> load_sample /path/to/pe/bad [\'bad\', \'case_69\']' % (color.LightBlue)
        help += '\n\n\t%sSearch for all samples in the database that are pe files,'  % (color.Green)
        help += '\n\t%sthis command returns the sample_set containing the matching items'% (color.Green)
        help += '\n\t%s> my_exes = search([\'exe\'])' % (color.LightBlue)
        help += '\n\n\t%sRun workers on this sample_set:'  % (color.Green)
        help += '\n\t%s> pe_outputs = set_work_request(\'pe_features\', my_exes, [\'md5\', \'dense_features.*\', \'tags\'])' % (color.LightBlue)
        help += '\n\n\t%sMake a DataFrame:'  % (color.Green)
        help += '\n\t%s> pe_df = pd.DataFrame(pe_outputs) %s' % (color.LightBlue, color.Normal)
        help += '\n\t%s> pe_df.head() %s' % (color.LightBlue, color.Normal)
        help += '\n\t%s> pe_df = flatten_tags(pe_df) %s' % (color.LightBlue, color.Normal)
        help += '\n\t%s> pe_df.hist(\'check_sum\',\'tags\') %s' % (color.LightBlue, color.Normal)
        help += '\n\t%s> pe_df.bloxplot(\'check_sum\',\'tags\') %s' % (color.LightBlue, color.Normal)
        return help

    ##################
    # Introspection
    ##################
    def _all_help_methods(self):
        """ Returns a list of all the Workbench commands"""
        methods = {name:method for name, method in inspect.getmembers(self, predicate=inspect.isroutine) if not name.startswith('_')}
        return methods

def test():
    """Test the Workbench Interactive Shell Help"""
    help = WorkbenchShellHelp()

    # Now execute all the help methods
    for name, method in help._all_help_methods().items():
        print('\n%s%s%s' % (color.Red, name, color.Normal))
        print('%s' % method())

if __name__ == '__main__':
    test()
