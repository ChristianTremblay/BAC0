import json
import os

from bacpypes3.app import Application
from bacpypes3.basetypes import BDTEntry, HostNPort

from ...core.utils.notes import note_and_log


@note_and_log
class BAC0Application:
    """
    Use bacpypes3 helpers to generate a BACnet application following
    the arguments given to BAC0.
    Everythign rely on the creation of the device object and the
    network port object. The BACnet mode in the network port object
    will also create the correct version of the link layer (normal, foreign, bbmd)

    I chose to keep the JSON file option over the arguments only and this way,
    I do not close the door to applications that could be entirely defined
    using a JSON file, instead of being dynamic-only.

    This is why I read a JSON file, update it with information from BAC0
    command line, and use bacpypes3 from_json to generate the app.

    A very important thing is to use the bacpypes3.local.objects version
    of the object. Or else, it fails.

    It is also required to register the local objects in the vendor_id variable
    (see base.py)

    """

    _learnedNetworks = set()
    _cfg = None

    def __init__(self, cfg, addr, json_file=None):
        self._cfg = cfg  # backup what we wanted
        self.cfg = self.update_config(cfg, json_file)
        self.localIPAddr = addr
        self.bdt = self._cfg["BAC0"]["bdt"]
        self.device_cfg, self.networkport_cfg = self.cfg["application"]
        self._log.info(f"Configuration sent to build application : {self.cfg}")
        self.app = Application.from_json(self.cfg["application"])

    def add_foreign_device_host(self, host):
        "TODO : Should be able to add to the existing list..."
        np = self.app.get_object_name("NetworkPort-1")
        hnp = HostNPort(host)
        np.fdBBMDAddress = hnp

    def populate_bdt(self):
        np = self.app.get_object_name("NetworkPort-1")
        # populate the BDT
        bdt = []
        for addr in self.bdt:
            bdt_entry = BDTEntry(addr)
            bdt.append(bdt_entry)
        np.bbmdBroadcastDistributionTable = bdt

    def get_bacnet_ip_mode(self):
        return self.app.get_object_name("NetworkPort-1").bacnetIPMode

    def unregister_from_bbmd(self):
        self.app.unregister()

    def update_config(self, cfg, json_file):
        if json_file is None:
            if os.path.exists(
                os.path.join(os.path.expanduser("~"), ".BAC0", "device.json")
            ):
                json_file = os.path.join(
                    os.path.expanduser("~"), ".BAC0", "device.json"
                )
                self._log.info("Using JSON Stored in user folder ~/.BAC0")

            else:
                json_file = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "device.json"
                )
                self._log.info("Using default JSON configuration file")
        with open(json_file, "r") as file:
            base_cfg = json.load(file)

        base_cfg["application"][0].update(cfg["device"])
        base_cfg["application"][1].update(cfg["network-port"])
        return base_cfg
