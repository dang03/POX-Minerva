"""
OF 1.0 - POX end-to-end latency measurer

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
from service_thread import ServiceThread

log = core.getLogger()

def handle_timer(message, nm):
    print "\n"+mcolors.OKGREEN+"INFO: %s" % message, mcolors.ENDC

    if nm.switched == True:
        nm.switched = False
        message = "Link Failure Simulation Raised at: %s" % get_time_now()
    else:
        nm.switched = True
        message = "Link Failure Simulation Raised at: %s" % get_time_now()

    ServiceThread.start_in_new_thread(network_measurer.logger_thread, message)
    flow_flush()
    return


def flow_flush():
    msg = of.ofp_flow_mod(command=of.OFPFC_DELETE)

    for connection in core.openflow.connections:
        connection.send(msg)
        log.info("-> Clearing all flows from %s!" % (dpidToStr(connection.dpid),))


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


    @staticmethod
    def logger_thread(message, log_file="./time_log_2v2.txt"):
        if os.path.exists(log_file):
            l = open(log_file, 'a')
            l.write(message+"\n")

        else:
            l = open(log_file, 'wb')
            l.write(message+"\n")
        l.close()


    def _handle_ConnectionUp(self, event):
        if not event.dpid in self.dpids.keys():
            log.info("Registering new DPID: %d" % event.dpid)
            self.dpids[event.dpid] = event.connection    


    def _handle_PacketIn(self, event):
        """
        OF 1.0 compatible flowmod messages for the switches
        """
        
        log.info(" Packet-in Event: DPID %s Port:%d" % (dpidToStr(event.dpid), event.port))
        log.info(" Link fail status: %s" % str(self.switched))
        #self.logger("======> PACKET_IN: %d:%d at: %s " % (event.dpid, event.port, str(datetime.datetime.now())))
        
        self._log_if_first_or_end_node(event)

        if self.switched:
            self._route_up(event)
        else:
            self._route_down(event)


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
        msg.match = of.ofp_match(in_port=in_port, dl_vlan=vlan)
        msg.idle_timeout = 200
        msg.hard_timeout = 200
        msg.actions.append(of.ofp_action_output(port=out_port))
        msg.actions.append(of.ofp_action_output(port=of.OFPP_CONTROLLER))
        return msg


    def _route_down(self, event):
        vlan_id = 1550
        if (event.dpid == 2) and (vlan_id == 1550):
            if event.port == 1:
                flow_mod = self._get_flow_mod(event.port, 2)
                event.connection.send(flow_mod)
                #log.info("Forwarding B, [@Tx] => S2.P1 -> S2.P2")
                
                dpid_5_conn = self.dpids[5]
                flow_mod_5 = self._get_flow_mod(6, 5)
                dpid_5_conn.send(flow_mod_5)
                #log.info("Forwarding B, [@S2.P2] => S5.P6 -> S5.P5")

                dpid_4_conn = self.dpids[4]
                flow_mod_4 = self._get_flow_mod(7, 4)
                dpid_4_conn.send(flow_mod_4)
                #log.info("Forwarding B, [@S5.P5] => S4.P7 -> S4.P4")

                dpid_3_conn = self.dpids[3]
                flow_mod_3 = self._get_flow_mod(5, 7)
                dpid_3_conn.send(flow_mod_3)
                #log.info("Forwarding B, [@S4.P4] => S3.P5 -> S3.P7")


    def _route_up(self, event):
        vlan_id = 1550
        if (event.dpid == 2) and (vlan_id == 1550):
            if event.port == 1:
                flow_mod = self._get_flow_mod(event.port, 3)
                event.connection.send(flow_mod)
                #log.info("Forwarding A, [@Tx] => S2.P1 -> S2.P3")

                dpid_1_conn = self.dpids[1]
                flow_mod_1 = self._get_flow_mod(1, 6)
                dpid_1_conn.send(flow_mod_1)
                #log.info("Forwarding A, [@S2.P3] => S1.P1 -> S1.P6")

                dpid_4_conn = self.dpids[4]
                flow_mod_4 = self._get_flow_mod(6, 4)
                dpid_4_conn.send(flow_mod_4)
                #log.info("Forwarding A, [@S1.P6] => S4.P6 -> S4.P4")

                dpid_3_conn = self.dpids[3]
                flow_mod_3 = self._get_flow_mod(5, 7)
                dpid_3_conn.send(flow_mod_3)
                #log.info("Forwarding A, [@S4.P4] => S3.P5 -> S3.P7")


def launch(reactive=False):
    global start_time
    start_time = datetime.datetime.now()
    print "start_time: ", start_time

    log.info(" Registering Measurement App")
    core.registerNew(network_measurer, reactive)

    Timer(10, handle_timer, args=["10 SECONDS - SWITCHING PATHS", network_measurer], recurring=True)

