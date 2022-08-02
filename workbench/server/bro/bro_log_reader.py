"""This module handles the mechanics around easily pulling in Bro Log data.

   The read_log method is a generator (in the python sense) for rows in a Bro log,
   because of this, it's memory efficient and does not read the entire file into memory.
"""

import datetime
import optparse
import time


class BroLogReader(object):
    """This class implements a python based Bro Log Reader."""

    def __init__(self, convert_datetimes=True):
        """Init for BroLogReader."""
        self.delimiter = '\t'
        self.convert_datetimes = convert_datetimes

    def read_log(self, logfile):
        """The read_log method returns a memory efficient generator for rows in a Bro log.

        Usage: 
            rows = my_bro_reader.read_log(logfile)
            for row in rows:
                do something with row

        Args:
            logfile: The Bro Log file.
        """

        # Make sure we're at the beginning
        logfile.seek(0)

        # First parse the header of the bro log
        field_names, _ = self._parse_bro_header(logfile)

        # Note: SO stupid to write a csv reader, but csv.DictReader on Bro
        #       files was doing something weird with generator output that
        #       affected zeroRPC and gave 'could not route _zpc_more' error.
        #       So wrote my own, put a sleep at the end, seems to fix it.
        while 1:
            _line = next(logfile).strip()
            if not _line.startswith('#close'):
                yield self._cast_dict(dict(list(zip(field_names, _line.split(self.delimiter)))))
            else:
                time.sleep(.1) # Give time for zeroRPC to finish messages
                break


    def _parse_bro_header(self, logfile):
        """This method tries to parse the Bro log header section.

        Note: My googling is failing me on the documentation on the format,
        so just making a lot of assumptions and skipping some shit.
        Assumption 1: The delimeter is a tab.
        Assumption 2: Types are either time, string, int or float
        Assumption 3: The header always ends with #fields and #types as
                      the last two lines.

        Format example:
            #separator \x09
            #set_separator	,
            #empty_field	(empty)
            #unset_field	-
            #path	httpheader_recon
            #fields	ts	origin	useragent	header_events_json
            #types	time	string	string	string

        Args:
            logfile: The Bro log file.

        Returns:
            A tuple of 2 lists. One for field names and other for field types.
        """

        # Skip until you find the #fields line
        _line = next(logfile)
        while (not _line.startswith('#fields')):
            _line = next(logfile)

        # Read in the field names
        _field_names = _line.strip().split(self.delimiter)[1:]

        # Read in the types
        _line = next(logfile)
        _field_types = _line.strip().split(self.delimiter)[1:]

        # Return the header info
        return _field_names, _field_types

    def _cast_dict(self, data_dict):
        """Internal method that makes sure any dictionary elements
        are properly cast into the correct types, instead of
        just treating everything like a string from the csv file.

        Args:
            data_dict: dictionary containing bro log data.

        Returns:
            Cleaned Data dict.
        """
        for key, value in data_dict.items():
            data_dict[key] = self._cast_value(value)

        # Fixme: resp_body_data can be very large so removing it for now
        if 'resp_body_data' in data_dict:
            del data_dict['resp_body_data']

        return data_dict

    def _cast_value(self, value):
        """Internal method that makes sure every value in dictionary
        is properly cast into the correct types, instead of
        just treating everything like a string from the csv file.

        Args:
            value : The value to be casted

        Returns:
            A casted Value.
        """
        # Try to convert to a datetime (if requested)
        if (self.convert_datetimes):
            try:
                date_time = datetime.datetime.fromtimestamp(float(value))
                if datetime.datetime(1970, 1, 1) > date_time:
                    raise ValueError
                else:
                    return date_time

            # Next try a set of primitive types
            except ValueError:
                pass

        # Try conversion to basic types
        tests = (int, float, str)
        for test in tests:
            try:
                return test(value)
            except ValueError:
                continue
        return value


if __name__ == '__main__':

    # Handle command-line arguments
    PARSER = optparse.OptionParser()
    PARSER.add_option('--logfile', default=None, help='Logfile to read from.  Default: %default')
    (OPTIONS, ARGUMENTS) = PARSER.parse_args()
    print(OPTIONS, ARGUMENTS)

    # Create a BRO log file reader and pull from the logfile
    BRO_LOG = BroLogReader()
    RECORDS = BRO_LOG.read_log(open(OPTIONS.logfile, 'rb'))
    for row in RECORDS:
        print(row)
