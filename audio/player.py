import sounddevice as sd
import numpy as np
from scipy.io import wavfile
import threading
import os
from PyQt5.QtCore import QObject, pyqtSignal

class AudioPlayer(QObject):
    # Signal emitted when volume levels change (for VU meter updates)
    volumeLevelsChanged = pyqtSignal(list)  # List of volume levels for each track
    
    def __init__(self):
        super().__init__()
        self.tracks = []
        self._is_playing = False
        self._is_paused = False
        self.stream = None
        self.current_position = 0
        self.volume_levels = []  # Store current volume levels for VU meters
        self.playback_thread = None
        self.should_stop = False
        
    def load_track(self, file_path):
        """Load an audio track from file"""
        try:
            # Check file extension
            if file_path.lower().endswith('.mp3'):
                # For MP3 files, we'll need to convert them to WAV first
                # In a real application, you might want to use a library like pydub
                # But since we're having issues with pydub, we'll skip MP3 for now
                print(f"MP3 support not available. Skipping {file_path}")
                return False
            elif file_path.lower().endswith('.wav'):
                sample_rate, samples = wavfile.read(file_path)
                # Ensure samples are in float format
                if samples.dtype != np.float32 and samples.dtype != np.float64:
                    samples = samples.astype(np.float32) / 32768.0
                    
                # If mono, convert to stereo
                if len(samples.shape) == 1:
                    samples = np.column_stack((samples, samples))
                
                # Apply normalization to prevent clipping in source files
                samples = self._normalize_audio(samples)
            else:
                raise ValueError("Unsupported file format")
                
            track = {
                'file_path': file_path,
                'sample_rate': sample_rate,
                'samples': samples,
                'volume': 0.8,  # 80% volume
                'muted': False
            }
            
            self.tracks.append(track)
            return True
        except Exception as e:
            print(f"Error loading track {file_path}: {e}")
            return False
            
    def set_volume(self, track_index, volume):
        """Set volume for a specific track (0.0 to 1.0)"""
        if 0 <= track_index < len(self.tracks):
            self.tracks[track_index]['volume'] = volume
            
    def set_mute(self, track_index, muted):
        """Mute/unmute a specific track"""
        if 0 <= track_index < len(self.tracks):
            self.tracks[track_index]['muted'] = muted
            
    def play_all(self):
        """Play all loaded tracks simultaneously"""
        if not self.tracks:
            return
            
        # If we're paused, just resume
        if self._is_paused:
            self._is_paused = False
            self._is_playing = True
            # Recreate and restart the stream when resuming
            if self.stream:
                try:
                    self.stream.stop()
                    self.stream.close()
                except:
                    pass
                self.stream = None
            
            # Start playback in a separate thread to avoid blocking UI
            self._start_playback_thread()
            return
            
        # If already playing, don't start again
        if self._is_playing:
            return
            
        self._is_playing = True
        self._is_paused = False
        self.should_stop = False
        # Initialize volume levels
        self.volume_levels = [0.0] * len(self.tracks)
        
        # Start playback in a separate thread to avoid blocking UI
        self._start_playback_thread()
        
    def _start_playback_thread(self):
        """Start the playback thread"""
        self.playback_thread = threading.Thread(target=self._playback_worker)
        self.playback_thread.daemon = True
        self.playback_thread.start()

    def pause(self):
        """Pause playback"""
        if self._is_playing and not self._is_paused:
            self._is_playing = False
            self._is_paused = True
            # Stop the stream when pausing
            if self.stream:
                try:
                    self.stream.stop()
                except:
                    pass
                    
    def stop(self):
        """Stop playback and reset position"""
        self.should_stop = True
        self._is_playing = False
        self._is_paused = False
        self.current_position = 0
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)  # Wait up to 1 second for thread to finish
            
    def is_playing(self):
        """Check if tracks are currently playing"""
        return self._is_playing and not self._is_paused
        
    def is_paused(self):
        """Check if tracks are currently paused"""
        return self._is_paused
        
    def _playback_worker(self):
        """Worker function for audio playback in separate thread"""
        try:
            # Find the maximum length among all tracks
            max_length = max(len(track['samples']) for track in self.tracks) if self.tracks else 0
            
            # Use sample rate of first track (in a real app, you might want to resample)
            if not self.tracks:
                return
                
            sample_rate = self.tracks[0]['sample_rate']
            blocksize = 1024
            
            # Create a callback function for audio playback
            def audio_callback(outdata, frames, time, status):
                try:
                    if self.should_stop or not self._is_playing:
                        raise sd.CallbackStop()
                        
                    # Initialize output buffer
                    mixed_audio = np.zeros((frames, 2), dtype=np.float32)
                    
                    # Calculate volume levels for each track
                    new_volume_levels = []
                    
                    # Mix all tracks
                    for i, track in enumerate(self.tracks):
                        if not track['muted'] and self.current_position < len(track['samples']):
                            # Get samples for this track at the current position
                            start_idx = self.current_position
                            end_idx = min(start_idx + frames, len(track['samples']))
                            track_samples = track['samples'][start_idx:end_idx]
                            
                            # Apply volume
                            track_samples = track_samples * track['volume']
                            
                            # Prevent clipping by applying a soft limiter
                            track_samples = self._apply_soft_limiter(track_samples)
                            
                            # Additional protection against extreme peaks
                            track_samples = self._protect_against_extreme_peaks(track_samples)
                            
                            # Calculate RMS volume level for this track
                            if len(track_samples) > 0:
                                rms = np.sqrt(np.mean(track_samples**2))
                                new_volume_levels.append(min(rms * 2.0, 1.0))  # Scale and clamp
                            else:
                                new_volume_levels.append(0.0)
                            
                            # Add to mixed audio
                            mix_end_idx = min(len(track_samples), len(mixed_audio))
                            mixed_audio[:mix_end_idx] += track_samples[:mix_end_idx]
                        else:
                            new_volume_levels.append(0.0)
                    
                    # Update volume levels
                    self.volume_levels = new_volume_levels
                    
                    # Emit volume levels signal (this needs to be thread-safe)
                    try:
                        self.volumeLevelsChanged.emit(self.volume_levels)
                    except:
                        pass  # Ignore errors in signal emission
                    
                    # Apply multiple stages of protection to prevent clipping
                    mixed_audio = self._apply_soft_limiter(mixed_audio)
                    mixed_audio = self._protect_against_extreme_peaks(mixed_audio)
                    
                    # Final normalization to prevent clipping (with safety margin)
                    max_val = np.max(np.abs(mixed_audio))
                    if max_val > 0.95:  # Safety margin to prevent clipping
                        mixed_audio = mixed_audio * (0.95 / max_val)
                        
                    outdata[:] = mixed_audio
                    
                    # Move to next position
                    self.current_position += frames
                    
                    # Stop when we've played all samples
                    if self.current_position >= max_length:
                        self._is_playing = False
                        self._is_paused = False
                        raise sd.CallbackStop()
                except Exception as e:
                    print(f"Error in audio callback: {e}")
                    
            # Start playback - using the original approach that worked
            self.stream = sd.OutputStream(
                samplerate=sample_rate,
                channels=2,
                callback=audio_callback,
                blocksize=blocksize
            )
            self.stream.start()
            
            # Keep the stream alive while playing (but not while paused)
            while self._is_playing and not self.should_stop:
                sd.sleep(100)  # Small delay to prevent busy waiting
                
        except Exception as e:
            print(f"Error during playback: {e}")
        finally:
            self._is_playing = False
            self.should_stop = False
            # Clean up stream
            if self.stream:
                try:
                    self.stream.stop()
                    self.stream.close()
                except:
                    pass
                self.stream = None
                
    def _normalize_audio(self, samples):
        """Normalize audio to prevent clipping while maintaining dynamics"""
        if len(samples) == 0:
            return samples
            
        # Calculate the peak amplitude
        peak_amplitude = np.max(np.abs(samples))
        
        # If the peak is too high, normalize with a safety margin
        if peak_amplitude > 0.9:
            # Normalize to 0.7 to leave headroom for mixing
            samples = samples * (0.7 / peak_amplitude)
            
        return samples

    def _apply_soft_limiter(self, samples):
        """Apply a soft limiter to prevent clipping while maintaining audio quality"""
        if len(samples) == 0:
            return samples
            
        # Pre-normalization to prevent extreme peaks
        samples = self._normalize_audio(samples)
        
        # Soft knee limiter to prevent harsh clipping
        threshold = 0.8  # Lower threshold for more conservative limiting
        knee_width = 0.1  # Width of the knee for smooth limiting
        
        # Calculate absolute values
        abs_samples = np.abs(samples)
        
        # Apply soft limiting only to samples that exceed the threshold
        mask = abs_samples > threshold
        if np.any(mask):
            # For samples exceeding threshold, apply soft knee compression
            excess = abs_samples[mask] - threshold
            # Soft knee compression formula with stronger compression
            compressed_excess = excess / (1 + (excess / knee_width) ** 3)  # Cubic compression
            # Apply compression to maintain audio quality
            compression_factor = (threshold + compressed_excess) / abs_samples[mask]
            samples[mask] = samples[mask] * compression_factor
            
        # Hard limit to prevent any samples from exceeding 1.0
        samples = np.clip(samples, -1.0, 1.0)
        
        return samples

    def _protect_against_extreme_peaks(self, samples):
        """Additional protection against extreme peaks that could cause distortion"""
        if len(samples) == 0:
            return samples
            
        # Apply a gentle high-shelf filter to reduce harshness in extreme highs
        # This helps with sibilance and harsh transients
        samples = np.clip(samples, -1.0, 1.0)
        
        # Apply a very gentle compression to extreme peaks only
        extreme_threshold = 0.95
        abs_samples = np.abs(samples)
        extreme_mask = abs_samples > extreme_threshold
        
        if np.any(extreme_mask):
            # Gentle compression for extreme peaks
            reduction_factor = 0.7
            samples[extreme_mask] = samples[extreme_mask] * reduction_factor + (
                samples[extreme_mask] * (1 - reduction_factor) * (extreme_threshold / abs_samples[extreme_mask])
            )
            
        return samples

    def get_volume_levels(self):
        """Get current volume levels for all tracks"""
        return self.volume_levels[:]
