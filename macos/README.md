# MACOS version

brew install hidapi libusb uv

uv run fosimc331-macos.py

Leave it running and it will monitor the port, and resend the command if it's disconnected and reconnected (eg rebooted)
