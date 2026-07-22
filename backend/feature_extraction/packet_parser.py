

from scapy.layers.inet import IP, TCP, UDP


def parse_packet(pkt, timestamp_us: int) -> dict | None:
    """Returns a dict of kwargs for FlowAssembler.ingest(), or None if the
    packet isn't an IPv4 TCP/UDP packet (everything else is out of scope for
    the 35-feature model, which is flow-level TCP/UDP only)."""

    if IP not in pkt:
        return None

    ip_layer = pkt[IP]
    src_ip, dst_ip = ip_layer.src, ip_layer.dst
    ip_header_len = ip_layer.ihl * 4 if ip_layer.ihl else 20

    if TCP in pkt:
        proto = "TCP"
        tcp = pkt[TCP]
        src_port, dst_port = int(tcp.sport), int(tcp.dport)
        tcp_header_len = tcp.dataofs * 4 if tcp.dataofs else 20
        header_length = ip_header_len + tcp_header_len
        flags_str = str(tcp.flags)
        tcp_flags = {
            "FIN": "F" in flags_str,
            "SYN": "S" in flags_str,
            "RST": "R" in flags_str,
            "PSH": "P" in flags_str,
            "ACK": "A" in flags_str,
            "URG": "U" in flags_str,
        }
        window_size = int(tcp.window) if tcp.window else 0
        payload_len = len(bytes(tcp.payload)) if tcp.payload else 0
        has_payload = payload_len > 0

    elif UDP in pkt:
        proto = "UDP"
        udp = pkt[UDP]
        src_port, dst_port = int(udp.sport), int(udp.dport)
        header_length = ip_header_len + 8  # UDP header is fixed 8 bytes
        tcp_flags = {"FIN": False, "SYN": False, "RST": False, "PSH": False, "ACK": False, "URG": False}
        window_size = 0
        payload_len = len(bytes(udp.payload)) if udp.payload else 0
        has_payload = payload_len > 0

    else:
        return None  

    return {
        "src_ip": src_ip, "dst_ip": dst_ip,
        "src_port": src_port, "dst_port": dst_port,
        "protocol": proto,
        "timestamp_us": timestamp_us,
        "length": len(pkt),
        "header_length": header_length,
        "tcp_flags": tcp_flags,
        "window_size": window_size,
        "has_payload": has_payload,
    }
