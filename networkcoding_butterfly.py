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
        
        self.a_flow = "A"
        self.b_flow = "B"
        self.axb_flow = "AxB"
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
        ## Maybe better to not use timeouts if the rules are only placed on start
        #timeouts = {
        #            "idle_timeout": False,
        #            "hard_timeout": False,
        #            }
        ##self._handle_PacketIn(event, handle_type="ConnectionUp", **timeouts)
        #self._handle_PacketIn(event, handle_type="ConnectionUp")
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

        butterfly = { 2 : {1:"000", 4:"000", 6:"000", 7:"000"},
                      5 : {6:"101"},
                      1 : {1:"110", 7:"200", 5:"200", 2:"200"},                       
                      3 : {8:"302", 4:"302", 6:"433"},
                      4 : {6:"320"},
                     }
        return butterfly[src_dpid][input_port]

    def __bid_to_dpid(self, bid):
        """
        INFO: fill depending on the configuration of each testbed
        
        Returns the dst DPID from a BID
        """

        butterfly = { "000" : 2,
                      "101" : 5,
                      "110" : 1,
                      "200" : 1,
                      "302" : 3,
                      "320" : 4, 
                      "433" : 3,
                    }
        return butterfly[bid]

    def __get_bids(self):
        """
        INFO: fill depending on the configuration of each testbed
        
        Return the list of all BIDs
        """

        self.bids = ["000", "101", "110", "200", "302", "320", "433"]
        return self.bids

    def __get_dst_bids(self, sbid, flow):
        """
        INFO: Algorithm independent of the testbeb
        
        Given the source BID (SBID) and its flow type (A, B or AxB)
            returns the Destination BID (DBID)
        """

        pbid = sbid # Potential BID
        log.info("\npbid = %s\n" % str(pbid))
        significant_char = 0
         
        if flow == self.a_flow:
            significant_char = 2
            unit = int(pbid[significant_char]) + 1
            log.info("\nA > unit: %s\n" % str(unit))
            #pbid[significant_char] = unit
            pbid = self.__replace_in_bid(pbid, significant_char, unit)
            log.info("\nA > pbid[significant_char]: %s\n" % str(pbid[significant_char]))
            log.info("\nsbid = %s\n" % str(sbid))

        elif flow == self.axb_flow:
            significant_char = 1
            ten = int(pbid[significant_char]) + 1
            #pbid[significant_char] = str(ten)
            pbid = self.__replace_in_bid(pbid, significant_char, ten)
            log.info("\nB > pbid[significant_char]: %s\n" % str(pbid[significant_char]))
            log.info("\nsbid = %s\n" % str(sbid))

        elif flow == self.b_flow:
            significant_char = 0
            hundred = int(pbid[significant_char]) + 1
            #pbid[significant_char] = str(hundred)
            pbid = self.__replace_in_bid(pbid, significant_char, hundred)
            log.info("\nC > pbid[significant_char]: %s\n" % str(pbid[significant_char]))
            log.info("\nsbid = %s\n" % str(sbid))
        else:
            #pass
            return []

        dbids = self.__find_dest_bids(pbid, significant_char)
        return dbids
    
    def __replace_in_bid(self, pbid, position, value):
        pbid = '{0}{1}{2}'.format(pbid[:position], str(value), pbid[position + 1:])
        return pbid
    
    def __find_dest_bids(self, pbid, significant_char):
        all_bids = self.__get_bids()
        sbids = list()
        log.info("")
        #log.warning("SBIDS: %s" % str(sbids))
        for bid in all_bids:
            if bid[significant_char] == pbid[significant_char]:
                sbids.append(bid)
        log.info("\ndstbids = %s\n" % str(sbids))
        return sbids    

    def __find_output_port(self, src_dpid, dst_dpid):
        ''' Finds the output port to send data to 2 connected datapaths given a src
            and dst DPIDs. This methods uses the Discovery APP launched during
            the launch() method of this app'''

        for link in self.topology:
            if (link.dpid1 == src_dpid) and (link.dpid2 == dst_dpid):
                return link.port1
        #XXX:Bad news, the overall topology is not discovered yet
        #Quick fix
        log.info("No link yet from dpid %d to %d " %(src_dpid, dst_dpid))
        self._update_topology()
        #self.__find_output_port(src_dpid, dst_dpid)

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
        static_links = {self.b_flow: {1:{1:3, 7:8, 5:4, 2:6},
                                       3:{4:7, 6:7, 5:7}, #Check XXX 5:7
                                      },
                         self.a_flow: {3:{8:7},
                                      },
                         self.axb_flow: {3:{6:7, 5:7},
                                        },
                         }
        try:
            log.info("Checking if the links are static")
            out_port = static_links[flow][src_dpid][in_port]
            log.info("Statically forwarding packet from %s:%d to ouput %d " %(src_dpid, in_port, out_port))
            return [out_port]
        except Exception as e:
            return False         
    
    def __add_flow_entries(self, src_dpid, in_port, out_ports, vlan_id, event):
        idle_timeout = 5
        hard_timeout = 0#10
        
        log.info("Flowmoding %s", dpidToStr(src_dpid))
        msg = of.ofp_flow_mod()
        #msg.priority = self.priority
        msg.match = of.ofp_match(in_port = in_port, dl_vlan=vlan_id)

        # Use idle and/or hard timeouts to help cleaning the table
        msg.idle_timeout = idle_timeout
        msg.hard_timeout = hard_timeout

        # Handle several output ports, where needed
        log.warning("msg.actions: %s" % str(msg.actions))
        for output_port in out_ports:
            # XXX Carolina: check what's going on with this
            msg.actions.append(of.ofp_action_output(port = output_port))
        event.connection.send(msg)
        return 

    def _update_topology(self):
        log.info("Updating topology")
        topology_map = core.openflow_discovery.adjacency #Update the topology calling the param adjacency from Discovery module started in handle()
        self.topology = topology_map.keys() #only the keys have relevant data to this app, the values are the the time since the link was discovered
    
    def _handle_PacketIn(self, event, handle_type="PacketIn"):
               
        #topology_map = core.openflow_discovery.adjacency #Update the topology calling the param adjacency from Discovery module started in handle()
        #self.topology = topology_map.keys() #only the keys have relevant data to this app, the values are the the time since the link was discovered
#        ####DEBUG INFO TODO: DELETE
#        for link in topology_map.keys():
#            log.info("LINK:\n\n----------")
#            log.info(link.dpid1)
#            log.info(link.port1)
#            log.info(link.dpid2)
#            log.info(link.port2)
#            log.info("----------\n\n") 
#        ####END DEBUG INFO   
        log.info("Handling Packet IN")
        eth_headers = event.parse() #Ethernet part of the packet L2
        log.info("Packet in Correctly Parsed")
        if eth_headers != pkt.ethernet.LLDP_TYPE:
            self._update_topology()
            log.info("Potential DATA packet found (no LLDP)")
            log.info("--- Packet In (event.dpid: %s) (event.port: %s) ---" % (str(event.dpid), str(event.port)))     
            vlan_headers = eth_headers.next #VLAN part of the Packet L2
            log.info("VLAN Packet in with VLAN ID = %d" % vlan_headers.id)            
            mpls_headers = vlan_headers.next #MPLS part of the packet L2.5         
        
            vlan_id = vlan_headers.id
            if vlan_id not in [4007,4008,4009]:
                return
            # XXX Carolina: cannot obtain "label" from "ipv4" objects (added try/except to handle)
            try:
                mpls_label = mpls_headers.label
            except:
                mpls_label = "2" # XXX Hack
            dpid = event.dpid
            in_port = event.port
            #TODO: Probably the MPLS label is not required 
            self.__route_packet(dpid, in_port, vlan_id, mpls_label, event)
    
    def __route_packet(self, src_dpid, in_port, vlan_id, mpls_tag, event):
        ''' Translates the src DPID to a src BID, identifies the dst BID, 
            transaltes the dst BID to a dst DPID and adds the required rules 
            to the switch flow table
        '''
        try:
            log.warning("ENTERING ROUTE PACKET")
            routes_to_vm = self.__routes_to_VM(src_dpid, in_port, vlan_id)
            if routes_to_vm:
                return self.__add_flow_entries(src_dpid, in_port, routes_to_vm, vlan_id,event)
            out_ports = list()
            log.info("Packet from DPID %d:%d" %(src_dpid, in_port))

            src_bid = self.__dpid_to_bid(src_dpid, in_port)
            flow = self.__vlan_to_flow(vlan_id)
            #dst_bids = self.__get_dst_bids(src_dpid, flow)
            dst_bids = self.__get_dst_bids(src_bid, flow)
            for dst_bid in dst_bids:
                dst_dpid = self.__bid_to_dpid(dst_bid)
                out_port = self.__find_output_port(src_dpid, dst_dpid)
                log.warning("out_ports: %s" % str(out_ports))
                out_ports.append(out_port)
            
            self.__add_flow_entries(src_dpid, in_port, out_ports, vlan_id,event) #TODO check this method 
        except Exception as e:
            log.info("\n> __route_packet. Packet could not be routed. Reason: %s\n" % str(e))
            log.info(traceback.format_exc())
            raise e

def launch(reactive = True):
    log.info("Launch!!")
    import pox.openflow.discovery
    try:
        pox.openflow.discovery.launch(no_flow=False, explicit_drop=True, link_timeout=100, eat_early_packets=False)
    except Exception as e:
        log.info("Exception trying to load the discovery APP: %s" % str(e))
        raise e
    log.info("Registering Network Coding App")
    #XXX: would it be a good idea to put sleep here in order to let the discovery up find all the nodes?
    core.registerNew(network_coding_butterfly, reactive)
