from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QScrollArea, QComboBox, QListWidget, QStyledItemDelegate, QStyleOptionViewItem, QCompleter, QStyle
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QPropertyAnimation, pyqtProperty, QRectF
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QLinearGradient, QPainterPath, QRegion
import sounddevice as sd
try:
    import mido
except Exception:
    mido = None


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


class TwoLineItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, subtitle_role=Qt.UserRole + 2, default_role=Qt.UserRole + 3):
        super().__init__(parent)
        self.subtitle_role = subtitle_role
        self.default_role = default_role

    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Background highlight for selection/hover
        if opt.state & QStyle.State_Selected:
            painter.fillRect(opt.rect, QColor(64, 64, 64))
        elif opt.state & QStyle.State_MouseOver:
            painter.fillRect(opt.rect, QColor(58, 58, 58))

        rect = opt.rect.adjusted(10, 6, -10, -6)
        title = opt.text
        subtitle = index.data(self.subtitle_role) or ""
        is_default = bool(index.data(self.default_role) or False)

        # Title
        title_font = QFont("SF Pro Display", 13)
        painter.setFont(title_font)
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(rect.left(), rect.top() + 18, title)

        # Subtitle
        if subtitle:
            sub_font = QFont("SF Pro Display", 11)
            painter.setFont(sub_font)
            painter.setPen(QColor(179, 179, 179))
            painter.drawText(rect.left(), rect.top() + 36, subtitle)

        # Default pill
        if is_default:
            pill_text = "Padrão"
            pill_font = QFont("SF Pro Display", 10)
            painter.setFont(pill_font)
            metrics = painter.fontMetrics()
            pill_w = metrics.width(pill_text) + 14
            pill_h = 18
            pill_x = rect.right() - pill_w
            pill_y = rect.top() + 6
            painter.setBrush(QColor(30, 215, 96))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(pill_x, pill_y, pill_w, pill_h, 9, 9)
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(pill_x + 7, pill_y + 13, pill_text)

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 48)


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
    audioOutputDeviceSelected = pyqtSignal(object)
    audioInputDeviceSelected = pyqtSignal(object)
    midiInputDeviceSelected = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configurações")
        # Modalidade forte e sem moldura do sistema para parecer parte do app
        self.setModal(True)
        try:
            self.setWindowModality(Qt.ApplicationModal)
            self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
            # Fundo sólido do modal (sem transparência total)
            self.setAttribute(Qt.WA_TranslucentBackground, True)
        except Exception:
            pass
        self.setMinimumSize(540, 620)
        self.setMaximumSize(540, 800)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.radius = 24
        
        # Flag to track if signals are connected
        self._signals_connected = False
        
        # Estilo moderno com gradiente
        self.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.4);
                border-radius: 3px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(240, 240, 240, 0.5);
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

        audio_devices_label = QLabel("DISPOSITIVOS DE ÁUDIO")
        audio_devices_label.setFont(QFont("SF Pro Display", 11, QFont.Bold))
        audio_devices_label.setStyleSheet("color: #B3B3B3; padding-top: 8px;")
        scroll_layout.addWidget(audio_devices_label)

        # Input Device Card
        input_card = QWidget()
        input_card.setStyleSheet(
            """
            QWidget {
                background-color: #1a1a1a;
                border-radius: 12px;
                border: 1px solid #282828;
            }
            """
        )
        input_card_layout = QVBoxLayout(input_card)
        input_card_layout.setContentsMargins(16, 12, 16, 12)
        input_card_layout.setSpacing(8)

        in_label = QLabel("Entrada de Áudio")
        in_label.setFont(QFont("SF Pro Display", 13, QFont.Medium))
        in_label.setStyleSheet("color: #FFFFFF; border: none; background: transparent;")
        input_card_layout.addWidget(in_label)

        self.input_combo = QComboBox()
        self.input_combo.setMinimumHeight(40)
        self.input_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #282828;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 1px solid #535353;
                background-color: #2a2a2a;
            }
            QComboBox:focus {
                border: 1px solid #FFFFFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #B3B3B3;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #282828;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 4px;
                selection-background-color: #404040;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #3a3a3a;
            }
            """
        )
        self.input_combo.setEditable(True)
        self.input_combo.setInsertPolicy(QComboBox.NoInsert)
        self.input_combo.lineEdit().setPlaceholderText("Selecione a entrada de áudio…")
        completer_in = QCompleter(self.input_combo.model(), self.input_combo)
        completer_in.setFilterMode(Qt.MatchContains)
        completer_in.setCaseSensitivity(Qt.CaseInsensitive)
        self.input_combo.setCompleter(completer_in)
        self.input_combo.setItemDelegate(TwoLineItemDelegate(self.input_combo))
        input_card_layout.addWidget(self.input_combo)
        scroll_layout.addWidget(input_card)

        # Output Device Card
        output_card = QWidget()
        output_card.setStyleSheet(
            """
            QWidget {
                background-color: #1a1a1a;
                border-radius: 12px;
                border: 1px solid #282828;
            }
            """
        )
        output_card_layout = QVBoxLayout(output_card)
        output_card_layout.setContentsMargins(16, 12, 16, 12)
        output_card_layout.setSpacing(8)

        out_label = QLabel("Saída de Áudio")
        out_label.setFont(QFont("SF Pro Display", 13, QFont.Medium))
        out_label.setStyleSheet("color: #FFFFFF; border: none; background: transparent;")
        output_card_layout.addWidget(out_label)

        self.output_combo = QComboBox()
        self.output_combo.setMinimumHeight(40)
        self.output_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #282828;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 1px solid #535353;
                background-color: #2a2a2a;
            }
            QComboBox:focus {
                border: 1px solid #FFFFFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #B3B3B3;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #282828;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 4px;
                selection-background-color: #404040;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #3a3a3a;
            }
            """
        )
        self.output_combo.setEditable(True)
        self.output_combo.setInsertPolicy(QComboBox.NoInsert)
        self.output_combo.lineEdit().setPlaceholderText("Selecione a saída de áudio…")
        completer_out = QCompleter(self.output_combo.model(), self.output_combo)
        completer_out.setFilterMode(Qt.MatchContains)
        completer_out.setCaseSensitivity(Qt.CaseInsensitive)
        self.output_combo.setCompleter(completer_out)
        self.output_combo.setItemDelegate(TwoLineItemDelegate(self.output_combo))
        output_card_layout.addWidget(self.output_combo)
        scroll_layout.addWidget(output_card)

        divider3 = QWidget()
        divider3.setFixedHeight(1)
        divider3.setStyleSheet("background-color: #282828; margin: 16px 0;")
        scroll_layout.addWidget(divider3)

        midi_label = QLabel("MIDI")
        midi_label.setFont(QFont("SF Pro Display", 11, QFont.Bold))
        midi_label.setStyleSheet("color: #B3B3B3; padding-top: 8px;")
        scroll_layout.addWidget(midi_label)

        midi_row_in = QHBoxLayout()
        midi_in_label = QLabel("Entrada MIDI")
        midi_in_label.setStyleSheet("color: #FFFFFF; font-size: 12px;")
        self.midi_input_combo = QComboBox()
        self.midi_input_combo.setMinimumHeight(40)
        self.midi_input_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #282828;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 1px solid #535353;
                background-color: #2a2a2a;
            }
            QComboBox:focus {
                border: 1px solid #FFFFFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #B3B3B3;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #282828;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 4px;
                selection-background-color: #404040;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #3a3a3a;
            }
            """
        )
        self.midi_input_combo.setEditable(True)
        self.midi_input_combo.setInsertPolicy(QComboBox.NoInsert)
        self.midi_input_combo.lineEdit().setPlaceholderText("Selecione a porta MIDI de entrada…")
        completer_midi_in = QCompleter(self.midi_input_combo.model(), self.midi_input_combo)
        completer_midi_in.setFilterMode(Qt.MatchContains)
        completer_midi_in.setCaseSensitivity(Qt.CaseInsensitive)
        self.midi_input_combo.setCompleter(completer_midi_in)
        self.midi_input_combo.setItemDelegate(TwoLineItemDelegate(self.midi_input_combo))
        midi_row_in.addWidget(midi_in_label)
        midi_row_in.addWidget(self.midi_input_combo, 1)
        midi_container_in = QWidget()
        midi_container_in.setLayout(midi_row_in)
        scroll_layout.addWidget(midi_container_in)

        midi_row_out = QHBoxLayout()
        midi_out_label = QLabel("Saída MIDI")
        midi_out_label.setStyleSheet("color: #FFFFFF; font-size: 12px;")
        self.midi_output_combo = QComboBox()
        self.midi_output_combo.setMinimumHeight(40)
        self.midi_output_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #282828;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }
            QComboBox:hover {
                border: 1px solid #535353;
                background-color: #2a2a2a;
            }
            QComboBox:focus {
                border: 1px solid #FFFFFF;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #B3B3B3;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #282828;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 8px;
                padding: 4px;
                selection-background-color: #404040;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #3a3a3a;
            }
            """
        )
        self.midi_output_combo.setEditable(True)
        self.midi_output_combo.setInsertPolicy(QComboBox.NoInsert)
        self.midi_output_combo.lineEdit().setPlaceholderText("Selecione a porta MIDI de saída…")
        completer_midi_out = QCompleter(self.midi_output_combo.model(), self.midi_output_combo)
        completer_midi_out.setFilterMode(Qt.MatchContains)
        completer_midi_out.setCaseSensitivity(Qt.CaseInsensitive)
        self.midi_output_combo.setCompleter(completer_midi_out)
        self.midi_output_combo.setItemDelegate(TwoLineItemDelegate(self.midi_output_combo))
        midi_row_out.addWidget(midi_out_label)
        midi_row_out.addWidget(self.midi_output_combo, 1)
        midi_container_out = QWidget()
        midi_container_out.setLayout(midi_row_out)
        scroll_layout.addWidget(midi_container_out)

        self.midi_list = QListWidget()
        self.midi_list.setStyleSheet("QListWidget { background-color: #2a2a2a; color: #ffffff; border-radius: 10px; }")
        scroll_layout.addWidget(self.midi_list)

        refresh_btn = QPushButton("Atualizar dispositivos")
        refresh_btn.setStyleSheet("QPushButton { background-color: #2a2a2a; color: #ffffff; border-radius: 10px; padding: 8px 12px; } QPushButton:hover { background-color: #3a3a3a; }")
        refresh_btn.clicked.connect(self._refresh_devices)
        scroll_layout.addWidget(refresh_btn)

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

    def set_current_devices(self, output_device_id, input_device_id):
        """Set the currently selected devices (to be called before showing the dialog)"""
        try:
            self._desired_output_device = output_device_id
            self._desired_input_device = input_device_id
        except Exception:
            pass

    def showEvent(self, event):
        super().showEvent(event)
        self.updateMask()
        self._populate_audio_devices()
        self._populate_midi_devices()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), float(self.radius), float(self.radius))
        painter.setClipPath(path)
        
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor("#121212"))
        gradient.setColorAt(1, QColor("#1a1a1a"))
        painter.fillPath(path, gradient)
        
        super().paintEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateMask()

    def updateMask(self):
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), float(self.radius), float(self.radius))
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

    def _populate_audio_devices(self):
        try:
            # Temporarily disconnect signals to avoid triggering during population
            if self._signals_connected:
                try:
                    self.input_combo.currentIndexChanged.disconnect(self._on_input_changed)
                    self.output_combo.currentIndexChanged.disconnect(self._on_output_changed)
                except Exception:
                    pass
            
            devices = sd.query_devices()
            try:
                default_in, default_out = sd.default.device
            except Exception:
                default_in, default_out = (None, None)

            self.input_combo.clear()
            self.output_combo.clear()

            # Populate input devices with subtitle and default tag
            for idx, d in enumerate(devices):
                if d.get('max_input_channels', 0) > 0:
                    name = f"{d['name']}"
                    subtitle = f"Canais: {d.get('max_input_channels', 0)} • {int(d.get('default_samplerate', 0))} Hz"
                    is_def = (default_in == idx)
                    display = f"{name}" + (" • padrão" if is_def else "")
                    self.input_combo.addItem(display, idx)  # idx is the device ID
                    row = self.input_combo.count() - 1
                    mi = self.input_combo.model().index(row, 0)
                    self.input_combo.model().setData(mi, subtitle, Qt.UserRole + 2)  # Use +2 to avoid overwriting device ID
                    self.input_combo.model().setData(mi, is_def, Qt.UserRole + 3)
                    tip = f"{name}\nEntrada • {subtitle}"
                    self.input_combo.setItemData(row, tip, Qt.ToolTipRole)

            # Populate output devices
            for idx, d in enumerate(devices):
                if d.get('max_output_channels', 0) > 0:
                    name = f"{d['name']}"
                    subtitle = f"Canais: {d.get('max_output_channels', 0)} • {int(d.get('default_samplerate', 0))} Hz"
                    is_def = (default_out == idx)
                    display = f"{name}" + (" • padrão" if is_def else "")
                    self.output_combo.addItem(display, idx)  # idx is the device ID
                    row = self.output_combo.count() - 1
                    mo = self.output_combo.model().index(row, 0)
                    self.output_combo.model().setData(mo, subtitle, Qt.UserRole + 2)  # Use +2 to avoid overwriting device ID
                    self.output_combo.model().setData(mo, is_def, Qt.UserRole + 3)
                    tip = f"{name}\nSaída • {subtitle}"
                    self.output_combo.setItemData(row, tip, Qt.ToolTipRole)

            # Select devices - prefer desired devices over defaults
            # Input device selection
            input_to_select = None
            if hasattr(self, '_desired_input_device') and self._desired_input_device is not None:
                input_to_select = self._desired_input_device
            elif default_in is not None:
                input_to_select = default_in
            
            if input_to_select is not None:
                i = next((i for i in range(self.input_combo.count()) if self.input_combo.itemData(i) == input_to_select), -1)
                if i >= 0:
                    self.input_combo.setCurrentIndex(i)
            
            # Output device selection
            output_to_select = None
            if hasattr(self, '_desired_output_device') and self._desired_output_device is not None:
                output_to_select = self._desired_output_device
            elif default_out is not None:
                output_to_select = default_out
            
            if output_to_select is not None:
                o = next((i for i in range(self.output_combo.count()) if self.output_combo.itemData(i) == output_to_select), -1)
                if o >= 0:
                    self.output_combo.setCurrentIndex(o)

            # Connect signals only once
            if not self._signals_connected:
                try:
                    self.input_combo.currentIndexChanged.connect(self._on_input_changed)
                    self.output_combo.currentIndexChanged.connect(self._on_output_changed)
                    self._signals_connected = True
                except Exception:
                    pass
            else:
                # Reconnect signals after population
                try:
                    self.input_combo.currentIndexChanged.connect(self._on_input_changed)
                    self.output_combo.currentIndexChanged.connect(self._on_output_changed)
                except Exception:
                    pass
        except Exception:
            pass

    def _on_input_changed(self, idx):
        try:
            device_id = self.input_combo.itemData(idx)
            sd.default.device = (device_id, sd.default.device[1] if sd.default.device else None)
            self.audioInputDeviceSelected.emit(device_id)
        except Exception:
            pass

    def _on_output_changed(self, idx):
        try:
            device_id = self.output_combo.itemData(idx)
            print(f"[Settings] Output device changed to: {device_id}")
            sd.default.device = (sd.default.device[0] if sd.default.device else None, device_id)
            self.audioOutputDeviceSelected.emit(device_id)
            print(f"[Settings] Signal emitted for device: {device_id}")
        except Exception as e:
            print(f"[Settings] Error in _on_output_changed: {e}")

    def _populate_midi_devices(self):
        try:
            self.midi_list.clear()
            if mido is None:
                self.midi_list.addItem("MIDI não disponível: instale 'mido' + 'python-rtmidi'")
                return
            names_in = []
            names_out = []
            try:
                names_in = mido.get_input_names()
            except Exception:
                pass
            try:
                names_out = mido.get_output_names()
            except Exception:
                pass
            if not names_in and not names_out:
                self.midi_list.addItem("Nenhum dispositivo MIDI detectado")
                return
            # Popular combo de entrada (para selecionarmos o controlador)
            self.midi_input_combo.clear()
            for n in names_in:
                self.midi_input_combo.addItem(n, n)
                row = self.midi_input_combo.count() - 1
                mi = self.midi_input_combo.model().index(row, 0)
                self.midi_input_combo.model().setData(mi, "Porta de entrada MIDI", Qt.UserRole + 2)
                self.midi_input_combo.model().setData(mi, False, Qt.UserRole + 3)
                self.midi_input_combo.setItemData(row, f"{n}\nEntrada MIDI", Qt.ToolTipRole)
            try:
                self.midi_input_combo.currentIndexChanged.connect(self._on_midi_input_changed)
            except Exception:
                pass
            # Popular combo de saída
            self.midi_output_combo.clear()
            for n in names_out:
                self.midi_output_combo.addItem(n, n)
                row = self.midi_output_combo.count() - 1
                mo = self.midi_output_combo.model().index(row, 0)
                self.midi_output_combo.model().setData(mo, "Porta de saída MIDI", Qt.UserRole + 2)
                self.midi_output_combo.model().setData(mo, False, Qt.UserRole + 3)
                self.midi_output_combo.setItemData(row, f"{n}\nSaída MIDI", Qt.ToolTipRole)
            if names_in:
                self.midi_list.addItem("Entradas:")
                for n in names_in:
                    self.midi_list.addItem(f"• {n}")
            if names_out:
                self.midi_list.addItem("Saídas:")
                for n in names_out:
                    self.midi_list.addItem(f"• {n}")
        except Exception:
            pass

    def _on_midi_input_changed(self, idx):
        try:
            name = self.midi_input_combo.itemData(idx)
            if name:
                self.midiInputDeviceSelected.emit(str(name))
        except Exception:
            pass

    def _refresh_devices(self):
        try:
            self._populate_audio_devices()
            self._populate_midi_devices()
        except Exception:
            pass

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

    def keyPressEvent(self, event):
        # Permite fechar com ESC sem depender da moldura do sistema
        try:
            if event.key() == Qt.Key_Escape:
                self.accept()
                return
        except Exception:
            pass
        super().keyPressEvent(event)
