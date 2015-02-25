# Copyright 2014 Bence Ladoczki <ladoczki@tmit.bme.hu>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
OF 1.0 controller code for Network Coding Scenario

"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.util import dpidToStr

log = core.getLogger()

class network_coding(object):
    def __init__(self, reactive, ignore = None):
        """
        Initialize
    
        See LearningSwitch for meaning of 'transparent'
        'reactive' indicates how 
        'ignore' is an optional list/set of DPIDs to ignore
        """
        core.openflow.addListeners(self)
        self.reactive = reactive
        self.ignore = set(ignore) if ignore else ()
        if self.reactive:
            core.openflow.addListenerByName("PacketIn", self._handle_PacketIn)
        else:
            None#core.openflow.addListenerByName("ConnectionUp", self._handle_ConnectionUp)
    
    def _handle_PacketIn(self, event):
        """
        OF 1.0 compatible flowmod messages for the switches
        """
        log.error("Discovering packet type somehow %s", str(event) )
        log.error("Packet: %s", str(event.parse()))
        log.info("Packet-in Event DPID %s Port:%d" %(dpidToStr(event.dpid),event.port))

        if (event.dpid == 2):
            if event.port == 7:
                log.info("Flowmoding %s", dpidToStr(event.dpid))
                # B Flow (eth4) # <-- ONLY THIS IS BEING RETRIEVED. WHY?
                msg = of.ofp_flow_mod()
                msg.match = of.ofp_match(in_port = event.port)
                # Always put idle and/or hard timeouts it helps to clean the table
                msg.idle_timeout = 10
                msg.hard_timeout = 20
                msg.actions.append(of.ofp_action_output(port = 5))
                msg.actions.append(of.ofp_action_output(port = 2))
                event.connection.send(msg)
                log.info("Forwarding B flow => S2.P7 -> S2.P5 & S2.P2")

            elif event.port == 4:
                # A+B Flow (eth2)
                msg = of.ofp_flow_mod()
                msg.match = of.ofp_match(in_port = event.port)
                msg.idle_timeout = 10
                msg.hard_timeout = 20
                msg.actions.append(of.ofp_action_output(port = 2))
                event.connection.send(msg)
                log.info("Forwarding A+B flow => S2.P4 -> S2.P2")

            elif event.port == 6:
                # A Flow (eth3)
                msg = of.ofp_flow_mod()
                msg.match = of.ofp_match(in_port = event.port)
                msg.idle_timeout = 10
                msg.hard_timeout = 20
                msg.actions.append(of.ofp_action_output(port = 5))
                event.connection.send(msg)
                log.info("Forwarding A flow => S2.P6 -> S2.P5")
            else:
                log.info("Packet-In From in DPID %d port %d" %(event.dpid, event.port)) 
        
        if (event.dpid == 4):
            if event.port == 1:
                log.info("Flowmoding %s", dpidToStr(event.dpid))
                # s4 -> NFTester (Vienna)
                msg = of.ofp_flow_mod()
                msg.match = of.ofp_match(in_port = event.port)
                msg.actions.append(of.ofp_action_output(port = 8))
                msg.idle_timeout = 10
                msg.hard_timeout = 20
                event.connection.send(msg)
                log.info("Forwarding B, A+B flows [@S2.P2] => S5.P6 -> S5.P8 [@ZAG]")
        
        if (event.dpid == 5):
            if event.port == 6:
                log.info("Flowmoding %s", dpidToStr(event.dpid))
                # s5 -> NFTester
                msg = of.ofp_flow_mod()
                msg.match = of.ofp_match(in_port = 6)
                msg.actions.append(of.ofp_action_output(port = 8))
                msg.idle_timeout = 10
                msg.hard_timeout = 20
                event.connection.send(msg)
                log.info("Forwarding B, A+B flows [@S2.P2] => S5.P6 -> S5.P8 [@ZAG]")

        if (event.dpid == 3):
            log.info("Flowmoding %s", dpidToStr(event.dpid))
            # s2 -> s5
            #msg = of.ofp_flow_mod()
            #msg.match = of.ofp_match(in_port = 8)
            #msg.actions.append(of.ofp_action_output(port = 7))
            #event.connection.send(msg)

    def _handle_PacketIn2(self, event):
        """
        Be a reactive hub by flooding every incoming packet
        """
        #msg = of.ofp_packet_out()
        #msg.data = event.ofp
        #msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
        #event.connection.send(msg)

def launch(reactive = False):
    core.registerNew(network_coding, reactive)
