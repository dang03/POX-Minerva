"""
OF 1.0 - POX U2 Case server synchronization
"""


from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
from pox.lib.util import dpidToStr
from pox.lib.recoco import Timer
import os
import datetime
import time
import traceback
import binascii
import random
import sys
import xmlrpclib
import socket
from service_thread import ServiceThread

log = core.getLogger()

def handle_timer(message, nm):
    print "\n"+mcolors.OKGREEN+"INFO: %s" % message, mcolors.ENDC

    if nm.switched:
        nm.switched = False
    else:
        nm.switched = True

    message = "Link Failure Simulation Raised at: %s" % get_time_now()
    message2 = "0-0-%s" % get_time_now()
    flow_flush(nm)
    ServiceThread.start_in_new_thread(network_measurer.logger_thread, message)
    return


def get_flow_mod(in_port, out_port, vlan=1550):
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match(in_port=in_port, dl_vlan=vlan)
        msg.idle_timeout = 200
        msg.hard_timeout = 200
        msg.priority = 40
        msg.actions.append(of.ofp_action_output(port=out_port))
        msg.actions.append(of.ofp_action_output(port=of.OFPP_CONTROLLER))
        return msg

def flow_flush(nm):
    dpids = dict()
    for connection in core.openflow.connections:
        if not connection.dpid in dpids.keys():
            dpids[connection.dpid] = connection

    if nm.switched: #Lower path
        dpid_2_conn = dpids[2]
        flow_mod_2 = get_flow_mod(1, 2)
        dpid_2_conn.send(flow_mod_2)

        dpid_5_conn = dpids[5]
        flow_mod_5 = get_flow_mod(2, 1)
        dpid_5_conn.send(flow_mod_5)

        dpid_4_conn = dpids[4]
        flow_mod_4 = get_flow_mod(3, 1)
        dpid_4_conn.send(flow_mod_4)

        dpid_3_conn = dpids[3]
        flow_mod_3 = get_flow_mod(1, 2)
        dpid_3_conn.send(flow_mod_3)

    else:   # Upper path
        dpid_2_conn = dpids[2]
        flow_mod_2 = get_flow_mod(1, 3)
        dpid_2_conn.send(flow_mod_2)

        dpid_1_conn = dpids[1]
        flow_mod_1 = get_flow_mod(1, 2)
        dpid_1_conn.send(flow_mod_1)

        dpid_4_conn = dpids[4]
        flow_mod_4 = get_flow_mod(2, 1)
        dpid_4_conn.send(flow_mod_4)

        dpid_3_conn = dpids[3]
        flow_mod_3 = get_flow_mod(1, 2)
        dpid_3_conn.send(flow_mod_3)

def get_time_now():
    return str(datetime.datetime.now().strftime('%M:%S.%f')[:-3])

class mcolors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.OKGREEN = ''
        self.FAIL = ''
        self.ENDC = ''

class network_measurer(object):

    switched = False

    def __init__(self, reactive, ignore=None):
        """
        Initialize

        See LearningSwitch for meaning of 'transparent'
        'reactive' indicates how
        'ignore' is an optional list/set of DPIDs to ignore
        """
        log.info(" Initializing Measurer")
        core.openflow.addListeners(self)
        self.reactive = reactive
        self.ignore = set(ignore) if ignore else ()

        self.dpids = dict()

        if self.reactive:
            core.openflow.addListenerByName("PacketIn", self._handle_PacketIn)
        else:
            None    #core.openflow.addListenerByName("ConnectionUp", self._handle_ConnectionUp)

        log.info(" Measurer Initialized")

    def logger(self, message):
        ServiceThread.start_in_new_thread(network_measurer.logger_thread, message)

    def logger_detail(self, message):
        detail_log = "./log_measurer_detail.txt"
        ServiceThread.start_in_new_thread(network_measurer.logger_thread, [message, detail_log])


    @staticmethod
    def logger_thread(message, log_file="./time_log_3v2.txt"):
        if os.path.exists(log_file):
            l = open(log_file, 'a')
            l.write(message+"\n")

        else:
            l = open(log_file, 'wb')
            l.write(message+"\n")
        l.close()

    def _handle_ConnectionUp(self, event):
        if not event.dpid in self.dpids.keys():
            log.info(" Registering new DPID: %d" % event.dpid)
            self.dpids[event.dpid] = event.connection

    def _handle_PacketIn(self, event):
        """
        OF 1.0 compatible flowmod messages for the switches
        """

        log.info(" Packet-in Event: DPID %s Port:%d" % (dpidToStr(event.dpid), event.port))
        log.info(" Link fail status: %s" % str(self.switched))
        self.logger_detail("%d-%d-%s" % (event.dpid, event.port, get_time_now()))

        self._log_if_first_or_end_node(event)
        if self.switched:
            self.route_up(event.dpid, event.port)
        else:
            self.route_down(event.dpid, event.port)


    def _log_if_first_or_end_node(self, event):
        if event.dpid == 2 and self.switched:
            message = "B-Packet_In DPID:%s Time: %s " % (dpidToStr(event.dpid), get_time_now())
        elif event.dpid == 2 and not self.switched:
            message = "A-Packet_In DPID:%s Time: %s " % (dpidToStr(event.dpid), get_time_now())
        elif event.dpid == 3 and event.port == 1 and self.switched:
            message = "B-Packet_In DPID:%s Time: %s " % (dpidToStr(event.dpid), get_time_now())
        elif event.dpid == 3 and event.port == 1 and not self.switched:
            message = "A-Packet_In DPID:%s Time: %s " % (dpidToStr(event.dpid), get_time_now())
        else:
            return
        self.logger(message)

    def _get_flow_mod(self, in_port, out_port, vlan=1550):
        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match(in_port=in_port)
        #msg.match = of.ofp_match(in_port=in_port, dl_vlan=vlan)
        msg.idle_timeout = 200
        msg.hard_timeout = 200
        msg.priority = 40
        msg.actions.append(of.ofp_action_output(port=out_port))
        msg.actions.append(of.ofp_action_output(port=of.OFPP_CONTROLLER))
        return msg

    def route_down(self, dpid, port):
        vlan_id = 1550
        if (dpid == 2) and (vlan_id == 1550):
            if port == 1:
                dpid_2_conn = self.dpids[2]
                flow_mod_2 = self._get_flow_mod(port, 2)
                dpid_2_conn.send(flow_mod_2)

                dpid_5_conn = self.dpids[5]
                flow_mod_5 = self._get_flow_mod(2, 1)
                dpid_5_conn.send(flow_mod_5)

                dpid_4_conn = self.dpids[4]
                flow_mod_4 = self._get_flow_mod(3, 1)
                dpid_4_conn.send(flow_mod_4)

                dpid_3_conn = self.dpids[3]
                flow_mod_3 = self._get_flow_mod(1, 2)
                dpid_3_conn.send(flow_mod_3)

    def route_up(self, dpid, port):
        vlan_id = 1550
        if (dpid == 2) and (vlan_id == 1550):
            if port == 1:
                dpid_2_conn = self.dpids[2]
                flow_mod_2 = self._get_flow_mod(port, 3)
                dpid_2_conn.send(flow_mod_2)

                dpid_1_conn = self.dpids[1]
                flow_mod_1 = self._get_flow_mod(1, 2)
                dpid_1_conn.send(flow_mod_1)

                dpid_4_conn = self.dpids[4]
                flow_mod_4 = self._get_flow_mod(2, 1)
                dpid_4_conn.send(flow_mod_4)

                dpid_3_conn = self.dpids[3]
                flow_mod_3 = self._get_flow_mod(1, 2)
                dpid_3_conn.send(flow_mod_3)

def launch(reactive=False):
    global start_time
    start_time = datetime.datetime.now()
    print "start_time: ", start_time

    log.info("Registering Synchronizer App")
    core.registerNew(network_measurer, reactive)

    Timer(10, handle_timer, args=["10 SECONDS - SWITCHING PATHS", network_measurer], recurring=True)

