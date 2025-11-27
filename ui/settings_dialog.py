from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QScrollArea
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QLinearGradient


class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None, checked=False):
        super().__init__(parent)
        self._checked = bool(checked)
        self._offset = 3.0
        self.setFixedSize(48, 26)
        self.setCursor(Qt.PointingHandCursor)
        self._update_offset_immediate()

    def sizeHint(self):
        return QSize(48, 26)

    def isChecked(self):
        return self._checked

    def setChecked(self, value):
        val = bool(value)
        if self._checked != val:
            self._checked = val
            self.animate_knob()
            self.update()
            try:
                self.toggled.emit(self._checked)
            except Exception:
                pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.setChecked(not self._checked)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Track com gradiente sutil
        track_rect = self.rect()
        radius = track_rect.height() / 2
        
        if self._checked:
            track_color = QColor(30, 215, 96)  # Verde Spotify
        else:
            track_color = QColor(40, 40, 40)
        
        painter.setBrush(track_color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(track_rect, radius, radius)

        # Knob
        knob_d = track_rect.height() - 6
        knob_y = 3
        knob_x = int(self._offset)
        if self._checked:
            knob_x = track_rect.width() - knob_d - 3
        if hasattr(self, '_animating') and self._animating:
            knob_x = int(self._offset)
        
        painter.setBrush(QColor(255, 255, 255))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(knob_x, knob_y, knob_d, knob_d)

    def _update_offset_immediate(self):
        if self._checked:
            self._offset = self.width() - (self.height() - 6) - 3
        else:
            self._offset = 3

    def animate_knob(self):
        try:
            self._animating = True
            start = 3 if self._checked else self.width() - (self.height() - 6) - 3
            end = self.width() - (self.height() - 6) - 3 if self._checked else 3
            anim = QPropertyAnimation(self, b"offset")
            anim.setDuration(200)
            anim.setStartValue(start)
            anim.setEndValue(end)
            anim.finished.connect(self._on_anim_finished)
            anim.start()
            self._anim = anim
        except Exception:
            self._animating = False
            self._update_offset_immediate()
            self.update()

    def _on_anim_finished(self):
        self._animating = False
        self.update()

    @pyqtProperty(float)
    def offset(self):
        return float(self._offset)

    @offset.setter
    def offset(self, value):
        self._offset = float(value)
        self.update()


class SettingRow(QWidget):
    def __init__(self, title, subtitle="", parent=None, checked=False):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 12, 0, 12)
        layout.setSpacing(16)
        
        # Textos
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(4)
        
        title_label = QLabel(title)
        title_label.setFont(QFont("SF Pro Display", 14, QFont.Normal))
        title_label.setStyleSheet("color: #FFFFFF;")
        text_layout.addWidget(title_label)
        
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setFont(QFont("SF Pro Display", 11))
            subtitle_label.setStyleSheet("color: #B3B3B3;")
            subtitle_label.setWordWrap(True)
            text_layout.addWidget(subtitle_label)
        
        layout.addWidget(text_container, 1)
        
        # Toggle
        self.toggle = ToggleSwitch(checked=checked)
        layout.addWidget(self.toggle)


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        self.setModal(True)
        self.setMinimumSize(540, 620)
        self.setMaximumSize(540, 800)
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # Estilo moderno com gradiente
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #121212,
                    stop:1 #1a1a1a
                );
                border-radius: 12px;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #404040;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #505050;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QPushButton {
                background-color: #FFFFFF;
                color: #000000;
                border: none;
                border-radius: 22px;
                padding: 12px 32px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #B3B3B3;
                transform: scale(1.04);
            }
            QPushButton:pressed {
                background-color: #A0A0A0;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background: transparent;")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(32, 28, 32, 20)
        header_layout.setSpacing(8)
        
        title = QLabel("Configurações")
        title.setFont(QFont("SF Pro Display", 28, QFont.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(title)
        
        subtitle = QLabel("Personalize sua experiência")
        subtitle.setFont(QFont("SF Pro Display", 13))
        subtitle.setStyleSheet("color: #B3B3B3;")
        header_layout.addWidget(subtitle)
        
        main_layout.addWidget(header)

        # Linha divisória
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #282828;")
        main_layout.addWidget(line)

        # Scroll Area para configurações
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(32, 24, 32, 24)
        scroll_layout.setSpacing(8)

        # Seção: Reprodução
        section_playback = QLabel("REPRODUÇÃO")
        section_playback.setFont(QFont("SF Pro Display", 11, QFont.Bold))
        section_playback.setStyleSheet("color: #B3B3B3; padding-top: 8px;")
        scroll_layout.addWidget(section_playback)
        
        self.lr_toggle = SettingRow(
            "LR (Lado Reverso)",
            "Ativa o modo de reprodução alternado",
            checked=False
        )
        scroll_layout.addWidget(self.lr_toggle)
        
        self.auto_skip = SettingRow(
            "Pular Automaticamente",
            "Ignora músicas marcadas para pular",
            checked=True
        )
        scroll_layout.addWidget(self.auto_skip)
        
        self.auto_save = SettingRow(
            "Salvar Automaticamente",
            "Salva o progresso das playlists em tempo real",
            checked=True
        )
        scroll_layout.addWidget(self.auto_save)

        # Divisória
        divider1 = QWidget()
        divider1.setFixedHeight(1)
        divider1.setStyleSheet("background-color: #282828; margin: 16px 0;")
        scroll_layout.addWidget(divider1)

        # Seção: Interface
        section_interface = QLabel("INTERFACE")
        section_interface.setFont(QFont("SF Pro Display", 11, QFont.Bold))
        section_interface.setStyleSheet("color: #B3B3B3; padding-top: 8px;")
        scroll_layout.addWidget(section_interface)
        
        self.show_time = SettingRow(
            "Exibir Hora",
            "Mostra o horário atual na interface",
            checked=False
        )
        scroll_layout.addWidget(self.show_time)

        # Divisória
        divider2 = QWidget()
        divider2.setFixedHeight(1)
        divider2.setStyleSheet("background-color: #282828; margin: 16px 0;")
        scroll_layout.addWidget(divider2)

        # Seção: Áudio
        section_audio = QLabel("ÁUDIO")
        section_audio.setFont(QFont("SF Pro Display", 11, QFont.Bold))
        section_audio.setStyleSheet("color: #B3B3B3; padding-top: 8px;")
        scroll_layout.addWidget(section_audio)
        
        self.equalize = SettingRow(
            "Equalizar Faixas Sonoras",
            "Normaliza o volume entre diferentes músicas",
            checked=True
        )
        scroll_layout.addWidget(self.equalize)
        
        self.high_quality = SettingRow(
            "Qualidade de Áudio Alta",
            "Reproduz em qualidade premium quando disponível",
            checked=False
        )
        scroll_layout.addWidget(self.high_quality)

        scroll_layout.addStretch(1)
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, 1)

        # Footer com botão
        footer = QWidget()
        footer.setStyleSheet("background: transparent;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(32, 20, 32, 28)
        
        footer_layout.addStretch(1)
        close_btn = QPushButton("Fechar")
        close_btn.setFixedHeight(44)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                padding: 0px 16px;
                border: none;
                border-radius: 22px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f6f6f6;
            }
            QPushButton:pressed {
                background-color: #e0e0e0;
            }
        """)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        
        main_layout.addWidget(footer)

    def center_on_parent(self):
        try:
            if self.parent() is not None:
                parent_geo = self.parent().frameGeometry()
                self.adjustSize()
                geo = self.frameGeometry()
                geo.moveCenter(parent_geo.center())
                self.move(geo.topLeft())
        except Exception:
            pass