'''dossier.label.tests

.. This software is released under an MIT/X11 open source license.
   Copyright 2012-2014 Diffeo, Inc.
'''
from __future__ import absolute_import, division, print_function
import time

import pytest

from dossier.label import Label


@pytest.mark.randomize(cid1=str, cid2=str, ann=str, v=int,
                       min_num=-1, max_num=1)
def test_label_reverse_equality(cid1, cid2, ann, v):
    lab = Label(cid1, cid2, ann, v)
    assert lab == lab.reversed()


@pytest.mark.randomize(cid1=str, cid2=str, ann=str, v1=int, v2=int,
                       min_num=-1, max_num=1)
def test_label_hash_equality(cid1, cid2, ann, v1, v2):
    lab1, lab2 = Label(cid1, cid2, ann, v1), Label(cid1, cid2, ann, v2)
    assert lab1 == lab2 and hash(lab1) == hash(lab2)


@pytest.mark.randomize(cid1=str, cid2=str, ann=str, v1=int, v2=int,
                       min_num=-1, max_num=1)
def test_label_hash_equality_unordered(cid1, cid2, ann, v1, v2):
    lab1, lab2 = Label(cid1, cid2, ann, v1), Label(cid2, cid1, ann, v2)
    assert lab1 == lab2 and hash(lab1) == hash(lab2)


@pytest.mark.randomize(cid1=str, cid2=str, ann=str, v1=int, v2=int,
                       min_num=-1, max_num=1)
def test_label_most_recent_first(cid1, cid2, ann, v1, v2):
    t = int(time.time() * 1000)
    lab1 = Label(cid1, cid2, ann, v1, epoch_ticks=t)
    lab2 = Label(cid1, cid2, ann, v2, epoch_ticks=t + 1)
    assert lab2 < lab1

    
@pytest.mark.randomize(cid1=str, cid2=str, ann=str, v1=int, v2=int,
                       min_num=-1, max_num=1)
def test_label_most_recent_first_unordered(cid1, cid2, ann, v1, v2):
    t = int(time.time() * 1000)
    lab1 = Label(cid1, cid2, ann, v1, epoch_ticks=t)
    lab2 = Label(cid2, cid1, ann, v2, epoch_ticks=t + 1)
    assert lab2 < lab1
