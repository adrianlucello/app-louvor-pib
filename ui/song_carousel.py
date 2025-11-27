from PyQt5.QtWidgets import QWidget, QHBoxLayout, QScrollArea, QFrame
from PyQt5.QtCore import Qt, pyqtSignal
from ui.music_card import MusicCard

class SongCarousel(QWidget):
    # Signal emitted when a new song needs to be added
    addSongRequested = pyqtSignal()
    
    # Signal emitted when a song is selected
    songSelected = pyqtSignal(object)
    
    # Signal emitted when add tracks is requested for a song
    addTracksRequested = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.songs = []
        self.song_cards = []
        self.selected_card = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(40, 0, 40, 0)
        layout.setSpacing(15)
        
        # Scroll area for horizontal scrolling
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #252525;
                border: none;
                border-radius: 0px;
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
        
        # Container widget for cards
        self.container = QWidget()
        self.container.setStyleSheet("background-color: #252525; border-radius: 0px;")
        self.cards_layout = QHBoxLayout()
        self.cards_layout.setContentsMargins(80, 10, 80, 10)
        self.cards_layout.setSpacing(15)
        self.cards_layout.setAlignment(Qt.AlignHCenter)
        self.container.setLayout(self.cards_layout)
        
        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)
        
        self.setLayout(layout)
        
    def add_song(self, song_data):
        """Add a new song to the carousel"""
        self.songs.append(song_data)
        
        # Create card for the song
        card = MusicCard(song_data)
        card.selected.connect(self.on_card_selected)
        card.addTrackRequested.connect(lambda: self.on_add_tracks_requested(len(self.songs)-1))
        card.deleteRequested.connect(lambda: self.remove_song(len(self.songs)-1))
        self.song_cards.append(card)
        self.cards_layout.addWidget(card)
        
        # Select the newly added card
        self.select_card(card)
        
        # Emit song selected signal
        self.songSelected.emit(song_data)
        
    def remove_song(self, index):
        """Remove a song from the carousel"""
        if 0 <= index < len(self.songs):
            # Remove from data
            del self.songs[index]
            
            # Remove card
            card = self.song_cards.pop(index)
            card.deleteLater()
            
            # Update selection
            if self.selected_card == card:
                self.selected_card = None
                if self.song_cards:
                    self.select_card(self.song_cards[0])
                else:
                    # No more songs, emit None
                    self.songSelected.emit(None)
                    
    def select_card(self, card):
        """Select a card and deselect others"""
        # Deselect current card
        if self.selected_card:
            self.selected_card.deselect()
            
        # Select new card
        self.selected_card = card
        if card:
            card.select()
            
    def on_card_selected(self, card):
        """Handle card selection"""
        self.select_card(card)
        # Emit song selected signal
        if not card.is_add_button:
            index = self.song_cards.index(card)
            if 0 <= index < len(self.songs):
                self.songSelected.emit(self.songs[index])
        
    def on_add_requested(self):
        """Handle add button click"""
        self.addSongRequested.emit()
        
    def on_add_tracks_requested(self, song_index):
        """Handle add tracks request for a specific song"""
        if 0 <= song_index < len(self.songs):
            self.addTracksRequested.emit(self.songs[song_index])
        
    def get_selected_song(self):
        """Get the currently selected song data"""
        if self.selected_card and not self.selected_card.is_add_button:
            index = self.song_cards.index(self.selected_card)
            if 0 <= index < len(self.songs):
                return self.songs[index]
        return None
        
    def get_songs(self):
        """Get all songs"""
        return self.songs[:]
