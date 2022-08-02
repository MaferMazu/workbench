
"""Workbench: Open Source Security Framework """

# Okay this monkey patch call needs to be first
# Note: The thread=False parameters appears to be needed
#       for MongoDB, if you know a better way please do PR :)
from gevent import monkey; monkey.patch_all(thread=False) # Monkey!
from gevent import signal as gevent_signal
import signal
import sys, os
import zerorpc
import zmq
import logging
logging.basicConfig()
import json
import hashlib
import inspect
import funcsigs
import configparser
import magic
import datetime
import lz4
from IPython.utils.coloransi import TermColors as color
#pylint: disable=no-member
try:
    from io import StringIO
except ImportError:
    from io import StringIO

# Workbench server imports
try:
    from . import data_store
    from . import els_indexer
    from . import neo_db
    from . import plugin_manager
    from .bro import bro_log_reader
    from . import version

# Okay this happens when you're running workbench in a debugger so having
# this is super handy and we'll keep it even though it hurts coverage score.
except ValueError:
    from . import data_store
    from . import els_indexer
    from . import neo_db
    from . import plugin_manager
    from .bro import bro_log_reader
    from . import version


class WorkBench(object):
    """ Workbench: Open Source Security Framework. """

    # Workbench DataNotFound exception class
    class DataNotFound(Exception):
        @staticmethod
        def message():
            return "Obi-Wan waves his hand... this isn't the data you're looking for..."

    def __init__(self, store_args=None, els_hosts=None, neo_uri=None):
        """Initialize the Framework.

        Args:
            store_args: Dictionary with keys uri,database,samples_cap, worker_cap.
            els_hosts: The address where Elastic Search Indexer is running.
            neo_uri: The address where Neo4j is running.
        """

        # Needs to be replaced by logger
        self.VERBOSE = False

        # Workbench Server Version
        self.version = version.__version__
        print('<<< Workbench Server Version %s >>>' % self.version)

        # Open DataStore
        self.data_store = data_store.DataStore(**store_args)

        # ELS Indexer
        try:
            self.indexer = els_indexer.ELSIndexer(**{'hosts': els_hosts} if els_hosts else {})
        except SystemExit:
            print('Could not connect to ELS. Is it running?')
            self.indexer = els_indexer.ELSStubIndexer(**{'uri': neo_uri} if neo_uri else {})

        # Neo4j DB
        try:
            self.neo_db = neo_db.NeoDB(**{'uri': neo_uri} if neo_uri else {})
        except RuntimeError:
            print('Could not connect to Neo4j DB. Is it running?  $ neo4j start')
            self.neo_db = neo_db.NeoDBStub(**{'uri': neo_uri} if neo_uri else {})

        # Create Plugin Manager
        self.plugin_meta = {}
        plugin_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'../workers')
        self.plugin_manager = plugin_manager.PluginManager(self._new_plugin, plugin_dir=plugin_dir)

        # Store information about commands and workbench
        self._store_information()

    def version(self):
        """Return the version of the Workbench server"""
        return self.version

    #######################
    # Sample Methods
    #######################
    def store_sample(self, input_bytes, filename, type_tag):
        """ Store a sample into the DataStore.
            Args:
                input_bytes: the actual bytes of the sample e.g. f.read()
                filename: name of the file (used purely as meta data not for lookup)
                type_tag: ('exe','pcap','pdf','json','swf', or ...)
            Returns:
                the md5 of the sample.
        """

        # If the sample comes in with an unknown type_tag try to determine it
        if type_tag == 'unknown':
            print('Info: Unknown File -- Trying to Determine Type...')
            type_tag = self.guess_type_tag(input_bytes, filename)

        # Do we have a compressed sample? If so decompress it
        if type_tag == 'lz4':
            input_bytes = lz4.loads(input_bytes)

        # Store the sample
        md5 = self.data_store.store_sample(input_bytes, filename, type_tag)

        # Add the type_tags to tags
        if type_tag != 'lz4':
            self.add_tags(md5, type_tag)

        return md5

    def get_sample(self, md5):
        """ Get a sample from the DataStore.
            Args:
                md5: the md5 of the sample
            Returns:
                A dictionary of meta data about the sample which includes
                a ['raw_bytes'] key that contains the raw bytes.
            Raises:
                Workbench.DataNotFound if the sample is not found.
        """
        # First we try a sample, if we can't find one we try getting a sample_set.
        sample = self.data_store.get_sample(md5)
        if not sample:
            return {'sample_set': {'md5_list': self.get_sample_set(md5)}}
        return {'sample': sample}

    def is_sample_set(self, md5):
        """ Does the md5 represent a sample_set?
            Args:
                md5: the md5 of the sample_set
            Returns:
                True/False
        """
        try:
            self.get_sample_set(md5)
            return True
        except WorkBench.DataNotFound:
            return False

    def get_sample_window(self, type_tag, size):
        """ Get a sample from the DataStore.
            Args:
                type_tag: the type of samples ('pcap','exe','pdf')
                size: the size of the window in MegaBytes (10 = 10MB)
            Returns:
                A sample_set handle which represents the newest samples within the size window
        """
        md5_list = self.data_store.get_sample_window(type_tag, size)
        return self.store_sample_set(md5_list)

    def has_sample(self, md5):
        """ Do we have this sample in the DataStore.
            Args:
                md5: the md5 of the sample
            Returns:
                True or False
        """
        return self.data_store.has_sample(md5)

    def combine_samples(self, md5_list, filename, type_tag):
        """Combine samples together. This may have various use cases the most significant 
           involving a bunch of sample 'chunks' got uploaded and now we combine them together

            Args:
                md5_list: The list of md5s to combine, order matters!
                filename: name of the file (used purely as meta data not for lookup)
                type_tag: ('exe','pcap','pdf','json','swf', or ...)
            Returns:
                the computed md5 of the combined samples
        """
        total_bytes = ""
        for md5 in md5_list:
            total_bytes += self.get_sample(md5)['sample']['raw_bytes']
            self.remove_sample(md5)

        # Store it
        return self.store_sample(total_bytes, filename, type_tag)

    def remove_sample(self, md5):
        """Remove the sample from the data store"""
        self.data_store.remove_sample(md5)

    @zerorpc.stream
    def stream_sample(self, md5, kwargs=None):
        """ Stream the sample by giving back a generator, typically used on 'logs'.
            Args:
                md5: the md5 of the sample
                kwargs: a way of specifying subsets of samples (None for all)
                    max_rows: the maximum number of rows to return
            Returns:
                A generator that yields rows of the file/log
        """

        # Get the max_rows if specified
        max_rows = kwargs.get('max_rows', None) if kwargs else None

        # Grab the sample and it's raw bytes
        sample = self.get_sample(md5)['sample']
        raw_bytes = sample['raw_bytes']

        # Figure out the type of file to be streamed
        type_tag = sample['type_tag']
        if type_tag == 'bro':
            bro_log = bro_log_reader.BroLogReader(convert_datetimes=False)
            mem_file = StringIO(raw_bytes)
            generator = bro_log.read_log(mem_file)
            return generator
        elif type_tag == 'els_query':
            els_log = json.loads(raw_bytes)
            # Try to determine a couple of different types of ELS query results
            if 'fields' in els_log['hits']['hits'][0]:
                generator = (row['fields'] for row in els_log['hits']['hits'][:max_rows])
            else:
                generator = (row['_source'] for row in els_log['hits']['hits'][:max_rows])
            return generator
        elif type_tag == 'log':
            generator = ({'row':row} for row in raw_bytes.split('\n')[:max_rows])
            return generator
        elif type_tag == 'json':
            generator = (row for row in json.loads(raw_bytes)[:max_rows])
            return generator
        else:
            raise RuntimeError('Cannot stream file %s with type_tag:%s' % (md5, type_tag))

    def get_dataframe(self, md5, compress='lz4'):
        """Return a dataframe from the DataStore. This is just a convenience method
           that uses get_sample internally. 
            Args:
                md5: the md5 of the dataframe
                compress: compression to use: (defaults to 'lz4' but can be set to None)
            Returns:
                A msgpack'd Pandas DataFrame
            Raises:
                Workbench.DataNotFound if the dataframe is not found.
        """
        # First we try a sample, if we can't find one we try getting a sample_set.
        sample = self.data_store.get_sample(md5)
        if not sample:
            raise WorkBench.DataNotFound("Could not find %s in the data store", md5)
        if not compress:
            return sample['raw_bytes']
        else:
            compress_df = lz4.dumps(sample['raw_bytes'])
            print('Info: DataFrame compression %.0f%%' % (len(compress_df)*100.0/float(len(sample['raw_bytes']))))
            return compress_df

    def guess_type_tag(self, input_bytes, filename):
        """ Try to guess the type_tag for this sample """
        mime_to_type = {'application/jar': 'jar',
                        'application/java-archive': 'jar',
                        'application/octet-stream': 'data',
                        'application/pdf': 'pdf',
                        'application/vnd.ms-cab-compressed': 'cab',
                        'application/vnd.ms-fontobject': 'ms_font',
                        'application/vnd.tcpdump.pcap': 'pcap',
                        'application/x-dosexec': 'exe',
                        'application/x-empty': 'empty',
                        'application/x-shockwave-flash': 'swf',
                        'application/xml': 'xml',
                        'application/zip': 'zip',
                        'image/gif': 'gif',
                        'text/html': 'html',
                        'image/jpeg': 'jpg',
                        'image/png': 'png',
                        'image/x-icon': 'icon',
                        'text/plain': 'txt'
                        }

        # See what filemagic can determine
        with magic.Magic(flags=magic.MAGIC_MIME_TYPE) as mag:
            mime_type = mag.id_buffer(input_bytes[:1024])
            if mime_type in mime_to_type:
                type_tag = mime_to_type[mime_type]

                # If we get 'data' back look at the filename
                if type_tag == 'data':
                    print('Info: File -- Trying to Determine Type from filename...')
                    ext = os.path.splitext(filename)[1][1:]
                    if ext in ['mem','vmem']:
                        type_tag = 'mem'
                    else:
                        print('Alert: Failed to Determine Type for %s' % filename)
                        exit(1) # Temp
                return type_tag
            else:
                print('Alert: Sample Type could not be Determined')
                return 'unknown'

    def add_tags(self, md5, tags):
        """Add tags to this sample"""
        if not tags: return
        tag_set = set(self.get_tags(md5)) if self.get_tags(md5) else set()
        if isinstance(tags, str):
            tags = [tags]
        for tag in tags:
            tag_set.add(tag)
        self.data_store.store_work_results({'tags': list(tag_set)}, 'tags', md5)

    def set_tags(self, md5, tags):
        """Set the tags for this sample"""
        if isinstance(tags, str):
            tags = [tags]
        tag_set = set(tags)
        self.data_store.store_work_results({'tags': list(tag_set)}, 'tags', md5)

    def get_tags(self, md5):
        """Get tags for this sample"""
        tag_data = self.data_store.get_work_results('tags', md5)
        return tag_data['tags'] if tag_data else None

    def get_all_tags(self):
        """Get tags for this sample"""
        return self.data_store.tags_all()


    #######################
    # Index Methods
    #######################
    def index_sample(self, md5, index_name):
        """ Index a stored sample with the Indexer.
            Args:
                md5: the md5 of the sample
                index_name: the name of the index
            Returns:
                Nothing
        """
        generator = self.stream_sample(md5)
        for row in generator:
            self.indexer.index_data(row, index_name)

    def index_worker_output(self, worker_name, md5, index_name, subfield):
        """ Index worker output with the Indexer.
            Args:
                worker_name: 'strings', 'pe_features', whatever
                md5: the md5 of the sample
                index_name: the name of the index
                subfield: index just this subfield (None for all)
            Returns:
                Nothing
        """

        # Grab the data
        if subfield:
            data = self.work_request(worker_name, md5)[worker_name][subfield]
        else:
            data = self.work_request(worker_name, md5)[worker_name]

        # Okay now index the data
        self.indexer.index_data(data, index_name=index_name, doc_type='unknown')

    def search_index(self, index_name, query):
        """ Search a particular index in the Indexer
            Args:
                index_name: the name of the index
                query: the query against the index
            Returns:
                All matches to the query
        """
        return self.indexer.search(index_name, query)


    #######################
    # Graph Methods
    #######################
    def add_node(self, node_id, name, labels):
        """ Add a node to the graph with name and labels.
            Args:
                node_id: the unique node_id e.g. 'www.evil4u.com'
                name: the display name of the node e.g. 'evil4u'
                labels: a list of labels e.g. ['domain','evil']
            Returns:
                Nothing
        """
        self.neo_db.add_node(node_id, name, labels)

    def has_node(self, node_id):
        """ Does the Graph DB have this node
            Args:
                node_id: the unique node_id e.g. 'www.evil4u.com'
            Returns:
                True/False
        """
        return self.neo_db.has_node(node_id)

    def add_rel(self, source_id, target_id, rel):
        """ Add a relationship: source, target must already exist (see add_node)
            'rel' is the name of the relationship 'contains' or whatever.
            Args:
                source_id: the unique node_id of the source
                target_id: the unique node_id of the target
                rel: name of the relationship
            Returns:
                Nothing
        """
        self.neo_db.add_rel(source_id, target_id, rel)

    def clear_graph_db(self):
        """ Clear the Graph Database of all nodes and edges.
            Args:
                None
            Returns:
                Nothing
        """
        self.neo_db.clear_db()

    def clear_db(self):
        """ Clear the Main Database of all samples and worker output.
            Args:
                None
            Returns:
                Nothing
        """
        self.data_store.clear_db()

        # Have the plugin manager reload all the plugins
        self.plugin_manager.load_all_plugins()

        # Store information about commands and workbench
        self._store_information()

    def clear_worker_output(self):
        """Drops all of the worker output collections
            Args:
                None
            Returns:
                Nothing
        """
        self.data_store.clear_worker_output()

        # Have the plugin manager reload all the plugins
        self.plugin_manager.load_all_plugins()

        # Store information about commands and workbench
        self._store_information()


    #######################
    # Work Request Methods
    #######################
    def work_request(self, worker_name, md5, subkeys=None):
        """ Make a work request for an existing stored sample.
            Args:
                worker_name: 'strings', 'pe_features', whatever
                md5: the md5 of the sample (or sample_set!)
                subkeys: just get a subkey of the output: 'foo' or 'foo.bar' (None for all) 
            Returns:
                The output of the worker.
        """

        # Pull the worker output
        work_results = self._recursive_work_resolver(worker_name, md5)

        # Subkeys (Fixme this is super klutzy)
        if subkeys:
            if isinstance(subkeys, str):
                subkeys = [subkeys]
            try:
                sub_results = {}
                for subkey in subkeys:
                    tmp = work_results[worker_name]

                    # Traverse any subkeys
                    for key in subkey.split('.')[:-1]:
                        tmp = tmp[key]

                    # Last subkey
                    key = subkey.split('.')[-1]
                    if key == '*':
                        for key in list(tmp.keys()):
                            sub_results[key] = tmp[key]
                    else:
                        sub_results[key] = tmp[key]

                # Set the output
                work_results = sub_results

            except (KeyError, TypeError):
                raise RuntimeError('Could not get one or more subkeys for: %s' % (work_results))

        # Clean it and ship it
        return self.data_store.clean_for_serialization(work_results)

    @zerorpc.stream
    def set_work_request(self, worker_name, sample_set, subkeys=None):
        """ Make a work request for an existing stored sample (or sample_set).
            Args:
                worker_name: 'strings', 'pe_features', whatever
                sample_set: the md5 of a sample_set in the Workbench data store
                subkeys: just get a subkey of the output: 'foo' or 'foo.bar' (None for all) 
            Returns:
                The output is a generator of the results of the worker output for the sample_set
        """

        # Does worker support sample_set_input?
        if self.plugin_meta[worker_name]['sample_set_input']:
            yield self.work_request(worker_name, sample_set, subkeys)
 
        # Loop through all the md5s and return a generator with yield
        else:
            md5_list = self.get_sample_set(sample_set)
            for md5 in md5_list:
                if subkeys:
                    yield self.work_request(worker_name, md5, subkeys)
                else:
                    yield self.work_request(worker_name, md5)[worker_name]

    def store_sample_set(self, md5_list):
        """ Store a sample set (which is just a list of md5s).

            Note: All md5s must already be in the data store.

            Args:
                md5_list: a list of the md5s in this set (all must exist in data store)

            Returns:
                The md5 of the set (the actual md5 of the set)
        """

        # Sanity check
        if not md5_list:
            print('Warning: Trying to store an empty sample_set')
            return None

        # Remove any duplicates
        md5_list = list(set(md5_list))

        for md5 in md5_list:
            if not self.has_sample(md5):
                raise RuntimeError('%s: Not found! All items in sample_set must be in the datastore' % (md5))
        set_md5 = hashlib.md5(str(md5_list)).hexdigest()
        self._store_work_results({'md5_list':md5_list}, 'sample_set', set_md5)
        return set_md5

    def generate_sample_set(self, tags=None):
        """Generate a sample_set that maches the tags or all if tags are not specified.

            Args:
                tags: Match samples against this tag list (or all if not specified)

            Returns:
                The sample_set of those samples matching the tags
        """
        if isinstance(tags, str):
            tags = [tags]
        md5_list = self.data_store.tag_match(tags)
        return self.store_sample_set(md5_list)

    def get_sample_set(self, md5):
        """ Retrieve a sample set (which is just a list of md5s).

            Args:
                md5: the md5 of the sample_set (returned with the 'store_sample_set' call)

            Returns:
                The list of md5s that comprise the sample_set
        """
        return self.data_store.clean_for_serialization(self._get_work_results('sample_set', md5))['sample_set']['md5_list']

    @zerorpc.stream
    def stream_sample_set(self, md5):
        """ Stream a sample set (which is just a list of md5s).

            Args:
                md5: the md5 of the sample_set

            Returns:
                A generator that yields the md5s in the sample set
        """
        for md5 in self._get_work_results('sample_set', md5)['md5_list']:
            yield md5

    def get_datastore_uri(self):
        """ Gives you the current datastore URI.

            Args:
                None

            Returns:
                The URI of the data store currently being used by Workbench
        """
        return self.data_store.get_uri()


    ##################
    # Help
    ##################        
    def help(self, topic=None):
        """ Returns the formatted, colored help """
        if not topic:
            topic = 'workbench'

        # It's possible to ask for help on something that doesn't exist
        # so we'll catch the exception and push back an object that
        # indicates we didn't find what they were asking for
        try:
            return self.work_request('help_formatter', topic)['help_formatter']['help']
        except WorkBench.DataNotFound as e:

            # Okay this is a bit tricky we want to give the user a nice error
            # message that has both the md5 of what they were looking for and
            # a nice informative message that explains what might have happened
            sample_md5 = e.args[0]
            return '%s%s\n\t%s%s%s' % (color.Yellow, sample_md5, color.Green, e.message(), color.Normal)

    # Fixme: These are internal methods that basically just provide help text
    def _help_workbench(self):
        """ Help on Workbench """
        help = '%sWelcome to Workbench Help:%s' % (color.Yellow, color.Normal)
        help += '\n\t%s- workbench.help(\'basic\') %s for getting started help' % (color.Green, color.LightBlue)
        help += '\n\t%s- workbench.help(\'workers\') %s for help on available workers' % (color.Green, color.LightBlue)
        help += '\n\t%s- workbench.help(\'commands\') %s for help on workbench commands' % (color.Green, color.LightBlue)
        help += '\n\t%s- workbench.help(topic) %s where topic can be a help, command or worker' % (color.Green, color.LightBlue)
        help += '\n\n%sSee http://github.com/SuperCowPowers/workbench for more information\n%s' % (color.Yellow, color.Normal)
        return help

    def _help_basic(self):
        """ Help for Workbench Basics """
        help =  '%sWorkbench: Getting started...' % (color.Yellow)
        help += '\n%sStore a sample into Workbench:'  % (color.Green)
        help += '\n\t%s$ workbench.store_sample(raw_bytes, filename, type_tag)' % (color.LightBlue)
        help += '\n\n%sNotice store_sample returns an md5 of the sample...'% (color.Yellow)
        help += '\n%sRun workers on the sample (view, meta, whatever...):'  % (color.Green)
        help += '\n\t%s$ workbench.work_request(\'view\', md5)%s' % (color.LightBlue, color.Normal)
        return help

    def _help_commands(self):
        """ Help on all the available commands """
        help =  'Workbench Commands:'
        for command in self.list_all_commands():
            full_help = self.work_request('help_formatter', command)['help_formatter']['help']
            compact_help = full_help.split('\n')[:2]
            help += '\n\n%s' % '\n'.join(compact_help)
        return help

    def _help_workers(self):
        """ Help on all the available workers """
        help =  'Workbench Workers:'
        for worker in self.list_all_workers():
            full_help = self.work_request('help_formatter', worker)['help_formatter']['help']
            compact_help = full_help.split('\n')[:4]
            help += '\n\n%s' % '\n'.join(compact_help)
        return help


    ##################
    # Introspection
    ##################
    def list_all_commands(self):
        """ Returns a list of all the Workbench commands"""
        commands = [name for name, _ in inspect.getmembers(self, predicate=inspect.isroutine) if not name.startswith('_')]
        return commands

    def list_all_workers(self):
        """ List all the currently loaded workers """
        return list(self.plugin_meta.keys())

    def get_info(self, component):
        """ Get the information about this component """

        # Grab it, clean it and ship it
        work_results = self._get_work_results('info', component)
        return self.data_store.clean_for_serialization(work_results)

    def store_info(self, info_dict, component, type_tag):
        """ Store information about a component. The component could be a
            worker or a commands or a class, or whatever you want, the
            only thing to be aware of is name collisions. """

        # Enforce dictionary input
        if not isinstance(info_dict, dict):
            print('Critical: info_dict must be a python dictionary, got %s' % type(info_dict))
            return

        # Ensure values are not functions/methods/classes
        info_storage = {key:value for key, value in info_dict.items() if not hasattr(value, '__call__')}

        # Place the type_tag on it and store it
        info_storage['type_tag'] = type_tag
        self._store_work_results(info_storage, 'info', component)

    ##################
    # Testing
    ##################
    def test_worker(self, worker_name):
        """ Run the test for a specific worker """

        # First find the plugin
        try:
            plugin = self.plugin_meta[worker_name]
        except KeyError:
            return '%s worker not found.. misspelled?' % worker_name

        # Now try to run the test
        try:
            return plugin['test']()
        except (AttributeError, KeyError) as error:
            output = 'Failure for plugin: %s' % (worker_name)
            output += 'Error: %s' % error
            return output


    ####################
    # Internal Methods
    ####################
    def _store_information(self):
        """ Store infomation about Workbench and its commands """
        
        print('<<< Generating Information Storage >>>')

        # Stores information on Workbench commands and signatures
        for name, meth in inspect.getmembers(self, predicate=inspect.isroutine):
            if not name.startswith('_'):
                info = {'command': name, 'sig': str(funcsigs.signature(meth)), 'docstring': meth.__doc__}
                self.store_info(info, name, type_tag='command')

        # Stores help text into the workbench information system
        self.store_info({'help': '<<< Workbench Server Version %s >>>' % self.version}, 'version', type_tag='help')
        self.store_info({'help': self._help_workbench()}, 'workbench', type_tag='help')
        self.store_info({'help': self._help_basic()}, 'basic', type_tag='help')
        self.store_info({'help': self._help_commands()}, 'commands', type_tag='help')
        self.store_info({'help': self._help_workers()}, 'workers', type_tag='help')

    def _new_plugin(self, plugin):
        """ Internal: This method handles the mechanics around new plugins. """

        # First store the plugin info into our data store
        self.store_info(plugin, plugin['name'], type_tag='worker')

        # Place it into our active plugin list
        self.plugin_meta[plugin['name']] = plugin

    def _store_work_results(self, results, collection, md5):
        """ Internal: Stores the work results of a worker."""
        self.data_store.store_work_results(results, collection, md5)
    def _get_work_results(self, collection, md5):
        """ Internal: Method for fetching work results."""
        results = self.data_store.get_work_results(collection, md5)
        if not results:
            raise WorkBench.DataNotFound(md5 + ': Data/Sample not found...')
        return {collection: results}

    def _work_chain_mod_time(self, worker_name):
        """ Internal: We compute a modification time of a work chain.
            Returns:
                The newest modification time of any worker in the work chain. 
        """

        # Bottom out on sample, info or tags
        if worker_name=='sample' or worker_name=='info' or worker_name=='tags':
            return datetime.datetime(1970, 1, 1)

        my_mod_time = self._get_work_results('info', worker_name)['info']['mod_time']
        dependencies = self.plugin_meta[worker_name]['dependencies']
        if not dependencies:
            return my_mod_time
        else:
            depend_mod_times = [my_mod_time]
            for depend in dependencies:
                depend_mod_times.append(self._work_chain_mod_time(depend))
            return max(depend_mod_times)

    def _recursive_work_resolver(self, worker_name, md5):
        """ Internal: Input dependencies are recursively backtracked, invoked and then
               passed down the pipeline until getting to the requested worker. """

        # Looking for the sample?
        if worker_name == 'sample':
            return self.get_sample(md5)

        # Looking for info?
        if worker_name == 'info':
            return self._get_work_results('info', md5)

        # Looking for tags?
        if worker_name == 'tags':
            return self._get_work_results('tags', md5)

        # Do I actually have this plugin? (might have failed, etc)
        if (worker_name not in self.plugin_meta):
            print('Alert: Request for non-existing or failed plugin: %s' % (worker_name))
            return {}

        # If the results exist and the time_stamp is newer than the entire work_chain, I'm done
        collection = self.plugin_meta[worker_name]['name']
        try:
            work_results = self._get_work_results(collection, md5)
            work_chain_mod_time = self._work_chain_mod_time(worker_name)
            if work_chain_mod_time < work_results[collection]['__time_stamp']:
                return work_results
            elif self.VERBOSE:
                print('VERBOSE: %s work_chain is newer than data' % (worker_name))
        except WorkBench.DataNotFound:
            if self.VERBOSE:
                print('Verbose: %s data not found generating' % (worker_name))

        # Okay either need to generate (or re-generate) the work results
        dependencies = self.plugin_meta[worker_name]['dependencies']
        dependant_results = {}
        for dependency in dependencies:
            dependant_results.update(self._recursive_work_resolver(dependency, md5))
        if self.VERBOSE:
            print('Verbose: new work for plugin: %s' % (worker_name))
        work_results = self.plugin_meta[worker_name]['class']().execute(dependant_results)

        # Enforce dictionary output
        if not isinstance(work_results, dict):
            print('Critical: Plugin %s MUST produce a python dictionary!' % worker_name)
            return None

        # Store the results and return
        self._store_work_results(work_results, collection, md5)
        return self._get_work_results(collection, md5)

    def _find_element(self,d,k):
        if k in d: return d[k]
        submatch = [d[_k][k] for _k in d if k in d[_k]]
        return submatch[0] if submatch else None


def run():
    """ Run the workbench server """

    # Load the configuration file relative to this script location
    config_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.ini')
    workbench_conf = configparser.ConfigParser()
    config_ini = workbench_conf.read(config_path)
    if not config_ini:
        print('Could not locate config.ini file, tried %s : exiting...' % config_path)
        exit(1)

    # Pull configuration settings
    datastore_uri = workbench_conf.get('workbench', 'datastore_uri')
    database = workbench_conf.get('workbench', 'database')
    worker_cap = workbench_conf.getint('workbench', 'worker_cap')
    samples_cap = workbench_conf.getint('workbench', 'samples_cap')

    # Spin up Workbench ZeroRPC
    try:
        store_args = {'uri': datastore_uri, 'database': database, 'worker_cap':worker_cap, 'samples_cap':samples_cap}
        workbench = zerorpc.Server(WorkBench(store_args=store_args), name='workbench', heartbeat=60)
        workbench.bind('tcp://0.0.0.0:4242')
        print('\nWorkbench is ready and feeling super duper!')
        gevent_signal(signal.SIGTERM, workbench.stop)
        gevent_signal(signal.SIGINT, workbench.stop)
        gevent_signal(signal.SIGKILL, workbench.stop)
        workbench.run()
        print('\nWorkbench Server Shutting Down... and dreaming of sheep...')

    except zmq.error.ZMQError:
        print('\nInfo: Could not start Workbench server (no worries, probably already running...)\n')


# Test that just calls main
def test():
    run()

if __name__ == '__main__':
    run()
