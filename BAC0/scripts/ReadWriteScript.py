#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 by Christian Tremblay, P.Eng <christian.tremblay@servisys.com>
# Licensed under LGPLv3, see file LICENSE in this source tree.
#
'''
ReadWriteScript - extended version of BasicScript.py

As everything is handled by the BasicScript, select the additional features you want::

    # Create a class that implements a basic script with read and write functions
    from BAC0.scripts.BasicScript import BasicScript
    from BAC0.core.io.Read import ReadProperty
    from BAC0.core.io.Write import WriteProperty
    class ReadWriteScript(BasicScript,ReadProperty,WriteProperty)

Once the class is created, create the local object and use it::

    bacnet = ReadWriteScript(localIPAddr = '192.168.1.10')
    bacnet.read('2:5 analogInput 1 presentValue)

'''
#--- standard Python modules ---
import time
import logging
from datetime import datetime

#--- 3rd party modules ---
from bacpypes.debugging import bacpypes_debugging

#--- this application's modules ---
from ..scripts.BasicScript import BasicScript

from ..core.io.Read import ReadProperty
from ..core.io.Write import WriteProperty
from ..core.functions.GetIPAddr import HostIP
from ..core.functions.WhoisIAm import WhoisIAm
from ..core.io.Simulate import Simulation
from ..core.io.IOExceptions import BokehServerCantStart
from ..core.functions.PrintDebug import print_list

from ..web.BokehRenderer import DevicesTableHandler, DynamicPlotHandler, NotesTableHandler
from ..web.BokehServer import Bokeh_Worker
from ..web.FlaskServer import FlaskServer

from ..infos import __version__ as version

from bokeh.application import Application

#------------------------------------------------------------------------------

# some debugging
_DEBUG = 0


@bacpypes_debugging
class ReadWriteScript(BasicScript, WhoisIAm, ReadProperty, WriteProperty, Simulation):
    """
    Build a BACnet application to accept read and write requests.
    [Basic Whois/IAm functions are implemented in parent BasicScript class.]
    Once created, execute a whois() to build a list of available controllers.
    Initialization requires information on the local device.

    :param ip='127.0.0.1': Address must be in the same subnet as the BACnet network 
        [BBMD and Foreign Device - not supported] 
        
    :param bokeh_server: (boolean) If set to false, will prevent Bokeh server
        from being started. Can help troubleshoot issues with Bokeh. By default,
        set to True.
    """
    def __init__(self, ip=None, bokeh_server=True, flask_port = 8111):
        print("Starting BAC0 version %s" % version)
        self._log = logging.getLogger('BAC0.script.%s' \
                    % self.__class__.__name__)
        self._log.debug("Configurating app")
        self.flask_port = flask_port
        self.notes = ('Not Set', None)
        if ip is None:
            host = HostIP()
            ip_addr = host.address
        else:
            ip_addr = ip

        BasicScript.__init__(self, localIPAddr=ip_addr)
        
        self.bokehserver = False
        # Force a global whois to find all devices on the network
        self.whois_answer = self.update_whois()
        time.sleep(2)
        if bokeh_server:
            self.start_bokeh()
            self.FlaskServer.start()
        else:
            self._log.warning('Bokeh server not started. Trend feature will not work')

    def update_whois(self):
        return (self.whois(),str(datetime.now())) 
    
    def start_bokeh(self):
        try:
            self._log.info('Starting Bokeh Serve')
            self.points_to_trend = []
            # Need to create the device document here
            devHandler = DevicesTableHandler(self)
            dev_app = Application(devHandler)
            trendHandler = DynamicPlotHandler(self)
            notesHandler = NotesTableHandler(self)
            self.trend_app = Application(trendHandler)
            self.notes_app = Application(notesHandler)
            self.bk_worker = Bokeh_Worker(dev_app, self.trend_app, self.notes_app)
            self.FlaskServer = FlaskServer(network = self, port=self.flask_port)        
            self.bk_worker.start()        
            self.bokehserver = True
            print('Server started : http://localhost:%s' % self.flask_port)

        except OSError as error:
            self.bokehserver = False
            self._log.error('[bokeh serve] required for trending (controller.chart) features')
            self._log.error(error)

        except RuntimeError as rterror:
            self.bokehserver = False
            self._log.warning('Server already running')

        except BokehServerCantStart:
            self.bokehserver = False
            self._log.error('No Bokeh Server - controller.chart not available')

    @property
    def number_of_devices(self):
        s = []
        [s.append(x) for x in self.whois_answer[0].items() if x[1]>0]
        return len(s)
    
    @property
    def number_of_registered_trends(self):
        if self.points_to_trend:
            return len(self.points_to_trend)
        else:
            return 0
        
    def number_of_devices_per_network(self):
        total = float(self.number_of_devices)
        if total == 0:
            return (['No Devices'], ['0'], ['0%%'])
        labels = ['IP']
        series_pct = ['%.2f %%' % (len(self.network_stats['ip_devices'])/total * 100)]
        series = [len(self.network_stats['ip_devices'])/total * 100]
        for each in (self.network_stats['mstp_map'].keys()):
            labels.append('MSTP #%s'% each)
            series_pct.append('%.2f %%' % (len(self.network_stats['mstp_map'][each])/total * 100))
            series.append(len(self.network_stats['mstp_map'][each])/total * 100)
        return (labels, series, series_pct)
    
    @property
    def network_stats(self):
        statistics = {}
        mstp_networks = []
        mstp_map = {}
        ip_devices = []
        bacoids = []
        mstp_devices = []
        for address, bacoid in self.whois_answer[0].keys():            
            if ':' in address:
                net, mac = address.split(':')
                mstp_networks.append(net)
                mstp_devices.append(mac)
                try:
                    mstp_map[net].append(mac)
                except KeyError:
                    mstp_map[net] = []
                    mstp_map[net].append(mac)
            else:
                net = 'ip'
                mac = address
                ip_devices.append(address)
            bacoids.append((bacoid, address))
        mstpnetworks = sorted(set(mstp_networks))
        statistics['mstp_networks'] = mstpnetworks                   
        statistics['ip_devices'] = sorted(ip_devices)
        statistics['bacoids'] = sorted(bacoids)
        statistics['mstp_map'] = mstp_map
        statistics['timestamp'] = str(datetime.now())
        statistics['number_of_devices'] = self.number_of_devices
        statistics['print_mstpnetworks'] = print_list(mstpnetworks)
        return statistics

        

    def disconnect(self):
#        if self.bokehserver:
#            self.bokeh_session._loop.stop()
        super().disconnect()

    def __repr__(self):
        return 'Bacnet Network using ip %s with device id %s' % (self.localIPAddr, self.Boid)

def log_debug(txt, *args):
    """ Helper function to log debug messages
    """
    if _DEBUG:
        msg= (txt % args) if args else txt
        BasicScript._debug(msg)


def log_exception(txt, *args):
    """ Helper function to log debug messages
    """
    msg= (txt % args) if args else txt
    BasicScript._exception(msg)