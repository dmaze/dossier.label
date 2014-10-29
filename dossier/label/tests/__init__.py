'''dossier.label.tests

.. This software is released under an MIT/X11 open source license.
   Copyright 2012-2014 Diffeo, Inc.
'''
from __future__ import absolute_import, division, print_function

from pyquchk.arbitraries import int_, str_letters
import pytest

import kvlayer
import yakonfig


# Generators of random values.
coref_value = int_(low=-1, high=1, uniform=True)
id_ = str_letters


@pytest.yield_fixture
def kvl():
    config = {
        'storage_type': 'local',
        'app_name': 'diffeo',
        'namespace': 'dossier.label.tests',
    }
    with yakonfig.defaulted_config([kvlayer], params=config) as config:
        client = kvlayer.client()
        yield client
        client.delete_namespace()
        client.close()
