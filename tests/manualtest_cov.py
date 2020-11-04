import BAC0
from BAC0.core.devices.local.models import analog_value
from bacpypes.primitivedata import Real
import time

device = BAC0.lite('192.168.211.55/24', deviceId=123)
client = BAC0.lite('192.168.212.12/24')

new_obj = analog_value()
new_obj.add_objects_to_application(device)

# From Server
dev_av = device.this_application.get_object_name('AV')
print(dev_av.covIncrement)

# From client
dev = dev = BAC0.device('192.168.211.55', 123, client, poll=0)
av = dev['AV']
dev['AV'].subscribe_cov(lifetime=0)

print()
while True:
    print(dev['AV'])
    time.sleep(1)
    dev['AV'] += 1
    time.sleep(1)