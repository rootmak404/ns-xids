

from .flow import Flow, PacketRecord

DEFAULT_FLOW_TIMEOUT_US = 120_000_000  
def _flow_key(src_ip, dst_ip, src_port, dst_port, protocol):
    """Normalize so both directions of a conversation map to the same key.
    The lexicographically smaller (ip, port) pair is treated as side 'A';
    the first packet's direction (A->B or B->A) determines which side is
    'forward' for that specific flow instance."""
    a = (src_ip, src_port)
    b = (dst_ip, dst_port)
    if a <= b:
        return (src_ip, src_port, dst_ip, dst_port, protocol)
    return (dst_ip, dst_port, src_ip, src_port, protocol)


class FlowAssembler:
    def __init__(self, flow_timeout_us: int = DEFAULT_FLOW_TIMEOUT_US):
        self.flow_timeout_us = flow_timeout_us
        self._active_flows = {}       
        self._flow_first_src = {}     
        self._fin_seen = {}           

    def ingest(self, *, src_ip, dst_ip, src_port, dst_port, protocol,
               timestamp_us, length, header_length, tcp_flags,
               window_size=0, has_payload=False):
        """Feed one packet in. Returns a completed Flow if this packet closed
        one (RST, or FIN seen from both directions) or None otherwise. Call
        flush_all() periodically/at the end to catch flows that are simply
        idle without a clean close."""

        key = _flow_key(src_ip, dst_ip, src_port, dst_port, protocol)

        if key not in self._active_flows:
            self._active_flows[key] = Flow(
                src_ip=src_ip, dst_ip=dst_ip,
                src_port=src_port, dst_port=dst_port, protocol=protocol,
            )
            self._flow_first_src[key] = (src_ip, src_port)
            self._fin_seen[key] = set()

        flow = self._active_flows[key]
        direction = "fwd" if (src_ip, src_port) == self._flow_first_src[key] else "bwd"

        flow.add_packet(PacketRecord(
            timestamp_us=timestamp_us, direction=direction, length=length,
            header_length=header_length, tcp_flags=tcp_flags or {},
            window_size=window_size, has_payload=has_payload,
        ))

        if tcp_flags and tcp_flags.get("RST"):
           
            del self._active_flows[key]
            del self._flow_first_src[key]
            del self._fin_seen[key]
            return flow

        if tcp_flags and tcp_flags.get("FIN"):
            self._fin_seen[key].add(direction)
            if {"fwd", "bwd"} <= self._fin_seen[key]:
                
                del self._active_flows[key]
                del self._flow_first_src[key]
                del self._fin_seen[key]
                return flow

        return None

    def expire_idle_flows(self, current_time_us: int) -> list:
        """Call periodically (e.g. once per batch of packets, or once per
        second in live capture) to flush flows that have gone quiet without
        a clean FIN/FIN close. Returns a list of completed Flow objects."""
        expired = []
        for key in list(self._active_flows.keys()):
            flow = self._active_flows[key]
            if current_time_us - flow.end_time > self.flow_timeout_us:
                expired.append(flow)
                del self._active_flows[key]
                del self._flow_first_src[key]
                del self._fin_seen[key]
        return expired

    def flush_all(self) -> list:
        """Force-complete every still-active flow. Call at end of pcap replay
        or on shutdown so no in-progress flow is silently dropped."""
        flows = list(self._active_flows.values())
        self._active_flows.clear()
        self._flow_first_src.clear()
        self._fin_seen.clear()
        return flows
