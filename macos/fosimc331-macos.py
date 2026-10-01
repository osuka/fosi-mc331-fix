import time

import hid
import usb.core


VENDOR_ID = 0x8888

PRODUCT_ID_USB = 0x1717
PRODUCT_ID_OPT = 0x171E

POLL_INTERVAL = 5
BOOT_DELAY = 3

COMMAND = bytes([
    0xA5, 0x5A, 0x88, 0x0B,
    0xFF, 0x00, 0x00, 0x70,
    0xE5, 0x03, 0x00, 0x05,
    0x00, 0x64, 0x00, 0x16,
])


def find_usb_device(pid):
    return usb.core.find(
        idVendor=VENDOR_ID,
        idProduct=pid,
    )


def get_active_pid():
    """
    Detect the current MC331 USB identity using PyUSB.

    0x1717 = USB audio mode
    0x171e = OPT / non-USB audio mode
    """
    if find_usb_device(PRODUCT_ID_OPT) is not None:
        return PRODUCT_ID_OPT

    if find_usb_device(PRODUCT_ID_USB) is not None:
        return PRODUCT_ID_USB

    return None


def disable_noise_gate_1717(silent=False):
    """
    USB audio mode.

    Uses HIDAPI:
      Report ID 0
      + 64-byte HID output report
      = 65 bytes passed to hid.write()
    """
    devices = hid.enumerate(
        VENDOR_ID,
        PRODUCT_ID_USB,
    )

    if not devices:
        if not silent:
            print(
                "[-] PID 0x1717 present but "
                "no HID interface found."
            )
        return False

    payload = b"\x00" + COMMAND
    payload = payload.ljust(65, b"\x00")

    for info in devices:
        path = info["path"]

        try:
            dev = hid.Device(path=path)

            result = dev.write(payload)

            dev.close()

            if result > 0:
                if not silent:
                    print(
                        f"[+] PID 0x1717: HID command sent "
                        f"(write={result}, bytes={len(payload)})"
                    )

                return True

        except Exception as e:
            if not silent:
                print(
                    f"[-] PID 0x1717 HID error on "
                    f"{path!r}: "
                    f"{type(e).__name__}: {e}"
                )

    return False


def disable_noise_gate_171e(silent=False):
    """
    OPT / non-USB audio mode.

    The 0x171e HID interface declares a 256-byte Output report
    and has no normal interrupt endpoint.

    Send HID SET_REPORT directly through endpoint 0 using PyUSB.
    """
    dev = find_usb_device(PRODUCT_ID_OPT)

    if dev is None:
        if not silent:
            print("[-] PID 0x171e not found.")
        return False

    payload = COMMAND.ljust(256, b"\x00")

    try:
        transferred = dev.ctrl_transfer(
            0x21,       # Host -> Device | Class | Interface
            0x09,       # HID SET_REPORT
            0x0200,     # Output report type 2, Report ID 0
            0,          # Interface 0
            payload,
        )

        success = transferred == len(payload)

        if not silent:
            if success:
                print(
                    f"[+] PID 0x171e: SET_REPORT sent "
                    f"({transferred}/{len(payload)} bytes)"
                )
            else:
                print(
                    f"[-] PID 0x171e: short SET_REPORT "
                    f"({transferred}/{len(payload)} bytes)"
                )

        return success

    except Exception as e:
        if not silent:
            print(
                f"[-] PID 0x171e SET_REPORT error: "
                f"{type(e).__name__}: {e}"
            )

        return False


def disable_noise_gate(pid, silent=False):
    if pid == PRODUCT_ID_USB:
        return disable_noise_gate_1717(
            silent=silent
        )

    if pid == PRODUCT_ID_OPT:
        return disable_noise_gate_171e(
            silent=silent
        )

    return False


def mode_name(pid):
    if pid == PRODUCT_ID_USB:
        return "USB audio"

    if pid == PRODUCT_ID_OPT:
        return "OPT / non-USB audio"

    return "unknown"


def main():
    last_pid = None

    print(
        "[*] Fosi MC331 noise-suppressor watcher started."
    )
    print(
        "[*] Supports PID 0x1717 and PID 0x171e."
    )
    print(
        f"[*] Poll interval: {POLL_INTERVAL}s"
    )
    print("[*] Ctrl+C to stop.")

    while True:
        try:
            current_pid = get_active_pid()

            #
            # Device disconnected or changed mode.
            #
            if current_pid != last_pid:

                if current_pid is None:
                    if last_pid is not None:
                        print(
                            "\n[-] Fosi MC331 disconnected."
                        )

                    last_pid = None

                else:
                    print(
                        f"\n[!] Fosi MC331 detected: "
                        f"{current_pid:#06x} "
                        f"({mode_name(current_pid)})"
                    )

                    print(
                        f"[*] Waiting {BOOT_DELAY}s "
                        "for MCU initialization..."
                    )

                    time.sleep(BOOT_DELAY)

                    if disable_noise_gate(
                        current_pid,
                        silent=False,
                    ):
                        print(
                            "[+] Noise suppressor disabled."
                        )
                    else:
                        print(
                            "[-] Failed to disable "
                            "noise suppressor."
                        )

                    last_pid = current_pid

            #
            # Same mode as previous poll.
            # Reapply silently because the setting
            # is not persistent.
            #
            elif current_pid is not None:

                disable_noise_gate(
                    current_pid,
                    silent=True,
                )

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\n[*] Watcher stopped.")
            break

        except Exception as e:
            print(
                f"\n[-] Watcher error: "
                f"{type(e).__name__}: {e}"
            )

            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
