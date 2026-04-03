"""
Custom Mininet Topology for QoS Priority Controller
Project 16 | UE24CS252B - Computer Networks | PES University

Topology:
    h1 (10.0.0.1) ─┐
    h2 (10.0.0.2) ──── s1 (OVS Switch) ──── POX Controller (6633)
    h3 (10.0.0.3) ─┘

How to run:
    Terminal 1 - Start POX (Normal):
        cd ~/pox && ./pox.py log.level --DEBUG ext.qos_controller

    Terminal 1 - Start POX (Failure):
        cd ~/pox && ./pox.py log.level --DEBUG ext.qos_controller --failure=true

    Terminal 2 - Start this topology:
        sudo python3 qos_topology.py
"""

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.topo import Topo
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.link import TCLink


class QoSTopology(Topo):
    def build(self):
        # Single switch
        s1 = self.addSwitch('s1', protocols='OpenFlow10')

        # Three hosts with fixed IPs and MACs (makes logs cleaner)
        h1 = self.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = self.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        h3 = self.addHost('h3', ip='10.0.0.3/24', mac='00:00:00:00:00:03')

        # Links with 10 Mbps bandwidth (makes iperf results visible)
        self.addLink(h1, s1, bw=10, delay='2ms')
        self.addLink(h2, s1, bw=10, delay='2ms')
        self.addLink(h3, s1, bw=10, delay='2ms')


def print_test_guide():
    info('\n')
    info('=' * 60 + '\n')
    info('  QoS PRIORITY CONTROLLER - TEST GUIDE\n')
    info('=' * 60 + '\n')
    info('\n--- SCENARIO 1: Normal Mode (QoS Priorities) ---\n')
    info('  Step 1: Basic connectivity\n')
    info('    mininet> pingall\n')
    info('    Expected: 0% packet loss\n\n')
    info('  Step 2: ICMP - High Priority (300)\n')
    info('    mininet> h1 ping -c 5 h2\n')
    info('    Expected: All 5 packets received, low RTT\n\n')
    info('  Step 3: TCP - Medium Priority (200)\n')
    info('    mininet> h2 iperf -s &\n')
    info('    mininet> h1 iperf -c 10.0.0.2 -t 5\n')
    info('    Expected: ~8-10 Mbps throughput\n\n')
    info('  Step 4: UDP - Low Priority (100)\n')
    info('    mininet> h3 iperf -s -u &\n')
    info('    mininet> h1 iperf -c 10.0.0.3 -u -b 5M -t 5\n\n')
    info('  Step 5: Check flow table\n')
    info('    mininet> sh ovs-ofctl dump-flows s1\n')
    info('    Expected: priority=300 (ICMP), 200 (TCP), 100 (UDP)\n\n')
    info('--- SCENARIO 2: Failure Mode (h3 isolated) ---\n')
    info('  Restart POX with: --failure=true\n')
    info('  Then run:\n')
    info('    mininet> h1 ping -c 5 h2   <- should SUCCEED\n')
    info('    mininet> h1 ping -c 5 h3   <- should FAIL (100% loss)\n')
    info('    mininet> sh ovs-ofctl dump-flows s1\n')
    info('    Expected: priority=400 DROP rule for h3 traffic\n')
    info('=' * 60 + '\n\n')


def run():
    setLogLevel('info')
    topo = QoSTopology()

    net = Mininet(
        topo=topo,
        controller=lambda name: RemoteController(
            name, ip='127.0.0.1', port=6633),
        switch=OVSSwitch,
        link=TCLink,
        autoSetMacs=False   # We set MACs manually above
    )

    net.start()

    # Verify OVS is using OpenFlow 1.0
    net['s1'].cmd('ovs-vsctl set bridge s1 protocols=OpenFlow10')

    info('\n*** Network started successfully!\n')
    info('    h1: 10.0.0.1  MAC: 00:00:00:00:00:01\n')
    info('    h2: 10.0.0.2  MAC: 00:00:00:00:00:02\n')
    info('    h3: 10.0.0.3  MAC: 00:00:00:00:00:03\n')
    info('    Switch: s1 | Controller: 127.0.0.1:6633\n')

    print_test_guide()

    CLI(net)
    net.stop()
    info('\n*** Network stopped cleanly\n')


if __name__ == '__main__':
    run()