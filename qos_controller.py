"""
SDN QoS Priority Controller using POX
Project 16: Simple QoS Priority Controller
Course: UE24CS252B - Computer Networks, PES University

Scenario 1 (Normal):  ./pox.py log.level --DEBUG ext.qos_controller
Scenario 2 (Failure): ./pox.py log.level --DEBUG ext.qos_controller --failure=true
"""

from pox.core import core
from pox.lib.util import dpidToStr
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

PRIORITY_BLOCK   = 400
PRIORITY_ICMP    = 300
PRIORITY_TCP     = 200
PRIORITY_UDP     = 100
PRIORITY_DEFAULT = 10

IDLE_TIMEOUT = 20
HARD_TIMEOUT = 60

FAILURE_MODE = False
BLOCKED_IP   = "10.0.0.3"


class QoSSwitch(object):

    def __init__(self, connection):
        self.connection  = connection
        self.mac_to_port = {}
        connection.addListeners(self)
        log.info("Switch %s connected | FAILURE_MODE=%s",
                 dpidToStr(connection.dpid), FAILURE_MODE)

    def _classify(self, packet):
        if packet.find('icmp'):
            return PRIORITY_ICMP, "ICMP"
        if packet.find('tcp'):
            return PRIORITY_TCP, "TCP"
        if packet.find('udp'):
            return PRIORITY_UDP, "UDP"
        return PRIORITY_DEFAULT, "OTHER"

    def _involves_blocked_host(self, packet):
        ip_pkt = packet.find('ipv4')
        if ip_pkt:
            if str(ip_pkt.srcip) == BLOCKED_IP or \
               str(ip_pkt.dstip) == BLOCKED_IP:
                return True
        return False

    def _install_forward_rule(self, packet, in_port, out_port, priority, label):
        """Install a forward flow rule. Uses event.parsed (ethernet object)."""
        msg              = of.ofp_flow_mod()
        msg.match        = of.ofp_match.from_packet(packet, in_port)
        msg.priority     = priority
        msg.idle_timeout = IDLE_TIMEOUT
        msg.hard_timeout = HARD_TIMEOUT
        msg.actions.append(of.ofp_action_output(port=out_port))
        self.connection.send(msg)
        log.info("[FORWARD] %s | priority=%d | port %d -> %d",
                 label, priority, in_port, out_port)

    def _install_drop_rule(self, packet, in_port, src_ip, dst_ip):
        """Install a DROP rule (no actions). Uses event.parsed (ethernet object)."""
        msg              = of.ofp_flow_mod()
        msg.match        = of.ofp_match.from_packet(packet, in_port)
        msg.priority     = PRIORITY_BLOCK
        msg.idle_timeout = IDLE_TIMEOUT
        msg.hard_timeout = HARD_TIMEOUT
        # No actions = DROP
        self.connection.send(msg)
        log.warning("[DROP] %s -> %s | priority=%d | *** FAILURE SCENARIO ***",
                    src_ip, dst_ip, PRIORITY_BLOCK)

    def _send_packet_out(self, event, out_port):
        """Send packet out without installing a rule (used for flooding)."""
        msg         = of.ofp_packet_out()
        msg.data    = event.ofp          # raw ofp message for packet_out
        msg.actions.append(of.ofp_action_output(port=out_port))
        self.connection.send(msg)

    def _handle_PacketIn(self, event):
        # event.parsed  = ethernet object  <- use for matching
        # event.ofp     = raw openflow msg <- use for packet_out only
        packet  = event.parsed
        in_port = event.port

        if not packet.parsed:
            log.warning("Incomplete packet ignored")
            return

        src_mac = str(packet.src)
        dst_mac = str(packet.dst)

        # MAC learning
        self.mac_to_port[src_mac] = in_port

        # ── SCENARIO 2: FAILURE MODE ──────────────────────────────
        if FAILURE_MODE and self._involves_blocked_host(packet):
            ip_pkt = packet.find('ipv4')
            src_ip = str(ip_pkt.srcip) if ip_pkt else src_mac
            dst_ip = str(ip_pkt.dstip) if ip_pkt else dst_mac
            self._install_drop_rule(packet, in_port, src_ip, dst_ip)
            return

        # ── SCENARIO 1: NORMAL MODE ───────────────────────────────
        priority, label = self._classify(packet)

        ip_pkt = packet.find('ipv4')
        if ip_pkt:
            log.info("[PKT_IN] %s -> %s | %s | priority=%d",
                     str(ip_pkt.srcip), str(ip_pkt.dstip), label, priority)
        else:
            log.info("[PKT_IN] %s -> %s | %s | priority=%d",
                     src_mac, dst_mac, label, priority)

        if dst_mac in self.mac_to_port:
            out_port = self.mac_to_port[dst_mac]
            # Install flow rule using the parsed ethernet packet
            self._install_forward_rule(packet, in_port, out_port, priority, label)
            # Also send this first packet out immediately
            self._send_packet_out(event, out_port)
        else:
            log.info("[FLOOD] dst=%s unknown, flooding", dst_mac)
            self._send_packet_out(event, of.OFPP_FLOOD)


class QoSLauncher(object):
    def __init__(self):
        core.openflow.addListeners(self)
        log.info("=" * 50)
        log.info("  QoS Priority Controller - Project 16")
        log.info("  PES University | UE24CS252B")
        log.info("=" * 50)
        log.info("  ICMP  -> priority %d (Highest)", PRIORITY_ICMP)
        log.info("  TCP   -> priority %d (Medium)",  PRIORITY_TCP)
        log.info("  UDP   -> priority %d (Low)",     PRIORITY_UDP)
        log.info("  DROP  -> priority %d (Failure)", PRIORITY_BLOCK)
        log.info("=" * 50)
        if FAILURE_MODE:
            log.warning("  FAILURE MODE: %s will be DROPPED", BLOCKED_IP)
        else:
            log.info("  NORMAL MODE: All hosts reachable")
        log.info("=" * 50)

    def _handle_ConnectionUp(self, event):
        log.info("Switch connected: %s", dpidToStr(event.dpid))
        QoSSwitch(event.connection)


def launch(failure=False):
    global FAILURE_MODE
    FAILURE_MODE = str(failure).lower() in ('true', '1', 'yes')
    core.registerNew(QoSLauncher)