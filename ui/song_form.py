from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QFileDialog, QMessageBox, QGroupBox, QListWidget, QListWidgetItem, QWidget, QSizePolicy, QScrollArea, QFrame, QApplication)
from PyQt5.QtCore import pyqtSignal, Qt, QPropertyAnimation, QEasingCurve, QTimer, pyqtProperty, QThread, QObject, QEvent, QStandardPaths, QSettings
from PyQt5.QtGui import QFont, QPixmap, QPainter, QPen, QColor
import os
from ui.tracks_panel import SongCardWidget
import numpy as np
from scipy.io import wavfile

class LoadingSpinner(QWidget):
    """Widget de loading circular animado"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.setFixedSize(20, 20)
        
        # Timer para animar
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate)
        
    def rotate(self):
        self.angle = (self.angle + 10) % 360
        self.update()
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Desenha o círculo de loading
        pen = QPen(QColor(255, 255, 255), 3)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        
        # Desenha arco animado
        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.angle)
        painter.drawArc(-8, -8, 16, 16, 0, 270 * 16)
        
    def start(self):
        self.timer.start(30)
        self.show()
        
    def stop(self):
        self.timer.stop()
        self.hide()


class SongForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Música")
        self.setModal(False)
        self.resize(600, 500)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                color: #ffffff;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLabel[heading="true"] {
                color: #ffffff;
                font-weight: 600;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
                padding: 12px 16px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 2px solid #4a4a4a;
                background-color: #333333;
            }
            QLineEdit:hover {
                border: 2px solid #4a4a4a;
            }
            QGroupBox {
                color: #ffffff;
                border: 1px solid #3a3a3a;
                border-radius: 10px;
                margin-top: 8px;
                padding: 20px;
                background-color: #202020;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
                color: #ffffff;
                background-color: transparent;
            }
            QPushButton {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
                padding: 12px 20px;
                font-weight: 500;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border: 2px solid #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #252525;
                border: 2px solid #3a3a3a;
            }
            QPushButton:disabled {
                background-color: #1a1a1a;
                color: #666666;
                border: 2px solid #2a2a2a;
            }
            QPushButton[accent="green"] {
                background-color: #2e7d32;
                border: 2px solid #3a3a3a;
                color: #ffffff;
                font-weight: 600;
            }
            QPushButton[accent="green"]:hover {
                background-color: #388e3c;
                border: 2px solid #4a4a4a;
            }
            QPushButton[accent="green"]:disabled {
                background-color: #1a4d1a;
                color: #666666;
                border: 2px solid #2a2a2a;
            }
            QPushButton[accent="red"] {
                background-color: #2d2d2d;
                border: 2px solid #3a3a3a;
                color: #ffffff;
            }
            QPushButton[accent="red"]:hover {
                background-color: #3a3a3a;
                border: 2px solid #4a4a4a;
            }
            QPushButton[accent="blue"] {
                background-color: #1976d2;
                border: 2px solid #1976d2;
                color: #ffffff;
            }
            QPushButton[accent="blue"]:hover {
                background-color: #2196f3;
                border: 2px solid #42a5f5;
            }
            QListWidget {
                background-color: #2d2d2d;
                border: 2px solid #3a3a3a;
                border-radius: 8px;
                outline: none;
            }
            QListWidget::item {
                border-radius: 6px;
                margin: 2px 0px;
            }
            QListWidget::item:hover {
                background-color: #353535;
            }
            QScrollBar:vertical {
                background: #2d2d2d;
                width: 14px;
                border-radius: 7px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background: #4a4a4a;
                border-radius: 7px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #5a5a5a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                background: none;
                height: 0px;
            }
        """)
        
        # Store selected tracks
        self.selected_tracks = []
        
        # Store banner image path
        self.banner_image_path = None
        
        # Loading state
        self.is_loading = False
        
        # Set font
        font = QFont()
        font.setPointSize(11)
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Área de scroll
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setSpacing(28)
        content_layout.setContentsMargins(32, 28, 32, 28)
        
        # Título com linha separadora
        header_layout = QVBoxLayout()
        header_layout.setSpacing(12)
        title_label = QLabel("Adicionar Nova Música")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignLeft)
        title_label.setProperty("heading", "true")
        header_layout.addWidget(title_label)
        
        # Linha separadora
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #3a3a3a; max-height: 2px;")
        header_layout.addWidget(separator)
        content_layout.addLayout(header_layout)
        
        # Seção: Informações Básicas
        info_section = QWidget()
        info_layout = QVBoxLayout()
        info_layout.setSpacing(18)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        section_title = QLabel("Informações Básicas")
        section_font = QFont()
        section_font.setPointSize(14)
        section_font.setBold(True)
        section_title.setFont(section_font)
        section_title.setProperty("heading", "true")
        info_layout.addWidget(section_title)
        
        # Campo: Nome da música
        name_group = QVBoxLayout()
        name_group.setSpacing(8)
        name_label = QLabel("Nome da Música")
        name_label.setFont(font)
        self.name_input = QLineEdit()
        self.name_input.setFont(font)
        self.name_input.setPlaceholderText("Digite o nome da música")
        self.name_input.setMinimumHeight(44)
        name_group.addWidget(name_label)
        name_group.addWidget(self.name_input)
        info_layout.addLayout(name_group)
        
        # Tom e BPM lado a lado
        details_layout = QHBoxLayout()
        details_layout.setSpacing(16)
        
        # Campo: Tom
        key_group = QVBoxLayout()
        key_group.setSpacing(8)
        key_label = QLabel("Tom")
        key_label.setFont(font)
        self.key_input = QLineEdit()
        self.key_input.setFont(font)
        self.key_input.setPlaceholderText("Ex.: C, Dm, G")
        self.key_input.setMinimumHeight(44)
        key_group.addWidget(key_label)
        key_group.addWidget(self.key_input)
        details_layout.addLayout(key_group)
        
        # Campo: BPM
        bpm_group = QVBoxLayout()
        bpm_group.setSpacing(8)
        bpm_label = QLabel("BPM")
        bpm_label.setFont(font)
        self.bpm_input = QLineEdit()
        self.bpm_input.setFont(font)
        self.bpm_input.setPlaceholderText("Ex.: 120")
        self.bpm_input.setMinimumHeight(44)
        bpm_group.addWidget(bpm_label)
        bpm_group.addWidget(self.bpm_input)
        details_layout.addLayout(bpm_group)
        
        info_layout.addLayout(details_layout)
        info_section.setLayout(info_layout)
        content_layout.addWidget(info_section)
        
        # Separador
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setStyleSheet("background-color: #3a3a3a; max-height: 1px;")
        content_layout.addWidget(separator2)
        
        # Seção: Mídia
        media_section = QWidget()
        media_layout = QVBoxLayout()
        media_layout.setSpacing(18)
        media_layout.setContentsMargins(0, 0, 0, 0)
        
        media_title = QLabel("Mídia")
        media_title.setFont(section_font)
        media_title.setProperty("heading", "true")
        media_layout.addWidget(media_title)
        
        # Botões de upload lado a lado
        upload_layout = QHBoxLayout()
        upload_layout.setSpacing(12)
        
        self.upload_banner_button = QPushButton("Adicionar Imagem")
        self.upload_banner_button.setFont(font)
        self.upload_banner_button.setMinimumHeight(48)
        # Padrão preto/cinza
        self.upload_banner_button.clicked.connect(self.upload_banner_image)
        
        self.upload_button = QPushButton("Adicionar Faixas de Áudio")
        self.upload_button.setFont(font)
        self.upload_button.setMinimumHeight(48)
        # Padrão preto/cinza
        self.upload_button.clicked.connect(self.upload_tracks)
        
        upload_layout.addWidget(self.upload_banner_button)
        upload_layout.addWidget(self.upload_button)
        media_layout.addLayout(upload_layout)
        
        # Campo URL da imagem
        url_group = QVBoxLayout()
        url_group.setSpacing(8)
        url_label = QLabel("URL da Imagem (opcional)")
        url_label.setFont(font)
        self.banner_url_input = QLineEdit()
        self.banner_url_input.setFont(font)
        self.banner_url_input.setPlaceholderText("Cole a URL da imagem aqui")
        self.banner_url_input.setMinimumHeight(44)
        url_group.addWidget(url_label)
        url_group.addWidget(self.banner_url_input)
        media_layout.addLayout(url_group)
        
        # Prévia do cartão
        preview_container = QVBoxLayout()
        preview_container.setSpacing(12)
        preview_label = QLabel("Prévia")
        preview_label.setFont(font)
        preview_container.addWidget(preview_label)
        
        self.card_preview = SongCardWidget("", "", "", None)
        self.card_preview.setFixedSize(340, 190)
        preview_container.addWidget(self.card_preview)
        media_layout.addLayout(preview_container)
        
        media_section.setLayout(media_layout)
        content_layout.addWidget(media_section)
        
        # Separador
        separator3 = QFrame()
        separator3.setFrameShape(QFrame.HLine)
        separator3.setStyleSheet("background-color: #3a3a3a; max-height: 1px;")
        content_layout.addWidget(separator3)
        
        # Seção: Faixas
        tracks_section = QWidget()
        tracks_layout = QVBoxLayout()
        tracks_layout.setSpacing(12)
        tracks_layout.setContentsMargins(0, 0, 0, 0)
        
        tracks_header = QHBoxLayout()
        tracks_title = QLabel("Faixas de Áudio")
        tracks_title.setFont(section_font)
        tracks_title.setProperty("heading", "true")
        self.tracks_count = QLabel("0 faixas")
        self.tracks_count.setStyleSheet("color: #888888; font-size: 12px;")
        tracks_header.addWidget(tracks_title)
        tracks_header.addWidget(self.tracks_count)
        tracks_header.addStretch()
        tracks_layout.addLayout(tracks_header)
        
        self.tracks_list = QListWidget()
        self.tracks_list.setMinimumHeight(300)
        self.tracks_list.setMaximumHeight(500)
        self.tracks_list.setSpacing(4)
        tracks_layout.addWidget(self.tracks_list)
        
        tracks_section.setLayout(tracks_layout)
        content_layout.addWidget(tracks_section)
        
        content_widget.setLayout(content_layout)
        
        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background-color: #1a1a1a; border: none; }")
        scroll_area.setWidget(content_widget)
        
        main_layout.addWidget(scroll_area)
        
        # Rodapé com botões
        footer = QWidget()
        footer.setStyleSheet("background-color: #202020; border-top: 2px solid #3a3a3a;")
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(32, 16, 32, 16)
        footer_layout.setSpacing(12)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.setFont(font)
        self.cancel_button.setMinimumHeight(48)
        self.cancel_button.setMinimumWidth(140)
        self.cancel_button.clicked.connect(self.reject)
        
        # Container para botão OK com loading
        ok_container = QWidget()
        ok_layout = QHBoxLayout()
        ok_layout.setContentsMargins(0, 0, 0, 0)
        ok_layout.setSpacing(10)
        ok_layout.setAlignment(Qt.AlignCenter)
        
        self.ok_button = QPushButton("Adicionar Música")
        self.ok_button.setFont(font)
        self.ok_button.setProperty("accent", "green")
        self.ok_button.setMinimumHeight(48)
        self.ok_button.setMinimumWidth(160)
        self.ok_button.setEnabled(False)
        self.ok_button.clicked.connect(self.on_ok_clicked)
        
        # Spinner de loading dentro do botão
        self.loading_spinner = LoadingSpinner(self.ok_button)
        self.loading_spinner.hide()
        self.ok_button.installEventFilter(self)
        ok_layout.addWidget(self.ok_button)
        ok_container.setLayout(ok_layout)
        
        footer_layout.addStretch()
        footer_layout.addWidget(self.cancel_button)
        footer_layout.addWidget(ok_container)
        
        footer.setLayout(footer_layout)
        main_layout.addWidget(footer)
        
        self.setLayout(main_layout)
        
        # Configura prévia inicial e bindings
        self.update_card_preview()
        self.name_input.textChanged.connect(self.on_input_changed)
        self.key_input.textChanged.connect(self.on_input_changed)
        self.bpm_input.textChanged.connect(self.on_input_changed)
        self.banner_url_input.textChanged.connect(self.on_input_changed)
        
        # Atualiza estado inicial
        self.validate_form()

    def _file_dialog_options(self):
        try:
            # Use native macOS open/save panels
            return QFileDialog.Options()
        except Exception:
            return QFileDialog.Options()

    def _run_native_file_dialog(self, callable_fn):
        try:
            app = QApplication.instance()
            if not app:
                return callable_fn()
            orig_stylesheet = app.styleSheet()
            orig_palette = app.palette()
            try:
                app.setStyleSheet("")
            except Exception:
                pass
            try:
                app.setPalette(app.style().standardPalette())
            except Exception:
                pass
            try:
                result = callable_fn()
            finally:
                try:
                    app.setStyleSheet(orig_stylesheet)
                except Exception:
                    pass
                try:
                    app.setPalette(orig_palette)
                except Exception:
                    pass
            return result
        except Exception:
            return callable_fn()

    def _start_dir(self):
        try:
            d = QStandardPaths.writableLocation(QStandardPaths.DownloadLocation)
            if d and os.path.isdir(d):
                return d
        except Exception:
            pass
        try:
            d = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
            if d and os.path.isdir(d):
                return d
        except Exception:
            pass
        return ''

    def _remember_dir(self, path):
        try:
            if path:
                base = path
                try:
                    if os.path.isfile(path):
                        base = os.path.dirname(path)
                except Exception:
                    pass
                settings = QSettings('AdoraPlay', 'AppPythonAdrian')
                settings.setValue('last_open_dir', base)
        except Exception:
            pass
        
    def on_ok_clicked(self):
        """Inicia loading e pré-computa a linha do tempo em background antes de aceitar"""
        if self.is_loading:
            return
        self.start_loading()
        if self.selected_tracks:
            target_points = 1200
            self._env_thread = QThread(self)
            self._env_worker = FormEnvelopeWorker(self.selected_tracks, target_points)
            self._env_worker.moveToThread(self._env_thread)
            self._env_thread.started.connect(self._env_worker.run)
            self._env_worker.done.connect(self._on_env_done)
            self._env_worker.error.connect(self._on_env_error)
            self._env_thread.finished.connect(self._cleanup_env)
            self._env_thread.start()
        else:
            self._precomputed_envelope = []
            self._precomputed_total_samples = 0
            self._precomputed_sample_rate = 0
            QTimer.singleShot(10, self.accept)
    
    def start_loading(self):
        """Inicia o estado de loading"""
        self.is_loading = True
        self.ok_button.setText("")
        self.ok_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.loading_spinner.start()
        self._center_spinner()
        
    def stop_loading(self):
        """Para o estado de loading"""
        self.is_loading = False
        self.ok_button.setText("Adicionar Música")
        self.cancel_button.setEnabled(True)
        self.loading_spinner.stop()
        self.validate_form()

    def eventFilter(self, obj, event):
        if obj is self.ok_button and event.type() in (QEvent.Resize, QEvent.Show):
            self._center_spinner()
        return super().eventFilter(obj, event)

    def _center_spinner(self):
        try:
            if not self.loading_spinner.isHidden():
                sw = self.loading_spinner.width()
                sh = self.loading_spinner.height()
                bw = self.ok_button.width()
                bh = self.ok_button.height()
                x = (bw - sw) // 2
                y = (bh - sh) // 2
                self.loading_spinner.move(x, y)
        except Exception:
            pass
    
    def on_input_changed(self):
        """Chamado quando qualquer campo de entrada é modificado"""
        self.update_card_preview()
        self.validate_form()
        
    def validate_form(self):
        """Valida o formulário e habilita/desabilita o botão OK"""
        name = self.name_input.text().strip()
        has_tracks = len(self.selected_tracks) > 0
        
        # Habilita o botão OK apenas se o nome estiver preenchido e houver pelo menos uma faixa
        is_valid = bool(name) and has_tracks
        self.ok_button.setEnabled(is_valid)
        
    def upload_tracks(self):
        """Abrir diálogo para selecionar faixas de áudio"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecionar Faixas de Áudio",
            self._start_dir(),
            "Todos (*.*);;Arquivos de Áudio (*.wav *.mp3)",
            options=self._file_dialog_options()
        )
        
        if file_paths:
            self.selected_tracks.extend(file_paths)
            self.refresh_tracks_list()
            # Sempre iniciamos em Downloads; não lembrar diretório
        
        self.validate_form()
            
    def upload_banner_image(self):
        """Abrir diálogo para selecionar imagem do banner"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Imagem do Banner",
            self._start_dir(),
            "Todos (*.*);;Arquivos de Imagem (*.png *.jpg *.jpeg *.bmp *.gif *.webp)",
            options=self._file_dialog_options()
        )
        
        if file_path:
            self.banner_image_path = file_path
            self.banner_url_input.clear()
            self.update_card_preview()
            
    def resizeEvent(self, event):
        """Atualiza a prévia ao redimensionar"""
        super().resizeEvent(event)
        self.update_card_preview()
            
    def get_data(self):
        """Retorna os dados da música como dicionário"""
        banner_path = self.banner_image_path or self.banner_url_input.text().strip()
        
        return {
            "name": self.name_input.text().strip(),
            "key": self.key_input.text().strip(),
            "bpm": self.bpm_input.text().strip(),
            "tracks": self.selected_tracks,
            "banner_image": banner_path if banner_path else None,
            "precomputed_envelope": getattr(self, "_precomputed_envelope", None),
            "precomputed_total_samples": getattr(self, "_precomputed_total_samples", 0),
            "precomputed_sample_rate": getattr(self, "_precomputed_sample_rate", 0),
        }

    def refresh_tracks_list(self):
        """Atualiza a lista com as faixas selecionadas"""
        self.tracks_list.clear()
        
        # Atualiza contador
        count = len(self.selected_tracks)
        self.tracks_count.setText(f"{count} {'faixa' if count == 1 else 'faixas'}")
        
        if not self.selected_tracks:
            empty_item = QListWidgetItem()
            empty_widget = QLabel("Nenhuma faixa adicionada ainda")
            empty_widget.setStyleSheet("color: #666666; padding: 20px; text-align: center;")
            empty_widget.setAlignment(Qt.AlignCenter)
            empty_item.setSizeHint(empty_widget.sizeHint())
            self.tracks_list.addItem(empty_item)
            self.tracks_list.setItemWidget(empty_item, empty_widget)
            return
            
        for idx, path in enumerate(self.selected_tracks):
            item = QListWidgetItem()
            row = QWidget()
            row.setStyleSheet("background-color: transparent;")
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(16, 12, 16, 12)
            row_layout.setSpacing(12)
            
            # Número da faixa
            number_label = QLabel(f"{idx + 1}")
            number_label.setStyleSheet("color: #666666; font-weight: bold; font-size: 14px;")
            number_label.setFixedWidth(30)
            number_label.setAlignment(Qt.AlignCenter)
            
            # Nome do arquivo
            label = QLabel(os.path.basename(path))
            label.setStyleSheet("color: #e0e0e0; font-size: 13px;")
            label.setWordWrap(True)
            
            # Botão remover
            remove_btn = QPushButton("✕")
            remove_btn.setFixedSize(36, 36)
            remove_btn.setStyleSheet("""
                QPushButton {
                    font-size: 16px;
                    font-weight: bold;
                    padding: 0px;
                    background-color: #2d2d2d;
                    border: 2px solid #3a3a3a;
                    border-radius: 8px;
                    color: #ffffff;
                }
                QPushButton:hover {
                    background-color: #3a3a3a;
                    border: 2px solid #4a4a4a;
                }
            """)
            remove_btn.setCursor(Qt.PointingHandCursor)
            remove_btn.clicked.connect(lambda _, i=idx: self.remove_track(i))
            
            row_layout.addWidget(number_label)
            row_layout.addWidget(label, 1)
            row_layout.addWidget(remove_btn)
            row.setLayout(row_layout)
            
            item.setSizeHint(row.sizeHint())
            self.tracks_list.addItem(item)
            self.tracks_list.setItemWidget(item, row)

    def remove_track(self, index):
        """Remove a faixa pelo índice e atualiza a lista"""
        if 0 <= index < len(self.selected_tracks):
            del self.selected_tracks[index]
            self.refresh_tracks_list()
            self.validate_form()

    def update_card_preview(self):
        """Atualiza o widget de prévia do cartão"""
        name = self.name_input.text().strip()
        key = self.key_input.text().strip()
        bpm = self.bpm_input.text().strip()
        banner = self.banner_image_path or self.banner_url_input.text().strip() or None
        self.card_preview.update_info(name or "Nome da Música", key or "Tom", bpm or "BPM", banner)

    def _on_env_done(self, envelope, total_samples, sample_rate):
        self._precomputed_envelope = envelope or []
        self._precomputed_total_samples = int(total_samples or 0)
        self._precomputed_sample_rate = int(sample_rate or 0)
        self.stop_loading()
        try:
            if self._env_thread:
                self._env_thread.quit()
                self._env_thread.wait(500)
        except Exception:
            pass
        self.accept()

    def _on_env_error(self, message):
        self._precomputed_envelope = []
        self._precomputed_total_samples = 0
        self._precomputed_sample_rate = 0
        self.stop_loading()
        try:
            if self._env_thread:
                self._env_thread.quit()
                self._env_thread.wait(500)
        except Exception:
            pass
        self.accept()

    def _cleanup_env(self):
        self._env_thread = None
        self._env_worker = None

class FormEnvelopeWorker(QObject):
    done = pyqtSignal(object, int, int)
    error = pyqtSignal(str)

    def __init__(self, file_paths, target_points=1000):
        super().__init__()
        self.file_paths = file_paths or []
        self.target_points = max(100, int(target_points or 1000))

    def run(self):
        try:
            if not self.file_paths:
                self.done.emit([], 0, 0)
                return
            tracks = []
            max_len = 0
            sample_rate = 44100
            for path in self.file_paths:
                try:
                    if not path.lower().endswith('.wav'):
                        # Ignora formatos não suportados neste fallback
                        continue
                    sr, samples = wavfile.read(path)
                    sample_rate = sr
                    # Converter para float32 normalizado se necessário
                    if samples.dtype != np.float32 and samples.dtype != np.float64:
                        samples = samples.astype(np.float32) / 32768.0
                    # Mono -> usar valores absolutos; Stereo -> média dos canais
                    if len(samples.shape) == 1:
                        mono = np.abs(samples)
                    else:
                        mono = np.mean(np.abs(samples), axis=1)
                    tracks.append(mono)
                    if len(mono) > max_len:
                        max_len = len(mono)
                except Exception:
                    continue
            if not tracks or max_len == 0:
                self.done.emit([], 0, sample_rate)
                return
            block = max(1, max_len // self.target_points)
            combined = None
            for mono in tracks:
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
            if combined is None or combined.size == 0:
                self.done.emit([], max_len, sample_rate)
                return
            max_val = combined.max() if combined.size > 0 else 1.0
            env = combined / max_val if max_val > 0 else combined
            env = np.clip(env, 0.0, 1.0)
            env = np.maximum(env, 0.05)
            self.done.emit(env.tolist(), max_len, sample_rate)
        except Exception as e:
            self.error.emit(str(e))
