'''dossier.label.tests

.. This software is released under an MIT/X11 open source license.
   Copyright 2012-2014 Diffeo, Inc.
'''
from __future__ import absolute_import, division, print_function
import time

from pyquchk import qc

from dossier.label import Label
from dossier.label.tests import coref_value, id_


@qc
def test_label_reverse_equality(cid1=id_, cid2=id_, ann=id_, v=coref_value):
    lab = Label(cid1, cid2, ann, v)
    assert lab == lab.reversed()


@qc
def test_label_hash_equality(cid1=id_, cid2=id_, ann=id_,
                             v1=coref_value, v2=coref_value):
    lab1, lab2 = Label(cid1, cid2, ann, v1), Label(cid1, cid2, ann, v2)
    assert lab1 == lab2 and hash(lab1) == hash(lab2)


@qc
def test_label_hash_equality_unordered(cid1=id_, cid2=id_, ann=id_,
                                       v1=coref_value, v2=coref_value):
    lab1, lab2 = Label(cid1, cid2, ann, v1), Label(cid2, cid1, ann, v2)
    assert lab1 == lab2 and hash(lab1) == hash(lab2)


@qc
def test_label_most_recent_first(cid1=id_, cid2=id_, ann=id_,
                                 v1=coref_value, v2=coref_value):
    t = int(time.time() * 1000)
    lab1 = Label(cid1, cid2, ann, v1, epoch_ticks=t)
    lab2 = Label(cid1, cid2, ann, v2, epoch_ticks=t + 1)
    assert lab2 < lab1


@qc
def test_label_most_recent_first_unordered(cid1=id_, cid2=id_, ann=id_,
                                           v1=coref_value, v2=coref_value):
    t = int(time.time() * 1000)
    lab1 = Label(cid1, cid2, ann, v1, epoch_ticks=t)
    lab2 = Label(cid2, cid1, ann, v2, epoch_ticks=t + 1)
    assert lab2 < lab1
