from PyQt5.QtCore import QObject, pyqtSignal
import threading
import time

try:
    import mido
    try:
        mido.set_backend('mido.backends.rtmidi')
    except Exception:
        pass
except Exception:
    mido = None


class MidiManager(QObject):
    messageReceived = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.input_name = None
        self._thread = None
        self._stop = threading.Event()

    def available(self):
        return mido is not None

    def list_input_names(self):
        if mido is None:
            return []
        try:
            return mido.get_input_names()
        except Exception:
            return []

    def list_output_names(self):
        if mido is None:
            return []
        try:
            return mido.get_output_names()
        except Exception:
            return []

    def start_listening(self, input_name: str):
        if mido is None:
            return False
        try:
            self.stop()
        except Exception:
            pass
        self.input_name = input_name
        self._stop.clear()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        try:
            self._stop.set()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.0)
        except Exception:
            pass

    def _worker(self):
        port = None
        try:
            port = mido.open_input(self.input_name)
            while not self._stop.is_set():
                try:
                    for msg in port.iter_pending():
                        try:
                            self.messageReceived.emit(msg)
                        except Exception:
                            pass
                except Exception:
                    pass
                time.sleep(0.01)
        except Exception:
            pass
        finally:
            try:
                if port:
                    port.close()
            except Exception:
                pass
