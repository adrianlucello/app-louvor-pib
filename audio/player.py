import sounddevice as sd
import numpy as np
from scipy.io import wavfile
import threading
import os
import unicodedata
import re
import hashlib
from PyQt5.QtCore import QObject, pyqtSignal, QStandardPaths

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
        self.lr_enabled = False
        self.output_device = None
        self.input_device = None
        self._cache_dir = self._ensure_cache_dir()
        # Limiter controls
        self.limiter_enabled = True       # Apply protection only on the master bus
        self.per_track_limiter = False    # Avoid limiting each track to preserve dynamics
        self.master_threshold = 0.99      # Very high threshold; acts only on extreme peaks
        
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
                # Prefer cached optimized version if available
                cached = self._load_cached_optimized(file_path)
                if cached is not None:
                    sample_rate, samples = cached
                else:
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
                
            # Detect route hint for LR based on filename and audio characteristics
            left_hint = self._detect_left_route(file_path, samples)

            track = {
                'file_path': file_path,
                'sample_rate': sample_rate,
                'samples': samples,
                'volume': 0.8,  # 80% volume
                'muted': False,
                'left_hint': left_hint,
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

    def set_lr_mode(self, enabled: bool):
        """Enable/disable LR routing mode."""
        self.lr_enabled = bool(enabled)

    def set_output_device(self, device):
        try:
            print(f"[AudioPlayer] set_output_device called with: {device}")
            self.output_device = device
            # If there's an active stream, we need to stop it completely
            if self.stream:
                print(f"[AudioPlayer] Active stream found, stopping it")
                was_playing = self._is_playing and not self._is_paused
                current_pos = self.current_position
                
                # Stop the stream and wait for thread to finish
                try:
                    self.should_stop = True
                    self._is_playing = False
                    if self.stream:
                        self.stream.stop()
                        self.stream.close()
                        self.stream = None
                    # Wait for playback thread to finish
                    if self.playback_thread and self.playback_thread.is_alive():
                        self.playback_thread.join(timeout=0.5)
                    print(f"[AudioPlayer] Stream stopped successfully")
                except Exception as e:
                    print(f"[AudioPlayer] Error stopping stream: {e}")
                
                # Reset state and restart if it was playing
                self.should_stop = False
                if was_playing:
                    print(f"[AudioPlayer] Restarting playback with new device {device}")
                    self.current_position = current_pos
                    self._is_playing = True
                    self._is_paused = False
                    self._start_playback_thread()
            else:
                print(f"[AudioPlayer] No active stream, device set to {device}")
        except Exception as e:
            print(f"[AudioPlayer] Error in set_output_device: {e}")

    def set_input_device(self, device):
        try:
            self.input_device = device
        except Exception:
            pass

    def set_limiter_enabled(self, enabled: bool):
        try:
            self.limiter_enabled = bool(enabled)
        except Exception:
            pass

    def set_per_track_limiter(self, enabled: bool):
        try:
            self.per_track_limiter = bool(enabled)
        except Exception:
            pass

    def set_master_threshold(self, threshold: float):
        try:
            # Clamp to sensible range
            self.master_threshold = max(0.90, min(1.0, float(threshold)))
        except Exception:
            pass
            
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

    def seek_to_fraction(self, frac: float):
        """Seek to a position given by fraction (0..1) of the song length. Disabled while playing."""
        try:
            if self.is_playing():
                return False
            max_length = max(len(t['samples']) for t in self.tracks) if self.tracks else 0
            if max_length <= 0:
                return False
            frac = max(0.0, min(1.0, float(frac)))
            idx = int(frac * max_length)
            return self.seek_to_sample(idx)
        except Exception:
            return False

    def seek_to_sample(self, index: int):
        """Seek to a specific sample index. Disabled while playing."""
        try:
            if self.is_playing():
                return False
            max_length = max(len(t['samples']) for t in self.tracks) if self.tracks else 0
            if max_length <= 0:
                return False
            index = int(index)
            index = max(0, min(index, max_length - 1))
            self.current_position = index
            return True
        except Exception:
            return False
        
    def _playback_worker(self):
        """Worker function for audio playback in separate thread"""
        try:
            # Find the maximum length among all tracks
            max_length = max(len(track['samples']) for track in self.tracks) if self.tracks else 0
            
            # Use sample rate of first track (in a real app, you might want to resample)
            if not self.tracks:
                return
                
            sample_rate = self.tracks[0]['sample_rate']
            blocksize = 2048
            try:
                default_pair = sd.default.device
            except Exception:
                default_pair = None
            device_id = self.output_device
            if isinstance(device_id, str):
                try:
                    device_id = int(device_id)
                except Exception:
                    device_id = None
            devices = sd.query_devices()
            def _valid_out(idx):
                try:
                    return isinstance(idx, int) and 0 <= idx < len(devices) and int(devices[idx].get('max_output_channels', 0)) > 0
                except Exception:
                    return False
            if not _valid_out(device_id):
                candidate = default_pair[1] if default_pair else None
                device_id = candidate if _valid_out(candidate) else None
            out_channels = 2
            if _valid_out(device_id):
                try:
                    ch = int(devices[device_id].get('max_output_channels', 0))
                    out_channels = 2 if ch >= 2 else 1
                except Exception:
                    out_channels = 2
            else:
                try:
                    idx2 = next((i for i, d in enumerate(devices) if int(d.get('max_output_channels', 0)) >= 2), None)
                except Exception:
                    idx2 = None
                if idx2 is None:
                    try:
                        idx2 = next((i for i, d in enumerate(devices) if int(d.get('max_output_channels', 0)) >= 1), None)
                    except Exception:
                        idx2 = None
                device_id = idx2
                try:
                    ch = int(devices[device_id].get('max_output_channels', 0)) if device_id is not None else 2
                    out_channels = 2 if ch >= 2 else 1
                except Exception:
                    out_channels = 2
            
            # Create a callback function for audio playback
            def audio_callback(outdata, frames, time, status):
                try:
                    if self.should_stop or not self._is_playing:
                        raise sd.CallbackStop()
                        
                    mixed_audio = np.zeros((frames, out_channels), dtype=np.float32)
                    
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

                            # Apply LR routing if enabled
                            if self.lr_enabled:
                                if track.get('left_hint'):
                                    # Route only to left
                                    if track_samples.shape[1] >= 2:
                                        track_samples[:, 1] = 0.0
                                else:
                                    # Route only to right
                                    if track_samples.shape[1] >= 2:
                                        track_samples[:, 0] = 0.0
                            
                            # Optional: per-track limiter disabled by default to preserve dynamics
                            if self.per_track_limiter:
                                track_samples = self._apply_soft_limiter(track_samples, threshold=self.master_threshold, knee_width=0.08)
                            
                            # Calculate RMS volume level for this track
                            if len(track_samples) > 0:
                                rms = np.sqrt(np.mean(track_samples**2))
                                new_volume_levels.append(min(rms * 2.0, 1.0))  # Scale and clamp
                            else:
                                new_volume_levels.append(0.0)
                            
                            mix_end_idx = min(len(track_samples), len(mixed_audio))
                            if out_channels >= 2:
                                mixed_audio[:mix_end_idx] += track_samples[:mix_end_idx]
                            else:
                                mono = np.mean(track_samples[:mix_end_idx], axis=1)
                                mixed_audio[:mix_end_idx, 0] += mono
                        else:
                            new_volume_levels.append(0.0)
                    
                    # Update volume levels
                    self.volume_levels = new_volume_levels
                    
                    # Emit volume levels signal (this needs to be thread-safe)
                    try:
                        self.volumeLevelsChanged.emit(self.volume_levels)
                    except:
                        pass  # Ignore errors in signal emission
                    
                    # Apply protection only on the master bus (if enabled)
                    if self.limiter_enabled:
                        mixed_audio = self._apply_soft_limiter(mixed_audio, threshold=self.master_threshold, knee_width=0.10)
                    
                    # Final normalization to prevent clipping (with safety margin)
                    max_val = np.max(np.abs(mixed_audio))
                    if max_val > 1.0:
                        mixed_audio = mixed_audio * (1.0 / max_val)
                        
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
            kwargs = {
                'samplerate': int(sample_rate),
                'channels': int(out_channels),
                'callback': audio_callback,
                'blocksize': int(blocksize),
                'dtype': 'float32',
                'latency': 'high',
            }
            try:
                if _valid_out(device_id):
                    kwargs['device'] = device_id
                    print(f"[AudioPlayer] Creating stream with device_id: {device_id}")
                else:
                    print(f"[AudioPlayer] Creating stream with default device (device_id {device_id} not valid)")
            except Exception as e:
                print(f"[AudioPlayer] Error setting device in kwargs: {e}")
            self.stream = sd.OutputStream(**kwargs)
            self.stream.start()
            print(f"[AudioPlayer] Stream started successfully")
            
            
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

    def _ensure_cache_dir(self):
        try:
            base = QStandardPaths.writableLocation(QStandardPaths.CacheLocation)
            if not base:
                base = os.path.expanduser('~/Library/Caches/AppPythonAdrian')
            if not os.path.isdir(base):
                os.makedirs(base, exist_ok=True)
            audio_dir = os.path.join(base, 'audio_opt')
            if not os.path.isdir(audio_dir):
                os.makedirs(audio_dir, exist_ok=True)
            return audio_dir
        except Exception:
            audio_dir = os.path.expanduser('~/Library/Caches/AppPythonAdrian/audio_opt')
            try:
                os.makedirs(audio_dir, exist_ok=True)
            except Exception:
                pass
            return audio_dir

    def _cache_key_for(self, file_path):
        try:
            abs_path = os.path.abspath(file_path)
            stat = os.stat(abs_path)
            payload = f"{abs_path}|{int(stat.st_mtime)}|{int(stat.st_size)}"
            h = hashlib.sha1(payload.encode('utf-8')).hexdigest()
            return h
        except Exception:
            return hashlib.sha1(file_path.encode('utf-8')).hexdigest()

    def _cached_npz_path(self, file_path):
        key = self._cache_key_for(file_path)
        return os.path.join(self._cache_dir, f"{key}.npz")

    def _load_cached_optimized(self, file_path):
        try:
            npz_path = self._cached_npz_path(file_path)
            if os.path.exists(npz_path):
                data = np.load(npz_path)
                samples = data['samples']
                sample_rate = int(data['sample_rate'])
                if len(samples.shape) == 1:
                    samples = np.column_stack((samples, samples))
                return sample_rate, samples.astype(np.float32)
        except Exception:
            pass
        return None

    def replace_track_samples(self, file_path, sample_rate, samples):
        """Replace samples for a loaded track if present."""
        try:
            for t in self.tracks:
                if t.get('file_path') == file_path:
                    t['sample_rate'] = int(sample_rate or t.get('sample_rate', 44100))
                    if len(samples.shape) == 1:
                        samples = np.column_stack((samples, samples))
                    t['samples'] = samples.astype(np.float32)
                    break
        except Exception:
            pass

    def _normalize_text(self, s):
        try:
            s = s or ""
            s = unicodedata.normalize('NFD', s)
            s = ''.join(c for c in s if not unicodedata.combining(c))
            return s.lower()
        except Exception:
            return (s or "").lower()

    def _detect_left_route(self, file_path, samples):
        """Heurística: retorna True se deve ir para o canal esquerdo (click/guia/metronomo)."""
        try:
            name = self._normalize_text(os.path.basename(file_path))
            tokens = [t for t in re.split(r'[^a-z0-9]+', name) if t]

            # Palavras-chave explícitas para enviar à ESQUERDA (prioridade absoluta)
            force_left = {
                'click', 'clicktrack', 'clk', 'tempo',
                'metronome', 'metronomo', 'metron', 'metro',
                'guia', 'gui', 'guide'
            }
            if any((kw in name) or (kw in tokens) for kw in force_left):
                return True

            # Palavras-chave de vozes/coral para enviar à DIREITA (se não contiver guia)
            voice_right = {
                'bgv', 'bgvs', 'bvg', 'bvgs',
                'choir', 'coral', 'vox', 'voxes', 'vozes', 'voz',
                'voice', 'vocals', 'backing', 'backs',
                'soprano', 'tenor', 'alto', 'baritone', 'baritono', 'contralto',
                'lead', 'solo'
            }
            if any((kw in name) or (kw in tokens) for kw in voice_right):
                # Apenas envia para direita se não houver termos de guia explícitos
                if not any((kw in name) or (kw in tokens) for kw in {'guia', 'guide', 'gui'}):
                    return False

            # Instrumentos típicos: manter à DIREITA
            instrument_right = {
                'piano', 'keys', 'keyboard', 'synth', 'pad', 'organ', 'rhodes',
                'bass', 'baixo', 'sub',
                'drum', 'drums', 'kick', 'snare', 'hihat', 'hi-hat', 'tom', 'perc', 'percussion',
                'gtr', 'guitar', 'acoustic', 'electric', 'eletric', 'leadguitar', 'rhythm',
                'flute', 'strings', 'violin', 'violino', 'cello', 'sax', 'trumpet'
            }
            if any((kw in name) or (kw in tokens) for kw in instrument_right):
                return False
        except Exception:
            pass
        # Fallback simples por áudio: analisa blocos RMS para silêncio vs atividade
        try:
            if samples is None or len(samples) == 0:
                return False
            mono = samples
            if len(mono.shape) > 1:
                mono = np.mean(np.abs(mono), axis=1)
            else:
                mono = np.abs(mono)
            block = max(512, min(4096, len(mono)//100))
            if block <= 0:
                return False
            trim_len = (len(mono)//block)*block
            mono = mono[:trim_len]
            blocks = mono.reshape(-1, block)
            rms = np.sqrt(np.mean(blocks**2, axis=1))
            # Normaliza RMS
            max_r = rms.max() if rms.size > 0 else 1.0
            if max_r <= 0:
                return False
            nrms = rms / max_r
            # Fração de blocos "silenciosos"
            silence_ratio = float(np.mean(nrms < 0.06))
            # Se quase nunca fica em silêncio -> parece click constante
            if silence_ratio < 0.03:
                return True
            # Guia intermitente (alternância marcada): mais restrito para evitar false positives
            active_ratio = 1.0 - silence_ratio
            if 0.25 <= active_ratio <= 0.75 and np.std(nrms) > 0.12:
                return True
        except Exception:
            pass
        return False
                
    def _normalize_audio(self, samples):
        """Normalize audio to prevent clipping while maintaining dynamics"""
        if len(samples) == 0:
            return samples
            
        # Calculate the peak amplitude
        peak_amplitude = np.max(np.abs(samples))
        
        # If the peak is too high, normalize with a safety margin
        if peak_amplitude > 0.95:
            # Normalize to ~0.9 to leave modest headroom for mixing without sounding too quiet
            samples = samples * (0.9 / peak_amplitude)
            
        return samples

    def _apply_soft_limiter(self, samples, threshold=0.98, knee_width=0.10):
        """Apply a soft limiter on a stereo buffer.
        - threshold: level at which compression begins.
        - knee_width: knee softness for smoother onset.
        """
        if len(samples) == 0:
            return samples
            
        # Soft knee limiter
        abs_samples = np.abs(samples)
        mask = abs_samples > threshold
        if np.any(mask):
            excess = abs_samples[mask] - threshold
            compressed_excess = excess / (1 + (excess / knee_width) ** 2)
            compression_factor = (threshold + compressed_excess) / abs_samples[mask]
            samples[mask] = samples[mask] * compression_factor
        # Gentle hard cap
        samples = np.clip(samples, -1.0, 1.0)
        
        return samples

    # Removed old extreme peaks protection; master soft limiter suffices when enabled

    def get_volume_levels(self):
        """Get current volume levels for all tracks"""
        return self.volume_levels[:]
