#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
"""
Simulate.py - simulate the value of controller I/O values
"""

# --- standard Python modules ---
# --- 3rd party modules ---
# --- this application's modules ---
from .IOExceptions import (
    OutOfServiceNotSet,
    OutOfServiceSet,
    NoResponseFromController,
    ApplicationNotStarted,
)


# ------------------------------------------------------------------------------


class Simulation:
    """
    Global informations regarding simulation
    """

    def sim(self, args):
        """
        Simulate I/O points by setting the Out_Of_Service property, then doing a 
        WriteProperty to the point's Present_Value.

        :param args: String with <addr> <type> <inst> <prop> <value> [ <indx> ] [ <priority> ]

        """
        if not self._started:
            raise ApplicationNotStarted("BACnet stack not running - use startApp()")

        # with self.this_application._lock: if use lock...won't be able to call read...
        args = args.split()
        addr, obj_type, obj_inst, prop_id, value = args[:5]

        if self.read("{} {} {} outOfService".format(addr, obj_type, obj_inst)):
            self.write(
                "{} {} {} {} {}".format(addr, obj_type, obj_inst, prop_id, value)
            )
        else:
            try:
                self.write(
                    "{} {} {} outOfService True".format(addr, obj_type, obj_inst)
                )
            except NoResponseFromController as e:
                self._log.warning(
                    "Failed to write to OutOfService property ({})".format(e)
                )

            try:
                if self.read("{} {} {} outOfService".format(addr, obj_type, obj_inst)):
                    self.write(
                        "{} {} {} {} {}".format(
                            addr, obj_type, obj_inst, prop_id, value
                        )
                    )
                else:
                    raise OutOfServiceNotSet()
            except NoResponseFromController as e:
                self._log.warning(
                    "Failed to write to OutOfService property ({})".format(e)
                )

    def out_of_service(self, args):
        """
        Set the Out_Of_Service property so the Present_Value of an I/O may be written.

        :param args: String with <addr> <type> <inst> <prop> <value> [ <indx> ] [ <priority> ]

        """
        if not self._started:
            raise ApplicationNotStarted("BACnet stack not running - use startApp()")

        # with self.this_application._lock: if use lock...won't be able to call read...
        args = args.split()
        addr, obj_type, obj_inst = args[:3]
        try:
            self.write("{} {} {} outOfService True".format(addr, obj_type, obj_inst))
        except NoResponseFromController as e:
            self._log.warning("Failed to write to OutOfService property ({})".format(e))

    def release(self, args):
        """
        Set the Out_Of_Service property to False - to release the I/O point back to 
        the controller's control.

        :param args: String with <addr> <type> <inst>

        """
        if not self._started:
            raise ApplicationNotStarted("BACnet stack not running - use startApp()")

        args = args.split()
        addr, obj_type, obj_inst = args[:3]
        try:
            self.write("{} {} {} outOfService False".format(addr, obj_type, obj_inst))
        except NoResponseFromController as e:
            self._log.warning("Failed to write to OutOfService property ({})".format(e))

        try:
            if self.read("{} {} {} outOfService".format(addr, obj_type, obj_inst)):
                raise OutOfServiceSet()
            else:
                pass  # Everything is ok"
        except NoResponseFromController as e:
            self._log.warning("Failed to read OutOfService property ({})".format(e))
