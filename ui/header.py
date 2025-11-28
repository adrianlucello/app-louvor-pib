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
    settingsRequested = pyqtSignal()
    playRequested = pyqtSignal()
    pauseRequested = pyqtSignal()
    restartRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #121212,
                    stop:1 #1a1a1a
                );
                border-bottom: 1px solid #282828;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(32, 0, 32, 0)
        layout.setSpacing(16)

        # Título com fonte SF Pro Display
        self.title_label = QLabel("")
        title_font = QFont("SF Pro Display", 24, QFont.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("""
            color: #FFFFFF; 
            padding: 0px;
            background: transparent;
        """)
        layout.addWidget(self.title_label)

        layout.addStretch()

        # Botão Add Song - mantém branco para ícones pretos
        self.add_song_button = QPushButton("+ Adicionar Música")
        self.add_song_button.setFixedHeight(44)
        self.add_song_button.setMinimumWidth(180)
        self.add_song_button.setCursor(Qt.PointingHandCursor)
        self.add_song_button.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                padding: 0px 28px;
                border: none;
                border-radius: 22px;
                font-size: 14px;
                font-weight: 600;
                letter-spacing: 0.3px;
                font-family: "SF Pro Display";
            }
            QPushButton:hover {
                background-color: #B3B3B3;
                transform: scale(1.04);
            }
            QPushButton:pressed {
                background-color: #A0A0A0;
            }
        """)
        self.add_song_button.clicked.connect(lambda: self.addSongRequested.emit())
        layout.addWidget(self.add_song_button)

        # Botão Save - mantém branco
        self.save_button = QPushButton("")
        self.save_button.setFixedSize(48, 44)
        self.save_button.setCursor(Qt.PointingHandCursor)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                border: none;
                border-radius: 22px;
            }
            QPushButton:hover {
                background-color: #B3B3B3;
            }
            QPushButton:pressed {
                background-color: #A0A0A0;
            }
        """)
        icon = self._load_save_icon(QSize(24, 24))
        if icon:
            self.save_button.setIcon(icon)
            self.save_button.setIconSize(QSize(24, 24))
        else:
            self.save_button.setText("💾")
            self.save_button.setStyleSheet(self.save_button.styleSheet() + """
                QPushButton {
                    font-size: 18px;
                }
            """)
        self.save_button.clicked.connect(lambda: self.saveRequested.emit())
        layout.addWidget(self.save_button)

        # Botão Settings - mantém branco
        self.settings_button = QPushButton("")
        self.settings_button.setFixedSize(48, 44)
        self.settings_button.setCursor(Qt.PointingHandCursor)
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                border: none;
                border-radius: 22px;
            }
            QPushButton:hover {
                background-color: #B3B3B3;
            }
            QPushButton:pressed {
                background-color: #A0A0A0;
            }
        """)
        settings_icon = self._load_settings_icon(QSize(22, 22))
        if settings_icon:
            self.settings_button.setIcon(settings_icon)
            self.settings_button.setIconSize(QSize(22, 22))
        else:
            self.settings_button.setText("⚙")
            self.settings_button.setStyleSheet(self.settings_button.styleSheet() + """
                QPushButton {
                    font-size: 18px;
                }
            """)
        self.settings_button.clicked.connect(lambda: self.settingsRequested.emit())
        layout.addWidget(self.settings_button)

        # Divisor visual sutil
        separator = QWidget()
        separator.setFixedSize(1, 32)
        separator.setStyleSheet("background-color: #282828;")
        layout.addWidget(separator)

        # Botões de controle - estilo moderno Spotify
        self.play_button = QPushButton("▶")
        self.pause_button = QPushButton("⏸")
        self.restart_button = QPushButton("↻")

        control_style = """
            QPushButton {
                background-color: #282828;
                color: #B3B3B3;
                border: none;
                border-radius: 20px;
                padding: 0px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #333333;
                color: #FFFFFF;
            }
            QPushButton:pressed {
                background-color: #1ED760;
                color: #000000;
            }
            QPushButton[active="true"] {
                background-color: #1ED760;
                color: #000000;
                border: 2px solid #1ED760;
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

    def _load_settings_icon(self, size):
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            for folder in [base_path, os.path.join(base_path, 'Resources')]:
                path = os.path.join(folder, 'settings.svg')
                if os.path.exists(path):
                    icon = QIcon(path)
                    return icon
        except Exception:
            pass
        if qtawesome:
            for name in ['fa5s.cog', 'fa.cog', 'mdi.cog']:
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

    def set_pause_blink(self, on: bool):
        self.pause_button.setProperty("active", bool(on))
        self.pause_button.style().unpolish(self.pause_button)
        self.pause_button.style().polish(self.pause_button)
        self.pause_button.update()

    def set_restart_blink(self, on: bool):
        self.restart_button.setProperty("active", bool(on))
        self.restart_button.style().unpolish(self.restart_button)
        self.restart_button.style().polish(self.restart_button)
        self.restart_button.update()
