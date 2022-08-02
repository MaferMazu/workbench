"""File Streaming for Workbench CLI"""

import os, sys
import lz4

class FileStreamer(object):
    """File Streaming for Workbench CLI"""

    def __init__(self, workbench, progress):
        ''' FileStreamer Initialization '''

        # Setup workbench and progress handles
        self.workbench = workbench
        self.progress = progress

        # Setup compression
        self.compressor = lz4.dumps
        self.decompressor = lz4.loads
        self.compress_ident = 'lz4'

        # Some defaults and counters
        self.chunk_size = 1024*1024 # 1 MB

    def _file_chunks(self, data, chunk_size):
        """ Yield compressed chunks from a data array"""
        for i in range(0, len(data), chunk_size):
            yield self.compressor(data[i:i+chunk_size])

    def stream_to_workbench(self, raw_bytes, filename, type_tag, tags):
        """Split up a large file into chunks and send to Workbench"""
        md5_list = []
        sent_bytes = 0
        total_bytes = len(raw_bytes)
        for chunk in self._file_chunks(raw_bytes, self.chunk_size):
            md5_list.append(self.workbench.store_sample(chunk, filename, self.compress_ident))
            sent_bytes += self.chunk_size
            self.progress(sent_bytes, total_bytes)

        # Now we just ask Workbench to combine these
        full_md5 = self.workbench.combine_samples(md5_list, filename, type_tag)

        # Add the tags
        self.workbench.add_tags(full_md5, tags)

        # Return the md5 of the finalized sample
        return full_md5
