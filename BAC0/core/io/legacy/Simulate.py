#!/usr/bin/python
# type: ignore
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
from ..IOExceptions import (
    ApplicationNotStarted,
    NoResponseFromController,
    OutOfServiceNotSet,
    OutOfServiceSet,
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

        if self.read(f"{addr} {obj_type} {obj_inst} outOfService"):
            self.write(
                f"{addr} {obj_type} {obj_inst} {prop_id} {value}"
            )
        else:
            try:
                self.write(
                    f"{addr} {obj_type} {obj_inst} outOfService True"
                )
            except NoResponseFromController as e:
                self._log.warning(
                    f"Failed to write to OutOfService property ({e})"
                )

            try:
                if self.read(f"{addr} {obj_type} {obj_inst} outOfService"):
                    self.write(
                        f"{addr} {obj_type} {obj_inst} {prop_id} {value}"
                    )
                else:
                    raise OutOfServiceNotSet()
            except NoResponseFromController as e:
                self._log.warning(
                    f"Failed to write to OutOfService property ({e})"
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
            self.write(f"{addr} {obj_type} {obj_inst} outOfService True")
        except NoResponseFromController as e:
            self._log.warning(f"Failed to write to OutOfService property ({e})")

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
            self.write(f"{addr} {obj_type} {obj_inst} outOfService False")
        except NoResponseFromController as e:
            self._log.warning(f"Failed to write to OutOfService property ({e})")

        try:
            if self.read(f"{addr} {obj_type} {obj_inst} outOfService"):
                raise OutOfServiceSet()
            else:
                pass  # Everything is ok"
        except NoResponseFromController as e:
            self._log.warning(f"Failed to read OutOfService property ({e})")
