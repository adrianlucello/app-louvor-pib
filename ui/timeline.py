from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath
import numpy as np


class TimelineWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._envelope = []
        self._playhead_frac = 0.0
        self.setMinimumHeight(100)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("background-color: #252525;")

    def set_envelope(self, envelope):
        self._envelope = envelope or []
        self.update()

    def set_playhead_fraction(self, frac):
        self._playhead_frac = max(0.0, min(1.0, float(frac)))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w = self.width()
        h = self.height()
        p.fillRect(self.rect(), QColor("#252525"))
        if not self._envelope:
            return
        center_y = h / 2
        max_amp = h * 0.45
        path = QPainterPath()
        path.moveTo(0, center_y)
        for x in range(w):
            idx = int((x / max(1, w - 1)) * (len(self._envelope) - 1))
            a = self._envelope[idx] * max_amp
            y = center_y - a
            path.lineTo(x, y)
        for x in range(w - 1, -1, -1):
            idx = int((x / max(1, w - 1)) * (len(self._envelope) - 1))
            a = self._envelope[idx] * max_amp
            y = center_y + a
            path.lineTo(x, y)
        path.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 200))
        p.drawPath(path)
        ph_x = int(self._playhead_frac * w)
        p.setPen(QPen(QColor("#49c149"), 2))
        p.drawLine(ph_x, 0, ph_x, h)


class TimelineWorker(QObject):
    envelopeReady = pyqtSignal(object, int, int, object)
    error = pyqtSignal(str)

    def __init__(self, tracks, target_points, song_id):
        super().__init__()
        self.tracks = tracks
        self.target_points = max(100, int(target_points or 1000))
        self.song_id = song_id

    def run(self):
        try:
            tracks = self.tracks or []
            if not tracks:
                self.envelopeReady.emit([], 0, 0, self.song_id)
                return
            max_len = max(len(t['samples']) for t in tracks)
            sample_rate = tracks[0].get('sample_rate', 44100)
            block = max(1, max_len // self.target_points)
            combined = None
            for t in tracks:
                samples = t['samples']
                vol = t.get('volume', 0.8)
                muted = t.get('muted', False)
                if muted:
                    continue
                try:
                    mono = np.mean(np.abs(samples), axis=1)
                except Exception:
                    mono = np.abs(samples.reshape(-1))
                mono = mono * float(vol)
                if len(mono) < max_len:
                    pad = np.zeros(max_len - len(mono), dtype=mono.dtype)
                    mono = np.concatenate([mono, pad])
                trim_len = (len(mono) // block) * block
                mono = mono[:trim_len]
                mono_blocks = mono.reshape(-1, block)
                rms = np.sqrt(np.mean(mono_blocks**2, axis=1))
                if combined is None:
                    combined = rms
                else:
                    combined = combined + rms
            if combined is None or len(combined) == 0:
                self.envelopeReady.emit([], max_len, sample_rate, self.song_id)
                return
            max_val = combined.max() if combined.size > 0 else 1.0
            env = combined / max_val if max_val > 0 else combined
            env = np.clip(env, 0.0, 1.0)
            env = np.maximum(env, 0.05)
            self.envelopeReady.emit(env.tolist(), max_len, sample_rate, self.song_id)
        except Exception as e:
            self.error.emit(str(e))
