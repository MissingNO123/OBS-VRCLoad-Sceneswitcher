# OBS VRC Load Scene Switcher

An OBS Studio script that automatically switches scenes when entering a loading screen in VRChat, and switches it back when done.

## Requirements
- Python 3.6+ installed and added to PATH (on Windows, ensure the "Add Python 3.x to PATH" option is checked during installation).
- OBS Studio

## Installation
1. Download `vrcload-sceneswitcher.py` from this repository.
2. In OBS Studio, go to Tools > Scripts.
3. Click the "+" button and add `vrcload-sceneswitcher.py`.

## Usage
0. Make sure Logging is enabled in VRChat!
1. Set the "Loading" and "Default" scenes to switch to. There is an option to automatically return to the last scene you had active before entering the loading screen.
2. Optionally, set the path to the folder your VRChat logs are output to. This is automatically set to the default directory on Windows and Linux (Proton).
3. Optionally, change the update interval.
4. The script will listen for VRChat log events and automatically switch scenes.
5. You can disable it using the checkbox in the script's properties.

## Demo
https://github.com/user-attachments/assets/74e36e11-0b14-4299-9628-157dfd953cda

