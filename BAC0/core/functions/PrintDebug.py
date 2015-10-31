#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
Module : PrintDebug.py
Author : Christian Tremblay, ing.
Inspired a lot by the work of Joel Bender (joel@carrickbender.com)
Email : christian.tremblay@servisys.com
"""


def print_debug(msg, args):
    """
    Used to print info to console when debug mode active
    """
    args = args.split()
    if _DEBUG:
        WriteProperty._debug(msg, args)
