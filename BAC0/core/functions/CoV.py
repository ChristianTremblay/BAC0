import asyncio
from typing import Tuple

from bacpypes3.basetypes import BinaryPV, PropertyIdentifier
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import Boolean, CharacterString, ObjectIdentifier

from ...core.app.asyncApp import BAC0Application
from ...scripts.Base import Base


class COVSubscription:
    def __init__(
        self,
        address: Address = None,
        objectID: Tuple[str, int] = None,
        lifetime: int = 900,
        confirmed: bool = False,
        callback=None,
        BAC0App: BAC0Application = None,
    ):
        self.address = Address(address) if isinstance(address, str) else address
        self.cov_fini = asyncio.Event()
        self.task = None
        self.obj_identifier = ObjectIdentifier(objectID)
        self._lite = BAC0App
        self._this_application = self._lite.this_application
        self._app = self._this_application.app
        self.callback = callback
        self.process_identifier = Base._last_cov_identifier + 1
        Base._last_cov_identifier = self.process_identifier

        # self.point = point
        self.lifetime = lifetime
        self.confirmed = confirmed
        self.callback = callback

    async def run(self):
        self._lite._log.debug(
            f"Subscribing to COV for {self.address} | {self.obj_identifier} -> {self._app}"
        )

        try:
            async with self._app.change_of_value(
                self.address,
                self.obj_identifier,
                self.process_identifier,
                self.confirmed,
                self.lifetime,
            ) as scm:
                cov_fini_task_monitor = asyncio.create_task(self.cov_fini.wait())
                while not self.cov_fini.is_set():
                    incoming: asyncio.Future = asyncio.ensure_future(scm.get_value())
                    done, pending = await asyncio.wait(
                        [
                            incoming,
                        ],
                        return_when=asyncio.FIRST_COMPLETED,
                    )
                    for task in pending:
                        task.cancel()

                    if incoming in done:
                        property_identifier, property_value = incoming.result()
                        self._lite._log.debug(
                            f"COV notification received for {self.address}|{self.obj_identifier} | {property_identifier} -> {type(property_identifier)} with value {property_value} | {property_value} -> {type(property_value)}"
                        )
                        if self.callback is not None:
                            self._lite._log.debug(
                                f"Calling callback for {property_identifier}"
                            )
                            if asyncio.iscoroutinefunction(self.callback):
                                asyncio.create_task(
                                    self.callback(
                                        property_identifier=property_identifier,
                                        property_value=property_value,
                                    )
                                )
                            elif hasattr(self.callback, "__call__"):
                                self.callback(
                                    property_identifier=property_identifier,
                                    property_value=property_value,
                                )
                            else:
                                self._lite._log.error(
                                    f"Callback {self.callback} is not callable"
                                )
                await cov_fini_task_monitor
        except Exception as e:
            self._lite._log.error(f"Error in COV subscription : {e}")

    def stop(self):
        self._lite._log.debug(
            f"Stopping COV subscription class for {self.address} | {self.obj_identifier}"
        )
        self.cov_fini.set()
