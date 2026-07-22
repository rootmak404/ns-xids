

from scapy.utils import PcapReader

from .flow_assembler import FlowAssembler
from .packet_parser import parse_packet


def replay_pcap(pcap_path: str, flow_timeout_us: int = 120_000_000):
    assembler = FlowAssembler(flow_timeout_us=flow_timeout_us)
    last_time_us = 0

    with PcapReader(pcap_path) as reader:
        for pkt in reader:
            timestamp_us = int(float(pkt.time) * 1_000_000)
            last_time_us = max(last_time_us, timestamp_us)

            parsed = parse_packet(pkt, timestamp_us)
            if parsed is None:
                continue

            completed = assembler.ingest(**parsed)
            if completed is not None:
                yield completed.extract_features(), _meta(completed)

            for expired in assembler.expire_idle_flows(timestamp_us):
                yield expired.extract_features(), _meta(expired)

   
    for flow in assembler.flush_all():
        yield flow.extract_features(), _meta(flow)


def _meta(flow) -> dict:
    return {
        "src_ip": flow.src_ip, "dst_ip": flow.dst_ip,
        "src_port": flow.src_port, "dst_port": flow.dst_port,
        "protocol": flow.protocol, "packet_count": len(flow.packets),
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python pcap_replay.py <path-to-pcap>")
        sys.exit(1)

    count = 0
    for features, meta in replay_pcap(sys.argv[1]):
        count += 1
        print(f"Flow #{count}: {meta['src_ip']}:{meta['src_port']} -> "
              f"{meta['dst_ip']}:{meta['dst_port']} ({meta['protocol']}, "
              f"{meta['packet_count']} pkts, {features['Flow Duration']}us)")
    print(f"\nTotal flows extracted: {count}")
