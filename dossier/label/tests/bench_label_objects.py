'''Some benchmarks for label construction.

This code demonstrates the performance differences between the
different choices of label representation. Notably, the current
representation is the slowest (by an order of magnitude compared
against the fastest, which is just a raw tuple).

The second fastest is a plain namedtuple with nothing going on
in its constructor. Apparently, we're paying dearly for all the
case analysis in ``dossier.label.Label.__new__``.

This performance comparison may be important some day because label
filtering is done *after* the construction of label objects, which
means we're being wasteful. (But it's oh-so convenient!)

To run the benchmarks, use ``python bench_label_objects.py``.
'''
from __future__ import absolute_import, division, print_function

from collections import namedtuple
import time
from timeit import timeit

from dossier.label import Label as RealLabel, CorefValue

cid, subid, ann_id, ticks = 'cid', 'subid', 'annid', int(time.time() * 1000)
coref_value = CorefValue.Positive


Label = namedtuple('_Label', 'content_id1 content_id2 subtopic_id1 ' +
                             'subtopic_id2 annotator_id epoch_ticks '+
                             'value')

class LabelSlots(object):
    __slots__ = ['cid1', 'cid2', 'subid1', 'subid2', 'ann_id', 'ticks', 'val']
    def __init__(self, cid1, cid2, ann_id, v, subid1, subid2, ticks):
        self.cid1, self.cid2 = cid1, cid2
        self.subid1, self.subid2 = subid1, subid2
        self.ann_id, self.val, self.ticks = ann_id, v, ticks


def bench_slots():
    for _ in xrange(100):
        LabelSlots(cid, cid, ann_id, coref_value, subid, subid, ticks)


def bench_real_namedtuple():
    for _ in xrange(100):
        RealLabel(cid, cid, ann_id, coref_value, subid, subid, ticks)


def bench_namedtuple():
    for _ in xrange(100):
        Label(cid, cid, ann_id, coref_value, subid, subid, ticks)


def bench_tuple():
    for _ in xrange(100):
        (cid, cid, ann_id, coref_value, subid, subid, ticks)


def run_benchmark(name):
    print(name)
    seconds = timeit(
        '%s()' % name, setup='from __main__ import %s' % name, number=10000)
    print(seconds)
    print()


if __name__ == '__main__':
    for item_name in globals().keys():
        if not item_name.startswith('bench_'):
            continue
        run_benchmark(item_name)
