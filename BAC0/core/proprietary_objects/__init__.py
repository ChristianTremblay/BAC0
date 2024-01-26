#!/usr/bin/python
# -*- coding: utf-8 -*-
import jci as _jci
from bacpypes3.vendor import VendorInfo, get_vendor_info
from bacpypes3.basetypes import ObjectTypesSupported

#
#   Proprietary Objects and their attributes
#   https://cgproducts.johnsoncontrols.com/MET_PDF/12013102.pdf
#
# Register Johnson Controls Proprietary Objects and properties
try:
    jci = VendorInfo(_jci._vendor_id)
except RuntimeError:
    pass  # we are re-running the script... forgive us or maybe we already read a jci device
    jci = get_vendor_info(_jci._vendor_id)

# create a VendorInfo object for this custom application before registering
# specialize object classes
jci_custom_vendor_info = VendorInfo(
    _jci._vendor_id, _jci.ProprietaryObjectType, _jci.ProprietaryPropertyIdentifier
)
jci.register_object_class(ObjectTypesSupported.device, _jci.DeviceObject)
jci.register_object_class(ObjectTypesSupported.analogInput, _jci.AnalogInputObject)
jci.register_object_class(ObjectTypesSupported.analogValue, _jci.AnalogValueObject)
jci.register_object_class(ObjectTypesSupported.analogOutput, _jci.AnalogOutputObject)
