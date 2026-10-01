import time
import hid
import usb.core

VENDOR_ID = 0x8888
PRODUCT_ID_USB = 0x1717
PRODUCT_ID_ACP = 0x171E

POLL_INTERVAL = 5
BOOT_DELAY = 3

# Actual MC331 DSP command, without a synthetic HID report-ID byte.
COMMAND = bytes([
    0xA5, 0x5A, 0x88, 0x0B, 0xFF, 0x00, 0x00,
    0x70, 0xE5, 0x03, 0x00, 0x05, 0x00, 0x64, 0x00, 0x16
])


def find_usb_device(pid):
    """Find the MC331 directly through libusb/PyUSB."""
    return usb.core.find(
        idVendor=VENDOR_ID,
        idProduct=pid,
    )


def get_active_pid():
    """
    Detect the current MC331 USB personality.

    PyUSB is used here rather than hid.enumerate(), because Fedora does not
    expose the 171e zero-endpoint HID interface through hidraw/HIDAPI.
    """
    if find_usb_device(PRODUCT_ID_ACP) is not None:
        return PRODUCT_ID_ACP

    if find_usb_device(PRODUCT_ID_USB) is not None:
        return PRODUCT_ID_USB

    return None


def disable_noise_gate_1717(silent=False):
    """
    USB-audio mode: PID 1717.

    In this mode Fedora exposes a normal hidraw interface, so use the
    Python 'hid' package.

    hid.Device.write() expects the first byte to be the HID report ID.
    Report ID 0 is represented by a leading 0x00.
    """

    devices = hid.enumerate(VENDOR_ID, PRODUCT_ID_USB)

    if not devices:
        if not silent:
            print("[-] PID 1717 presente ma nessuna interfaccia HID trovata.")
        return False

    # 1-byte report ID + 64-byte HID report.
    payload = b"\x00" + COMMAND
    payload = payload.ljust(65, b"\x00")

    success_count = 0

    for info in devices:
        path = info["path"]

        try:
            device = hid.Device(path=path)

            result = device.write(payload)

            device.close()

            success_count += 1

            if not silent:
                print(
                    f"[+] PID 1717: payload inviato a {path!r}"
                    f" (write={result!r})"
                )

        except Exception as e:
            if not silent:
                print(
                    f"[-] PID 1717: errore su {path!r}: "
                    f"{type(e).__name__}: {e}"
                )

    return success_count > 0


def disable_noise_gate_171e(silent=False):
    """
    Non-USB-audio mode: PID 171e.

    The 171e HID descriptor has zero interrupt endpoints, so Fedora does
    not expose it through hidraw. Send HID SET_REPORT directly over USB
    endpoint 0 using a class control transfer.

    Descriptor:
      Report Size  = 8 bits
      Report Count = 256
      Output report = 256 bytes
    """

    dev = find_usb_device(PRODUCT_ID_ACP)

    if dev is None:
        if not silent:
            print("[-] PID 171e non trovato.")
        return False

    # The 171e HID descriptor declares a 256-byte Output report.
    payload = COMMAND.ljust(256, b"\x00")

    try:
        transferred = dev.ctrl_transfer(
            0x21,       # Host -> Device | Class | Interface
            0x09,       # HID SET_REPORT
            0x0200,     # Output report (2), Report ID 0
            0,          # Interface 0
            payload,
        )

        if not silent:
            print(
                f"[+] PID 171e: SET_REPORT inviato "
                f"({transferred}/{len(payload)} bytes)"
            )

        return transferred == len(payload)

    except Exception as e:
        if not silent:
            print(
                f"[-] PID 171e: errore SET_REPORT: "
                f"{type(e).__name__}: {e}"
            )

        return False


def disable_noise_gate(pid, silent=False):
    """Dispatch to the correct transport for the active MC331 mode."""

    if pid == PRODUCT_ID_USB:
        return disable_noise_gate_1717(silent=silent)

    if pid == PRODUCT_ID_ACP:
        return disable_noise_gate_171e(silent=silent)

    return False


def main():
    last_pid = None

    print("[*] Fosi MC331 noise-gate watcher avviato.")
    print("[*] Monitoraggio continuo attivo.")
    print("[*] Ctrl+C per terminare.")

    while True:
        try:
            current_pid = get_active_pid()

            # Device appeared or changed personality.
            if current_pid != last_pid:
                if current_pid is None:
                    print("\n[-] Fosi Audio scollegato.")

                else:
                    mode = (
                        "USB audio"
                        if current_pid == PRODUCT_ID_USB
                        else "ACP / OPT / non-USB audio"
                    )

                    print(
                        f"\n[!] Fosi Audio rilevato: "
                        f"PID {hex(current_pid)} ({mode})"
                    )

                    print(
                        f"[*] Attesa inizializzazione MCU "
                        f"({BOOT_DELAY}s)..."
                    )

                    time.sleep(BOOT_DELAY)

                    if disable_noise_gate(current_pid, silent=False):
                        print("[+] Noise suppressor command inviato.")
                    else:
                        print("[-] Invio del comando fallito.")

                last_pid = current_pid

            # Device remains connected: reapply periodically.
            elif current_pid is not None:
                disable_noise_gate(current_pid, silent=True)

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\n[*] Watcher terminato.")
            break

        except Exception as e:
            print(
                f"\n[-] Errore nel loop principale: "
                f"{type(e).__name__}: {e}"
            )
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
