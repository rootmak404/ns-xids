

import threading

from backend.database.models import SessionLocal
from backend.feature_extraction.live_capture import capture_live
from backend.api.pipeline import process_flow


class CaptureManager:
    def __init__(self):
        self._thread = None
        self._stop_event = None
        self._start_error = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, interface: str):
        if self.is_running:
            raise RuntimeError("Capture is already running")

        self._stop_event = threading.Event()
        self._start_error = None
        started = threading.Event()  

        def _run():
            db = SessionLocal()

            def on_flow(features, meta):
                try:
                    process_flow(
                        db, features=features,
                        src_ip=meta["src_ip"], dst_ip=meta["dst_ip"],
                        src_port=meta["src_port"], dst_port=meta["dst_port"],
                        protocol=meta["protocol"],
                    )
                except Exception as e:
                    
                    print(f"[monitoring] failed to process a flow: {e}")

            try:
                started.set()  # best-effort: sniff() below may still fail immediately
                capture_live(interface, on_flow, stop_event=self._stop_event)
            except Exception as e:
                self._start_error = str(e)
            finally:
                db.close()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        started.wait(timeout=2)

        self._thread.join(timeout=1.5)
        if self._start_error:
            self._thread = None
            self._stop_event = None
            raise RuntimeError(self._start_error)

    def stop(self):
        if not self.is_running:
            raise RuntimeError("Capture is not running")
        self._stop_event.set()
        self._thread.join(timeout=5)
        self._thread = None
        self._stop_event = None


capture_manager = CaptureManager()
