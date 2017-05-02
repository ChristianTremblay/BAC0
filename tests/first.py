''' first.py  - explore BAC0
'''
#--- standard Python modules ---
#--- 3rd party modules ---
#--- this application's modules ---

#------------------------------------------------------------------------------

import BAC0
import time

bacnet= BAC0.connect()
time.sleep(3)

'''
who= bacnet.whois()
print(who)
'''

d12= BAC0.device('20020:12',1200,bacnet)

print(d12['Out4'])
d12['Out4'].default(5)
d12['Out4']= 56
print(d12['Out4'])

d12['Out4']= 'auto'
print(d12['Out4'])

print(d12['Temperature'])
d12['Temperature']=  23.5
print(d12['Temperature'])

'''
for i in range(4):
    val= d12['junk']    # read AV24
'''

pass
 