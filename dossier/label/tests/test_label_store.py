'''dossier.label.tests

.. This software is released under an MIT/X11 open source license.
   Copyright 2012-2014 Diffeo, Inc.
'''
from __future__ import absolute_import, division, print_function

from pyquchk import qc
import pytest

from dossier.label import Label, LabelStore
from dossier.label.tests import kvl, coref_value, id_


@pytest.yield_fixture
def label_store(kvl):
    lstore = LabelStore(kvl)
    yield lstore
    lstore.delete_all()


def test_put_get(label_store):
    @qc
    def _(cid1=id_, cid2=id_, ann=id_, v=coref_value):
        label_store.delete_all()

        lab = Label(cid1, cid2, ann, v)
        label_store.put(lab)
        got = label_store.get(cid1, cid2, ann)
        assert lab == got and lab.value == got.value
    _()


def test_put_get_unordered(label_store):
    @qc
    def _(cid1=id_, cid2=id_, ann=id_, v=coref_value):
        label_store.delete_all()

        lab = Label(cid1, cid2, ann, v)
        label_store.put(lab)
        got = label_store.get(cid2, cid1, ann)
        assert lab == got and lab.value == got.value
    _()


def test_put_get_recent(label_store):
    @qc
    def _(cid1=id_, cid2=id_, ann=id_, v1=coref_value, v2=coref_value):
        label_store.delete_all()

        lab1 = Label(cid1, cid2, ann, v1)
        lab2 = Label(cid1, cid2, ann, v2, epoch_ticks=lab1.epoch_ticks + 1)
        label_store.put(lab1)
        label_store.put(lab2)
        got = label_store.get(cid1, cid2, ann)
        assert lab1 == got and lab2 == got and lab2.value == got.value
    _()


def test_put_get_recent_unordered(label_store):
    @qc
    def _(cid1=id_, cid2=id_, ann=id_, v1=coref_value, v2=coref_value):
        label_store.delete_all()

        lab1 = Label(cid1, cid2, ann, v1)
        lab2 = Label(cid2, cid1, ann, v2, epoch_ticks=lab1.epoch_ticks + 1)
        label_store.put(lab1)
        label_store.put(lab2)
        got = label_store.get(cid1, cid2, ann)
        assert lab1 == got and lab2 == got and lab2.value == got.value
    _()


def test_direct_connect_recent(label_store):
    @qc
    def _(cid1=id_, cid2=id_, ann=id_, v1=coref_value, v2=coref_value):
        label_store.delete_all()

        lab1 = Label(cid1, cid2, ann, v1)
        lab2 = Label(cid1, cid2, ann, v2, epoch_ticks=lab1.epoch_ticks + 1)
        label_store.put(lab1)
        label_store.put(lab2)

        direct = list(label_store.get_all_for_content_id(cid1))
        assert direct == [lab2] and direct == [lab1]
        assert direct[0].value == lab2.value

        direct = list(label_store.get_all_for_content_id(cid2))
        assert direct == [lab2] and direct == [lab1]
        assert direct[0].value == lab2.value
    _()


def test_direct_connect_recent_unordered(label_store):
    @qc
    def _(cid1=id_, cid2=id_, ann=id_, v1=coref_value, v2=coref_value):
        label_store.delete_all()

        lab1 = Label(cid1, cid2, ann, v1)
        lab2 = Label(cid2, cid1, ann, v2, epoch_ticks=lab1.epoch_ticks + 1)
        label_store.put(lab1)
        label_store.put(lab2)

        direct = list(label_store.get_all_for_content_id(cid1))
        assert direct == [lab2] and direct == [lab1]
        assert direct[0].value == lab2.value

        direct = list(label_store.get_all_for_content_id(cid2))
        assert direct == [lab2] and direct == [lab1]
        assert direct[0].value == lab2.value
    _()


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

    connected = list(label_store.connected_component('a'))
    assert frozenset(connected) == frozenset([ab, ac, bc])


def test_connected_component_unordered(label_store):
    ab = Label('a', 'b', '', 1)
    ac = Label('c', 'a', '', 1)
    bc = Label('b', 'c', '', 1)
    label_store.put(ab)
    label_store.put(ac)
    label_store.put(bc)

    connected = list(label_store.connected_component('a'))
    assert frozenset(connected) == frozenset([ab, ac, bc])


def test_connected_component_diff_value(label_store):
    ab = Label('a', 'b', '', 1)
    ac = Label('a', 'c', '', -1)
    bc = Label('b', 'c', '', 1)
    label_store.put(ab)
    label_store.put(ac)
    label_store.put(bc)

    connected = list(label_store.connected_component('a'))
    assert frozenset(connected) == frozenset([ab, bc])


def test_connected_component_many(label_store):
    ab = Label('a', 'b', '', 1)
    bc = Label('b', 'c', '', 1)
    cd = Label('c', 'd', '', 1)
    label_store.put(ab)
    label_store.put(bc)
    label_store.put(cd)

    connected = list(label_store.connected_component('a'))
    assert frozenset(connected) == frozenset([ab, bc, cd])


def test_connected_component_many_diff_value(label_store):
    ab = Label('a', 'b', '', 1)
    bc = Label('b', 'c', '', -1)
    cd = Label('c', 'd', '', 1)
    label_store.put(ab)
    label_store.put(bc)
    label_store.put(cd)

    connected = list(label_store.connected_component('a'))
    assert frozenset(connected) == frozenset([ab])


def test_connected_component_many_most_recent(label_store):
    ab = Label('a', 'b', '', 1)
    bc = Label('b', 'c', '', -1)
    cd = Label('c', 'd', '', 1)
    label_store.put(ab)
    label_store.put(bc)
    label_store.put(cd)

    connected = list(label_store.connected_component('a'))
    assert frozenset(connected) == frozenset([ab])

    # This label should overwrite the existing `bc` label and expand
    # the connected component to `cd` through transitivity.
    bc = Label('b', 'c', '', 1, epoch_ticks=bc.epoch_ticks + 1)
    label_store.put(bc)

    connected = list(label_store.connected_component('a'))
    assert frozenset(connected) == frozenset([ab, bc, cd])


def test_connected_component_many_most_recent_diff_value(label_store):
    ab = Label('a', 'b', '', 1)
    bc = Label('b', 'c', '', 1)
    cd = Label('c', 'd', '', 1)
    label_store.put(ab)
    label_store.put(bc)
    label_store.put(cd)

    connected = list(label_store.connected_component('a'))
    assert frozenset(connected) == frozenset([ab, bc, cd])

    # This label should overwrite the existing `bc` label and contract
    # the connected component to just `ab`.
    bc = Label('b', 'c', '', -1, epoch_ticks=bc.epoch_ticks + 1)
    label_store.put(bc)

    connected = list(label_store.connected_component('a'))
    assert frozenset(connected) == frozenset([ab])


def test_expand(label_store):
    ab = Label('a', 'b', '', 1)
    bc = Label('b', 'c', '', 1)
    cd = Label('c', 'd', '', 1)
    ae = Label('a', 'e', '', -1)
    fg = Label('f', 'g', '', 1)

    label_store.put(ab)
    label_store.put(bc)
    label_store.put(cd)
    label_store.put(ae)
    label_store.put(fg)

    def get_pair(label):
        return (label.content_id1, label.content_id2)

    correct_pairs = [('a', 'b'),
                     ('a', 'c'),
                     ('a', 'd'),
                     ('b', 'c'),
                     ('b', 'd'),
                     ('c', 'd')]

    expansion = label_store.expand('a')

    assert frozenset(map(get_pair, expansion)) == \
        frozenset(correct_pairs)

    expansion = label_store.expand('e')

    assert frozenset(map(get_pair, expansion)) == frozenset([])

    expansion = label_store.expand('f')

    correct_pairs = [('f', 'g')]

    assert frozenset(map(get_pair, expansion)) == frozenset(correct_pairs)


def test_negative_label_inference(label_store):
    ac = Label('a', 'c', '', 1)
    bc = Label('b', 'c', '', 1)

    de = Label('d', 'e', '', 1)
    df = Label('d', 'f', '', 1)
    dg = Label('d', 'g', '', -1)

    cd = Label('c', 'd', '', -1)

    label_store.put(ac)
    label_store.put(bc)
    label_store.put(de)
    label_store.put(df)
    label_store.put(cd)
    label_store.put(dg)

    def get_pair(label):
        return (label.content_id1, label.content_id2)

    correct_pairs = [('c', 'e'),
                     ('c', 'f'),
                     ('d', 'a'),
                     ('d', 'b'),
                     ('c', 'd')]

    inference = label_store.negative_label_inference(cd)

    assert frozenset(map(get_pair, inference)) == \
        frozenset(correct_pairs)


def test_negative_inference(label_store):
    ac = Label('a', 'c', '', 1)
    bc = Label('b', 'c', '', 1)

    de = Label('d', 'e', '', 1)
    df = Label('d', 'f', '', 1)

    cg = Label('c', 'g', '', -1)
    dg = Label('d', 'g', '', -1)

    hg = Label('h', 'g', '', 1)

    label_store.put(ac)
    label_store.put(bc)
    label_store.put(de)
    label_store.put(df)
    label_store.put(cg)
    label_store.put(dg)
    label_store.put(hg)

    def get_pair(label):
        return (label.content_id1, label.content_id2)

    correct_pairs = [('g', 'a'),
                     ('g', 'b'),
                     ('c', 'h'),
                     ('g', 'e'),
                     ('g', 'f'),
                     ('d', 'h'),
                     ('g', 'c'),
                     ('g', 'd')]

    inference = label_store.negative_inference('g')

    assert frozenset(map(get_pair, inference)) == \
        frozenset(correct_pairs)
