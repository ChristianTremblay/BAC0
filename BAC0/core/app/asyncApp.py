import json
import os
from typing import Any, Dict, List, Optional, Set

from bacpypes3.app import Application
from bacpypes3.basetypes import BDTEntry, HostNPort

from ...core.utils.notes import note_and_log


@note_and_log
class BAC0Application:
    _learnedNetworks: Set = set()
    _cfg: Optional[Dict[str, Any]] = None

    def __init__(
        self, cfg: Dict[str, Any], addr: str, json_file: Optional[str] = None
    ) -> None:
        self._cfg = cfg
        self.cfg: Dict[str, Any] = self.update_config(cfg, json_file)
        self.localIPAddr: str = addr
        self.bdt: List[str] = self._cfg["BAC0"]["bdt"]
        self.device_cfg, self.networkport_cfg = self.cfg["application"]
        self.log(f"Configuration sent to build application : {self.cfg}", level="debug")

        self.app: Application = Application.from_json(self.cfg["application"])

    def register_as_foreign_device_to(self, host: str, lifetime: int = 900) -> None:
        np = self.app.get_object_name("NetworkPort-1")
        linklayer = self.app.link_layers[np.objectIdentifier]
        hnp = HostNPort(host)
        np.fdBBMDAddress = hnp
        linklayer.register(hnp.address, lifetime)

    def populate_bdt(self) -> None:
        np = self.app.get_object_name("NetworkPort-1")
        linklayer = self.app.link_layers[np.objectIdentifier]
        for addr in self.bdt:
            bdt_entry = BDTEntry(addr)
            np.bbmdBroadcastDistributionTable.append(bdt_entry)
            linklayer.add_peer(bdt_entry.address)

    def get_bacnet_ip_mode(self) -> str:
        return self.app.get_object_name("NetworkPort-1").bacnetIPMode

    def unregister_from_bbmd(self) -> None:
        self.app.unregister()

    def update_config(
        self, cfg: Dict[str, Any], json_file: Optional[str]
    ) -> Dict[str, Any]:
        if json_file is None:
            if os.path.exists(
                os.path.join(os.path.expanduser("~"), ".BAC0", "device.json")
            ):
                json_file = os.path.join(
                    os.path.expanduser("~"), ".BAC0", "device.json"
                )
                self.log("Using JSON Stored in user folder ~/.BAC0", level="info")

            else:
                json_file = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)), "device.json"
                )
                self.log("Using default JSON configuration file", level="info")
        with open(json_file, "r") as file:
            base_cfg = json.load(file)

        base_cfg["application"][0].update(cfg["device"])
        base_cfg["application"][1].update(cfg["network-port"])
        return base_cfg
