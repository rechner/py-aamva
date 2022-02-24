"""
apt install libhidapi-hidraw0
pip install hidapi
"""

import hid

vid = 0x05E0
pid = 0x0600


def blocking_scan(dev):
    buffer = b""
    while True:
        read = dev.read(32, timeout=1000)
        if read:
            buffer += read

        if b"\r\n" in buffer[-32:]:
            return buffer.strip(b"\0")


with hid.Device(vid, pid) as dev:
    print(f"Device manufacturer: {dev.manufacturer}")
    print(f"Product: {dev.product}")
    print(f"Serial Number: {dev.serial}")

    print(hid.enumerate(vid, pid))

    while True:
        print(blocking_scan())
