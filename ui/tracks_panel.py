from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QPushButton, 
                             QGroupBox, QCheckBox, QScrollArea, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QTimer, QSize, QPropertyAnimation, QEasingCurve, QObject
from PyQt5.QtGui import QFont, QPainter, QColor, QPen, QPixmap, QPainterPath
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from audio.player import AudioPlayer
from audio.manager import AudioManager


class CustomFader(QSlider):
    """Custom fader as a thin vertical line"""
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.vu_level = 0.0
        self._smoothed_vu = 0.0
        self.setTickPosition(QSlider.NoTicks)
        # Don't invert the slider - keep natural behavior (bottom = 0, top = 100)
        self.setInvertedAppearance(False)
        self.setFocusPolicy(Qt.NoFocus)
        
        # Load hand image
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            hand_path = os.path.join(base_path, "hand.png")
            self.hand_pixmap = QPixmap(hand_path)
        except:
            self.hand_pixmap = None
            
        # Animation for smooth movement
        self.animation = QPropertyAnimation(self, b"value")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # Set fixed size for the fader - increased width to accommodate markings
        self.setFixedWidth(100)  # Increased from 60 to 100
        self.setMinimumHeight(300)
        
        # Flag to track dragging
        self.dragging = False

    def _handle_rect(self):
        handle_y = self.height() - 10 - int((self.height() - 20) * (self.value() - self.minimum()) / (self.maximum() - self.minimum()))
        return QRect(35, handle_y - 20, 40, 40)
        
    def set_vu_level(self, level):
        """Set the VU level (0.0 to 1.0)"""
        level = max(0.0, min(1.0, level))
        self._smoothed_vu = 0.85 * self._smoothed_vu + 0.15 * level
        self.vu_level = self._smoothed_vu
        self.update()
        
    def setValue(self, value):
        """Override setValue to use animation"""
        self.animation.stop()
        self.animation.setStartValue(self.value())
        self.animation.setEndValue(value)
        self.animation.start()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._handle_rect().contains(event.pos()):
            self.dragging = True
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            event.ignore()
            
    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() & Qt.LeftButton:
            usable = max(1, self.height() - 20)
            y = min(max(event.y(), 10), self.height() - 10)
            ratio = (self.height() - 10 - y) / usable
            value = self.minimum() + int(ratio * (self.maximum() - self.minimum()))
            super().setValue(value)
            event.accept()
        else:
            if self._handle_rect().contains(event.pos()):
                self.setCursor(Qt.OpenHandCursor)
            else:
                self.setCursor(Qt.ArrowCursor)
            event.ignore()
            
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(Qt.OpenHandCursor if self._handle_rect().contains(event.pos()) else Qt.ArrowCursor)
            event.accept()
        else:
            event.ignore()

    def wheelEvent(self, event):
        event.ignore()
            
    def paintEvent(self, event):
        """Custom paint event to draw fader with VU meter and markings"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw scale markings on both sides
        self._draw_scale_markings(painter)
        
        # Draw fader background - perfectly centered
        # Widget width = 100px
        # Left space = 45px, Fader width = 10px, Right space = 45px
        fader_rect = QRect(45, 10, 10, self.height() - 20)  # Centered at x=50 (widget center)
        painter.setPen(QPen(QColor("#2a2a2a"), 1))
        painter.setBrush(QColor("#4a4a4a"))
        painter.drawRoundedRect(fader_rect, 5, 5)
        
        # Draw VU meter
        if self.vu_level > 0.02:
            displayed = self.vu_level
            if displayed < 0.25:
                displayed = displayed * 1.5
            elif displayed < 0.7:
                displayed = max(0.6, displayed)
            displayed = max(0.0, min(displayed, 1.0))
            vu_height = int((self.height() - 20) * displayed)
            vu_top = self.height() - 10 - vu_height
            
            # White VU bar for clearer visibility on dark theme
            color = QColor(255, 255, 255)
                
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawRoundedRect(QRect(45, vu_top, 10, vu_height), 5, 5)
        
        # Draw hand (handle) - perfectly centered on the fader
        handle_y = self.height() - 10 - int((self.height() - 20) * (self.value() - self.minimum()) / (self.maximum() - self.minimum()))
        if self.hand_pixmap and not self.hand_pixmap.isNull():
            # Scale the pixmap to 40x40
            scaled_pixmap = self.hand_pixmap.scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # Position: center of fader is at x=50, pixmap is 40px wide, so x=50-20=30
            painter.drawPixmap(30, handle_y - 20, scaled_pixmap)
        else:
            # Fallback: draw a circle if image fails to load
            painter.setPen(QPen(QColor("#5a9bd5"), 2))
            painter.setBrush(QColor("#2a2a2a"))
            # Center of fader is at x=50, circle is 20px wide, so x=50-10=40
            painter.drawEllipse(40, handle_y - 10, 20, 20)

    def _draw_scale_markings(self, painter):
        """Draw scale markings on both sides of the fader"""
        painter.setPen(QPen(QColor("#6a6a6a"), 1))
        painter.setFont(QFont("Arial", 6))
        
        # Draw markings on both left and right sides of the fader
        # Widget is 100px wide
        # Left markings from x=5 to x=40 (35px wide)
        # Right markings from x=60 to x=95 (35px wide)
        # Center fader from x=45 to x=55 (10px wide)
        for i in range(0, 11):
            y_pos = 10 + (self.height() - 20) * (10 - i) / 10
            if i % 2 == 0:  # Major markings
                # Left side major markings
                painter.drawLine(20, int(y_pos), 34, int(y_pos))
                # Right side major markings
                painter.drawLine(66, int(y_pos), 80, int(y_pos))
                # Draw percentage text
                painter.drawText(4, int(y_pos) + 2, str(i * 10))      # Left text com gap da linha
                painter.drawText(92, int(y_pos) + 2, str(i * 10))     # Right text com gap da linha
            else:  # Minor markings
                # Left side minor markings
                painter.drawLine(24, int(y_pos), 34, int(y_pos))
                # Right side minor markings
                painter.drawLine(66, int(y_pos), 76, int(y_pos))

class TrackControl(QWidget):
    # Signals for volume and mute changes
    volumeChanged = pyqtSignal(int, float)  # track_index, volume
    muteChanged = pyqtSignal(int, bool)     # track_index, muted
    soloChanged = pyqtSignal(int, bool)     # track_index, solo_state
    
    def __init__(self, track_index, track_name, parent=None):
        super().__init__(parent)
        self.track_index = track_index
        self.track_name = track_name
        self.is_solo = False
        self.setup_ui()
        
    def setup_ui(self):
        # Set wider width for the track control to accommodate the wider fader
        self.setFixedWidth(100)  # Increased from 60 to 100
        
        # Main layout
        layout = QVBoxLayout()
        # Mais respiro na margem esquerda para o master
        layout.setContentsMargins(10, 5, 5, 5)
        layout.setSpacing(8)
        
        # Track name
        self.name_label = QLabel(self.track_name[:12] + "..." if len(self.track_name) > 12 else self.track_name)
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("color: #dddddd; font-size: 10px; font-weight: bold;")
        layout.addWidget(self.name_label)
        
        # Buttons layout (M and S buttons below the track name, centered)
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)
        buttons_layout.setAlignment(Qt.AlignCenter)
        
        # Mute button
        self.mute_button = QPushButton("M")
        self.mute_button.setFixedSize(20, 20)
        self.mute_button.setCheckable(True)
        self.mute_button.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border-radius: 10px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #ff4444;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:checked:hover {
                background-color: #ff6666;
            }
        """)
        self.mute_button.clicked.connect(self.on_mute_clicked)
        buttons_layout.addWidget(self.mute_button)
        
        # Solo button
        self.solo_button = QPushButton("S")
        self.solo_button.setFixedSize(20, 20)
        self.solo_button.setCheckable(True)
        self.solo_button.setStyleSheet("""
            QPushButton {
                background-color: #4a4a4a;
                color: #ffffff;
                border-radius: 10px;
                font-size: 9px;
                font-weight: bold;
            }
            QPushButton:checked {
                background-color: #3399ff;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:checked:hover {
                background-color: #4da6ff;
            }
        """)
        self.solo_button.clicked.connect(self.on_solo_clicked)
        buttons_layout.addWidget(self.solo_button)
        
        layout.addLayout(buttons_layout)
        
        # Volume fader as thin vertical line
        self.volume_fader = CustomFader(Qt.Vertical)
        self.volume_fader.setMinimum(0)
        self.volume_fader.setMaximum(100)
        self.volume_fader.setValue(80)
        # Don't invert the slider - keep natural behavior (bottom = 0, top = 100)
        self.volume_fader.setInvertedAppearance(False)
        self.volume_fader.setFixedHeight(300)  # Keep height
        self.volume_fader.valueChanged.connect(self.on_volume_changed)
        # Centralização exata: coloca o fader entre dois stretches
        fader_row = QHBoxLayout()
        fader_row.setContentsMargins(0, 0, 0, 0)
        fader_row.addStretch(1)
        fader_row.addWidget(self.volume_fader)
        fader_row.addStretch(1)
        layout.addLayout(fader_row)
        
        # Volume label
        self.volume_label = QLabel("80%")
        self.volume_label.setAlignment(Qt.AlignCenter)
        self.volume_label.setStyleSheet("color: #aaaaaa; font-size: 9px;")
        layout.addWidget(self.volume_label)
        
        self.setLayout(layout)
        
    def on_volume_changed(self, value):
        self.volume_label.setText(f"{value}%")
        # Emit signal with track index and volume (0.0 to 1.0)
        self.volumeChanged.emit(self.track_index, value / 100.0)
        
    def on_mute_clicked(self):
        # Emit signal with track index and mute state
        self.muteChanged.emit(self.track_index, self.mute_button.isChecked())
        
    def on_solo_clicked(self):
        # Toggle solo state
        self.is_solo = self.solo_button.isChecked()
        # Emit signal with track index and solo state
        self.soloChanged.emit(self.track_index, self.is_solo)
        
    def set_volume(self, volume):
        """Set volume fader value (0-100)"""
        self.volume_fader.setValue(int(volume * 100))
        
    def set_muted(self, muted):
        """Set mute button state"""
        self.mute_button.setChecked(muted)
        
    def set_solo(self, solo):
        """Set solo button state"""
        self.is_solo = solo
        self.solo_button.setChecked(solo)
        
    def update_vu_meter(self, level):
        """Update the VU meter with a new level (0.0 to 1.0)"""
        self.volume_fader.set_vu_level(level)

class MasterTrackControl(QWidget):
    """Master fader control with same size/layout as track faders, without M/S buttons"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        # Largura um pouco maior para evitar corte visual
        self.setFixedWidth(200)
        # Fundo cinza igual aos outros faders; canto esquerdo reto para encostar na borda
        self.setStyleSheet("background-color: #252525; border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 10px; border-bottom-right-radius: 10px;")
        # Garante que o QSS pinte o fundo do QWidget
        try:
            self.setAttribute(Qt.WA_StyledBackground, True)
        except Exception:
            pass

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        # Header label indicating master
        self.name_label = QLabel("MASTER")
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("color: #dddddd; font-size: 10px; font-weight: bold; background-color: #444343; border-radius: 6px; padding: 6px;")
        layout.addWidget(self.name_label)

        # Volume fader (no M/S buttons)
        self.volume_fader = CustomFader(Qt.Vertical)
        self.volume_fader.setMinimum(0)
        self.volume_fader.setMaximum(100)
        self.volume_fader.setValue(80)
        self.volume_fader.setInvertedAppearance(False)
        self.volume_fader.setFixedHeight(300)
        # Centraliza o fader no container usando uma linha com stretches nas laterais
        fader_row = QHBoxLayout()
        fader_row.setContentsMargins(0, 0, 0, 0)
        fader_row.addStretch(1)
        fader_row.addWidget(self.volume_fader)
        fader_row.addStretch(1)
        layout.addLayout(fader_row)

        # Volume label
        self.volume_label = QLabel("80%")
        self.volume_label.setAlignment(Qt.AlignCenter)
        self.volume_label.setStyleSheet("color: #aaaaaa; font-size: 9px;")
        layout.addWidget(self.volume_label)

        self.setLayout(layout)
        self.volume_fader.valueChanged.connect(self.on_volume_changed)

    def on_volume_changed(self, value):
        self.volume_label.setText(f"{value}%")

    def get_volume(self):
        return self.volume_fader.value() / 100.0

    def set_volume(self, volume):
        self.volume_fader.setValue(int(volume * 100))

class TracksPanel(QWidget):
    songCardSelected = pyqtSignal(object)
    def __init__(self, tracks=None, parent=None):
        super().__init__(parent)
        self.tracks = tracks or []
        self.track_controls = []
        self.audio_manager = AudioManager()  # Use AudioManager instead of direct AudioPlayer
        self.solo_states = {}  # Track solo states
        self.original_mute_states = {}  # Store original mute states when solo is activated
        self.song_cards = []  # Store song card widgets
        self.song_card_map = {}  # Map song_id -> card to avoid duplicates
        self.selected_card = None  # Currently selected song card
        self._current_player = None
        self.timeline_widget = None
        self.timeline_total_samples = 0
        self.timeline_sample_rate = 0
        self.timeline_envelope = None
        self.timeline_cache = {}
        self._timeline_thread = None
        self._timeline_worker = None
        self.setup_ui()
        
        # Connect to playback state change signal
        self.audio_manager.playbackStateChanged.connect(self.on_playback_state_changed)
        # Blink timer for selected card border
        self.card_blink_timer = QTimer(self)
        self.card_blink_timer.setInterval(500)
        self.card_blink_timer.timeout.connect(self._toggle_card_blink)
        self._card_blink_on = False
        # VU polling timer as a fallback to ensure UI updates even if signals drop
        self.vu_poll_timer = QTimer(self)
        self.vu_poll_timer.setInterval(75)
        self.vu_poll_timer.timeout.connect(self._poll_vu_levels)
        
        # Load tracks into audio player
        for track_path in self.tracks:
            self.audio_manager.current_player.load_track(track_path) if self.audio_manager.current_player else None

    def connect_player_signals(self):
        """Connect to the current player's signals for VU meter updates, safely handling reconnection."""
        try:
            player = self.audio_manager.current_player
            if player is None:
                return
            # Disconnect old player if different
            if self._current_player and self._current_player is not player:
                try:
                    self._current_player.volumeLevelsChanged.disconnect(self.update_vu_meters)
                except Exception:
                    pass
            # Connect new player
            self._current_player = player
            try:
                player.volumeLevelsChanged.connect(self.update_vu_meters)
            except Exception:
                pass
        except Exception:
            pass
            
    def setup_ui(self):
        # Set background color
        self.setStyleSheet("background-color: #1e1e1e;")
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to cover full width
        layout.setSpacing(15)
        
        # Song cards container
        self.song_cards_container = QWidget()
        self.song_cards_container.setStyleSheet("background-color: #252525; border-radius: 10px;")
        self.song_cards_container.setVisible(False)  # Hidden by default
        song_cards_layout = QVBoxLayout()
        song_cards_layout.setContentsMargins(15, 15, 15, 15)
        self.song_cards_layout = QHBoxLayout()
        self.song_cards_layout.setSpacing(15)
        self.song_cards_layout.setAlignment(Qt.AlignLeft)
        song_cards_layout.addLayout(self.song_cards_layout)
        self.song_cards_container.setLayout(song_cards_layout)
        layout.addWidget(self.song_cards_container)

        # Timeline widget below song cards
        try:
            self.timeline_widget = TimelineWidget()
            self.timeline_widget.setVisible(False)
            layout.addWidget(self.timeline_widget)
        except Exception:
            self.timeline_widget = None
        
        # Tracks scroll area - modified to cover full width
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #1e1e1e;
            }
            QScrollBar:horizontal {
                background: #2d2d2d;
                height: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background: #4a4a4a;
                border-radius: 6px;
                min-width: 20px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #5a5a5a;
            }
        """)
        
        # Tracks container - remove black background (use transparent to inherit scroll area bg)
        tracks_container = QWidget()
        tracks_container.setStyleSheet("background-color: transparent;")
        
        # Horizontal layout for tracks and master fader
        tracks_main_layout = QHBoxLayout()
        # Sem padding à esquerda para encostar o master na borda
        tracks_main_layout.setContentsMargins(0, 0, 0, 0)
        tracks_main_layout.setSpacing(0)  # Remove spacing between tracks and master
        
        # Add master fader (same size/layout as tracks) on the left
        self.master_control = MasterTrackControl()
        # Connect master fader to update all track volumes
        self.master_control.volume_fader.valueChanged.connect(self.on_master_volume_changed)
        tracks_main_layout.addWidget(self.master_control)
        
        # Add separator line between master fader and tracks
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: rgba(42,42,42,60); background-color: rgba(42,42,42,60);")  # quase transparente
        separator.setFixedWidth(1)
        tracks_main_layout.addWidget(separator)
        
        # Tracks layout - gray background
        tracks_layout_container = QWidget()
        # Container pai dos faders das músicas com radius apenas no topo
        tracks_layout_container.setStyleSheet(
            "background-color: #252525;"
            "border-top-left-radius: 18px;"
            "border-top-right-radius: 18px;"
            "border-bottom-left-radius: 0px;"
            "border-bottom-right-radius: 0px;"
        )
        try:
            tracks_layout_container.setAttribute(Qt.WA_StyledBackground, True)
        except Exception:
            pass
        tracks_layout_inner = QHBoxLayout()
        tracks_layout_inner.setContentsMargins(10, 10, 10, 10)
        tracks_layout_inner.setSpacing(15)
        tracks_layout_inner.setAlignment(Qt.AlignLeft)
        self.tracks_layout = QHBoxLayout()
        self.tracks_layout.setSpacing(15)
        self.tracks_layout.setAlignment(Qt.AlignLeft)
        tracks_layout_inner.addLayout(self.tracks_layout)
        tracks_layout_container.setLayout(tracks_layout_inner)
        tracks_main_layout.addWidget(tracks_layout_container)
        
        tracks_container.setLayout(tracks_main_layout)
        scroll_area.setWidget(tracks_container)
        # Increase the height of the scroll area
        scroll_area.setMinimumHeight(450)
        layout.addWidget(scroll_area)
        
        self.setLayout(layout)
        
    # Add method to add song cards
    def add_song_card(self, song_name, key, bpm, banner_image_path=None, song_data=None):
        """Add a song card to the display"""
        try:
            song_id = self._get_song_id(song_data) if song_data else None
            if song_id and song_id in self.song_card_map:
                # Update existing card info
                existing = self.song_card_map[song_id]
                existing.update_info(song_name, key, bpm, banner_image_path)
            else:
                song_card = SongCardWidget(song_name, key, bpm, banner_image_path)
                song_card.song_data = song_data
                song_card.clicked.connect(lambda sc=song_card, sd=song_data: self.on_song_card_clicked(sc, sd))
                self.song_cards.append(song_card)
                self.song_cards_layout.addWidget(song_card)
                if song_id:
                    self.song_card_map[song_id] = song_card
                self.song_cards_container.setVisible(True)
        except Exception as e:
            print(f"Error adding song card: {e}")

    # Add method to update song cards
    def update_song_card(self, index, song_name, key, bpm, banner_image_path=None):
        """Update an existing song card"""
        if 0 <= index < len(self.song_cards):
            self.song_cards[index].update_info(song_name, key, bpm, banner_image_path)

    # Add method to clear song cards
    def clear_song_cards(self):
        """Clear all song cards"""
        for card in self.song_cards:
            self.song_cards_layout.removeWidget(card)
            card.deleteLater()
        self.song_cards.clear()
        self.song_card_map.clear()
        self.song_cards_container.setVisible(False)
        self.selected_card = None

    def _get_song_id(self, song_data):
        """Generate a unique ID for the song card to avoid duplicates"""
        if not song_data:
            return None
        name = song_data.get("name", "")
        tracks = "|".join(song_data.get("tracks", []))
        return f"{name}:{tracks}"
        
    def toggle_playback(self):
        """Toggle between play and pause"""
        if self.audio_manager.is_playing():
            self.audio_manager.pause_current_song()
        else:
            self.audio_manager.play_current_song()

    def stop_playback(self):
        """Stop playback"""
        self.audio_manager.stop_all()
        
        # Reset VU meters
        for control in self.track_controls:
            control.update_vu_meter(0.0)
            
    def on_playback_state_changed(self, is_playing):
        """Handle playback state changes"""
        # Blink selected card border when playing
        if self.selected_card:
            if is_playing:
                self.start_card_blink()
            else:
                self.stop_card_blink()
        # Ensure player signals are connected when playback starts
        if is_playing:
            self.connect_player_signals()
            if not self.vu_poll_timer.isActive():
                self.vu_poll_timer.start()
        else:
            if self.vu_poll_timer.isActive():
                self.vu_poll_timer.stop()
        # Reset VU meters when playback stops
        if not is_playing:
            for control in self.track_controls:
                control.update_vu_meter(0.0)
            # Reset playhead
            if self.timeline_widget:
                self.timeline_widget.set_playhead_fraction(0.0)

    def _poll_vu_levels(self):
        try:
            player = self.audio_manager.current_player
            if player:
                levels = player.get_volume_levels()
                if levels:
                    self.update_vu_meters(levels)
                # Update playhead position on timeline
                if self.timeline_total_samples > 0 and self.timeline_widget:
                    frac = min(max(player.current_position / float(self.timeline_total_samples), 0.0), 1.0)
                    self.timeline_widget.set_playhead_fraction(frac)
        except Exception:
            pass

    def on_song_card_clicked(self, card, song_data):
        """Select a song card, update UI, and emit selection"""
        # Deselect previous
        if self.selected_card and self.selected_card is not card:
            self.selected_card.set_selected(False)
            self.selected_card.set_blink_on(False)
        # Select new
        self.selected_card = card
        card.set_selected(True)
        # Emit selection to MainWindow
        try:
            self.songCardSelected.emit(song_data)
        except Exception:
            pass

    def build_timeline_for_current_song(self):
        """Compute and display the envelope asynchronously to avoid blocking the UI."""
        try:
            player = self.audio_manager.current_player
            tracks = getattr(player, 'tracks', [])
            if not tracks:
                self.timeline_widget.setVisible(False)
                return
            # Cache by song id
            try:
                song_id = self._get_song_id(self.audio_manager.current_song)
            except Exception:
                song_id = None
            if song_id and song_id in self.timeline_cache:
                cached = self.timeline_cache[song_id]
                self.timeline_total_samples = cached.get('total_samples', 0)
                self.timeline_sample_rate = cached.get('sample_rate', 44100)
                self.timeline_envelope = cached.get('envelope', [])
                self.timeline_widget.set_envelope(self.timeline_envelope)
                self.timeline_widget.set_playhead_fraction(0.0)
                self.timeline_widget.setVisible(True)
                return
            # Cancel previous worker if running
            self._cleanup_timeline_worker()
            target_points = max(1000, self.timeline_widget.width())
            # Start worker thread
            self._timeline_thread = QThread(self)
            self._timeline_worker = TimelineWorker(tracks, target_points, song_id)
            self._timeline_worker.moveToThread(self._timeline_thread)
            self._timeline_thread.started.connect(self._timeline_worker.run)
            self._timeline_worker.envelopeReady.connect(self._on_timeline_ready)
            self._timeline_worker.error.connect(lambda msg: print(f"Timeline worker error: {msg}"))
            self._timeline_thread.finished.connect(self._cleanup_timeline_worker)
            self._timeline_thread.start()
        except Exception as e:
            print(f"Error building timeline: {e}")

    def _on_timeline_ready(self, envelope, total_samples, sample_rate, song_id):
        # Update state and cache
        self.timeline_total_samples = total_samples
        self.timeline_sample_rate = sample_rate
        self.timeline_envelope = envelope or []
        if song_id:
            self.timeline_cache[song_id] = {
                'envelope': self.timeline_envelope,
                'total_samples': self.timeline_total_samples,
                'sample_rate': self.timeline_sample_rate,
            }
        # Update widget
        if self.timeline_widget:
            self.timeline_widget.set_envelope(self.timeline_envelope)
            self.timeline_widget.set_playhead_fraction(0.0)
            self.timeline_widget.setVisible(bool(self.timeline_envelope))
        # Cleanup thread
        if self._timeline_thread:
            self._timeline_thread.quit()
            self._timeline_thread.wait()

    def _cleanup_timeline_worker(self):
        try:
            if self._timeline_thread and self._timeline_thread.isRunning():
                self._timeline_thread.quit()
                self._timeline_thread.wait(500)
        except Exception:
            pass
        self._timeline_thread = None
        self._timeline_worker = None

    def _toggle_card_blink(self):
        self._card_blink_on = not self._card_blink_on
        if self.selected_card:
            self.selected_card.set_blink_on(self._card_blink_on)

    def start_card_blink(self):
        if self.selected_card:
            self.selected_card.set_blink_on(True)
        if not self.card_blink_timer.isActive():
            self.card_blink_timer.start()

    def stop_card_blink(self):
        self.card_blink_timer.stop()
        self._card_blink_on = False
        if self.selected_card:
            self.selected_card.set_blink_on(False)

    def select_card_by_song(self, song_data):
        """Select the card corresponding to the given song data"""
        try:
            song_id = self._get_song_id(song_data)
            card = self.song_card_map.get(song_id)
            if card:
                # Deselect previous
                if self.selected_card and self.selected_card is not card:
                    self.selected_card.set_selected(False)
                    self.selected_card.set_blink_on(False)
                # Select new without emitting (avoid recursion)
                self.selected_card = card
                card.set_selected(True)
                # If currently playing, ensure blink reflects state
                if hasattr(self.audio_manager, 'is_playing') and self.audio_manager.is_playing():
                    self.start_card_blink()
        except Exception:
            pass

    def on_track_volume_changed(self, track_index, volume):
        """Handle volume change for a track"""
        # Map slider values to perceptual gain and apply master
        master_pct = self.master_control.volume_fader.value()
        master_gain = self._slider_to_gain_pct(master_pct)
        track_pct = volume * 100.0
        track_gain = self._slider_to_gain_pct(track_pct)
        adjusted_gain = track_gain * master_gain
        self.audio_manager.current_player.set_volume(track_index, adjusted_gain)

    def on_track_mute_changed(self, track_index, muted):
        """Handle mute change for a track"""
        self.audio_manager.current_player.set_mute(track_index, muted)
        
    def on_track_solo_changed(self, track_index, is_solo):
        """Handle solo change for a track"""
        # Update solo state
        self.solo_states[track_index] = is_solo
        
        # Check if any track is soloed
        any_soloed = any(self.solo_states.values())
        
        if is_solo:  # Solo button was just pressed
            # Store original mute states of all tracks before applying solo
            for i, control in enumerate(self.track_controls):
                self.original_mute_states[i] = control.mute_button.isChecked()
            
            # Mute all tracks except the soloed ones and update UI
            for i, control in enumerate(self.track_controls):
                if i == track_index:
                    # Soloed track - unmute it and keep solo button active
                    control.set_muted(False)
                    self.audio_manager.current_player.set_mute(i, False)
                else:
                    # Not soloed - mute it and show mute button as active (visual feedback)
                    control.set_muted(True)
                    self.audio_manager.current_player.set_mute(i, True)
        else:  # Solo button was just released
            # Check if any other tracks are still soloed
            if not any_soloed:
                # No tracks soloed - restore original mute states
                for i, control in enumerate(self.track_controls):
                    original_muted = self.original_mute_states.get(i, False)
                    control.set_muted(original_muted)
                    self.audio_manager.current_player.set_mute(i, original_muted)
            else:
                # Other tracks are still soloed - apply solo logic again
                for i, control in enumerate(self.track_controls):
                    if self.solo_states.get(i, False):
                        # Soloed track - unmute it
                        control.set_muted(False)
                        self.audio_manager.current_player.set_mute(i, False)
                    else:
                        # Not soloed - mute it and show mute button as active (visual feedback)
                        control.set_muted(True)
                        self.audio_manager.current_player.set_mute(i, True)

    def on_master_volume_changed(self, value):
        """Handle master volume changes and apply to all tracks"""
        master_gain = self._slider_to_gain_pct(value)
        # Update all track volumes based on their individual settings and master gain
        for i, control in enumerate(self.track_controls):
            track_pct = control.volume_fader.value()
            track_gain = self._slider_to_gain_pct(track_pct)
            adjusted_gain = track_gain * master_gain
            self.audio_manager.current_player.set_volume(i, adjusted_gain)

    def update_vu_meters(self, volume_levels):
        """Update all VU meters with new volume levels"""
        for i, level in enumerate(volume_levels):
            if i < len(self.track_controls):
                self.track_controls[i].update_vu_meter(level)

    def _slider_to_gain_pct(self, s_pct):
        """Map slider percent (0..100) to amplitude gain using a dB law.
        - 0% -> ~-60 dB
        - 80% -> 0 dB (unity)
        - 100% -> +6 dB (~2x)
        """
        try:
            s = float(s_pct)
            s = max(0.0, min(100.0, s))
            if s <= 80.0:
                db = -60.0 + (s / 80.0) * 60.0  # -60 .. 0 dB
            else:
                db = 0.0 + ((s - 80.0) / 20.0) * 6.0  # 0 .. +6 dB
            gain = 10.0 ** (db / 20.0)
            return gain
        except Exception:
            return s_pct / 100.0

    def _gain_to_slider_pct(self, gain):
        """Inverse mapping: amplitude gain -> slider percent.
        - gain=1.0 -> 80%
        - gain<=1.0 maps into 0..80%; gain>1.0 maps into 80..100% up to +6 dB
        """
        try:
            import numpy as _np
            g = max(1e-6, float(gain))
            db = 20.0 * _np.log10(g)
            if db <= 0.0:
                s = 80.0 * (db + 60.0) / 60.0
            else:
                s = 80.0 + 20.0 * (db / 6.0)
            return int(max(0.0, min(100.0, s)))
        except Exception:
            return int(max(0.0, min(100.0, gain * 100.0)))


class SongCardWidget(QWidget):
    clicked = pyqtSignal()
    """Widget to display song information in a visual card format"""
    def __init__(self, song_name, key, bpm, banner_image_path=None, parent=None):
        super().__init__(parent)
        self.song_name = song_name
        self.key = key
        self.bpm = bpm
        self.banner_image_path = banner_image_path
        self.banner_pixmap = None
        self.is_selected = False
        self._blink_on = False
        
        # Load banner image if provided
        if self.banner_image_path:
            self.load_banner_image()
            
        self.setFixedSize(320, 180)  # Increased size for more prominence (16:9 ratio, larger)
        self.setup_ui()
        
    def load_banner_image(self):
        """Load banner image from file path or URL"""
        try:
            # For now, we only support local files
            # In a future implementation, we could add URL support
            if self.banner_image_path and os.path.exists(self.banner_image_path):
                self.banner_pixmap = QPixmap(self.banner_image_path)
        except Exception as e:
            print(f"Error loading banner image: {e}")
            self.banner_pixmap = None
        
    def setup_ui(self):
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
                border: none;
                border-radius: 15px;
            }
        """)
        self.setAttribute(Qt.WA_StyledBackground, True)
        
    def paintEvent(self, event):
        """Custom paint event to draw the song card"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        radius = 15
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), radius, radius)
        painter.setClipPath(path)
        
        # Draw background or banner image
        if self.banner_pixmap and not self.banner_pixmap.isNull():
            # Scale pixmap to fit the card while maintaining aspect ratio
            scaled_pixmap = self.banner_pixmap.scaled(
                self.width(), 
                self.height(), 
                Qt.KeepAspectRatioByExpanding, 
                Qt.SmoothTransformation
            )
            
            # Center the pixmap in the widget
            x = (self.width() - scaled_pixmap.width()) // 2
            y = (self.height() - scaled_pixmap.height()) // 2
            
            # Draw the scaled pixmap
            painter.drawPixmap(x, y, scaled_pixmap)
        else:
            # Draw default background
            painter.fillRect(self.rect(), QColor("#2d2d2d"))

        # Draw selection border (thin green), blink when playing
        if self.is_selected:
            color = QColor("#49c149")
            color.setAlpha(200 if self._blink_on else 100)
            painter.setClipping(False)
            painter.setPen(QPen(color, 2))
            painter.drawRoundedRect(1, 1, self.width()-2, self.height()-2, radius, radius)

        # Draw song name at bottom left with larger font
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Arial", 14, QFont.Bold))  # Larger font
        metrics = painter.fontMetrics()
        text_width = metrics.horizontalAdvance(self.song_name)
        # Limit text width and add ellipsis if needed
        display_name = self.song_name
        if text_width > 300:
            display_name = self.song_name[:35] + "..."
        painter.drawText(15, self.height() - 25, display_name)  # Lower position
        
        # Draw key and BPM at top right with larger font
        info_text = f"{self.key} | {self.bpm} BPM"
        painter.setFont(QFont("Arial", 12))  # Larger font
        info_metrics = painter.fontMetrics()
        info_width = info_metrics.horizontalAdvance(info_text)
        painter.drawText(self.width() - info_width - 15, 30, info_text)  # Higher position

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self.update()

    def set_blink_on(self, on: bool):
        self._blink_on = on
        if self.is_selected:
            self.update()
        
    def update_info(self, song_name, key, bpm, banner_image_path=None):
        """Update the song information"""
        self.song_name = song_name
        self.key = key
        self.bpm = bpm
        
        # Update banner image if provided
        if banner_image_path and banner_image_path != self.banner_image_path:
            self.banner_image_path = banner_image_path
            self.load_banner_image()
            
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            try:
                self.clicked.emit()
            except:
                pass
        super().mousePressEvent(event)

class TimelineWidget(QWidget):
    """Displays a waveform timeline of the mixed song with a playhead."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._envelope = []  # list of floats 0..1
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
        # Background
        p.fillRect(self.rect(), QColor("#252525"))
        if not self._envelope:
            return
        # Draw waveform as a filled shape symmetrical around center
        center_y = h / 2
        max_amp = h * 0.45
        path = QPainterPath()
        # Top path
        path.moveTo(0, center_y)
        for x in range(w):
            idx = int((x / max(1, w-1)) * (len(self._envelope) - 1))
            a = self._envelope[idx] * max_amp
            y = center_y - a
            path.lineTo(x, y)
        # Bottom path (mirror)
        for x in range(w-1, -1, -1):
            idx = int((x / max(1, w-1)) * (len(self._envelope) - 1))
            a = self._envelope[idx] * max_amp
            y = center_y + a
            path.lineTo(x, y)
        path.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 200))
        p.drawPath(path)
        # Playhead
        ph_x = int(self._playhead_frac * w)
        p.setPen(QPen(QColor("#49c149"), 2))
        p.drawLine(ph_x, 0, ph_x, h)
class TimelineWorker(QObject):
    """Background worker to compute downsampled RMS envelope for the current song."""
    envelopeReady = pyqtSignal(object, int, int, object)  # (envelope:list, total_samples:int, sample_rate:int, song_id:any)
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
