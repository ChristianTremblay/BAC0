import asyncio
from typing import Tuple

from bacpypes3.basetypes import BinaryPV, PropertyIdentifier
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import Boolean, CharacterString, ObjectIdentifier

from ...scripts.Base import Base
from ..devices.Points import Point


class COVSubscription:
    def __init__(
        self,
        address: Address = None,
        objectID: Tuple[str, int] = None,
        lifetime: int = 900,
        confirmed: bool = False,
        callback=None,
    ):
        self.address = address
        self.cov_fini = asyncio.Event()
        self.task = None
        self.obj_identifier = ObjectIdentifier(objectID)
        self._app = self.this_application.app
        self.callback = callback
        self.process_identifier = Base._last_cov_identifier + 1
        Base._last_cov_identifier = self.process_identifier

        # self.point = point
        self.lifetime = lifetime
        self.confirmed = confirmed
        self.callback = callback

    async def run(self):
        self.log(
            f"Subscribing to COV for {self.address} | {self.obj_identifier}",
            level="info",
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
                        val = None
                        flag = None
                        property_identifier, property_value = incoming.result()
                        self.point.log(
                            f"COV notification received for {self.point.properties.name} | {property_identifier} -> {type(property_identifier)} with value {property_value} | {property_value} -> {type(property_value)}",
                            level="info",
                        )
                        if self.callback is not None:
                            self.log(
                                f"Calling callback for {property_identifier}",
                                level="info",
                            )
                            if asyncio.iscoroutinefunction(self.callback):
                                await self.callback(
                                    property_identifier=property_identifier,
                                    property_value=property_value,
                                )
                            elif hasattr(self.callback, "__call__"):
                                self.callback(
                                    property_identifier=property_identifier,
                                    property_value=property_value,
                                )
                            else:
                                self.log(
                                    f"Callback {self.callback} is not callable",
                                    level="error",
                                )
                await cov_fini_task_monitor
        except Exception as e:
            self.log(f"Error in COV subscription : {e}", level="error")

    def stop(self):
        self.log(
            f"Stopping COV subscription class for {self.address} | {self.obj_identifier}",
            level="debug",
        )
        self.cov_fini.set()
