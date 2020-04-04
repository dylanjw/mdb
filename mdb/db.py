#!/usr/bin/env python3

import json
from .utils import mutate_merge


class FileDb(dict):
    """
    Dictionary that saves to a json file on every write.

    Ive changed strategies a little bit.

    My initial idea was to append each write into
    the file. Then when initializing new FileDB instances, load each entry
    from the file and update the in-memory-dict, as they appear in the file so
    the last entry in the file has the highest precedence.

    Instead of doing that I am writing the whole dictionary to the file with
    json.dump.

    Another feature, is I made FileDB a subclass of `dict`, so that it can be a
    drop in replacement for the dict I had before. It now writes to the file on
    key sets and updates.

    Where I would take this next:

    Instead of writing to the file on every db set/update, it would only write a
    snapshot when possible.

    To do this, I would rewrite the server code to run in a non-blocking loop
    using asyncio. I would set a flag for when there have been writes since
    the last file write, and make `write_file_to_db` a coroutine. Then I would
    schedule `write_file_to_db` to run when the server was not busy with
    serving requests. I might need to force it to write when a maximum time
    is exceeded if the server is getting inundated with requests.

    This is essentially just a backup system for an in memory database,
    rather than a file based db. This is a simpler first step than implementing
    a fully filebased storage system. To do that, I would need to figure out
    some things, like how to partition the data in each read/write. postgres
    has something it calls "pages". If the reads/writes are concurrent or
    multi-threaded, how would I make sure that data in a read doesnt get stale?
    Implement locks? Use a queue to schedule reads and writes on the same page?
    """

    filename = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filename = "fdb.json"
        fdb = self.read_file_db()
        mutate_merge(self, fdb)

    def __setitem__(self, key, value):
        ret = super().__setitem__(key, value)
        self.write_file_to_db()
        return ret

    def write_file_to_db(self):
        with open(self.filename, 'w') as f:
            json.dump(self, f)

    def read_file_db(self):
        with open(self.filename, 'r') as f:
            return json.load(f)

    def __getitem__(self, key):
        return super().__getitem__(key)

    def update(self, *args, **kwargs):
        ret = super().update(*args, **kwargs)
        self.write_file_to_db()
        return ret


memdb = FileDb()
