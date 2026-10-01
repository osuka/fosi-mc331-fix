# Fedora permissions

sudo nvim /etc/udev/rules.d/70-fosi-mc331.rules

```
# Fosi MC331 - USB audio mode
SUBSYSTEM=="usb", ATTR{idVendor}=="8888", ATTR{idProduct}=="1717", TAG+="uaccess"

# Fosi MC331 - ACP / optical / non-USB-audio mode
SUBSYSTEM=="usb", ATTR{idVendor}=="8888", ATTR{idProduct}=="171e", TAG+="uaccess"

# HID raw interface used in 1717 mode
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="8888", ATTRS{idProduct}=="1717", TAG+="uaccess"

# Harmless to include in case another kernel exposes 171e as hidraw
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", ATTRS{idVendor}=="8888", ATTRS{idProduct}=="171e", TAG+="uaccess"
```

Reload the rules

```sh
sudo udevadm control --reload-rules
sudo udevadm trigger
```
