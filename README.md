# Audio Track Mixer Application

This is a PyQt5 application for managing and mixing audio tracks for worship services, with a professional UI/UX inspired by digital audio workstations like Reaper.

## Features

1. Create worship services with name and date
2. Add multiple songs with name, key, and BPM
3. Upload multiple audio tracks (WAV supported, MP3 experimental)
4. Real-time audio mixing capabilities
5. Professional DAW-style interface with song cards carousel
6. Individual track volume control with tall faders (0% at bottom, 100% at top)
7. Mute/Solo buttons for each track
8. Play/Stop all tracks simultaneously
9. Integrated VU meters within faders showing real-time audio activity

## UI/UX Highlights

- Dark theme interface similar to professional DAWs
- Horizontal carousel of square song cards for easy navigation
- Tall individual track faders with correct orientation (0% at bottom, 100% at top)
- Dark gray fader handles for consistent UI/UX
- Integrated VU meters within faders for precise audio level visualization
- Color-coded VU indicators (blue/yellow/red) for quick level recognition
- Clean, professional layout with proper spacing
- Ability to add tracks to existing songs

## Components

- `main.py`: Entry point of the application
- `ui/main_window.py`: Main application window with pencil button
- `ui/worship_form.py`: Form for entering worship service details
- `ui/song_form.py`: Form for adding songs and uploading tracks
- `ui/song_carousel.py`: Horizontal carousel for song navigation
- `ui/music_card.py`: Individual song cards with track information
- `ui/tracks_panel.py`: Panel for controlling individual audio tracks
- `audio/player.py`: Audio playback engine using sounddevice

## Requirements

- Python 3.6+
- PyQt5
- sounddevice
- numpy
- scipy
- QDarkStyle

## Installation

```bash
pip install -r requirements.txt
```

Note: For MP3 support, you may need additional libraries like pydub and ffmpeg.

## Usage

```bash
python main.py
```

1. Click the pencil button to create a new worship service
2. Enter the worship name and date
3. Add songs with their details using the "+ Add Song" button
4. Upload audio tracks (WAV format recommended) for each song
5. Navigate between songs using the carousel
6. Add additional tracks to existing songs
7. Adjust individual track volumes using the tall faders (move handle up to increase volume)
8. Click "Play All Tracks" to start playback and see real-time VU meters within faders

## Future Implementation

- Full MP3 support with pydub integration
- Waveform visualization with zoom capabilities
- Timeline management for sequencing songs
- Export functionality for Mac .app bundle
- Advanced audio effects (EQ, reverb, etc.)
- Multi-bus mixing capabilities
- Recording functionality