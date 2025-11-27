from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, pyqtSignal, QEvent, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QFont, QPalette, QColor

class SkeletonWidget(QWidget):
    """Widget que simula um skeleton loader animado"""
    def __init__(self, width, height, parent=None):
        super().__init__(parent)
        self.setFixedSize(width, height)
        self._opacity = 0.3
        
        # Animação de pulso
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(1500)
        self.animation.setStartValue(0.3)
        self.animation.setEndValue(0.6)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.setLoopCount(-1)  # Loop infinito
        self.animation.start()
        
        self.update_style()
    
    @pyqtProperty(float)
    def opacity(self):
        return self._opacity
    
    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.update_style()
    
    def update_style(self):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: rgba(70, 70, 70, {self._opacity});
                border-radius: 8px;
            }}
        """)

class MusicCard(QWidget):
    # Signal emitted when the card is selected
    selected = pyqtSignal(object)
    
    # Signal emitted when the add track button is clicked
    addTrackRequested = pyqtSignal()
    
    # Signal emitted when the delete button is clicked
    deleteRequested = pyqtSignal()
    
    def __init__(self, song_data=None, is_add_button=False, is_skeleton=False, parent=None):
        super().__init__(parent)
        self.song_data = song_data
        self.is_add_button = is_add_button
        self.is_skeleton = is_skeleton
        self.is_selected = False
        self.setup_ui()
        
    def setup_ui(self):
        # Set fixed size for the card (square shape)
        self.setFixedSize(180, 200)
        self.setAttribute(Qt.WA_StyledBackground, True)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        if self.is_skeleton:
            # Skeleton loader
            self.setup_skeleton_ui(layout)
        elif self.is_add_button:
            # Add button card
            self.setup_add_button_ui(layout)
        else:
            # Song card
            self.setup_song_card_ui(layout)
        
        self.setLayout(layout)
        self.update_style()
        
        # Install event filter for click detection
        if not self.is_add_button and not self.is_skeleton:
            for child in self.findChildren(QWidget):
                child.installEventFilter(self)
    
    def setup_skeleton_ui(self, layout):
        """Setup skeleton loader UI"""
        # Album art placeholder
        album_skeleton = SkeletonWidget(120, 120, self)
        layout.addWidget(album_skeleton, alignment=Qt.AlignCenter)
        
        # Title skeleton
        title_skeleton = SkeletonWidget(140, 16, self)
        layout.addWidget(title_skeleton, alignment=Qt.AlignCenter)
        
        # Details skeleton
        details_skeleton = SkeletonWidget(100, 12, self)
        layout.addWidget(details_skeleton, alignment=Qt.AlignCenter)
        
        layout.addStretch()
    
    def setup_add_button_ui(self, layout):
        """Setup add button UI"""
        # Container para o ícone +
        icon_container = QWidget()
        icon_container.setFixedSize(100, 100)
        icon_container.setStyleSheet("""
            QWidget {
                background-color: #2a2a2a;
                border: 2px dashed #555555;
                border-radius: 15px;
            }
        """)
        
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        
        self.add_button = QPushButton("+")
        self.add_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                font-size: 48px;
                font-weight: 300;
                border: none;
            }
            QPushButton:hover {
                color: #aaaaaa;
            }
        """)
        self.add_button.clicked.connect(lambda: self.addTrackRequested.emit())
        icon_layout.addWidget(self.add_button)
        
        layout.addWidget(icon_container, alignment=Qt.AlignCenter)
        
        # Label
        label = QLabel("Add New Song")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            color: #999999; 
            font-size: 13px;
            font-weight: 500;
            letter-spacing: 0.5px;
        """)
        layout.addWidget(label)
        
        layout.addStretch()
    
    def setup_song_card_ui(self, layout):
        """Setup song card UI"""
        # Header com delete button
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # Spacer
        header_layout.addStretch()
        
        # Delete button (top-right)
        self.delete_button = QPushButton("×")
        self.delete_button.setFixedSize(28, 28)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 68, 68, 0.9);
                color: white;
                border-radius: 14px;
                font-weight: bold;
                font-size: 18px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 68, 68, 1);
            }
        """)
        self.delete_button.clicked.connect(lambda: self.deleteRequested.emit())
        header_layout.addWidget(self.delete_button)
        
        layout.addLayout(header_layout)
        
        # Album art placeholder (simulação)
        album_art = QWidget()
        album_art.setFixedSize(120, 120)
        album_art.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #3a3a3a, stop:1 #2a2a2a);
                border-radius: 12px;
                border: 1px solid #404040;
            }
        """)
        layout.addWidget(album_art, alignment=Qt.AlignCenter)
        
        # Song name
        self.name_label = QLabel(self.song_data.get("name", "Untitled"))
        self.name_label.setAlignment(Qt.AlignCenter)
        self.name_label.setStyleSheet("""
            color: #ffffff; 
            font-size: 14px; 
            font-weight: 600;
            letter-spacing: 0.3px;
        """)
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumHeight(40)
        layout.addWidget(self.name_label)
        
        # Song details container
        details_container = QWidget()
        details_layout = QHBoxLayout(details_container)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(8)
        
        # Key badge
        key_label = QLabel(self.song_data.get('key', 'N/A'))
        key_label.setAlignment(Qt.AlignCenter)
        key_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 11px;
                font-weight: 500;
                background-color: #333333;
                border-radius: 4px;
                padding: 2px 8px;
            }
        """)
        details_layout.addWidget(key_label)
        
        # BPM badge
        bpm_label = QLabel(f"{self.song_data.get('bpm', 'N/A')} BPM")
        bpm_label.setAlignment(Qt.AlignCenter)
        bpm_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 11px;
                font-weight: 500;
                background-color: #333333;
                border-radius: 4px;
                padding: 2px 8px;
            }
        """)
        details_layout.addWidget(bpm_label)
        
        layout.addWidget(details_container)
        
        # Track count
        track_count = len(self.song_data.get("tracks", []))
        self.track_label = QLabel(f"{track_count} track{'s' if track_count != 1 else ''}")
        self.track_label.setAlignment(Qt.AlignCenter)
        self.track_label.setStyleSheet("""
            color: #777777; 
            font-size: 11px;
            font-weight: 400;
        """)
        layout.addWidget(self.track_label)
        
        # Button to add tracks to this song
        self.add_tracks_button = QPushButton("+ Adicionar Faixas")
        self.add_tracks_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #e0e0e0;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                border: 1px solid #4a4a4a;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #252525;
                border: 1px solid #3a3a3a;
            }
        """)
        self.add_tracks_button.clicked.connect(self.on_add_tracks_clicked)
        layout.addWidget(self.add_tracks_button)
        
        layout.addStretch()
        
    def update_style(self):
        """Update the card style based on selection state"""
        if self.is_add_button or self.is_skeleton:
            base_style = """
                QWidget {
                    background-color: #1a1a1a;
                    border: 1px solid #2a2a2a;
                    border-radius: 15px;
                }
                QWidget:hover {
                    border: 1px solid #3a3a3a;
                }
            """
            self.setStyleSheet(base_style)
            return
            
        if self.is_selected:
            self.setStyleSheet("""
                QWidget {
                    background-color: #1a1a1a;
                    border: 2px solid #e0e0e0;
                    border-radius: 15px;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #1a1a1a;
                    border: 1px solid #2a2a2a;
                    border-radius: 15px;
                }
                QWidget:hover {
                    border: 1px solid #404040;
                    background-color: #1e1e1e;
                }
            """)
            
    def select(self):
        """Mark this card as selected"""
        self.is_selected = True
        self.update_style()
        
    def deselect(self):
        """Mark this card as deselected"""
        self.is_selected = False
        self.update_style()
        
    def mousePressEvent(self, event):
        """Handle mouse click to select this card"""
        if not self.is_add_button and not self.is_skeleton:
            self.selected.emit(self)
        super().mousePressEvent(event)
    
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress and not self.is_add_button and not self.is_skeleton:
            self.selected.emit(self)
            return False
        return False
        
    def on_add_tracks_clicked(self):
        """Handle add tracks button click"""
        self.addTrackRequested.emit()
