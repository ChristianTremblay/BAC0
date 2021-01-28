# --- standard Python modules ---
import weakref

# --- 3rd party modules ---
from bacpypes.core import deferred

# --- this application's modules ---
from .TaskManager import Task
from ..core.utils.notes import note_and_log


@note_and_log
class Update_local_COV(Task):
    """
    Start a task to validate each points inside local device and send 
    cov notifications to subscribers.
    """

    def __init__(self, device, delay=1, name="", prefix="update_local_cov"):
        """
        :param device: (BAC0.core.devices.Device.Device) device to poll
        :param delay: (int) Delay between polls in seconds, defaults = 10sec
        
        A delay cannot be < 10sec 
        For delays under 10s, use DeviceFastPoll class.

        :returns: Nothing
        """
        self._device = weakref.ref(device)
        Task.__init__(self, name="{}_{}".format(prefix, name), delay=delay)
        self._counter = 0

    @property
    def device(self):
        return self._device()

    def task(self):
        try:
            for k, cov in self.device.this_application.cov_detections.items():
                objName = k.objectName
                obj = self.device.this_application.get_object_name(objName)
                # get the detection algorithm object
                cov_detection = self.device.this_application.cov_detections.get(
                    obj, None
                )
                if (not cov_detection) or (len(cov_detection.cov_subscriptions) == 0):
                    self._log.debug(
                        "no subscriptions for that object : {}".format(objName)
                    )
                    continue

                # tell it to send out notifications
                self._log.info("Sending COV for {}".format(objName))
                deferred(cov_detection.send_cov_notifications)

        except Exception as error:
            self.device._log.error(
                "Something is wrong with update_local_cov : {}".format(error)
            )
