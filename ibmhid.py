"""
apt install libhidapi-hidraw0
pip install hid
"""
from healthcards import parser
from pprint import pprint
import hid

vid = 0x05e0
pid = 0x0600


def blocking_scan(dev):
    buffer = b""
    while True:
        read = dev.read(65, timeout=1000)
        if read:
            buffer += read[1:]
            # print(buffer)
            if read[-8:] == b"\x00" * 8:
                return buffer.strip(b"\x00")[2:]


with hid.Device(vid, pid) as dev:
    print(f'Device manufacturer: {dev.manufacturer}')
    print(f'Product: {dev.product}')
    print(f'Serial Number: {dev.serial}')

    print(hid.enumerate(vid, pid))

    while True:
        raw_scan = blocking_scan(dev).decode("latin_1")
        if raw_scan[:5] == "shc:/":
            jws_string = parser.decode_qr_to_jws(raw_scan)
            jws = parser.JWS(jws_string)
            print(f"Verified: {jws.verified}")
            pprint(jws.as_dict())
        else:
            print(raw_scan)
