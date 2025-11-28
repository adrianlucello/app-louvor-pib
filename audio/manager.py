import threading
import time
from PyQt5.QtCore import QObject, pyqtSignal
from audio.player import AudioPlayer

class AudioManager(QObject):
    """Manager for handling audio playback across multiple songs"""
    
    # Signal emitted when playback state changes
    playbackStateChanged = pyqtSignal(bool)  # True if playing, False if stopped/paused
    
    def __init__(self):
        super().__init__()
        self.current_player = None
        self.players = {}  # Dictionary to store players for each song
        self.current_song = None
        self._is_playing = False
        self.lr_enabled = False
        self.output_device = None
        self.input_device = None
        
    def set_current_song(self, song_data):
        """Set the current song and initialize its audio player"""
        song_id = self._get_song_id(song_data)
        self.current_song = song_data
        
        # Create a new player for this song if it doesn't exist
        if song_id not in self.players:
            player = AudioPlayer()
            try:
                player.set_lr_mode(self.lr_enabled)
            except Exception:
                pass
            try:
                if self.output_device is not None:
                    player.set_output_device(self.output_device)
            except Exception:
                pass
            # Load all tracks for this song
            for track_path in song_data.get("tracks", []):
                player.load_track(track_path)
            self.players[song_id] = player
        else:
            player = self.players[song_id]
            
        self.current_player = player

    def reload_song_tracks(self, song_data):
        """Rebuild the player's tracks for a song, preferring cached optimized audio."""
        try:
            song_id = self._get_song_id(song_data)
            was_playing = self._is_playing and self.current_player and (self._get_song_id(self.current_song) == song_id)
            # Create a fresh player
            new_player = AudioPlayer()
            try:
                new_player.set_lr_mode(self.lr_enabled)
            except Exception:
                pass
            try:
                if self.output_device is not None:
                    new_player.set_output_device(self.output_device)
            except Exception:
                pass
            for track_path in song_data.get("tracks", []):
                new_player.load_track(track_path)
            # Replace in map
            self.players[song_id] = new_player
            # If this is the current song, swap current player
            if self.current_song and self._get_song_id(self.current_song) == song_id:
                self.current_player = new_player
                # Resume playback if it was playing
                if was_playing:
                    try:
                        self.current_player.play_all()
                        self._is_playing = True
                        self.playbackStateChanged.emit(True)
                    except Exception:
                        pass
        except Exception:
            pass

    def set_lr_mode(self, enabled: bool):
        """Enable/disable LR mode across all players"""
        self.lr_enabled = bool(enabled)
        for p in self.players.values():
            try:
                p.set_lr_mode(self.lr_enabled)
            except Exception:
                pass

    def set_output_device(self, device):
        print(f"[AudioManager] set_output_device called with: {device}")
        self.output_device = device
        # Store playback state before changing device
        was_playing = self._is_playing
        current_position = None
        
        # If currently playing, stop and save position
        if was_playing and self.current_player:
            try:
                print(f"[AudioManager] Stopping current playback to change device")
                current_position = self.current_player.current_position
                self.current_player.stop()
                # Wait for the playback thread to fully stop
                time.sleep(0.1)  # Small delay to ensure clean shutdown
            except Exception as e:
                print(f"[AudioManager] Error stopping playback: {e}")
        
        # Update device for all players
        for p in self.players.values():
            try:
                print(f"[AudioManager] Setting device {device} on player")
                p.set_output_device(device)
            except Exception as e:
                print(f"[AudioManager] Error setting device on player: {e}")
        
        # Resume playback if it was playing before
        if was_playing and self.current_player:
            try:
                print(f"[AudioManager] Resuming playback with new device")
                # Restore position if we saved it
                if current_position is not None:
                    self.current_player.current_position = current_position
                self.current_player.play_all()
                self._is_playing = True
                self.playbackStateChanged.emit(True)
            except Exception as e:
                print(f"[AudioManager] Error resuming playback: {e}")

    def set_input_device(self, device):
        self.input_device = device
        for p in self.players.values():
            try:
                p.set_input_device(device)
            except Exception:
                pass
        
    def play_current_song(self):
        """Play the current song"""
        if self.current_player:
            if hasattr(self.current_player, "is_paused") and self.current_player.is_paused():
                for player in self.players.values():
                    if player is not self.current_player:
                        player.stop()
                self.current_player.play_all()
                self._is_playing = True
                self.playbackStateChanged.emit(True)
            else:
                for player in self.players.values():
                    if player is not self.current_player:
                        player.stop()
                self.current_player.play_all()
                self._is_playing = True
                self.playbackStateChanged.emit(True)
            
    def pause_current_song(self):
        """Pause the current song"""
        if self.current_player and self._is_playing:
            self.current_player.pause()
            self._is_playing = False
            self.playbackStateChanged.emit(False)
            
    def stop_all(self):
        """Stop all playing songs"""
        for player in self.players.values():
            player.stop()
        self._is_playing = False
        self.playbackStateChanged.emit(False)
        
    def is_playing(self):
        """Check if any song is currently playing"""
        return self._is_playing and self.current_player and self.current_player.is_playing()
        
    def is_current_song(self, song_data):
        """Check if the given song is the current song"""
        if not self.current_song:
            return False
        return self._get_song_id(self.current_song) == self._get_song_id(song_data)
        
    def _get_song_id(self, song_data):
        """Generate a unique identifier for a song"""
        # Use song name and tracks to create a unique ID
        name = song_data.get("name", "")
        tracks = "|".join(song_data.get("tracks", []))
        return f"{name}:{tracks}"
        
    def cleanup(self):
        """Clean up all audio resources"""
        self.stop_all()
        self.players.clear()
        self.current_player = None
        self.current_song = None
