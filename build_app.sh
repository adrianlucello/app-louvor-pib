#!/bin/bash

# Create app bundle structure
mkdir -p AudioTrackMixer.app/Contents/MacOS
mkdir -p AudioTrackMixer.app/Contents/Resources

# Create Info.plist
cat > AudioTrackMixer.app/Contents/Info.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>English</string>
    <key>CFBundleExecutable</key>
    <string>AudioTrackMixer</string>
    <key>CFBundleIconFile</key>
    <string>app.icns</string>
    <key>CFBundleIdentifier</key>
    <string>com.example.AudioTrackMixer</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>AudioTrackMixer</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Copy Python files
cp -r main.py ui/ AudioTrackMixer.app/Contents/MacOS/

# Create executable script
cat > AudioTrackMixer.app/Contents/MacOS/AudioTrackMixer << EOF
#!/bin/bash
cd "\$(dirname "\$0")"
python3 main.py
EOF

# Make executable
chmod +x AudioTrackMixer.app/Contents/MacOS/AudioTrackMixer

echo "App bundle created: AudioTrackMixer.app"
echo "To use this app, you'll need to:"
echo "1. Install the required dependencies: pip3 install -r requirements.txt"
echo "2. Optionally add an icon file as Resources/app.icns"