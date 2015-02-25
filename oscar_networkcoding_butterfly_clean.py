"""
OF 1.0 controller code for Network Coding Scenario

"""


from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
from pox.lib.util import dpidToStr
import time
import traceback

log = core.getLogger()

class network_coding_butterfly(object):

    def __init__(self, reactive, ignore = None):
        """
        Initialize

        See LearningSwitch for meaning of 'transparent'
        'reactive' indicates how
        'ignore' is an optional list/set of DPIDs to ignore
        """
        log.info("Initializing Network Coding Butterfly")
        core.openflow.addListeners(self)
        self.reactive = reactive
        self.ignore = set(ignore) if ignore else ()

        self.a_flow = {"id": "A", "x": (0, 0, 1), "l": 2}
        self.b_flow = {"id": "B", "x": (1, 0, 0), "l": 0}
        self.axb_flow = {"id": "AxB", "x": (0, 1, 0), "l": 1}
        self.topology = list()
        self.priority = 65000 #16777215 # Highest priority

        if self.reactive:
            try:
                core.openflow.addListenerByName("PacketIn", self._handle_PacketIn)
            except Exception as e:
                log.info(e)
        else:
            core.openflow.addListenerByName("ConnectionUp", self._handle_ConnectionUp)
        log.info("Network Coding Correctly Initialized")

    def _handle_ConnectionUp(self, event):
        """
        OF 1.0 compatible flowmod messages for the switches
        """
        pass

    def __vlan_to_flow(self, vlan):
        flows = {4009: self.a_flow,
                 4007: self.b_flow,
                 4008: self.axb_flow,}

        return flows[vlan]

    def __dpid_to_bid(self, src_dpid, input_port):
        """
        INFO: fill depending on the configuration of each testbed

        Returns the "Butterfly ID" (BID) given a DPID and
            an input port
        """
        butterfly = {2: {1: (0, 0, 0), 4: (0, 0, 0), 6: (0, 0, 0), 7: (0, 0, 0)},
                     5: {6: (1, 0, 1)},
                     1: {1: (1, 1, 0), 7: (2, 0, 0), 5: (2, 0, 0), 2: (2, 0, 0)},
                     3: {8: (3, 0, 2), 4: (3, 0, 2), 6: (4, 3, 3)},
                     4: {6: (3, 2, 0)},
                     }

        return butterfly[src_dpid][input_port]

    def __bid_to_dpid(self, bid):
        """
        INFO: fill depending on the configuration of each testbed
        Returns the dst DPID from a BID
        *Provided BID must be a tuple
        """
        butterfly = {(0, 0, 0): 2,
                     (1, 0, 1): 5,
                     (1, 1, 0): 1,
                     (2, 0, 0): 1,
                     (3, 0, 2): 3,
                     (3, 2, 0): 4,
                     (4, 3, 3): 3,
                    }
        return butterfly[bid]

    def __get_bids(self):
        """
        INFO: fill depending on the configuration of each testbed
        Return the list of all BIDs
        """
        self.bids = [(0, 0, 0), (1, 0, 1), (1, 1, 0), (2, 0, 0), (3, 0, 2), (3, 2, 0), (4, 3, 3)]
        return self.bids

    def __get_dst_bids(self, sbid, flow):
        """
        INFO: Algorithm independent of the testbed
        Given the source BID (SBID) and its flow type (A, B or AxB)
            returns the Destination BID (DBID)
        """
        l = flow["l"]
        dst_bid__l = sbid[l] + flow["x"][l]
        dbids = self.__find_dest_bids(dst_bid__l, l)
        return dbids

    def __find_dest_bids(self, dst_bid__l, l):
        """
        Given l and the value of x[l] and src_bid[l],
        return all the BIDs where BID[l] == dst_bid__l
        """
        all_bids = self.__get_bids()
        result = list()
        for bid in all_bids:
            if bid[l] == dst_bid__l:
                result.append(bid)
        return result

    def __find_output_port(self, src_dpid, dst_dpid):
        ''' Finds the output port to send data to 2 connected datapaths given a src
            and dst DPIDs. This methods uses the Discovery APP launched during
            the launch() method of this app'''

        for link in self.topology:
            if (link.dpid1 == src_dpid) and (link.dpid2 == dst_dpid):
                return link.port1
        log.info("No link yet from dpid %d to %d " %(src_dpid, dst_dpid))
        self._update_topology()
        return 

    def __routes_to_VM(self, src_dpid, in_port, vlan_id):
        """
        INFO: Fill with static rules (connections between switches and VMs)

        Returns the out port (if any) of the static_links
            (those links between switch and VM). to retrieve the
            out port a dict struct is used in the following way:
            static_links[flow_type][src_dpid][src_port]
            if no out port this function returns False
        """
        flow = self.__vlan_to_flow(vlan_id)
        static_links = {self.b_flow["id"]: {1:{1:3, 7:8, 5:4, 2:6},
                                       3:{4:7, 6:7, 5:7}, #Check XXX 5:7
                                      },
                         self.a_flow["id"]: {3:{8:7},
                                      },
                         self.axb_flow["id"]: {3:{6:7, 5:7},
                                        },
                         }
        try:
            log.info("Checking if the links are static")
            out_port = static_links[flow["id"]][src_dpid][in_port]
            log.info("Statically forwarding packet from %s:%d to ouput %d " %(src_dpid, in_port, out_port))
            return [out_port]
        except Exception as e:
            return False

    def __add_flow_entries(self, src_dpid, in_port, out_ports, vlan_id, event):
        idle_timeout = 5
        hard_timeout = 0 #In order to avoid unnecessary messages between the switches and the controller

        msg = of.ofp_flow_mod()
        msg.match = of.ofp_match(in_port = in_port, dl_vlan=vlan_id)

        # Use idle and/or hard timeouts to help cleaning the table
        msg.idle_timeout = idle_timeout
        msg.hard_timeout = hard_timeout

        # Handle several output ports, where needed
        for output_port in out_ports:
            msg.actions.append(of.ofp_action_output(port = output_port))
        event.connection.send(msg)
        return

    def _update_topology(self):
        log.info("Updating topology")
        topology_map = core.openflow_discovery.adjacency #Update the topology calling the param adjacency from Discovery module started in handle()
        #print "topology_map: ", topology_map
        self.topology = topology_map.keys() #only the keys have relevant data to this app, the values are the the time since the link was discovered
        #print "topology.keys(): ", self.topology

        for link in self.topology:
            print "link", link
            print "link.dpid1", link.dpid1
            print "link.dpid2", link.dpid2
            print "link.port1", link.port1
            print "link.port2", link.port2

        """
        topology_map:  {Link(dpid1=5,port1=2, dpid2=3,port2=2): 1422875036.217856, Link(dpid1=5,port1=1, dpid2=2,port2=4): 1422875043.467909, Link(dpid1=3,port1=2, dpid2=5,port2=2): 1422875029.003284, Link(dpid1=4,port1=2, dpid2=3,port2=3): 1422875071.895366, Link(dpid1=4,port1=3, dpid2=5,port2=3): 1422875067.453045, Link(dpid1=6,port1=2, dpid2=4,port2=4): 1422875060.269776, Link(dpid1=2,port1=3, dpid2=6,port2=1): 1422875045.898465, Link(dpid1=5,port1=3, dpid2=4,port2=3): 1422875033.803537, Link(dpid1=6,port1=3, dpid2=5,port2=4): 1422875057.856547, Link(dpid1=6,port1=1, dpid2=2,port2=3): 1422875065.065647, Link(dpid1=2,port1=1, dpid2=3,port2=1): 1422875055.455617, Link(dpid1=5,port1=4, dpid2=6,port2=3): 1422875041.051544, Link(dpid1=3,port1=1, dpid2=2,port2=1): 1422875031.421775, Link(dpid1=2,port1=4, dpid2=5,port2=1): 1422875053.054623, Link(dpid1=4,port1=1, dpid2=2,port2=2): 1422875024.185476, Link(dpid1=3,port1=3, dpid2=4,port2=2): 1422875026.572237, Link(dpid1=2,port1=2, dpid2=4,port2=1): 1422875048.286152, Link(dpid1=4,port1=4, dpid2=6,port2=2): 1422875021.769976}
        topology.keys():  [Link(dpid1=5,port1=2, dpid2=3,port2=2), Link(dpid1=5,port1=1, dpid2=2,port2=4), Link(dpid1=3,port1=2, dpid2=5,port2=2), Link(dpid1=4,port1=2, dpid2=3,port2=3), Link(dpid1=4,port1=3, dpid2=5,port2=3), Link(dpid1=6,port1=2, dpid2=4,port2=4), Link(dpid1=2,port1=3, dpid2=6,port2=1), Link(dpid1=5,port1=3, dpid2=4,port2=3), Link(dpid1=6,port1=3, dpid2=5,port2=4), Link(dpid1=6,port1=1, dpid2=2,port2=3), Link(dpid1=2,port1=1, dpid2=3,port2=1), Link(dpid1=5,port1=4, dpid2=6,port2=3), Link(dpid1=3,port1=1, dpid2=2,port2=1), Link(dpid1=2,port1=4, dpid2=5,port2=1), Link(dpid1=4,port1=1, dpid2=2,port2=2), Link(dpid1=3,port1=3, dpid2=4,port2=2), Link(dpid1=2,port1=2, dpid2=4,port2=1), Link(dpid1=4,port1=4, dpid2=6,port2=2)]
        """





    def _handle_PacketIn(self, event, handle_type="PacketIn"):

        log.info("Handling Packet IN")
        eth_headers = event.parse() #Ethernet part of the packet L2
        log.info("Packet in Correctly Parsed")

        if eth_headers != pkt.ethernet.LLDP_TYPE:
            self._update_topology()
            vlan_headers = eth_headers.next #VLAN part of the Packet L2
            mpls_headers = vlan_headers.next #MPLS part of the packet L2.5

            vlan_id = vlan_headers.id
            if vlan_id not in [4007,4008,4009]:
                return
            try:
                mpls_label = mpls_headers.label
            except:
                mpls_label = None
            dpid = event.dpid
            in_port = event.port
            self.__route_packet(dpid, in_port, vlan_id, mpls_label, event)

    def __route_packet(self, src_dpid, in_port, vlan_id, mpls_tag, event):
        ''' Translates the src DPID to a src BID, identifies the dst BID,
            transaltes the dst BID to a dst DPID and adds the required rules
            to the switch flow table
        '''
        try:
            routes_to_vm = self.__routes_to_VM(src_dpid, in_port, vlan_id)
            if routes_to_vm:
                return self.__add_flow_entries(src_dpid, in_port, routes_to_vm, vlan_id,event)
            out_ports = list()

            src_bid = self.__dpid_to_bid(src_dpid, in_port) 
            flow = self.__vlan_to_flow(vlan_id) 
            dst_bids = self.__get_dst_bids(src_bid, flow)
            for dst_bid in dst_bids:
                dst_dpid = self.__bid_to_dpid(dst_bid)
                out_port = self.__find_output_port(src_dpid, dst_dpid)
                out_ports.append(out_port)
            self.__add_flow_entries(src_dpid, in_port, out_ports, vlan_id,event) 
        except Exception as e:
            log.info(traceback.format_exc())
            raise e

def launch(reactive = True):
    import pox.openflow.discovery
    try:
        pox.openflow.discovery.launch(no_flow=False, explicit_drop=True, link_timeout=100, eat_early_packets=False)
    except Exception as e:
        log.info("Exception trying to load the discovery APP: %s" % str(e))
        raise e
    log.info("Registering Network Coding App")
    #XXX: would it be a good idea to put sleep here in order to let the discovery up find all the nodes?
    core.registerNew(network_coding_butterfly, reactive)

