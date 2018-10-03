#!/usr/bin/env python
# -*- coding utf-8 -*-

"""
Test Bacpypes version
"""

import bacpypes

def test_BacpypesVersion():
    maj, minor, patch = bacpypes.__version__.split('.')
    assert float(maj) == 0
    assert float(minor) == 17
    assert float(patch) >= 5
