#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
#
# Licensed under LGPLv3, see file LICENSE in this source tree.
"""
This module define a way to simulate value of IO variables
"""

from .IOExceptions import OutOfServiceNotSet, OutOfServiceSet, NoResponseFromController, ApplicationNotStarted


class Simulation():
    """
    Global informations regarding simulation
    """
    def sim(self, args):
        """
        This function allow the simulation of IO points by turning on the
        out_of_service property. When out_of_service, write the value to
        the point

        :param args: String with <addr> <type> <inst> <prop> <value> [ <indx> ] [ <priority> ]

        """
        if not self._started:
            raise ApplicationNotStarted('App not running, use startApp() function')
        #with self.this_application._lock: if use lock...won't be able to call read...
        args = args.split()
        addr, obj_type, obj_inst, prop_id, value = args[:5]
        if self.read('%s %s %s outOfService' % (addr, obj_type, obj_inst)):
            self.write(
                '%s %s %s %s %s' %
                (addr, obj_type, obj_inst, prop_id, value))
        else:
            try:
                self.write(
                    '%s %s %s outOfService True' %
                    (addr, obj_type, obj_inst))
            except NoResponseFromController:
                pass
            try:
                if self.read('%s %s %s outOfService' %
                             (addr, obj_type, obj_inst)):
                    self.write('%s %s %s %s %s' %
                               (addr, obj_type, obj_inst, prop_id, value))
                else:
                    raise OutOfServiceNotSet()
            except NoResponseFromController:
                pass

    def release(self, args):
        """
        This function will turn out_of_service property to false so the
        point will resume it's normal behaviour

        :param args: String with <addr> <type> <inst>

        """
        if not self._started:
            raise ApplicationNotStarted('App not running, use startApp() function')
        args = args.split()
        addr, obj_type, obj_inst = args[:3]
        try:
            self.write(
                '%s %s %s outOfService False' %
                (addr, obj_type, obj_inst))
        except NoResponseFromController:
            pass
        try:
            if self.read('%s %s %s outOfService' % (addr, obj_type, obj_inst)):
                raise OutOfServiceSet()
            else:
                "Everything is ok"
                pass
        except NoResponseFromController:
            pass
