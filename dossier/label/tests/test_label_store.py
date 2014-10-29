'''dossier.label.tests

.. This software is released under an MIT/X11 open source license.
   Copyright 2012-2014 Diffeo, Inc.
'''
from __future__ import absolute_import, division, print_function

import pytest

from dossier.label import Label, LabelStore
from dossier.label.tests import kvl


@pytest.yield_fixture
def label_store(kvl):
    lstore = LabelStore(kvl)
    yield lstore
    lstore.delete_all()


# @pytest.mark.randomize(cid1=str, cid2=str, ann=str, v=int, 
                       # min_num=-1, max_num=1) 
# def test_put_get(label_store, cid1, cid2, ann, v): 
    # lab = Label(cid1, cid2, ann, v) 
    # label_store.put(lab) 
    # got = label_store.get(cid1, cid2, ann) 
    # assert lab == got and lab.value == got.value 
#  
#  
# @pytest.mark.randomize(cid1=str, cid2=str, ann=str, v=int, 
                       # min_num=-1, max_num=1) 
# def test_put_get_unordered(label_store, cid1, cid2, ann, v): 
    # lab = Label(cid1, cid2, ann, v) 
    # label_store.put(lab) 
    # got = label_store.get(cid2, cid1, ann) 
    # assert lab == got and lab.value == got.value 
#  
#  
# @pytest.mark.randomize(cid1=str, cid2=str, ann=str, v1=int, v2=int, 
                       # min_num=-1, max_num=1) 
# def test_put_get_recent(label_store, cid1, cid2, ann, v1, v2): 
    # lab1 = Label(cid1, cid2, ann, v1) 
    # lab2 = Label(cid1, cid2, ann, v2, epoch_ticks=lab1.epoch_ticks + 1) 
    # label_store.put(lab1) 
    # label_store.put(lab2) 
    # got = label_store.get(cid1, cid2, ann) 
    # assert lab1 == got and lab2 == got and lab2.value == got.value 
#  
#  
# @pytest.mark.randomize(cid1=str, cid2=str, ann=str, v1=int, v2=int, 
                       # min_num=-1, max_num=1) 
# def test_put_get_recent_unordered(label_store, cid1, cid2, ann, v1, v2): 
    # lab1 = Label(cid1, cid2, ann, v1) 
    # lab2 = Label(cid2, cid1, ann, v2, epoch_ticks=lab1.epoch_ticks + 1) 
    # label_store.put(lab1) 
    # label_store.put(lab2) 
    # got = label_store.get(cid1, cid2, ann) 
    # assert lab1 == got and lab2 == got and lab2.value == got.value 
#  
#  
# @pytest.mark.randomize(cid1=str, cid2=str, ann=str, v1=int, v2=int, 
                       # min_num=-1, max_num=1) 
# def test_direct_connect_recent(label_store, cid1, cid2, ann, v1, v2): 
    # lab1 = Label(cid1, cid2, ann, v1) 
    # lab2 = Label(cid1, cid2, ann, v2, epoch_ticks=lab1.epoch_ticks + 1) 
    # label_store.put(lab1) 
    # label_store.put(lab2) 
#  
    # direct = list(label_store.get_all_for_content_id(cid1)) 
    # assert direct == [lab2] and direct == [lab1] 
    # assert direct[0].value == lab2.value 
#  
    # direct = list(label_store.get_all_for_content_id(cid2)) 
    # assert direct == [lab2] and direct == [lab1] 
    # assert direct[0].value == lab2.value 
#  
#  
# @pytest.mark.randomize(cid1=str, cid2=str, ann=str, v1=int, v2=int, 
                       # min_num=-1, max_num=1) 
# def test_direct_connect_recent_unordered(label_store, cid1, cid2, ann, v1, v2): 
    # lab1 = Label(cid1, cid2, ann, v1) 
    # lab2 = Label(cid2, cid1, ann, v2, epoch_ticks=lab1.epoch_ticks + 1) 
    # label_store.put(lab1) 
    # label_store.put(lab2) 
#  
    # direct = list(label_store.get_all_for_content_id(cid1)) 
    # assert direct == [lab2] and direct == [lab1] 
    # assert direct[0].value == lab2.value 
#  
    # direct = list(label_store.get_all_for_content_id(cid2)) 
    # assert direct == [lab2] and direct == [lab1] 
    # assert direct[0].value == lab2.value 


def test_direct_connect(label_store):
    ab = Label('a', 'b', '', 1)
    ac = Label('a', 'c', '', 1)
    bc = Label('b', 'c', '', 1)
    label_store.put(ab)
    label_store.put(ac)
    label_store.put(bc)

    direct = list(label_store.get_all_for_content_id('a'))
    assert direct == [ab, ac]


def test_direct_connect_unordered(label_store):
    ab = Label('a', 'b', '', 1)
    ac = Label('c', 'a', '', 1)
    bc = Label('b', 'c', '', 1)
    label_store.put(ab)
    label_store.put(ac)
    label_store.put(bc)

    direct = list(label_store.get_all_for_content_id('a'))
    assert direct == [ab, ac]


def test_connected_component_basic(label_store):
    ab = Label('a', 'b', '', 1)
    ac = Label('a', 'c', '', 1)
    bc = Label('b', 'c', '', 1)
    label_store.put(ab)
    label_store.put(ac)
    label_store.put(bc)

    connected = list(label_store.connected_component('a', 1))
    assert frozenset(connected) == frozenset([ab, ac, bc])


def test_connected_component_unordered(label_store):
    ab = Label('a', 'b', '', 1)
    ac = Label('c', 'a', '', 1)
    bc = Label('b', 'c', '', 1)
    label_store.put(ab)
    label_store.put(ac)
    label_store.put(bc)

    connected = list(label_store.connected_component('a', 1))
    assert frozenset(connected) == frozenset([ab, ac, bc])


def test_connected_component_diff_value(label_store):
    ab = Label('a', 'b', '', 1)
    ac = Label('a', 'c', '', -1)
    bc = Label('b', 'c', '', 1)
    label_store.put(ab)
    label_store.put(ac)
    label_store.put(bc)

    connected = list(label_store.connected_component('a', 1))
    assert frozenset(connected) == frozenset([ab, bc])


def test_connected_component_many(label_store):
    ab = Label('a', 'b', '', 1)
    bc = Label('b', 'c', '', 1)
    cd = Label('c', 'd', '', 1)
    label_store.put(ab)
    label_store.put(bc)
    label_store.put(cd)

    connected = list(label_store.connected_component('a', 1))
    assert frozenset(connected) == frozenset([ab, bc, cd])


def test_connected_component_many_diff_value(label_store):
    ab = Label('a', 'b', '', 1)
    bc = Label('b', 'c', '', -1)
    cd = Label('c', 'd', '', 1)
    label_store.put(ab)
    label_store.put(bc)
    label_store.put(cd)

    connected = list(label_store.connected_component('a', 1))
    assert frozenset(connected) == frozenset([ab])


def test_connected_component_many_most_recent(label_store):
    ab = Label('a', 'b', '', 1)
    bc = Label('b', 'c', '', -1)
    cd = Label('c', 'd', '', 1)
    label_store.put(ab)
    label_store.put(bc)
    label_store.put(cd)

    connected = list(label_store.connected_component('a', 1))
    assert frozenset(connected) == frozenset([ab])

    # This label should overwrite the existing `bc` label and expand
    # the connected component to `cd` through transitivity.
    bc = Label('b', 'c', '', 1, epoch_ticks=bc.epoch_ticks + 1)
    label_store.put(bc)

    connected = list(label_store.connected_component('a', 1))
    assert frozenset(connected) == frozenset([ab, bc, cd])


def test_connected_component_many_most_recent_diff_value(label_store):
    ab = Label('a', 'b', '', 1)
    bc = Label('b', 'c', '', 1)
    cd = Label('c', 'd', '', 1)
    label_store.put(ab)
    label_store.put(bc)
    label_store.put(cd)

    connected = list(label_store.connected_component('a', 1))
    assert frozenset(connected) == frozenset([ab, bc, cd])

    # This label should overwrite the existing `bc` label and contract
    # the connected component to just `ab`.
    bc = Label('b', 'c', '', -1, epoch_ticks=bc.epoch_ticks + 1)
    label_store.put(bc)

    connected = list(label_store.connected_component('a', 1))
    assert frozenset(connected) == frozenset([ab])
