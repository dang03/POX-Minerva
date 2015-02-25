"""
OF 1.0 controller code for RFC
"""


from pox.core import core
from pox.host_tracker import host_tracker
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
from pox.lib.util import dpidToStr
import time
import traceback
from service_thread import ServiceThread

log = core.getLogger()

import logging

log.setLevel(logging.INFO)


class AttachmentPoints():
    def __init__(self):
        self.hosts = {}     #mac -> dpid

    def _handle_core_ComponentRegistered(self, event):
        if event.name == "host_tracker":
            event.component.addListenerByName("HostEvent", self.__handle_host_tracker_HostEvent)

    def __handle_host_tracker_HostEvent(self, event):
        ip = str(event.entry.ipaddr)
        mac = str(event.entry.macaddr)
        dp_id = dpidToStr(event.entry.dpid)

        print "HOST ATTACHMENTS: ", ip, mac, dp_id





def launch():

    import pox.topology
    pox.topology.launch()
    import pox.openflow.discovery
    pox.openflow.discovery.launch()
    import pox.openflow.topology
    pox.openflow.topology.launch()
    log.info("Registering Network Host Tracker")
    pox.host_tracker.launch()
    core.registerNew(attachment)
    #ServiceThread.start_in_new_thread(attachment_points.host_logger,None)
