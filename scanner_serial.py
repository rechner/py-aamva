import json
import os
import re
import webbrowser

import fhirclient.models.bundle as b
import requests
import serial
from fhirclient import models
from healthcards import parser, cvx

from aamva import AAMVA

eval_bool = lambda x: x.lower() in ('true', '1', 't', 'y', 'yes')

SERIAL_READ_TIMEOUT = 1
USE_HID = os.environ.get("USE_HID", False)

vid = hex(os.environ.get("VID", 0x05E0))
pid = hex(os.environ.get("PID", 0x0600))

if USE_HID:
    import hid

ISSUERS_URL = "https://raw.githubusercontent.com/the-commons-project/vci-directory/main/vci-issuers.json"

SHC_REGEX = re.compile(r"^[sS][hH][cC]:/")
URL_REGEX = re.compile(r"^https?://")


class Issuers(object):
    def __init__(self, local=False):
        if local:
            with open("vci-issuers.json") as f:
                vci_issuers = json.load(f)
        else:
            vci_issuers = requests.get(ISSUERS_URL).json()
        self.issuers = {
            row["iss"]: row["name"] for row in vci_issuers["participating_issuers"]
        }

    def lookup_url(self, url):
        return self.issuers.get(url)


def human_name(human_name_instance):
    if human_name_instance is None:
        return "???"

    parts = []
    for n in [human_name_instance.prefix, human_name_instance.given]:
        if n is not None:
            parts.extend(n)
    if human_name_instance.family:
        parts.append(human_name_instance.family)
    if human_name_instance.suffix and len(human_name_instance.suffix) > 0:
        if len(parts) > 0:
            parts[len(parts) - 1] = parts[len(parts) - 1] + ","
        parts.extend(human_name_instance.suffix)

    return " ".join(parts) if len(parts) > 0 else "Unnamed"


def decode_vaccinations(bundle):
    vaccinations = []
    for e in bundle.entry:
        if type(e.resource) == models.immunization.Immunization:
            decoded = cvx.CVX_CODES.get(int(e.resource.vaccineCode.coding[0].code))
            decoded["lotNumber"] = e.resource.lotNumber
            decoded["status"] = e.resource.status
            decoded["date"] = e.resource.occurrenceDateTime.isostring
            try:
                decoded["performer"] = e.resource.performer[0].actor.display
            except TypeError:
                decoded["performer"] = None

            vaccinations.append(dict(decoded))
    return vaccinations


def check_shc(barcode_data):
    # Unpack SHC payload to a JWS
    jws_str = parser.decode_qr_to_jws(barcode_data)

    # Decode the JWS
    jws = parser.JWS(jws_str)

    shc_dict = jws.as_dict()

    issuer = issuers.lookup_url(shc_dict["payload"]["iss"])
    shc_dict["verification"]["trusted"] = False
    if issuer:
        shc_dict["verification"]["trusted"] = True
        shc_dict["verification"]["issuer"] = issuer

    bundle = b.Bundle(shc_dict["payload"]["vc"]["credentialSubject"]["fhirBundle"])

    name = human_name(bundle.entry[0].resource.name[0])
    birthday = bundle.entry[0].resource.birthDate.isostring
    vaccines = decode_vaccinations(bundle)

    print(name, birthday)
    for vac in vaccines:
        print(f"{vac['date']}: {vac['name']}, Lot # {vac['lotNumber']}")
    print("Verified:", "✅" if shc_dict["verification"]["verified"] else "❌")
    print("Trusted: ", "✅" if shc_dict["verification"]["trusted"] else "❌")
    if "issuer" in shc_dict["verification"]:
        print("Issuer: ", shc_dict["verification"]["issuer"])


def read_until_timeout(ser):
    buffer = b""
    while True:
        char = ser.read(1)
        if char:
            buffer += char
        else:
            return buffer


def blocking_hid_scan(dev):
    buffer = b""
    while True:
        read = dev.read(32, timeout=1000)
        if read:
            buffer += read

        if b"\r\n" in buffer[-32:]:
            return buffer.strip(b"\0")


if __name__ == "__main__":
    if USE_HID:
        hid_dev = hid.Device(vid, pid)
    else:
        ser = serial.Serial(os.environ.get("SERIAL_DEVICE", "/dev/ttyACM0"), timeout=SERIAL_READ_TIMEOUT)

    issuers = Issuers()
    aamva = AAMVA()

    while True:
        try:
            if USE_HID:
                buffer = blocking_hid_scan(hid_dev)
            else:
                buffer = read_until_timeout(ser)
            if buffer:
                raw_input = buffer.decode("utf-8")
                if SHC_REGEX.match(raw_input):
                    check_shc(raw_input)

                elif URL_REGEX.match(raw_input):
                    webbrowser.open(raw_input)

                elif raw_input.startswith("@"):
                    dl = aamva.decode_barcode(raw_input)
                    print(f"{dl['first']} {dl['last']} {dl['dob'].isoformat()}")

                else:
                    print(raw_input)

        except KeyboardInterrupt:
            ser.close()
