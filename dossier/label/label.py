from __future__ import absolute_import, division, print_function

from collections import namedtuple
from itertools import groupby, imap
import logging
import sys
import time as pytime


logger = logging.getLogger(__name__)


class Label(namedtuple('_Label', 'content_id1 content_id2 subtopic_id1 ' +
                                 'subtopic_id2 annotator_id time value')):
    def __new__(cls, content_id1, content_id2, annotator_id, value,
                subtopic_id1=None, subtopic_id2=None, time=None):
        assert value in (-1, 0, 1)
        if time is None:
            time = long(pytime.time() * 1000)
        if subtopic_id1 is None:
            subtopic_id1 = ''
        if subtopic_id2 is None:
            subtopic_id2 = ''
        return super(Label, cls).__new__(
            cls, content_id1=content_id1, content_id2=content_id2,
            subtopic_id1=subtopic_id1, subtopic_id2=subtopic_id2,
            annotator_id=annotator_id, time=time, value=value)

    def reversed(self):
        return self._replace(
            content_id1=self.content_id2, content_id2=self.content_id1,
            subtopic_id1=self.subtopic_id2, subtopic_id2=self.subtopic_id1)

    def _to_kvlayer(self):
        return (self._replace(time=-self.time)[0:len(self)-1], str(self.value))

    @staticmethod
    def _from_kvlayer((key, value)):
        cid1, cid2, subid1, subid2, ann, time = key
        return Label(content_id1=cid1, content_id2=cid2,
                     subtopic_id1=subid1, subtopic_id2=subid2,
                     annotator_id=ann, time=int(time), value=int(value))

    def __eq__(l1, l2):
        return (
            l1.annotator_id == l2.annotator_id
            and unordered_eq((l1.content_id1, l1.content_id2),
                             (l2.content_id1, l2.content_id2))
            and unordered_eq((l1.subtopic_id1, l1.subtopic_id2),
                             (l2.subtopic_id1, l2.subtopic_id2))
        )

    def __hash__(self):
        content_id = frozenset((self.content_id1, self.content_id2))
        subtopic_id = frozenset((self.subtopic_id1, self.subtopic_id2))
        return hash((self.annotator_id, content_id, subtopic_id))


class LabelStore(object):
    '''A label database.'''
    TABLE = 'label'

    _kvlayer_namespace = {
        # (cid1, cid2, subid1, subid2, annotator_id, time) -> value
        # N.B. The `long` type here is for the benefit of the underlying
        # database storage. It will hopefully result in a storage type
        # that is big enough to contain milliseconds epoch ticks.
        TABLE: (str, str, str, str, str, long),
    }

    def __init__(self, kvlclient):
        self.kvl = kvlclient
        self.kvl.setup_namespace(self._kvlayer_namespace)

    def put(self, label):
        logger.info('adding label "%r"', label)
        self.kvl.put(self.TABLE,
                     label._to_kvlayer(), label.reversed()._to_kvlayer())

    def get(self, cid1, cid2, annotator_id, subid1='', subid2=''):
        s = (cid1, cid2, subid1, subid2, annotator_id, -sys.maxint - 1)
        e = (cid1, cid2, subid1, subid2, annotator_id, sys.maxint)

        # We return the first result because the `kvlayer` abstraction
        # guarantees that the first result will be the most recent entry
        # for this particular key (since the timestamp is inserted as a
        # negative value).
        for row in self.kvl.scan(self.TABLE, (s, e)):
            return Label._from_kvlayer(row)
        return None, None

    def get_all_for_content_id(self, cid):
        s = (cid,)
        e = (cid + '\xff',)
        results = imap(Label._from_kvlayer, self.kvl.scan(self.TABLE, (s, e)))
        return latest_labels(results)

    def connected_component(self, cid):
        done = set()  # set of cids that we've queried with
        todo = set([cid])  # set of cids to do a query for
        labels = set()
        while todo:
            cid = todo.pop()
            done.add(cid)
            for label in self.get_all_for_content_id(cid):
                if label.content_id1 not in done:
                    todo.add(label.content_id1)
                if label.content_id2 not in done:
                    todo.add(label.content_id2)
                labels.add(label)
        return sorted(labels, key=lambda lab: lab.time)


def unordered_eq(pair1, pair2):
    (x1, y1), (x2, y2) = pair1, pair2
    return (x1 == x2 and y1 == y2) or (x1 == y2 and y1 == x2)


def latest_labels(label_iterable):
    for _, group in groupby(label_iterable):
        for lab in group:
            yield lab
            break
