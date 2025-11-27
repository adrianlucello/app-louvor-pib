from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtGui import QFont, QIcon
import os
try:
    import qtawesome
except Exception:
    qtawesome = None

class HeaderWidget(QWidget):
    addSongRequested = pyqtSignal()
    saveRequested = pyqtSignal()
    playRequested = pyqtSignal()
    pauseRequested = pyqtSignal()
    restartRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(70)
        self.setStyleSheet("background-color: transparent; border-bottom: 1px solid #282828;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 0)
        layout.setSpacing(16)

        # Título com fonte maior e espaçamento
        self.title_label = QLabel("")
        title_font = QFont("Segoe UI", 20, QFont.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #ffffff; padding: 0px;")
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Botão Add Song - estilo Spotify com hover suave
        self.add_song_button = QPushButton("+ Adicionar Música")
        self.add_song_button.setFixedHeight(40)
        self.add_song_button.setMinimumWidth(160)
        self.add_song_button.setCursor(Qt.PointingHandCursor)
        self.add_song_button.setStyleSheet(
            """
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                padding: 0px 24px;
                border: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            QPushButton:hover {
                background-color: #f6f6f6;
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
            """
        )
        self.add_song_button.clicked.connect(lambda: self.addSongRequested.emit())
        layout.addWidget(self.add_song_button)

        self.save_button = QPushButton("")
        self.save_button.setFixedHeight(40)
        self.save_button.setMinimumWidth(60)
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.setStyleSheet(
            """
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                padding: 0px 16px;
                border: none;
                border-radius: 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f6f6f6;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
            """
        )
        icon = self._load_save_icon(QSize(28, 28))
        if icon:
            self.save_button.setIcon(icon)
            self.save_button.setIconSize(QSize(28, 28))
        else:
            self.save_button.setText("Salvar")
        self.save_button.clicked.connect(lambda: self.saveRequested.emit())
        layout.addWidget(self.save_button)

        # Espaçamento antes dos controles
        layout.addSpacing(32)

        # Botões de controle - estilo minimalista Spotify
        self.play_button = QPushButton("▶")
        self.pause_button = QPushButton("❚❚")
        self.restart_button = QPushButton("⟲")

        control_style = """
            QPushButton {
                background-color: transparent;
                color: #b3b3b3;
                border: none;
                border-radius: 20px;
                padding: 0px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ffffff;
                background-color: #1a1a1a;
            }
            QPushButton:pressed {
                color: #ffffff;
                background-color: #282828;
            }
            QPushButton[active="true"] {
                color: #1db954;
            }
        """

        for btn in (self.play_button, self.pause_button, self.restart_button):
            btn.setStyleSheet(control_style)
            btn.setFixedSize(40, 40)
            btn.setCursor(Qt.PointingHandCursor)
            layout.addWidget(btn)

        self.play_button.clicked.connect(lambda: self.playRequested.emit())
        self.pause_button.clicked.connect(lambda: self.pauseRequested.emit())
        self.restart_button.clicked.connect(lambda: self.restartRequested.emit())

    def _load_save_icon(self, size):
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            for folder in [base_path, os.path.join(base_path, 'Resources')]:
                path = os.path.join(folder, 'save.svg')
                if os.path.exists(path):
                    icon = QIcon(path)
                    return icon
        except Exception:
            pass
        if qtawesome:
            for name in ['fa5s.save', 'fa.save', 'mdi.content-save']:
                try:
                    return qtawesome.icon(name, color='#000000')
                except Exception:
                    continue
        return None

    def set_worship_title(self, text: str):
        self.title_label.setText(text or "")

    def set_play_blink(self, on: bool):
        self.play_button.setProperty("active", bool(on))
        self.play_button.style().unpolish(self.play_button)
        self.play_button.style().polish(self.play_button)
        self.play_button.update()
