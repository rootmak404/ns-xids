

import statistics
from dataclasses import dataclass, field

ACTIVE_IDLE_THRESHOLD_US = 1_000_000  


@dataclass
class PacketRecord:
    timestamp_us: int      
    direction: str         
    length: int             
    header_length: int      
    tcp_flags: dict          
    window_size: int = 0
    has_payload: bool = False


@dataclass
class Flow:
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    packets: list = field(default_factory=list)

    def add_packet(self, pkt: PacketRecord):
        self.packets.append(pkt)

    @property
    def start_time(self):
        return self.packets[0].timestamp_us

    @property
    def end_time(self):
        return self.packets[-1].timestamp_us

    def _by_direction(self, direction):
        return [p for p in self.packets if p.direction == direction]

    def _iat(self, pkts):
        """Inter-arrival times (microseconds) between consecutive packets in `pkts`."""
        times = sorted(p.timestamp_us for p in pkts)
        return [t2 - t1 for t1, t2 in zip(times, times[1:])]

    def _active_idle_periods(self):
        """Segment the flow into active bursts separated by idle gaps > threshold.
        Returns (active_durations, idle_durations), both in microseconds."""
        times = sorted(p.timestamp_us for p in self.packets)
        if len(times) < 2:
            return [0], [0]

        active_durations, idle_durations = [], []
        burst_start = times[0]
        last_t = times[0]

        for t in times[1:]:
            gap = t - last_t
            if gap > ACTIVE_IDLE_THRESHOLD_US:
                active_durations.append(last_t - burst_start)
                idle_durations.append(gap)
                burst_start = t
            last_t = t
        active_durations.append(last_t - burst_start)

        if not idle_durations:
            idle_durations = [0]
        return active_durations, idle_durations

    def extract_features(self) -> dict:
        """Returns a raw (unscaled) feature dict with exactly the 35 keys
        required by models/feature_names.pkl. Caller is responsible for
        clipping (iqr_bounds.pkl) and scaling (scaler.pkl) before prediction --
        see backend/ml/predict.py, which does this for you if you pass this
        dict straight into IDSPredictor.predict()."""

        fwd = self._by_direction("fwd")
        bwd = self._by_direction("bwd")

        duration_us = max(1, self.end_time - self.start_time)  
        duration_s = duration_us / 1_000_000

        fwd_lengths = [p.length for p in fwd]
        bwd_lengths = [p.length for p in bwd]
        all_lengths = fwd_lengths + bwd_lengths

        flow_iat = self._iat(self.packets)
        fwd_iat = self._iat(fwd)
        bwd_iat = self._iat(bwd)

        active_durations, idle_durations = self._active_idle_periods()

        flags = {"FIN": 0, "RST": 0, "PSH": 0, "ACK": 0, "URG": 0}
        for p in self.packets:
            for flag in flags:
                if p.tcp_flags.get(flag):
                    flags[flag] += 1

        fwd_psh = sum(1 for p in fwd if p.tcp_flags.get("PSH"))

        total_bytes = sum(all_lengths)

        return {
            "Destination Port": self.dst_port,
            "Flow Duration": duration_us,
            "Total Fwd Packets": len(fwd),
            "Total Length of Fwd Packets": sum(fwd_lengths),
            "Fwd Packet Length Max": max(fwd_lengths) if fwd_lengths else 0,
            "Fwd Packet Length Min": min(fwd_lengths) if fwd_lengths else 0,
            "Bwd Packet Length Max": max(bwd_lengths) if bwd_lengths else 0,
            "Bwd Packet Length Min": min(bwd_lengths) if bwd_lengths else 0,
            "Flow Bytes/s": total_bytes / duration_s if duration_s > 0 else 0,
            "Flow Packets/s": len(self.packets) / duration_s if duration_s > 0 else 0,
            "Flow IAT Mean": statistics.fmean(flow_iat) if flow_iat else 0,
            "Flow IAT Std": statistics.pstdev(flow_iat) if len(flow_iat) > 1 else 0,
            "Flow IAT Min": min(flow_iat) if flow_iat else 0,
            "Fwd IAT Mean": statistics.fmean(fwd_iat) if fwd_iat else 0,
            "Fwd IAT Min": min(fwd_iat) if fwd_iat else 0,
            "Bwd IAT Total": sum(bwd_iat) if bwd_iat else 0,
            "Bwd IAT Mean": statistics.fmean(bwd_iat) if bwd_iat else 0,
            "Bwd IAT Std": statistics.pstdev(bwd_iat) if len(bwd_iat) > 1 else 0,
            "Bwd IAT Min": min(bwd_iat) if bwd_iat else 0,
            "Fwd PSH Flags": fwd_psh,   # NOTE: documented dead feature post-clipping, see models/README.md
            "Fwd Header Length": sum(p.header_length for p in fwd),
            "Bwd Packets/s": len(bwd) / duration_s if duration_s > 0 else 0,
            "Min Packet Length": min(all_lengths) if all_lengths else 0,
            "FIN Flag Count": flags["FIN"],   # dead feature post-clipping
            "RST Flag Count": flags["RST"],   # dead feature post-clipping
            "PSH Flag Count": flags["PSH"],
            "ACK Flag Count": flags["ACK"],
            "URG Flag Count": flags["URG"],   # dead feature post-clipping
            "Down/Up Ratio": (len(bwd) / len(fwd)) if fwd else 0,
            "Init_Win_bytes_forward": fwd[0].window_size if fwd else 0,
            "Init_Win_bytes_backward": bwd[0].window_size if bwd else 0,
            "act_data_pkt_fwd": sum(1 for p in fwd if p.has_payload),
            "Active Mean": statistics.fmean(active_durations) if active_durations else 0,
            "Active Std": statistics.pstdev(active_durations) if len(active_durations) > 1 else 0,  # dead feature
            "Idle Std": statistics.pstdev(idle_durations) if len(idle_durations) > 1 else 0,          # dead feature
        }
