
"""rekall_adapter: Helps Workbench utilize the Rekall Memory Forensic Framework.
    See Google Github: http://github.com/google/rekall
    All credit for good stuff goes to them, all credit for bad stuff goes to us. :).
"""


import os, sys
import logging
from rekall import session as rekall_session
from rekall.plugins.addrspaces import standard
from rekall.ui.renderer import BaseRenderer
from rekall.ui.text import Formatter
import datetime
import pprint
import pytz
import gevent
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

def gsleep():
    ''' Convenience method for gevent.sleep '''
    print '*** Gevent Sleep ***'
    gevent.sleep(0)

class RekallAdapter(object):
    """RekallAdapter: Helps utilize the Rekall Memory Forensic Framework."""

    def __init__(self, raw_bytes):
        """Initialization."""

        # Spin up the logging
        logging.getLogger().setLevel(logging.ERROR)

        self.session = MemSession(raw_bytes).get_session()
        self.formatter = Formatter(session=self.session)
        self.renderer = WorkbenchRenderer(self.formatter)

    def get_session(self):
        ''' Return the Rekall session object '''
        return self.session

    def get_renderer(self):
        ''' Return the Rekall renderer object '''
        return self.renderer


class MemSession(object):
    """MemSession: Helps utilize the Rekall Memory Forensic Framework."""

    def __init__(self, raw_bytes):
        """Create a Rekall session for this memory image (raw_bytes)"""

        # Spin up the logging
        logging.getLogger().setLevel(logging.ERROR)

        # Set up profile path
        local = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'profiles')
        remote = 'http://profiles.rekall-forensic.com'
        profile_path = [local, remote]

        # Open up a rekall session
        s = rekall_session.JsonSerializableSession(profile_path=profile_path)

        # Set up a memory space for our raw memory image
        with s:
            mem_file = StringIO(raw_bytes)
            s.physical_address_space = standard.FDAddressSpace(fhandle=mem_file, session=s)
            s.GetParameter("profile")

        # Store session handle
        self.session = s
 

    def get_session(self):
        """Get the current session handle."""
        return self.session

class WorkbenchRenderer(BaseRenderer):
    """Workbench Renderer: Extends BaseRenderer and simply populates local python
        data structures, not meant to be serialized or sent over the network."""

    def __init__(self, formatter):
        self.output_data = None
        self.active_section = None
        self.active_headers = None
        self.header_types = None
        self.incoming_section = False
        self.formatter = formatter
        self.start()

    def start(self, plugin_name=None, _kwargs=None):
        """Start method: initial data structures and store some meta data."""
        self.output_data = {'sections':{}}
        self.section('Info')        
        self.output_data['plugin_name'] = plugin_name
        return self

    def end(self):
        """Just a stub method."""

    def format(self, formatstring, *args):
        """Presentation Information from the Plugin"""

        # Make a new section
        if self.incoming_section:
            section_name = self.formatter.format(formatstring, *args).strip()
            self.section(section_name)
            self.incoming_section = False
        else:
            print 'Format called with %s' % self.formatter.format(formatstring, *args)

    def section(self, name=None, **_kwargs):
        """Called by the plugin when a new section is output"""

        # Check for weird case where an section call is made wit
        # no name and then a format call is made
        if not name:
            self.incoming_section = True
            return

        # Create a new section and make it the active one
        self.active_section = name
        self.output_data['sections'][self.active_section] = [] 

    def report_error(self, message):
        """Report an error"""
        print 'Error Message: %s' % message

    def table_header(self, columns=None, **kwargs):
        """A new table header"""
        if isinstance(columns[0], tuple):
            self.active_headers = [col[0] for col in columns]
            self.header_types = [col[1] for col in columns]
        else:
            self.active_headers = [col['cname'] for col in columns]
            self.header_types = [col['type'] if 'type' in col else 'unknown' for col in columns]

    def table_row(self, *args, **kwargs):
        """A new table row"""
        self.output_data['sections'][self.active_section]. \
            append(self._cast_row(self.active_headers, args, self.header_types))

    def write_data_stream(self):
        """Just a stub method."""
        print 'Calling write_data_stream on WorkbenchRenderer does nothing'

    def flush(self):
        """Just a stub method."""
        print 'Calling flush on WorkbenchRenderer does nothing'

    def open(self, directory=None, filename=None, mode="rb"):
        """Opens a file for writing or reading."""
        path = os.path.join(directory, filename)
        return open(path, mode) # Errr.. we need to close this somewhere...

    def render(self, plugin):
        """This method starts the plugin, calls render and returns the plugin output """
        self.start(plugin_name=plugin.name)
        plugin.render(self)
        return self.output_data

    def _cast_row(self, keys, values, data_types):
        """Internal method that makes sure that the row elements
            are properly cast into the correct types, instead of
            just treating everything like a string from the csv file
       ."""
        output_dict = {}
        for key, value, dtype in zip(keys, values, data_types):
            output_dict[key] = self._cast_value(value, dtype)

        return output_dict

    def _cast_value(self, value, dtype):
        """Internal method that makes sure any dictionary elements
            are properly cast into the correct types, instead of
            just treating everything like a string from the csv file
       ."""

        # Try to convert to a datetime
        if 'time' in dtype:
            date_time = value.as_datetime()
            if date_time == datetime.datetime(1970, 1, 1, 0, 0, tzinfo=pytz.utc): # Special case
                return '-'
            return date_time

        # Rekall puts a bunch of data_modeling semantics that we're just ignoring for now :(
        value = str(value)

        # Try conversion to basic types
        tests = (int, float, str)
        for test in tests:
            try:
                return test(value)
            except (AttributeError, ValueError):
                continue
        return value


# Unit test: Create the class, the proper input and run the execute() method for a test
import pytest
@pytest.mark.rekall
def test():
    """rekall_adapter.py: Test."""

    # Do we have the memory forensics file?
    data_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../data/memory_images/exemplar4.vmem')
    if not os.path.isfile(data_path):
        print 'Not finding exemplar4.mem... Downloading now...'
        import urllib
        urllib.urlretrieve('http://s3-us-west-2.amazonaws.com/workbench-data/memory_images/exemplar4.vmem', data_path)

    # Did we properly download the memory file?
    if not os.path.isfile(data_path):
        print 'Could not open exemplar4.vmem'
        sys.exit(1)

    # Got the file, now process it
    raw_bytes = open(data_path, 'rb').read()

    adapter = RekallAdapter(raw_bytes)
    session = adapter.get_session()
    renderer = adapter.get_renderer()

    # Create any kind of plugin supported by this session
    output = renderer.render(session.plugins.imageinfo())
    pprint.pprint(output.keys())
    assert 'Error' not in output

    output = renderer.render(session.plugins.pslist())
    pprint.pprint(output.keys())
    assert 'Error' not in output

    output = renderer.render(session.plugins.dlllist())
    pprint.pprint(output.keys())
    assert 'Error' not in output


    # Code coverage: These calls are simply for code coverage
    renderer.format('foo')
    renderer.section()
    renderer.format('foo')

if __name__ == "__main__":
    test()
