

import time
import threading

from scapy.all import sniff

from .flow_assembler import FlowAssembler
from .packet_parser import parse_packet


def capture_live(interface: str, on_flow, flow_timeout_us: int = 120_000_000,
                  expire_check_interval_s: float = 5.0, stop_event: threading.Event = None):
    """
    interface: e.g. "en0", "eth0" -- see `ifconfig`/`ip link` to list yours.
    on_flow: callback(feature_dict, flow_metadata) called for every completed flow.
    stop_event: optional threading.Event to signal graceful shutdown from
                another thread (e.g. the FastAPI /monitoring/stop endpoint).
    """
    assembler = FlowAssembler(flow_timeout_us=flow_timeout_us)

    def _expire_loop():
        while stop_event is None or not stop_event.is_set():
            time.sleep(expire_check_interval_s)
            now_us = int(time.time() * 1_000_000)
            for flow in assembler.expire_idle_flows(now_us):
                on_flow(flow.extract_features(), _meta(flow))

    expire_thread = threading.Thread(target=_expire_loop, daemon=True)
    expire_thread.start()

    def _on_packet(pkt):
        timestamp_us = int(float(pkt.time) * 1_000_000)
        parsed = parse_packet(pkt, timestamp_us)
        if parsed is None:
            return
        completed = assembler.ingest(**parsed)
        if completed is not None:
            on_flow(completed.extract_features(), _meta(completed))

    try:
        sniff(
            iface=interface,
            prn=_on_packet,
            store=False,
            stop_filter=lambda p: stop_event is not None and stop_event.is_set(),
        )
    finally:
        for flow in assembler.flush_all():
            on_flow(flow.extract_features(), _meta(flow))


def _meta(flow) -> dict:
    return {
        "src_ip": flow.src_ip, "dst_ip": flow.dst_ip,
        "src_port": flow.src_port, "dst_port": flow.dst_port,
        "protocol": flow.protocol, "packet_count": len(flow.packets),
    }


if __name__ == "__main__":
    import sys
    iface = sys.argv[1] if len(sys.argv) > 1 else "en0"
    print(f"Capturing on {iface}... (Ctrl+C to stop; needs sudo/admin)")

    def _print_flow(features, meta):
        print(f"{meta['src_ip']}:{meta['src_port']} -> {meta['dst_ip']}:{meta['dst_port']} "
              f"({meta['protocol']}, {meta['packet_count']} pkts)")

    capture_live(iface, _print_flow)
