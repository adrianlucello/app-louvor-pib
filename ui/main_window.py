import sys
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, 
                             QStackedWidget, QHBoxLayout, QLabel, QFileDialog, QStyle)
from PyQt5.QtCore import Qt, QPoint, pyqtSignal, QSize, QRectF, QByteArray, QTimer
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QPolygon, QFont, QGuiApplication
from PyQt5.QtSvg import QSvgRenderer
import os
try:
    import qtawesome
except Exception:
    qtawesome = None
from ui.worship_form import WorshipForm
from ui.song_form import SongForm
from ui.tracks_panel import TracksPanel, TrackControl
from ui.header import HeaderWidget
import json

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Audio Track Mixer")
        self.setGeometry(100, 100, 1000, 700)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
        """)
        
        # Create stacked widget to switch between views
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create initial view
        self.create_initial_view()
        
        # Initialize data
        self.worship_data = None
        self.songs = []  # List to store all songs
        self.current_song = None  # Currently selected song
        
    def create_initial_view(self):
        """Create the initial view with the pencil button"""
        initial_widget = QWidget()
        initial_widget.setStyleSheet("background-color: #1e1e1e;")
        layout = QVBoxLayout(initial_widget)
        layout.setContentsMargins(50, 50, 50, 50)
        layout.setSpacing(30)
        
        # Header
        header_label = QLabel("Mixer de Áudio")
        header_font = QFont()
        header_font.setPointSize(24)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setStyleSheet("color: #ffffff; padding: 20px;")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Botões principais (Criar Culto e Abrir Projeto)
        buttons_container = QWidget()
        buttons_layout = QHBoxLayout(buttons_container)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(20)
        
        # Botão Criar Culto (primário)
        self.pencil_button = QPushButton("Criar Culto")
        # Remover ícone/emoji do botão
        self.pencil_button.setFixedSize(250, 120)
        self.pencil_button.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #000000;
                font-size: 18px;
                font-weight: bold;
                border-radius: 12px;
                border: 2px solid #ffffff;
            }
            QPushButton:hover {
                background-color: #f2f2f2; /* branco mais fraco no hover */
                color: #000000;
                border: 2px solid #f2f2f2;
            }
            QPushButton:pressed {
                background-color: #e6e6e6;
                color: #000000;
                border: 2px solid #e6e6e6;
            }
        """)
        self.pencil_button.clicked.connect(self.open_worship_form)
        buttons_layout.addWidget(self.pencil_button)

        # Botão Abrir Projeto
        self.open_project_button = QPushButton("Abrir Projeto")
        self.open_project_button.setFixedSize(250, 120)
        self.open_project_button.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: #e0e0e0;
                font-size: 18px;
                font-weight: bold;
                border-radius: 12px;
                border: 2px solid #3a3a3a;
            }
            QPushButton:hover {
                background-color: #333333;
                border: 2px solid #4a4a4a;
            }
            QPushButton:pressed {
                background-color: #252525;
                border: 2px solid #3a3a3a;
            }
        """)
        self.open_project_button.clicked.connect(self.open_project)
        buttons_layout.addWidget(self.open_project_button)

        layout.addWidget(buttons_container, alignment=Qt.AlignCenter)
        
        # Instruções
        instructions = QLabel("Clique acima para criar um novo culto e começar a adicionar músicas")
        instructions.setStyleSheet("color: #aaaaaa; font-size: 14px;")
        instructions.setAlignment(Qt.AlignCenter)
        layout.addWidget(instructions)
        
        self.stacked_widget.addWidget(initial_widget)
        
    def create_main_view(self):
        """Create the main view with song carousel and tracks panel"""
        main_widget = QWidget()
        self.main_widget = main_widget
        main_widget.setStyleSheet("background-color: #1e1e1e;")
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        worship_title = f"{self.worship_data['name']} - {self.worship_data['date']}"
        self.header_widget = HeaderWidget()
        self.header_widget.set_worship_title(worship_title)
        self.header_widget.addSongRequested.connect(self.open_song_form)
        self.header_widget.saveRequested.connect(self.save_project)
        self.header_widget.playRequested.connect(self.handle_play_clicked)
        self.header_widget.pauseRequested.connect(self.handle_pause_clicked)
        self.header_widget.restartRequested.connect(self.restart_current_song)
        layout.addWidget(self.header_widget)

        self.play_blink_timer = QTimer(self)
        self.play_blink_timer.setInterval(500)
        self.play_blink_timer.timeout.connect(self._toggle_play_blink)
        self._play_blink_on = False
        
        # Removed the song carousel to keep a single card container (image cards in TracksPanel)
        
        # Tracks panel (initially empty)
        self.tracks_panel = TracksPanel()
        self.tracks_panel.songCardSelected.connect(self.on_song_selected)
        try:
            self.tracks_panel.audio_manager.playbackStateChanged.connect(self.on_playback_state_changed_main)
        except Exception:
            pass
        layout.addWidget(self.tracks_panel)
        
        self.stacked_widget.addWidget(main_widget)
        self.stacked_widget.setCurrentWidget(main_widget)
        
    def back_to_initial(self):
        """Go back to the initial view"""
        # Reset data
        self.worship_data = None
        self.songs = []
        self.current_song = None
        # Remove main view and show initial view
        if self.stacked_widget.count() > 1:
            main_view = self.stacked_widget.widget(1)
            self.stacked_widget.removeWidget(main_view)
            main_view.deleteLater()
        self.stacked_widget.setCurrentIndex(0)
        
    def create_tracks_view(self, tracks):
        """Create the tracks view"""
        # This method is no longer used as we have the carousel view
        pass
        
    def play_all_tracks(self):
        """Play all tracks simultaneously"""
        if hasattr(self, 'tracks_panel') and self.tracks_panel:
            self.tracks_panel.audio_manager.play_current_song()
            # Update play button text
            if hasattr(self, 'play_button'):
                pass
                
    def toggle_playback(self):
        """Toggle playback between play and pause"""
        try:
            if hasattr(self, 'tracks_panel') and self.tracks_panel:
                if self.tracks_panel.audio_manager.is_playing():
                    self.tracks_panel.audio_manager.pause_current_song()
                    pass
                else:
                    self.tracks_panel.audio_manager.play_current_song()
                    pass
        except Exception as e:
            print(f"Error toggling playback: {e}")
            # Reset button text in case of error
            if hasattr(self, 'play_button'):
                pass

    def stop_all_tracks(self):
        """Stop all tracks"""
        try:
            if hasattr(self, 'tracks_panel') and self.tracks_panel:
                self.tracks_panel.audio_manager.stop_all()
                # Update play button text
                if hasattr(self, 'play_button'):
                    pass
        except Exception as e:
            print(f"Error stopping tracks: {e}")

    def restart_current_song(self):
        """Restart the current song from the beginning and play"""
        try:
            if hasattr(self, 'tracks_panel') and self.tracks_panel:
                self.tracks_panel.audio_manager.stop_all()
                self.tracks_panel.audio_manager.play_current_song()
        except Exception as e:
            print(f"Error restarting song: {e}")

    def handle_play_clicked(self):
        try:
            if hasattr(self, 'tracks_panel') and self.tracks_panel:
                self.tracks_panel.audio_manager.play_current_song()
                self.start_play_blink()
        except Exception:
            pass

    def handle_pause_clicked(self):
        try:
            if hasattr(self, 'tracks_panel') and self.tracks_panel:
                self.tracks_panel.audio_manager.pause_current_song()
                self.stop_play_blink()
        except Exception:
            pass

    def on_playback_state_changed_main(self, is_playing):
        if is_playing:
            self.start_play_blink()
        else:
            self.stop_play_blink()

    def _toggle_play_blink(self):
        self._play_blink_on = not self._play_blink_on
        if hasattr(self, 'header_widget') and self.header_widget:
            self.header_widget.set_play_blink(self._play_blink_on)

    def start_play_blink(self):
        self._play_blink_on = True
        if hasattr(self, 'header_widget') and self.header_widget:
            self.header_widget.set_play_blink(True)
        if not self.play_blink_timer.isActive():
            self.play_blink_timer.start()

    def stop_play_blink(self):
        self.play_blink_timer.stop()
        self._play_blink_on = False
        if hasattr(self, 'header_widget') and self.header_widget:
            self.header_widget.set_play_blink(False)

    def on_song_selected(self, song_data):
        """Handle song selection from TracksPanel image cards"""
        try:
            # Check if reselecting the same song to avoid unnecessary rebuilds
            old_id = None
            new_id = None
            try:
                if hasattr(self, 'current_song') and self.current_song:
                    old_id = self.tracks_panel._get_song_id(self.current_song)
                new_id = self.tracks_panel._get_song_id(song_data)
            except Exception:
                pass
            self.current_song = song_data
            if song_data:
                # Stop any currently playing audio
                if hasattr(self, 'tracks_panel') and self.tracks_panel:
                    if old_id != new_id:
                        self.tracks_panel.audio_manager.stop_all()
                # Clear existing tracks
                if old_id != new_id:
                    for control in self.tracks_panel.track_controls:
                        self.tracks_panel.tracks_layout.removeWidget(control)
                        control.deleteLater()
                    self.tracks_panel.track_controls.clear()
                    self.tracks_panel.solo_states.clear()
                    self.tracks_panel.original_mute_states.clear()
                # Set the current song in the audio manager
                self.tracks_panel.audio_manager.set_current_song(song_data)
                # Connect VU meter signal from player to panel
                try:
                    self.tracks_panel.connect_player_signals()
                except Exception:
                    pass
                
                # Update track list and controls
                if old_id != new_id:
                    self.tracks_panel.tracks = song_data.get("tracks", [])
                    for i, track_path in enumerate(self.tracks_panel.tracks):
                        track_name = os.path.basename(track_path)
                        track_control = TrackControl(i, track_name)
                        track_control.volumeChanged.connect(self.tracks_panel.on_track_volume_changed)
                        track_control.muteChanged.connect(self.tracks_panel.on_track_mute_changed)
                        track_control.soloChanged.connect(self.tracks_panel.on_track_solo_changed)
                        player_tracks = getattr(self.tracks_panel.audio_manager.current_player, 'tracks', [])
                        if 0 <= i < len(player_tracks):
                            vol = player_tracks[i].get('volume')
                            # Convert stored amplitude gain to slider percent using panel mapping
                            try:
                                pct = self.tracks_panel._gain_to_slider_pct(vol if vol is not None else 0.8)
                                track_control.set_volume(pct / 100.0)
                            except Exception:
                                track_control.set_volume(vol if vol is not None else 0.8)
                            track_control.set_muted(player_tracks[i].get('muted', False))
                        # Estilo especial para o primeiro fader após o master
                        if i == 0:
                            try:
                                track_control.setStyleSheet(
                                    "background-color: #252525;"
                                    "border-top-left-radius: 10px;"
                                    "border-bottom-left-radius: 10px;"
                                )
                                track_control.setAttribute(Qt.WA_StyledBackground, True)
                            except Exception:
                                pass
                        self.tracks_panel.track_controls.append(track_control)
                        self.tracks_panel.tracks_layout.addWidget(track_control)
                
                # Highlight selected song card in UI (selection only, no re-emit)
                self.tracks_panel.select_card_by_song(song_data)
                # Build/update timeline waveform below cards
                if old_id != new_id:
                    try:
                        self.tracks_panel.build_timeline_for_current_song()
                    except Exception:
                        pass
            else:
                # No song selected: clear tracks only
                for control in self.tracks_panel.track_controls:
                    self.tracks_panel.tracks_layout.removeWidget(control)
                    control.deleteLater()
                self.tracks_panel.track_controls.clear()
                self.tracks_panel.tracks = []
        except Exception as e:
            print(f"Error in on_song_selected: {e}")
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Error")
            msg_box.setText(f"An error occurred while selecting the song: {str(e)}")
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.exec_()

    def add_tracks_to_song(self, song_data):
        """Add tracks to an existing song"""
        # Open file dialog to select audio tracks
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, 
            "Select Audio Tracks", 
            "", 
            "Audio Files (*.mp3 *.wav)"
        )
        
        if file_paths:
            # Add tracks to the song data
            song_data["tracks"].extend(file_paths)
            print(f"Added tracks to song: {song_data['name']}")
            
            # If this is the currently selected song, update the tracks panel
            if song_data == self.current_song:
                self.on_song_selected(song_data)
        
    def create_pencil_icon(self):
        """Create a custom pencil icon using QPixmap"""
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw pencil body
        painter.setBrush(QColor(50, 150, 250))
        painter.drawRect(8, 2, 16, 28)
        
        # Draw pencil tip
        painter.setBrush(QColor(200, 200, 200))
        points = QPolygon([
            QPoint(8, 26),
            QPoint(24, 26),
            QPoint(16, 30)
        ])
        painter.drawPolygon(points)
        
        # Draw eraser
        painter.setBrush(QColor(255, 100, 100))
        painter.drawRect(8, 2, 16, 6)
        
        painter.end()
        return QIcon(pixmap)

    def create_play_icon(self):
        """Create a play icon (fallback if play.png not provided)"""
        pm, _ = self._make_hidpi_pixmap(QSize(24, 24))
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(255, 255, 255))
        p.setPen(Qt.NoPen)
        w, h = pm.width(), pm.height()
        points = QPolygon([
            QPoint(int(0.35 * w), int(0.25 * h)),
            QPoint(int(0.72 * w), int(0.50 * h)),
            QPoint(int(0.35 * w), int(0.75 * h))
        ])
        p.drawPolygon(points)
        p.end()
        return QIcon(pm)

    def create_pause_icon(self):
        """Create a pause icon (fallback)"""
        pm, _ = self._make_hidpi_pixmap(QSize(24, 24))
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setBrush(QColor(255, 255, 255))
        p.setPen(Qt.NoPen)
        w, h = pm.width(), pm.height()
        bar_w = int(0.20 * w)
        gap = int(0.06 * w)
        top = int(0.20 * h)
        height = int(0.60 * h)
        p.drawRect(int(0.30 * w), top, bar_w, height)
        p.drawRect(int(0.30 * w) + bar_w + gap, top, bar_w, height)
        p.end()
        return QIcon(pm)

    def create_restart_icon(self):
        """Create a restart icon (fallback if restart.png not provided)"""
        pm, _ = self._make_hidpi_pixmap(QSize(24, 24))
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QColor(255, 255, 255))
        p.setBrush(Qt.NoBrush)
        # Arc (semi circle)
        w, h = pm.width(), pm.height()
        margin = int(0.22 * w)
        p.drawArc(margin, margin, w - 2 * margin, h - 2 * margin, 30 * 16, 300 * 16)
        # Arrow head
        p.setBrush(QColor(255, 255, 255))
        p.setPen(Qt.NoPen)
        arrow = QPolygon([
            QPoint(int(0.62 * w), int(0.26 * h)),
            QPoint(int(0.74 * w), int(0.26 * h)),
            QPoint(int(0.68 * w), int(0.38 * h))
        ])
        p.drawPolygon(arrow)
        p.end()
        return QIcon(pm)

    def load_icon(self, filename, fallback=None):
        """Load icon from file if available; otherwise use a fallback drawing."""
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidates = [
                os.path.join(base_path, filename),
                os.path.join(base_path, "Resources", filename),
            ]
            for path in candidates:
                if os.path.exists(path):
                    return QIcon(QPixmap(path))
        except Exception:
            pass
        # Fallback to drawn icon
        if fallback == "play":
            return self.create_play_icon()
        if fallback == "pause":
            return self.create_pause_icon()
        if fallback == "restart":
            return self.create_restart_icon()
        return QIcon()

    def get_icon(self, kind):
        """Prefer provided SVG icons; then qtawesome in white; finally crisp drawn icons."""
        # 1) Try explicit SVG filenames
        svg_map = {
            'play': ['play_arrow_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg'],
            'pause': ['pause_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg'],
            'restart': ['restart_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg', 'refresh_24dp_E3E3E3_FILL0_wght400_GRAD0_opsz24.svg'],
        }
        icon = self._try_svg_list(svg_map.get(kind, []), QSize(24, 24))
        if icon:
            return icon
        # 2) Try any matching SVG by keyword in project/Resources
        keyword_map = {
            'play': ['play', 'arrow'],
            'pause': ['pause'],
            'restart': ['restart', 'redo', 'refresh'],
        }
        icon = self._try_svg_by_keywords(keyword_map.get(kind, []), QSize(24, 24))
        if icon:
            return icon
        # 3) Try qtawesome (FontAwesome/MDI) with forced white color
        if qtawesome:
            name_lists = {
                'play': ['fa5s.play', 'fa.play', 'mdi.play'],
                'pause': ['fa5s.pause', 'fa.pause', 'mdi.pause'],
                'restart': ['fa5s.redo', 'fa.redo', 'mdi.refresh'],
            }
            for icon_name in name_lists.get(kind, []):
                try:
                    return qtawesome.icon(icon_name, color='#ffffff')
                except Exception:
                    continue
        # 4) Fallback to high-res drawn icons (always white)
        if kind == 'play':
            return self.create_play_icon()
        if kind == 'pause':
            return self.create_pause_icon()
        if kind == 'restart':
            return self.create_restart_icon()
        return QIcon()

    def _try_svg_list(self, filenames, size):
        for filename in filenames:
            icon = self.load_svg_icon(filename, size)
            if icon:
                return icon
        return None

    def _try_svg_by_keywords(self, keywords, size):
        if not keywords:
            return None
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            for folder in [base_path, os.path.join(base_path, 'Resources')]:
                if not os.path.isdir(folder):
                    continue
                for fn in os.listdir(folder):
                    lower = fn.lower()
                    if not lower.endswith('.svg'):
                        continue
                    if all(kw in lower for kw in keywords):
                        icon = self.load_svg_icon(fn, size)
                        if icon:
                            return icon
        except Exception:
            pass
        return None

    def load_svg_icon(self, filename, size=QSize(36, 36)):
        """Render an SVG to a high-DPI pixmap and wrap in QIcon."""
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            candidates = [
                os.path.join(base_path, filename),
                os.path.join(base_path, 'Resources', filename),
            ]
            for path in candidates:
                if os.path.exists(path):
                    # Read and force white color for fills/strokes to ensure high contrast
                    try:
                        with open(path, 'rb') as f:
                            raw = f.read()
                        text = raw.decode('utf-8', errors='ignore')
                        for key in ['#E3E3E3', '#e3e3e3', '#000000']:
                            text = text.replace(key, '#FFFFFF')
                        data = QByteArray(text.encode('utf-8'))
                        renderer = QSvgRenderer(data)
                    except Exception:
                        renderer = QSvgRenderer(path)
                    pm, _ = self._make_hidpi_pixmap(size)
                    painter = QPainter(pm)
                    painter.setRenderHint(QPainter.Antialiasing)
                    # Render to full device-pixel area for crisp output
                    renderer.render(painter, QRectF(0, 0, pm.width(), pm.height()))
                    painter.end()
                    return QIcon(pm)
        except Exception:
            pass
        return None

    def _make_hidpi_pixmap(self, size):
        """Create a transparent pixmap scaled for device pixel ratio for crisp icons."""
        try:
            screen = QGuiApplication.primaryScreen()
            dpr = float(screen.devicePixelRatio()) if screen else 1.0
        except Exception:
            dpr = 1.0
        pm = QPixmap(int(size.width() * dpr), int(size.height() * dpr))
        pm.fill(Qt.transparent)
        pm.setDevicePixelRatio(dpr)
        return pm, dpr
        
    def open_worship_form(self):
        """Open the worship form as a full-page inside the app"""
        form = WorshipForm(self)

        def on_form_accepted():
            self.worship_data = form.get_data()
            print(f"Worship Data: {self.worship_data}")
            # Build the main view and switch to it
            self.create_main_view()
            try:
                # Remove the form page
                idx = self.stacked_widget.indexOf(form)
                if idx != -1:
                    self.stacked_widget.removeWidget(form)
                    form.deleteLater()
            except Exception:
                pass

        def on_form_rejected():
            # Return to initial view and remove form page
            try:
                self.stacked_widget.setCurrentIndex(0)
                idx = self.stacked_widget.indexOf(form)
                if idx != -1:
                    self.stacked_widget.removeWidget(form)
                    form.deleteLater()
            except Exception:
                pass

        form.accepted.connect(on_form_accepted)
        form.rejected.connect(on_form_rejected)
        # Embed as a stacked page
        self.stacked_widget.addWidget(form)
        self.stacked_widget.setCurrentWidget(form)
            
    def open_song_form(self):
        """Open the song form"""
        try:
            # Check if audio is currently playing
            if hasattr(self, 'tracks_panel') and self.tracks_panel:
                if self.tracks_panel.audio_manager.is_playing():
                    # Show warning message
                    msg_box = QMessageBox()
                    msg_box.setWindowTitle("Áudio Tocando")
                    msg_box.setText("Por favor, pause a música atual antes de adicionar uma nova.")
                    msg_box.setIcon(QMessageBox.Warning)
                    msg_box.exec_()
                    return
                    
            form = SongForm(self)

            def on_form_accepted():
                song_data = form.get_data()
                print(f"Song Data: {song_data}")
                # Add song to our list
                self.songs.append(song_data)
                if hasattr(self, 'tracks_panel') and self.tracks_panel:
                    try:
                        song_id = self.tracks_panel._get_song_id(song_data)
                        env = song_data.get("precomputed_envelope") or None
                        if env:
                            self.tracks_panel.timeline_cache[song_id] = {
                                'envelope': env,
                                'total_samples': song_data.get('precomputed_total_samples', 0),
                                'sample_rate': song_data.get('precomputed_sample_rate', 44100),
                            }
                    except Exception:
                        pass
                    song_name = song_data.get("name", "Unknown Song")
                    key = song_data.get("key", "Unknown Key")
                    bpm = song_data.get("bpm", "Unknown BPM")
                    banner_image = song_data.get("banner_image", None)
                    self.tracks_panel.add_song_card(song_name, key, bpm, banner_image, song_data)
                    self.on_song_selected(song_data)
                # Volta para a view principal e remove a página do formulário
                try:
                    self.stacked_widget.setCurrentWidget(self.main_widget)
                    idx = self.stacked_widget.indexOf(form)
                    if idx != -1:
                        self.stacked_widget.removeWidget(form)
                        form.deleteLater()
                except Exception:
                    pass
            
            def on_form_rejected():
                # Simply return to the main view
                try:
                    self.stacked_widget.setCurrentWidget(self.main_widget)
                    # Remove the form page from stack
                    idx = self.stacked_widget.indexOf(form)
                    if idx != -1:
                        self.stacked_widget.removeWidget(form)
                        form.deleteLater()
                except Exception:
                    pass

            form.accepted.connect(on_form_accepted)
            form.rejected.connect(on_form_rejected)
            # Embed the form inside the app using the stacked widget
            self.stacked_widget.addWidget(form)
            self.stacked_widget.setCurrentWidget(form)
        except Exception as e:
            print(f"Error in open_song_form: {e}")
            # Show error message to user
            msg_box = QMessageBox()
            msg_box.setWindowTitle("Error")
            msg_box.setText(f"An error occurred while adding the song: {str(e)}")
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.exec_()
        
    def save_project(self):
        try:
            worship = self.worship_data or {}
            songs = self.songs[:]
            data = {
                "version": 1,
                "worship": worship,
                "songs": songs,
            }
            default_name = "Projeto.wproj"
            try:
                name = (worship.get("name") or "Projeto").strip()
                date = (worship.get("date") or "").strip()
                base = f"{name} - {date}".strip().strip(" -")
                safe = "".join(c for c in base if c.isalnum() or c in " _-")
                default_name = f"{safe}.wproj"
            except Exception:
                pass
            path, _ = QFileDialog.getSaveFileName(self, "Salvar Projeto", default_name, "Projeto de Culto (*.wproj);;JSON (*.json)")
            if not path:
                return
            try:
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                msg = QMessageBox(self)
                msg.setWindowTitle("Erro ao Salvar")
                msg.setText(f"Não foi possível salvar o projeto: {str(e)}")
                msg.setIcon(QMessageBox.Critical)
                msg.exec_()
        except Exception as e:
            print(f"Error in save_project: {e}")
            msg = QMessageBox(self)
            msg.setWindowTitle("Erro")
            msg.setText(f"Ocorreu um erro ao salvar: {str(e)}")
            msg.setIcon(QMessageBox.Critical)
            msg.exec_()

    def open_project(self):
        try:
            path, _ = QFileDialog.getOpenFileName(self, "Abrir Projeto", "", "Projeto de Culto (*.wproj);;JSON (*.json);;Todos (*.*)")
            if not path:
                return
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except Exception as e:
                msg = QMessageBox(self)
                msg.setWindowTitle("Erro ao Abrir")
                msg.setText(f"Não foi possível abrir o projeto: {str(e)}")
                msg.setIcon(QMessageBox.Critical)
                msg.exec_()
                return
            worship = data.get("worship", {})
            songs = data.get("songs", [])
            self.worship_data = worship
            self.songs = songs
            self.create_main_view()
            try:
                for song in self.songs:
                    song_name = song.get("name", "Unknown Song")
                    key = song.get("key", "Unknown Key")
                    bpm = song.get("bpm", "Unknown BPM")
                    banner_image = song.get("banner_image", None)
                    self.tracks_panel.add_song_card(song_name, key, bpm, banner_image, song)
                if self.songs:
                    self.on_song_selected(self.songs[0])
            except Exception:
                pass
        except Exception as e:
            print(f"Error in open_project: {e}")
            msg = QMessageBox(self)
            msg.setWindowTitle("Erro")
            msg.setText(f"Ocorreu um erro ao abrir: {str(e)}")
            msg.setIcon(QMessageBox.Critical)
            msg.exec_()
        
