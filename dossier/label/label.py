'''dossier.label.label

.. This software is released under an MIT/X11 open source license.
   Copyright 2012-2014 Diffeo, Inc.
'''
from __future__ import absolute_import, division, print_function

from collections import namedtuple
from datetime import datetime
import functools
from itertools import groupby, imap
import logging
import sys
import time

import enum


logger = logging.getLogger(__name__)


MAX_MILLI_TICKS = ((60 * 60 * 24) * 365 * 100) * 1000
'''The maximum number of milliseconds supported.

Our kvlayer backend cannot (currently) guarantee a correct ordering
of signed integers, but can guarantee a correct ordering of unsigned
integers.

Labels, however, should be sorted with the most recent label first.
This is trivially possible by negating its epoch ticks.

Because kvlayer cannot guarantee a correct ordering of signed integers,
we avoid the sign switch by subtracting the ticks from an arbitrary
date in the future (UNIX epoch + 100 years).
'''


class CorefValue(enum.Enum):
    '''
    An enumeration that describes the value of a coreference judgment by a
    human. The judgment is always made with respect to a pair of content
    items.

    :cvar Negative: The two items are not coreferent.
    :cvar Unknown: It is unknown whether the two items are coreferent.
    :cvar Positive: The two items are coreferent.
    '''
    Negative = -1
    Unknown = 0
    Positive = 1


@functools.total_ordering
class Label(namedtuple('_Label', 'content_id1 content_id2 subtopic_id1 ' +
                                 'subtopic_id2 annotator_id epoch_ticks '+
                                 'value')):
    '''A label is an immutable unit of ground truth data.'''

    def __new__(cls, content_id1, content_id2, annotator_id, value,
                subtopic_id1=None, subtopic_id2=None, epoch_ticks=None):
        # `__new__` is overridden instead of `__init__` because `namedtuple`
        # defines a `__new__` method. We modify construction by making
        # several values optional.
        if isinstance(value, int):
            value = CorefValue(value)
        if epoch_ticks is None:
            epoch_ticks = long(time.time() * 1000)
        if subtopic_id1 is None:
            subtopic_id1 = ''
        if subtopic_id2 is None:
            subtopic_id2 = ''
        return super(Label, cls).__new__(
            cls, content_id1=content_id1, content_id2=content_id2,
            subtopic_id1=subtopic_id1, subtopic_id2=subtopic_id2,
            annotator_id=annotator_id, epoch_ticks=epoch_ticks, value=value)

    def reversed(self):
        '''Returns a new label with ids swapped.

        This method satisfies the following law: for every label
        ``lab``, ``lab == lab.reversed()``.
        '''
        return self._replace(
            content_id1=self.content_id2, content_id2=self.content_id1,
            subtopic_id1=self.subtopic_id2, subtopic_id2=self.subtopic_id1)

    def _to_kvlayer(self):
        '''Converts this label to a kvlayer tuple.

        The tuple returned can be used directly in a :mod:`kvlayer`
        ``put`` call.

        :rtype: ``(key, value)``
        '''
        epoch_ticks_rev = MAX_MILLI_TICKS - self.epoch_ticks
        negated = self._replace(epoch_ticks=epoch_ticks_rev)[0:len(self)-1]
        return (negated, str(self.value.value))

    @staticmethod
    def _from_kvlayer(row):
        '''Create a new :cls:`Label` from a kvlayer result.

        The ``row`` should be a tuple of ``(key, value)``
        where ``key`` corresponds to the namespace defined at
        :attr:`LabelStore._kvlayer_namespace`.

        :type row: ``(key, value)``
        :rtype: :cls:`Label`
        '''
        key, value = row
        cid1, cid2, subid1, subid2, ann, ticks = key
        return Label(content_id1=cid1, content_id2=cid2,
                     subtopic_id1=subid1, subtopic_id2=subid2, annotator_id=ann,
                     epoch_ticks=MAX_MILLI_TICKS - int(ticks),
                     value=int(value))

    def __lt__(l1, l2):
        '''Defines a total ordering for labels.

        The ordering is meant to be the same as the ordering used
        in the underlying database storage. Namely, the key used
        to determine ordering is: ``(cid1, cid2, subid1, subid2,
        annotator_id, MAX_TIME - epoch_ticks)`` where ``cid1 <= cid2``
        and ``subid1 <= subid2``.

        Notably, the ordering does not include the coreferent ``value``
        and it complements ``epoch_ticks`` so that more recent
        labels appear first in ascending order.
        '''
        return l1._cmp_value < l2._cmp_value

    @property
    def _cmp_value(self):
        cid1, cid2 = normalize_pair(self.content_id1, self.content_id2)
        subid1, subid2 = normalize_pair(self.subtopic_id1, self.subtopic_id2)
        ticks = time_complement(self.epoch_ticks)
        return (cid1, cid2, subid1, subid2, self.annotator_id, ticks)

    def __eq__(l1, l2):
        '''Tests equality between two labels.

        Equality is keyed on ``annotator_id`` and the unordered
        comparison between content ids and subtopic ids.

        This definition of equality does not include the values for
        ``epoch_ticks`` or ``value``.
        '''
        return (
            l1.annotator_id == l2.annotator_id
            and unordered_pair_eq((l1.content_id1, l1.content_id2),
                                  (l2.content_id1, l2.content_id2))
            and unordered_pair_eq((l1.subtopic_id1, l1.subtopic_id2),
                                  (l2.subtopic_id1, l2.subtopic_id2))
        )

    def __hash__(self):
        '''Returns a hash of this label.

        The hash is made up of the content ids, subtopic ids and the
        annotator id. This hash function obeys the following law:
        for all labels ``x`` and ``y``, ``x == y`` if and only if
        ``hash(x) == hash(y)``.
        '''
        # This code is clearer if we use `frozenset`, but let's avoid
        # creating intermediate objects.
        cid1, cid2 = normalize_pair(self.content_id1, self.content_id2)
        subid1, subid2 = normalize_pair(self.subtopic_id1, self.subtopic_id2)
        return hash((self.annotator_id, cid1, cid2, subid1, subid2))

    def __repr__(self):
        tpl = 'Label({cid1}, {cid2}, ' + \
                    '{subid1}{subid2}annotator={ann}, {tstr}, value={v})'
        subid1, subid2 = '', ''
        if self.subtopic_id1:
            subid1 = 'subtopic1=%s, ' % self.subtopic_id1
        if self.subtopic_id2:
            subid2 = 'subtopic2=%s, ' % self.subtopic_id2
        dt = datetime.utcfromtimestamp(self.epoch_ticks / 1000.0)
        return tpl.format(cid1=self.content_id1, cid2=self.content_id2,
                         subid1=subid1, subid2=subid2, tstr=str(dt),
                         ann=self.annotator_id, v=self.value)


class LabelStore(object):
    '''A label database.'''
    config_name = 'dossier.label'
    TABLE = 'label'

    _kvlayer_namespace = {
        # (cid1, cid2, subid1, subid2, annotator_id, time) -> value
        # N.B. The `long` type here is for the benefit of the underlying
        # database storage. It will hopefully result in a storage type
        # that is big enough to contain milliseconds epoch ticks. (A 64 bit
        # integer is more than sufficient, which makes `long` unnecessary from
        # a Python 2 perspective.)
        TABLE: (str, str, str, str, str, long),
    }

    def __init__(self, kvlclient):
        '''Create a new label store.

        :type kvlclient: :cls:`kvlayer._abstract_storage.AbstractStorage`
        :rtype: :cls:`LabelStore`
        '''
        self.kvl = kvlclient
        self.kvl.setup_namespace(self._kvlayer_namespace)

    def put(self, label):
        '''Add a new label to the store.

        :type label: :cls:`Label`
        '''
        logger.info('adding label "%r"', label)
        self.kvl.put(self.TABLE,
                     label._to_kvlayer(), label.reversed()._to_kvlayer())

    def get(self, cid1, cid2, annotator_id, subid1='', subid2=''):
        '''Retrieve a label from the store.

        When ``subid1`` and ``subid2`` are empty, then a label without
        subtopic identifiers will be returned.

        Note that the combination of content ids, subtopic ids and
        an annotator id *uniquely* identifies a label.

        :rtype: :cls:`Label`
        :raises: :exc:`KeyError` if no label could be found.
        '''
        s = (cid1, cid2, subid1, subid2, annotator_id, long(-sys.maxint - 1))
        e = (cid1, cid2, subid1, subid2, annotator_id, long(sys.maxint))

        # We return the first result because the `kvlayer` abstraction
        # guarantees that the first result will be the most recent entry
        # for this particular key (since the timestamp is inserted as a
        # complement value).
        for row in self.kvl.scan(self.TABLE, (s, e)):
            return Label._from_kvlayer(row)
        raise KeyError((s, e))

    def get_all_for_content_id(self, content_id):
        '''Return a generator of labels connected to ``content_id``.

        If no labels are defined for ``content_id``, then the generator
        will yield no labels.

        Note that this only returns *directly* connected labels. It
        will not follow transitive relationships.

        :rtype: generator of :cls:`Label`
        '''
        s = (content_id,)
        e = (content_id + '\xff',)
        results = imap(Label._from_kvlayer, self.kvl.scan(self.TABLE, (s, e)))
        return latest_labels(results)

    def connected_component(self, content_id, value):
        '''Return a connected component for ``content_id``.

        Given a ``content_id`` and a coreferent ``value`` (which must
        be ``-1``, ``0`` or ``1``), return the corresponding connected
        component by following all transitive relationships.

        For example, if ``(a, b, 1)`` is a label and ``(b, c, 1)`` is
        a label, then ``connected_component('a', 1)`` will return both
        labels even though ``a`` and ``c`` are not directly connected.

        The ``value`` indicates which labels to include in the
        connected component.
        '''
        if isinstance(value, int):
            value = CorefValue(value)
        done = set()  # set of cids that we've queried with
        todo = set([content_id])  # set of cids to do a query for
        labels = set()
        while todo:
            cid = todo.pop()
            done.add(cid)
            for label in self.get_all_for_content_id(cid):
                if label.value != value:
                    continue
                if label.content_id1 not in done:
                    todo.add(label.content_id1)
                if label.content_id2 not in done:
                    todo.add(label.content_id2)
                labels.add(label)
        return list(labels)

    def everything(self, include_deleted=False):
        '''Returns a generator of all labels in the store.

        If ``include_deleted`` is ``True``, labels that have been
        deleted are also included.

        :rtype: generator of :cls:`Label`
        '''
        results = imap(Label._from_kvlayer, self.kvl.scan(self.TABLE))
        return results if include_deleted else latest_labels(results)

    def delete_all(self):
        '''Deletes all labels in the store.'''
        self.kvl.clear_table(self.TABLE)


def unordered_pair_eq(pair1, pair2):
    '''Performs pairwise unordered equality.

    ``pair1`` == ``pair2`` if and only if
    ``frozenset(pair1)`` == ``frozenset(pair2)``.
    '''
    (x1, y1), (x2, y2) = pair1, pair2
    return (x1 == x2 and y1 == y2) or (x1 == y2 and y1 == x2)


def normalize_pair(x, y):
    '''Normalize a pair of values.

    Returns ``(y, x)`` if and only if ``y < x`` and ``(x, y)``
    otherwise.
    '''
    if y < x:
        return y, x
    else:
        return x, y


def latest_labels(label_iterable):
    '''Returns the most recent labels from a sorted iterable.
    '''
    for _, group in groupby(label_iterable):
        for lab in group:
            yield lab
            break


def time_complement(t):
    return MAX_MILLI_TICKS - t
