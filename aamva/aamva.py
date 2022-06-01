# aamva.py
#
# Copyright © 2022 Rechner Fox <rechner@totallylegit.agency>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.

# Simple class for decoding information from an AMVAA-compliant driver's
# license, either from a magstripe or PDF417 barcode (or potentailly
# a SmartCard, although no implementations currently exist).

# WARNING:  Use of the information from machine-legible formats on
# a North-American identification card is subject to compliance with
# 18 U.S.C. chapter 123, §2721, available here:
# (http://uscode.house.gov/download/pls/18C123.txt)  The author of this
# code claims no responsibility for it's use contrary to this or any
# later act, law, or jurisdiction.  In most cases you must obtain
# written permission from the license holder to compile or /share/ a
# database of information obtained from their machine-readable
# information.  For example, it is legal to make a private database of
# this information to prevent check fraud or process credit-cards, but
# it may not be used to create a mailing list without permission.  You
# are responsible for maintaining compliance or risk fines of up to
# $5,000 per day of non-compliance in the US.  Individual states may
# have their own restrictions on swiping as well: at the time of
# writing,  S.B. No. 1445 applies to the state of Texas:
# http://www.legis.state.tx.us/tlodocs/78R/billtext/html/SB01445F.htm

# TODO: Implement reading in straight from the device instead of just
# keyboard support: http://blog.flip-edesign.com/_rst/MagTek_USB_Card_Reader_Hacking_with_Python.html
# TODO: Add federal commercial driving codes "DCH" to all versions.

import datetime

debug = False

if debug:
    import pprint

""" Constants and signals """  # Better way to do this?
ANY = 0
MAGSTRIPE = 1
PDF417 = 2
SMARTCARD = 4
METRIC = "ISO"
IMPERIAL = "USA"
MALE = "M"
FEMALE = "F"
NOT_SPECIFIED = "X"
DRIVER_LICENSE = "DL"
IDENTITY_CARD = "ID"
EYECOLOURS = ["BLK", "BLU", "BRO", "GRY",
              "HAZ", "MAR", "PNK", "DIC", "UNK", "GRN"]
HAIRCOLOURS = ["BAL", "BLK", "BLN", "BRO", "GRY", "RED", "SDY", "WHI", "UNK"]
# Human-readable weight ranges
METRIC_WEIGHTS = {
    0: "0 - 31 kg",
    1: "32 - 45 kg",
    2: "46 - 59 kg",
    3: "60 - 70 kg",
    4: "71 - 86 kg",
    5: "87 - 100 kg",
    6: "101 - 113 kg",
    7: "114 - 127 kg",
    8: "128 - 145 kg",
    9: "146+ kg",
}
IMPERIAL_WEIGHTS = {
    0: "0 - 70 lbs",
    1: "71 - 100 lbs",
    2: "101 - 130 lbs",
    3: "131 - 160 lbs",
    4: "161 - 190 lbs",
    5: "191 - 220 lbs",
    6: "221 - 250 lbs",
    7: "251 - 280 lbs",
    8: "281 - 320 lbs",
    9: "321+ lbs",
}

# PDF417 format specifications and validations
PDF_LINEFEED = "\x0A"  # '\n' (line feed)
PDF_RECORDSEP = "\x1E"  # record seperator
PDF_SEGTERM = "\x0D"  # '\r' segment terminator (carriage return)
PDF_FILETYPE = "ANSI "  # identifies the file as an AAMVA compliant
PDF_VERSIONS = list(range(64))  # decimal between 0 - 63
PDF_ENTRIES = list(range(1, 100))  # decimal number of subfile identifiers

ISSUERS = {
    636033: "Alabama",
    646059: "Alaska",
    604427: "American Samoa",
    604430: "Northern Marianna Islands",
    604433: "Nunavut",
    636026: "Arizona",
    636021: "Arkansas",
    636028: "British Columbia",
    636014: "California",
    636056: "Caohulia",
    636020: "Colorado",
    636006: "Connecticut",
    636043: "District of Columbia",
    636011: "Delaware",
    636010: "Florida",
    636055: "Georgia",
    636019: "Guam",
    636047: "Hawaii",
    636057: "Hidalgo",
    636050: "Idaho",
    636035: "Illinois",
    636037: "Indiana",
    636018: "Iowa",
    636022: "Kansas",
    636046: "Kentucky",
    636007: "Louisiana",
    636041: "Maine",
    636048: "Manitoba",
    636003: "Maryland",
    636002: "Massachusetts",
    636032: "Michigan",
    636038: "Minnesota",
    636051: "Mississippi",
    636030: "Missouri",
    636008: "Montana",
    636054: "Nebraska",
    636049: "Nevada",
    636017: "New Brunswick",
    636039: "New Hampshire",
    636036: "New Jersey",
    636009: "New Mexico",
    636001: "New York",
    636016: "Newfoundland",
    636004: "North Carolina",
    636034: "North Dakota",
    636013: "Nova Scotia",
    636023: "Ohio",
    636058: "Oklahoma",
    636012: "Ontario",
    636029: "Oregon",
    636025: "Pennsylvania",
    604426: "Prince Edward Island",
    604428: "Quebec",
    636052: "Rhode Island",
    636044: "Saskatchewan",
    636005: "South Carolina",
    636042: "South Dakota",
    636053: "Tennessee",
    636027: "State Department (USA)",
    636015: "Texas",
    636062: "US Virgin Islands",
    636040: "Utah",
    636024: "Vermont",
    636000: "Virginia",
    636045: "Washington",
    636061: "West Virginia",
    636031: "Wisconsin",
    636060: "Wyoming",
    604429: "Yukon",
}


class AAMVA:
    def __init__(self, data=None, format=[ANY], strict=True):
        self.format = format
        assert not isinstance(format, str)
        self.data = data
        self.strict = strict

    def decode(self, data=None):
        """
        Decodes data from a string and returns a dictionary of values.
        Data is decoded in the format preference specified in the constructor.
        Missing or empty fields will usually be represented by 'None' type.
        Note that the issue date is missing from the magstripe encoding, and
        will always be represented by 'None'.
        """
        if data is None:
            data = self.data
        if data is None:
            raise ValueError("No data to parse")

        for form in self.format:
            if form == ANY or form == MAGSTRIPE:
                try:
                    return self.decode_magstripe(data)
                except (IndexError, AssertionError) as e:
                    if form == MAGSTRIPE:
                        raise ReadError(e)
                    # fail silently and continue to the next format
            if form == ANY or form == PDF417:
                # ~ pprint.pprint(data)
                # ~ return self.decode_barcode(data)
                try:
                    return self.decode_barcode(data)
                except (IndexError, AssertionError, ReadError) as e:
                    log(e)
                    raise ReadError("Unable to decode as barcode")

    def decode_magstripe(self, data):
        fields = data.split("^")  # split the field seperators
        # check for start of sentinel character
        assert fields[0][0] == "%", "Missing start sentinel character (%)"
        assert fields[0][0:3] != "%E?", "Error reading card"

        state = fields[0][1:3]
        city = fields[0][3:16]
        if len(city) == 13 and "^" not in city:
            # City maxes out at 13 characters, and excludes the field
            # separator.  Thus, name will be in the first field.
            # city+name+address together should be no longer than 77 chars.
            name_pre = fields[0][16:]
            address = fields[1].split("$")
            # track 2 data will be one behind in this case
            remaining = fields[2]
        else:
            name_pre = fields[1]
            address = fields[2].split("$")[0]
            remaining = fields[3]  # track 2 & 3

        assert len(name_pre) > 0, "Empty name field"
        assert "$" in name_pre, "Name field missing delimiter ($)"
        # entire name field is 35 characters with delimiters
        name = name_pre.split("$")
        middle = None
        if len(name) == 3:
            middle = name[2]

        remaining = remaining.split("?")[1:3]  # remove prepended end sentinel

        # track 2 start sentinel character
        assert remaining[0][0] == ";", "Missing track 2 start sentinel (;)"
        track2 = remaining[0].strip(";")
        track2 = track2.split("=")
        track3 = remaining[1]

        assert len(track2) == 2 or len(track2) == 3, "Invalid track 2 length"
        issue_identifier = track2[0][0:6]
        if len(track2) == 3:
            # up to 13 digits, overflow for more at end of track 2.
            # in this case there's no overflow, indicated by the extra = seperator.
            license_number = track2[0][6:20]
        else:
            license_number = track2[0][6:20] + track2[1][13:25]

        expiry_str = track2[1][0:4]  # e.g. 1310 for 31 October 2013
        expiry = datetime.date(
            2000 + int(expiry_str[0:2]), int(expiry_str[2:4]) + 1, 1
        ) - datetime.timedelta(days=1)

        dob_str = track2[1][4:12]  # e.g. 19850215
        dob = datetime.date(int(dob_str[0:4]), int(
            dob_str[4:6]), int(dob_str[6:8]))

        # parse track3:
        template = track3[
            1:2
        ]  # FIXME: according to A.4.3 should only be 0,2 but mine says 1
        security = track3[
            2:3
        ]  # FIXME: docs says 1 character long but says 00-63 are valid values.
        postal_code = track3[3:14].strip()  # remove space padding
        license_class = track3[14:16].strip()
        restrictions = track3[16:26].strip()
        endorsements = track3[26:30].strip()  # according to ANSI-20 4.11.7
        sex = track3[30:31]
        height = track3[31:34].strip()
        weight = track3[34:37].strip()  # lbs for US, kg for CA/MX
        hair = track3[37:40]
        eyes = track3[40:43]

        # assert 'F' in sex or 'M' in sex, "Invalid sex %s" % sex
        #assert height.isdigit() or height == "", "Invalid height"
        #assert weight.isdigit() or weight == "", "Invalid weight"
        # assert hair in HAIRCOLOURS, "Invalid hair colour %s" % hair
        # assert eyes in EYECOLOURS, "Invalid eye colour %s" % eyes

        # Since there's no way to determine if a magstripe is for USA or
        # Canada, we'll just have to set a default and assume units:
        # cast weight to Weight() type:
        if weight != "":
            weight = Weight(None, int(weight), "USA")
        else:
            weight is None
        # cast height (Also assumes no one is taller than 9'11"
        height = Height((int(height[0]) * 12) + int(height[1:]), "USA")

        return {
            "first": name[1],
            "last": name[0],
            "middle": middle,
            "city": city,
            "state": state,
            "address": address,
            "IIN": issue_identifier,
            "license_number": license_number,
            "expiry": expiry,
            "dob": dob,
            "ZIP": postal_code,
            "class": license_class,
            "restrictions": restrictions,
            "endorsements": endorsements,
            "sex": sex,
            "height": height,
            "weight": weight,
            "hair": hair,
            "eyes": eyes,
            "issued": None,
            "units": IMPERIAL,
            "suffix": None,
            "prefix": None,
        }

    def decode_barcode(self, data):
        # header
        segterm = PDF_SEGTERM

        # strip all before compliance character:
        data = "@" + "@".join(data.split("@")[1:])
        # check for compliance character:
        assert data[0] == "@", "Missing compliance character (@)"
        assert data[1] == PDF_LINEFEED, "Missing data element separator (LF)"
        if data[2] == "\x1C":
            # SCDMV sample deviates from standard here
            log("RECORDSEP (0x1E) missing, got FS instead (0x1C, SCDMV)")
            # segterm = '\x0a' # Have to override to work with SC old format
        else:
            assert (
                data[2] == PDF_RECORDSEP
            ), "Missing record separator (RS) got (%s)" % repr(data[2])
        assert data[3] == PDF_SEGTERM, "Missing segment terminator (CR)"
        assert (data[4:9] == PDF_FILETYPE) or (data[4:9] == "AAMVA"), (
            'Wrong file type (got "%s", should be "ANSI ")' % data[4:9]
        )
        issue_identifier = data[9:15]
        assert issue_identifier.isdigit(), "Issue Identifier is not an integer"
        version = int(data[15:17])
        assert version in PDF_VERSIONS, (
            "Invalid data version number (got %s, should be 0 - 63)" % version
        )

        log("Format version: " + str(version))

        parsed_data = ""
        subfiles_raw = []
        rev_offset = 0

        if version in (0, 1):
            nEntries = data[17:19]
            assert nEntries.isdigit(), "Number of entries is not an integer"
            nEntries = int(nEntries)
            log("Entries: " + str(nEntries))
            # subfile designator
            # FIXME could also be 'ID'
            assert data[19:21] == "DL" or data[19:21] == "ID", (
                "Not a driver's license (Got '%s', should be 'DL')" % data[19:21]
            )
            offset = data[21:25]
            assert offset.isdigit(), "Subfile offset is not an integer"
            offset = int(offset)
            # FIXME Either MD or SC is off-by-one on this part of the standard
            if issue_identifier in ("636005"):
                offset += 1
            length = data[25:29]
            assert length.isdigit(), "Subfile length is not an integer"
            length = int(length)
            decode_function = self._decode_barcode_v1

            # parse subfile designators
            read_offset = 10
            record_type = data[19:21]
            beginning = data[offset: offset + length].strip("\r")
            if not beginning.startswith(record_type):
                beginning = record_type + beginning

            subfiles_raw.append(beginning)

            # parse subfile designators
            for fileId in range(nEntries - 1):
                # Read each subfile designator
                log("=== Subfile {0} ===".format(fileId))
                if record_type is None:  # Subfile type determines document type
                    record_type = data[read_offset + 19: read_offset + 21]
                offset = data[read_offset + 21: read_offset + 25]
                length = data[read_offset + 25: read_offset + 29]
                assert offset.isdigit(), "Subfile offset is not an integer"
                assert length.isdigit(), "Subfile length is not an integer"
                offset = int(offset)
                length = int(length) + 2
                log("Offset: {0}".format(offset))
                log("Length: {0}".format(length))
                subfiles_raw.append(
                    data[offset: offset + length]
                )  # suck in all of record
                log(data[offset: offset + length])
                log("=== End Subfile ===")
                read_offset += 10

        elif version in (2, 3, 4, 5, 6, 7, 8, 9):
            # version 2 and later add a jurisdiction field
            jurisdiction_version = data[17:19]
            assert (
                jurisdiction_version.isdigit()
            ), "Jurisidiction version number is not an integer"
            nEntries = data[19:21]
            assert nEntries.isdigit(), "Number of entries is not an integer"
            nEntries = int(nEntries)
            log("Entries: " + str(nEntries))

            # parse subfile designators
            read_offset = 0
            record_type = None

            for fileId in range(nEntries):
                # Read each subfile designator
                log("=== Subfile {0} ===".format(fileId))
                if record_type is None:  # Subfile type determines document type
                    record_type = data[read_offset + 21: read_offset + 23]
                offset = data[read_offset + 23: read_offset + 27]
                length = data[read_offset + 27: read_offset + 31]
                assert offset.isdigit(), "Subfile offset is not an integer"
                assert length.isdigit(), "Subfile length is not an integer"
                offset = int(offset)
                length = int(length)
                log("Offset: {0}".format(offset))
                log("Length: {0}".format(length))
                subfiles_raw.append(
                    data[offset: offset + length]
                )  # suck in all of record
                log(data[offset: offset + length])
                log("=== End Subfile ===")
                read_offset += 10

            # ~ assert data[21:23] == 'DL', \
            # ~ "Not a driver's license (Got '%s', should be 'DL')" % data[21:23]
            # ~ offset = data[23:27]
            # ~ assert offset.isdigit(), 'Subfile offset is not an integer'
            # ~ offset = int(offset)
            # ~ print "Offset: " + str(offset)
            # ~ length = data[27:31]
            # ~ assert length.isdigit(), 'Subfile length is not an integer'
            # ~ length = int(length)
            # ~ print "Length: " + str(length)

            if version == 3:
                decode_function = self._decode_barcode_v3
            if version == 4:
                decode_function = self._decode_barcode_v4
            if version == 5:
                decode_function = self._decode_barcode_v5
            if version == 6:
                decode_function = self._decode_barcode_v6
            if version == 7:
                decode_function = (
                    self._decode_barcode_v8
                )  # FIXME: Seems to only be optional field changes
            if version == 8:
                decode_function = self._decode_barcode_v8
            if version == 9:
                decode_function = self._decode_barcode_v9

        # Seperate out subfiles, removing trailing empty list
        parsed_data = "\n".join(subfiles_raw)
        parsed_data.strip("\n")
        parsed_data = parsed_data.split(segterm)

        parsed_data = "".join(parsed_data)

        log(parsed_data)
        subfile = parsed_data.split(PDF_LINEFEED)
        if debug:
            pprint.pprint(subfile)

        #assert subfile[0][:2] == "DL" or subfile[0][:2] == "ID", (
        #    "Not a driver's license (Got '%s', should be 'DL')" % subfile[0][:2]
        #)
        subfile[0] = subfile[0][2:]  # remove prepended "DL"
        subfile[-1] = subfile[-1].strip(segterm)
        # Decode fields as a dictionary
        fields = dict((key[0:3], key[3:].strip()) for key in subfile)

        try:
            return decode_function(fields, issue_identifier)
        except UnboundLocalError:
            raise NotImplemented(
                "ERROR: Version {0} decoding not implemented!".format(version)
            )

    def _decode_barcode_v0(self, data):
        """Decodes a version 0 barcode specification (prior to 2000)"""
        pass  # TODO

    def _decode_barcode_v1(self, fields, issueIdentifier):
        warnings = []
        # Version 1 (AAMVA DL/ID-2000 standard)
        try:  # Prefer the optional, field-seperated values
            name = []
            name[0] = fields["DAB"]  # Lastname, OPTIONAL 31
            name[1] = fields["DAC"]  # Firstname, OPTIONAL 32
            name[2] = fields["DAD"]  # Middle name/initial, OPTIONAL 33
            nameSuffix = fields["DAE"]  # OPTIONAL 34
            namePrefix = fields["DAF"]  # OPTIONAL 35
        except KeyError:  # fall back on the required field
            name = fields["DAA"].split(",")  # REQUIRED 1
            nameSuffix = None
            namePrefix = None

        # Convert datetime objects
        dba = fields["DBA"]  # Expiry date REQUIRED 11
        expiry = datetime.date(int(dba[0:4]), int(dba[4:6]), int(dba[6:8]))
        dbb = fields["DBB"]  # Date of Birth REQUIRED 12
        dob = datetime.date(int(dbb[0:4]), int(dbb[4:6]), int(dbb[6:8]))
        dbd = fields["DBD"]  # Document issue date REQUIRED 14
        issued = datetime.date(int(dbd[0:4]), int(dbd[4:6]), int(dbd[6:8]))

        sex = fields["DBC"]  # REQUIRED 13
        if sex == "1":  # SCDMV v1 discrepancy
            sex = "M"
        elif sex == "2":
            sex = "F"
        assert "F" in sex or "M" in sex, "Invalid sex"

        # Optional fields:
        country = "USA"
        try:
            height = fields["DAV"]  # Prefer metric units OPTIONAL 42
            weight = fields["DAX"]  # OPTIONAL 43
            units = METRIC
            country = "CAN"
        except KeyError:
            try:
                height = fields["DAU"]  # U.S. imperial units OPTIONAL 20
                weight = fields["DAW"]  # OPTIONAL 21
                units = IMPERIAL
            except KeyError:
                # No height/weight defined (these fields are optional by the standard)
                height = None
                weight = None
                units = None
        finally:
            pass
            #assert height.isdigit() or height is not None, "Invalid height"
            #assert weight.isdigit() or height is not None, "Invalid weight"

        # weight is optional
        if units == METRIC:
            try:
                weight = Weight(None, int(fields["DAX"]))
            except KeyError:
                weight = None
        elif units == IMPERIAL:
            try:
                weight = Weight(None, int(fields["DAW"]), "USA")
            except KeyError:
                weight = None

        try:
            hair = fields["DAZ"].strip()
            eyes = fields["DAY"].strip()
        except KeyError:
            hair = None
            eyes = None

        address2 = None  # (OPTIONAL 2009 a.)
        if "DAH" in list(fields.keys()):
            address2 = fields["DAH"].strip()

        # assert hair in HAIRCOLOURS, "Invalid hair colour"
        # assert eyes in EYECOLOURS, "Invalid eye colour"

        # MD doesn't always encode restrictions (2015 license):
        try:
            restrictions = fields["DAS"].strip()
        except:
            restrictions = None
            warnings.append("Missing required field: restrictions (DAS)")
        try:
            endorsements = fields["DAT"].strip()
            card_type = "DL"
        except:
            restrictions = None
            card_type = "ID"
            warnings.append("Missing required field: endorsements (DAT)")

        # Middle name not always encoded, or comma skipped:
        if len(name) == 2:
            name.append(None)

        arrival_dates = {}

        rv = {
            "first": name[1].strip(),
            "last": name[0].strip(),
            "middle": name[2],
            "address": fields["DAG"].strip(),
            "address2": address2,
            "city": fields["DAI"].strip(),
            "state": fields["DAJ"].strip(),
            "country": country,
            "ZIP": fields["DAK"].strip(),
            "IIN": issueIdentifier,
            "license_number": fields["DAQ"].strip(),
            "expiry": expiry,
            "dob": dob,
            "class": fields["DAR"].strip(),
            "restrictions": restrictions,
            "endorsements": endorsements,
            "sex": sex,
            "height": height,
            "weight": weight,
            "hair": hair,
            "eyes": eyes,
            "units": units,
            "issued": issued,
            "suffix": nameSuffix,
            "prefix": namePrefix,
            "document": None,
            "arrival_dates": arrival_dates,
            "card_type": card_type,
            "version": 1,
            "standards": (len(warnings) == 0),
            "warnings": warnings,
        }
        return rv

    def _decode_barcode_v3(self, fields, issueIdentifier):
        warnings = []
        if debug:
            pprint.pprint(fields)
        # required fields
        country = fields["DCG"]  # USA or CAN

        # convert dates
        dba = fields["DBA"]  # expiry (REQUIRED REF d.)
        expiry = self._parse_date(dba, country)
        dbd = fields["DBD"]  # issue date (REQUIRED REF g.)
        issued = self._parse_date(dbd, country)
        dbb = fields["DBB"]  # date of birth (REQUIRED REF h.)
        dob = self._parse_date(dbb, country)

        # jurisdiction-specific (required for DL only):
        try:
            vehicle_class = fields["DCA"].strip()
            restrictions = fields["DCB"].strip()
            endorsements = fields["DCD"].strip()
            card_type = DRIVER_LICENSE
        except KeyError:
            # not a DL, use None instead
            vehicle_class = None
            restrictions = None
            endorsements = None
            card_type = IDENTITY_CARD

        # Physical description
        sex = fields["DBC"]
        assert sex in "129", "Invalid sex"
        if sex == "1":
            sex = MALE
        if sex == "2":
            sex = FEMALE
        if sex == "9":
            sex = NOT_SPECIFIED

        # Some v.03 barcodes (Indiana) [wrongly, and stupidly] omit
        # the mandatory height (DAU) field.
        try:
            # Normal v.03 barcodes:
            height = fields["DAU"]
            if height[-2:] == "in":  # inches
                height = int(height[0:3])
                units = IMPERIAL
                height = Height(height, format="USA")
            elif height[-2:].lower() == "cm":  # metric
                height = int(height[0:3])
                units = METRIC
                height = Height(height)
            else:
                height = None
                #raise AssertionError("Invalid unit for height")
        except KeyError:
            try:  # Indiana puts it in the jurisdiction field ZIJ
                height = fields["ZIJ"].split("-")
                units = IMPERIAL
                height = Height(
                    (int(height[0]) * 12) + int(height[1]), format="USA")
            except KeyError:
                # Give up on parsing height
                log("ERROR: Unable to parse height.")
                height = None

        # Eye colour is mandatory
        eyes = fields["DAY"]
        assert eyes in EYECOLOURS, "Invalid eye colour: {0}".format(eyes)

        # But hair colour is optional for some reason in this version
        try:
            hair = fields["DAZ"]
            assert hair in HAIRCOLOURS, "Invalid hair colour: {0}".format(hair)
        except KeyError:
            try:  # Indiana
                hair = fields["ZIL"]
                assert hair in HAIRCOLOURS, "Invalid hair colour: {0}".format(
                    hair)
            except KeyError:
                hair = None

        # name suffix optional. No prefix field in this version.
        try:
            name_suffix = fields["DCU"].strip()
        except KeyError:
            name_suffix = None

        # Try weight range
        try:
            weight = fields["DCE"]
            if units == METRIC:
                weight = Weight(int(weight), format="ISO")
            elif units == IMPERIAL:
                weight = Weight(int(weight), format="USA")
        except KeyError:
            try:  # Indiana again
                weight = fields["ZIK"]
                assert weight.isdigit(
                ), "Weight is non-integer: {0}".format(weight)
                weight = Weight(int(weight), format="USA")
            except KeyError:
                weight = None  # Give up

        # Abstract the name field:
        names = fields["DCT"].split(",")
        firstname = names[0].strip()
        if len(names) == 1:  # No middle name
            middlename = None
        else:
            middlename = ", ".join(names[1:]).strip()

        # Indiana, again, uses spaces instead
        if "," not in fields["DCT"]:
            names = fields["DCT"].split(" ")
            firstname = names[0].strip()
            if len(names) == 1:
                middlename = None
            else:
                middlename = " ".join(names[1:]).strip()

        address2 = None  # (OPTIONAL 2009 a.)
        if "DAH" in list(fields.keys()):
            address2 = fields["DAH"].strip()

        arrival_dates = {}

        lastname = fields["DCS"].strip()  # (REQUIRED 2005 e)

        rv = {
            "first": firstname,
            "last": lastname,
            "middle": middlename,
            "address": fields["DAG"].strip(),
            "address2": address2,
            "city": fields["DAI"].strip(),
            "state": fields["DAJ"].strip(),
            "country": country,
            "ZIP": fields["DAK"].strip(),
            "IIN": issueIdentifier,
            "license_number": fields["DAQ"].strip(),
            "expiry": expiry,
            "dob": dob,
            "class": vehicle_class,
            "restrictions": restrictions,
            "endorsements": endorsements,
            "sex": sex,
            "height": height,
            "weight": weight,
            "hair": hair,
            "eyes": eyes,
            "units": units,
            "issued": issued,
            "suffix": name_suffix,
            "prefix": None,
            "document": fields["DCF"].strip(),  # Mandatory 2005 q.
            "arrival_dates": arrival_dates,
            "card_type": card_type,
            "version": 3,
            "standards": (len(warnings) == 0),
            "warnings": warnings,
        }
        return rv

    def _decode_barcode_v4(self, fields, issueIdentifier):
        warnings = []
        # required fields
        country = fields["DCG"]  # USA or CAN

        # convert dates
        dba = fields["DBA"]  # expiry (REQUIRED REF d.)
        expiry = self._parse_date(dba, country)
        dbd = fields["DBD"]  # issue date (REQUIRED REF g.)
        issued = self._parse_date(dbd, country)
        dbb = fields["DBB"]  # date of birth (REQUIRED REF h.)
        dob = self._parse_date(dbb, country)

        # jurisdiction-specific (required for DL only):
        try:
            vehicleClass = fields["DCA"].strip()
            restrictions = fields["DCB"].strip()
            endorsements = fields["DCD"].strip()
            card_type = DRIVER_LICENSE
        except KeyError:
            # not a DL, use None instead
            vehicleClass = None
            restrictions = None
            endorsements = None
            card_type = IDENTITY_CARD

        # Physical description
        sex = fields["DBC"]
        assert sex in "129", "Invalid sex"
        if sex == "1":
            sex = MALE
        if sex == "2":
            sex = FEMALE
        if sex == "9":
            sex = NOT_SPECIFIED

        height = fields["DAU"]
        if height[-2:].lower() == "cm":  # metric
            height = int(height[0:3])
            units = METRIC
            height = Height(height)
        elif height[-1] == '"':
            # US height encoding for some implementations of this version is feet and inches
            # (e.g. 6'-01"")
            feet = int(height[0])
            inches = int(height[3:5])
            units = IMPERIAL
            height = Height((feet * 12 + inches), format="USA")
        elif height[-2:].lower() == "in":
            height = int(height[0:3])
            units = IMPERIAL
            height = Height(height, format="USA")
        else:
            height = None
            #raise AssertionError("Invalid unit for height")

        # weight is optional
        if units == METRIC:
            try:
                weight = Weight(None, int(fields["DAX"]))
            except KeyError:
                weight = None
        elif units == IMPERIAL:
            try:
                weight = Weight(None, int(fields["DAW"]), "USA")
            except KeyError:
                weight = None
        if weight is None:
            # Try weight range
            try:
                weight = fields["DCE"]
                if units == METRIC:
                    weight = Weight(int(weight), format="ISO")
                elif units == IMPERIAL:
                    weight = Weight(int(weight), format="USA")
            except KeyError:
                weight = None

        # Hair/eye colour are mandatory, but some (NJ) don't encode hair colour
        try:
            hair = fields["DAZ"]
            if hair not in HAIRCOLOURS:
                warnings.append("Invalid hair colour: {0}".format(hair))
        except KeyError:
            hair = None
            warnings.append("Missing mandatory field: hair colour (DAZ)")
        try:
            eyes = fields["DAY"]
            if eyes not in EYECOLOURS:
                warnings.append("Invalid eye colour: {0}".format(eyes))
        except KeyError:
            eyes = None
            warnings.append("Missing mandatory field: hair colour (DAZ)")

        # name suffix optional. No prefix field in this version.
        try:
            name_suffix = fields["DCU"].strip()
        except KeyError:
            name_suffix = None

        address2 = None  # (OPTIONAL 2009 a.)
        if "DAH" in list(fields.keys()):
            address2 = fields["DAH"].strip()

        lastname = fields["DCS"].strip()  # (REQUIRED 2005 e)
        firstname = fields["DAC"].strip()  # (REQUIRED 2005 f)
        arrival_dates = {}

        rv = {
            "first": fields["DAC"].strip(),
            "last": fields["DCS"].strip(),
            "middle": fields["DAD"].strip(),
            "address": fields["DAG"].strip(),
            "address2": address2,
            "city": fields["DAI"].strip(),
            "state": fields["DAJ"].strip(),
            "country": country,
            "IIN": issueIdentifier,
            "license_number": fields["DAQ"].strip(),
            "expiry": expiry,
            "dob": dob,
            "ZIP": fields["DAK"].strip(),
            "class": vehicleClass,
            "restrictions": restrictions,
            "endorsements": endorsements,
            "sex": sex,
            "height": height,
            "weight": weight,
            "hair": hair,
            "eyes": eyes,
            "units": units,
            "issued": issued,
            "suffix": name_suffix,
            "prefix": None,  # Removed from this version
            "document": fields["DCF"].strip(),
            "arrival_dates": arrival_dates,
            "card_type": card_type,
            "version": 4,
            "standards": (len(warnings) == 0),
            "warnings": warnings,
        }
        return rv

    def _decode_barcode_v5(self, fields, issueIdentifier):
        warnings = []
        # required fields
        country = fields["DCG"]  # USA or CAN

        # convert dates
        dba = fields["DBA"]  # expiry (REQUIRED REF d.)
        expiry = self._parse_date(dba, country)
        dbd = fields["DBD"]  # issue date (REQUIRED REF g.)
        issued = self._parse_date(dbd, country)
        dbb = fields["DBB"]  # date of birth (REQUIRED REF h.)
        dob = self._parse_date(dbb, country)

        # jurisdiction-specific (required for DL only):
        # FIXME - check if fields are empty
        try:
            vehicleClass = fields["DCA"].strip()
            restrictions = fields["DCB"].strip()
            endorsements = fields["DCD"].strip()
            card_type = DRIVER_LICENSE
        except KeyError:
            # not a DL, use None instead
            vehicleClass = None
            restrictions = None
            endorsements = None
            card_type = IDENTITY_CARD

        # Physical description
        sex = fields["DBC"]
        assert sex in "129", "Invalid sex"
        if sex == "1":
            sex = MALE
        if sex == "2":
            sex = FEMALE
        if sex == "9":
            sex == NOT_SPECIFIED

        height = fields["DAU"]
        if height[-2:] == "in":  # inches
            height = int(height[0:3])
            units = IMPERIAL
            height = Height(height, format="USA")
        elif height[-2:].lower() == "cm":  # metric
            height = int(height[0:3])
            units = METRIC
            height = Height(height)
        else:
            height = None
            #raise AssertionError("Invalid unit for height")

        # weight is optional
        if units == METRIC:
            try:
                weight = Weight(None, int(fields["DAX"]))
            except KeyError:
                weight = None
        elif units == IMPERIAL:
            try:
                weight = Weight(None, int(fields["DAW"]), "USA")
            except KeyError:
                weight = None
        if weight is None:
            # Try weight range
            try:
                weight = fields["DCE"]
                if units == METRIC:
                    weight = Weight(int(weight), format="ISO")
                elif units == IMPERIAL:
                    weight = Weight(int(weight), format="USA")
            except KeyError:
                weight = None

        # Hair/eye colour are mandatory
        hair = fields.get("DAZ")
        eyes = fields.get("DAY")
        #assert hair in HAIRCOLOURS, "Invalid hair colour: {0}".format(eyes)
        #assert eyes in EYECOLOURS, "Invalid eye colour: {0}".format(hair)

        # name suffix optional. No prefix field in this version.
        try:
            nameSuffix = fields["DCU"].strip()
        except KeyError:
            nameSuffix = None

        # v5 adds optional date fields DDH, DDI, and DDJ (Under 18/19/21 until)
        arrival_dates = {}
        if "DDH" in list(fields.keys()):
            arrival_dates["under_18_until"] = self._parse_date(fields["DDH"])
        if "DDI" in list(fields.keys()):
            arrival_dates["under_19_until"] = self._parse_date(fields["DDI"])
        if "DDJ" in list(fields.keys()):
            arrival_dates["under_21_until"] = self._parse_date(fields["DDJ"])

        address2 = None  # (OPTIONAL 2009 a.)
        if "DAH" in list(fields.keys()):
            address2 = fields["DAH"].strip()

        rv = {
            "first": fields["DAC"].strip(),
            "last": fields["DCS"].strip(),
            "middle": fields["DAD"].strip(),
            "address": fields["DAG"].strip(),
            "address2": address2,
            "city": fields["DAI"].strip(),
            "state": fields["DAJ"].strip(),
            "country": country,
            "IIN": issueIdentifier,
            "license_number": fields["DAQ"].strip(),
            "expiry": expiry,
            "dob": dob,
            "ZIP": fields["DAK"].strip(),
            "class": vehicleClass,
            "restrictions": restrictions,
            "endorsements": endorsements,
            "sex": sex,
            "height": height,
            "weight": weight,
            "hair": hair,
            "eyes": eyes,
            "units": units,
            "issued": issued,
            "suffix": nameSuffix,
            "prefix": None,
            "document": fields["DCF"].strip(),
            "arrival_dates": arrival_dates,
            "card_type": card_type,
            "version": 5,
            "standards": (len(warnings) == 0),
            "warnings": warnings,
        }
        return rv

    def _decode_barcode_v6(self, fields, issueIdentifier):  # 2011 standard
        warnings = []
        # required fields
        country = fields["DCG"]  # USA or CAN

        # 2011 e, f, g, are required name fields
        lastname = fields["DCS"].strip()  # (REQUIRED 2011 e)
        firstname = fields["DAC"].strip()  # (REQUIRED 2011 f)
        middlename = fields["DAD"].strip()  # (REQUIRED 2011 g)

        # 2011 t, u, and v indicate if names are truncated:
        if fields["DDE"] == "T":
            lastname += "…"
        if fields["DDF"] == "T":
            firstname += "…"
        if fields["DDG"] == "T":
            middlename += "…"

        # convert dates
        dba = fields["DBA"]  # expiry (REQUIRED 2011 d.)
        expiry = self._parse_date(dba, country)
        dbd = fields["DBD"]  # issue date (REQUIRED 2011 h.)
        issued = self._parse_date(dbd, country)
        dbb = fields["DBB"]  # date of birth (REQUIRED 2011 i.)
        dob = self._parse_date(dbb, country)

        # jurisdiction-specific (required for DL only):
        # FIXME - check if fields are empty
        try:
            vehicle_class = fields["DCA"].strip()  # (REQUIRED 2011 a.)
            restrictions = fields["DCB"].strip()  # (REQUIRED 2011 b.)
            endorsements = fields["DCD"].strip()  # (REQUIRED 2011 c.)
            card_type = DRIVER_LICENSE
        except KeyError:
            # not a DL, use None instead
            vehicle_class = None
            restrictions = None
            endorsements = None
            card_type = IDENTITY_CARD

        # Physical description
        sex = fields["DBC"]  # (REQUIRED 2011 j.)
        assert sex in "12", "Invalid sex"
        if sex == "1":
            sex = MALE
        if sex == "2":
            sex = FEMALE
        if sex == "9":
            sex = NOT_SPECIFIED

        eyes = fields["DAY"]  # (REQUIRED 2011 k.)
        assert eyes in EYECOLOURS, "Invalid eye colour: {0}".format(eyes)

        height = fields["DAU"]  # (REQUIRED 2011 l.)
        if height[-2:] == "in":  # inches
            height = int(height[0:3])
            units = IMPERIAL
            height = Height(height, format="USA")
        elif height[-2:].lower() == "cm":  # metric
            height = int(height[0:3])
            units = METRIC
            height = Height(height)
        else:
            height = None
            #raise AssertionError("Invalid unit for height")

        # 2011 m, n, o, p, are required address elements

        # weight is optional
        if units == METRIC:
            try:
                weight = Weight(None, int(fields["DAX"]))
            except KeyError:
                weight = None
        elif units == IMPERIAL:
            try:
                weight = Weight(None, int(fields["DAW"]), "USA")
            except KeyError:
                weight = None
        if weight is None:
            # Try weight range
            try:
                weight = fields["DCE"]
                if units == METRIC:
                    weight = Weight(int(weight), format="ISO")
                elif units == IMPERIAL:
                    weight = Weight(int(weight), format="USA")
            except KeyError:
                weight = None

        # optional fields:
        address2 = None  # (OPTIONAL 2011 a.)
        if "DAH" in list(fields.keys()):
            address2 = fields["DAH"].strip()

        hair = None  # (OPTIONAL 2011 b.)
        if "DAZ" in list(fields.keys()):
            hair = fields["DAZ"]  # Optional
            assert hair in HAIRCOLOURS, "Invalid hair colour: {0}".format(hair)

        # TODO: OPTIONAL 2011 fields c - h

        # name suffix optional. No prefix field in this version.
        try:
            nameSuffix = fields["DCU"].strip()  # (OPTIONAL 2011 i.)
        except KeyError:
            nameSuffix = None

        # TODO: OPTIONAL 2011 fields j - u

        # v6 adds optional date fields DDH, DDI, and DDJ (Under 18/19/21 until)
        arrival_dates = {}
        if "DDH" in list(fields.keys()):
            arrival_dates["under_18_until"] = self._parse_date(fields["DDH"])
        if "DDI" in list(fields.keys()):
            arrival_dates["under_19_until"] = self._parse_date(fields["DDI"])
        if "DDJ" in list(fields.keys()):
            arrival_dates["under_21_until"] = self._parse_date(fields["DDJ"])

        # TODO: OPTIONAL 2011 field a.a.

        rv = {
            "first": firstname,
            "last": lastname,
            "middle": middlename,
            "address": fields["DAG"].strip(),
            "address2": address2,
            "city": fields["DAI"].strip(),
            "state": fields["DAJ"].strip(),
            "country": country,
            "IIN": issueIdentifier,
            "license_number": fields["DAQ"].strip(),
            "expiry": expiry,
            "dob": dob,
            "ZIP": fields["DAK"].strip(),
            "class": vehicle_class,
            "restrictions": restrictions,
            "endorsements": endorsements,
            "sex": sex,
            "height": height,
            "weight": weight,
            "hair": hair,
            "eyes": eyes,
            "units": units,
            "issued": issued,
            "suffix": nameSuffix,
            "prefix": None,
            "document": fields["DCF"].strip(),
            "arrival_dates": arrival_dates,
            "card_type": card_type,
            "version": 7,
            "standards": (len(warnings) == 0),
            "warnings": warnings,
        }
        return rv

    def _decode_barcode_v8(self, fields, issueIdentifier):  # 2013 standard
        warnings = []
        # required fields
        country = fields["DCG"]  # USA or CAN

        # 2013 e, f, g, are required name fields
        lastname = fields["DCS"].strip()  # (REQUIRED 2013 e)
        firstname = fields["DAC"].strip()  # (REQUIRED 2013 f)
        middlename = fields["DAD"].strip()  # (REQUIRED 2013 g)

        # 2013 t, u, and v indicate if names are truncated:
        if fields["DDE"] == "T":
            lastname += "…"
        if fields["DDF"] == "T":
            firstname += "…"
        if fields["DDG"] == "T":
            middlename += "…"

        # convert dates
        dba = fields["DBA"]  # expiry (REQUIRED 2013 d.)
        expiry = self._parse_date(dba, country)
        dbd = fields["DBD"]  # issue date (REQUIRED 2013 h.)
        issued = self._parse_date(dbd, country)
        dbb = fields["DBB"]  # date of birth (REQUIRED 2013 i.)
        dob = self._parse_date(dbb, country)

        # jurisdiction-specific (required for DL only):
        # FIXME - check if fields are empty
        try:
            vehicle_class = fields["DCA"].strip()  # (REQUIRED 2013 a.)
            restrictions = fields["DCB"].strip()  # (REQUIRED 2013 b.)
            endorsements = fields["DCD"].strip()  # (REQUIRED 2013 c.)
            card_type = DRIVER_LICENSE
        except KeyError:
            # not a DL, use None instead
            vehicle_class = None
            restrictions = None
            endorsements = None
            card_type = IDENTITY_CARD

        # Physical description
        sex = fields["DBC"]  # (REQUIRED 2013 j.)
        assert sex in "129", "Invalid sex"
        if sex == "1":
            sex = MALE
        if sex == "2":
            sex = FEMALE
        if sex == "9":
            sex = NOT_SPECIFIED

        eyes = fields["DAY"]  # (REQUIRED 2013 k.)
        assert eyes in EYECOLOURS, "Invalid eye colour: {0}".format(eyes)

        height = fields["DAU"]  # (REQUIRED 2013 l.)
        if height[-2:] == "in":  # inches
            height = int(height[0:3])
            units = IMPERIAL
            height = Height(height, format="USA")
        elif height[-2:].lower() == "cm":  # metric
            height = int(height[0:3])
            units = METRIC
            height = Height(height)
        else:
            height = None
            #raise AssertionError("Invalid unit for height")

        # 2013 m, n, o, p, are required address elements

        # weight is optional
        if units == METRIC:
            try:
                weight = Weight(None, int(fields["DAX"]))
            except KeyError:
                weight = None
        elif units == IMPERIAL:
            try:
                weight = Weight(None, int(fields["DAW"]), "USA")
            except KeyError:
                weight = None
        if weight is None:
            # Try weight range
            try:
                weight = fields["DCE"]
                if units == METRIC:
                    weight = Weight(int(weight), format="ISO")
                elif units == IMPERIAL:
                    weight = Weight(int(weight), format="USA")
            except KeyError:
                weight = None

        # optional fields:
        address2 = None  # (OPTIONAL 2013 a.)
        if "DAH" in list(fields.keys()):
            address2 = fields["DAH"].strip()

        hair = None  # (OPTIONAL 2013 b.)
        if "DAZ" in list(fields.keys()):
            hair = fields["DAZ"]  # Optional
            assert hair in HAIRCOLOURS, "Invalid hair colour: {0}".format(hair)

        # TODO: OPTIONAL 2013 fields c - h

        # name suffix optional. No prefix field in this version.
        try:
            name_suffix = fields["DCU"].strip()  # (OPTIONAL 2013 i.)
        except KeyError:
            name_suffix = None

        # TODO: OPTIONAL 2013 fields j - u

        # v6 adds optional date fields DDH, DDI, and DDJ (Under 18/19/21 until)
        arrival_dates = {}
        if "DDH" in list(fields.keys()):
            arrival_dates["under_18_until"] = self._parse_date(fields["DDH"])
        if "DDI" in list(fields.keys()):
            arrival_dates["under_19_until"] = self._parse_date(fields["DDI"])
        if "DDJ" in list(fields.keys()):
            arrival_dates["under_21_until"] = self._parse_date(fields["DDJ"])

        # TODO: OPTIONAL 2013 field a.a.

        rv = {
            "first": firstname,
            "last": lastname,
            "middle": middlename,
            "address": fields["DAG"].strip(),
            "address2": address2,
            "city": fields["DAI"].strip(),
            "state": fields["DAJ"].strip(),
            "country": country,
            "IIN": issueIdentifier,
            "license_number": fields["DAQ"].strip(),
            "expiry": expiry,
            "dob": dob,
            "ZIP": fields["DAK"].strip(),
            "class": vehicle_class,
            "restrictions": restrictions,
            "endorsements": endorsements,
            "sex": sex,
            "height": height,
            "weight": weight,
            "hair": hair,
            "eyes": eyes,
            "units": units,
            "issued": issued,
            "suffix": name_suffix,
            "prefix": None,
            "document": fields["DCF"].strip(),
            "arrival_dates": arrival_dates,
            "card_type": card_type,
            "version": 8,
            "standards": (len(warnings) == 0),
            "warnings": warnings,
        }
        return rv

    def _decode_barcode_v9(self, fields, issueIdentifier):  # 2016 standard
        warnings = []
        # Add: "unspecified" sex option
        # required fields
        country = fields["DCG"]  # USA or CAN

        # 2016 e, f, g, are required name fields
        lastname = fields["DCS"].strip()  # (REQUIRED 2016 e)
        firstname = fields["DAC"].strip()  # (REQUIRED 2016 f)
        middlename = fields["DAD"].strip()  # (REQUIRED 2016 g)

        # 2016 t, u, and v indicate if names are truncated:
        if fields["DDE"] == "T":
            lastname += "…"
        if fields["DDF"] == "T":
            firstname += "…"
        if fields["DDG"] == "T":
            middlename += "…"

        # convert dates
        dba = fields["DBA"]  # expiry (REQUIRED 2016 d.)
        expiry = self._parse_date(dba, country)
        dbd = fields["DBD"]  # issue date (REQUIRED 2016 h.)
        issued = self._parse_date(dbd, country)
        dbb = fields["DBB"]  # date of birth (REQUIRED 2016 i.)
        dob = self._parse_date(dbb, country)

        # jurisdiction-specific (required for DL only):
        # FIXME - check if fields are empty
        try:
            vehicle_class = fields["DCA"].strip()  # (REQUIRED 2016 a.)
            restrictions = fields["DCB"].strip()  # (REQUIRED 2016 b.)
            endorsements = fields["DCD"].strip()  # (REQUIRED 2016 c.)
            card_type = DRIVER_LICENSE
        except KeyError:
            # not a DL, use None instead
            vehicle_class = None
            restrictions = None
            endorsements = None
            card_type = IDENTITY_CARD

        # Physical description
        sex = fields["DBC"]  # (REQUIRED 2016 j.)
        assert sex in "129", "Invalid sex"
        if sex == "1":
            sex = MALE
        if sex == "2":
            sex = FEMALE
        if sex == "9":
            sex = NOT_SPECIFIED

        eyes = fields["DAY"]  # (REQUIRED 2016 k.)
        assert eyes in EYECOLOURS, "Invalid eye colour: {0}".format(eyes)

        height = fields["DAU"]  # (REQUIRED 2016 l.)
        if height[-2:].lower() == "in":  # inches
            height = int(height[0:3])
            units = IMPERIAL
            height = Height(height, format="USA")
        elif height[-2:].lower() == "cm":  # metric
            height = int(height[0:3])
            units = METRIC
            height = Height(height)
        else:
            height = None
            #raise AssertionError("Invalid unit for height")

        # 2016 m, n, o, p, are required address elements

        # weight is optional
        if units == METRIC:
            try:
                weight = Weight(None, int(fields["DAX"]))
            except KeyError:
                weight = None
        elif units == IMPERIAL:
            try:
                weight = Weight(None, int(fields["DAW"]), "USA")
            except KeyError:
                weight = None
        if weight is None:
            # Try weight range
            try:
                weight = fields["DCE"]
                if units == METRIC:
                    weight = Weight(int(weight), format="ISO")
                elif units == IMPERIAL:
                    weight = Weight(int(weight), format="USA")
            except KeyError:
                weight = None

        # optional fields:
        address2 = None  # (OPTIONAL 2016 a.)
        if "DAH" in list(fields.keys()):
            address2 = fields["DAH"].strip()

        hair = None  # (OPTIONAL 2016 b.)
        if "DAZ" in list(fields.keys()):
            hair = fields["DAZ"]  # Optional
            assert hair in HAIRCOLOURS, "Invalid hair colour: {0}".format(hair)

        # TODO: OPTIONAL 2013 fields c - h

        # name suffix optional. No prefix field in this version.
        try:
            nameSuffix = fields["DCU"].strip()  # (OPTIONAL 2016 i.)
        except KeyError:
            nameSuffix = None

        # TODO: OPTIONAL 2016 fields j - u

        # v6 adds optional date fields DDH, DDI, and DDJ (Under 18/19/21 until)
        arrival_dates = {}
        if "DDH" in list(fields.keys()):
            arrival_dates["under_18_until"] = self._parse_date(fields["DDH"])
        if "DDI" in list(fields.keys()):
            arrival_dates["under_19_until"] = self._parse_date(fields["DDI"])
        if "DDJ" in list(fields.keys()):
            arrival_dates["under_21_until"] = self._parse_date(fields["DDJ"])

        # TODO: OPTIONAL 2016 field a.a.

        rv = {
            "first": firstname,
            "last": lastname,
            "middle": middlename,
            "address": fields["DAG"].strip(),
            "address2": address2,
            "city": fields["DAI"].strip(),
            "state": fields["DAJ"].strip(),
            "country": country,
            "IIN": issueIdentifier,
            "license_number": fields["DAQ"].strip(),
            "expiry": expiry,
            "dob": dob,
            "ZIP": fields["DAK"].strip(),
            "class": vehicle_class,
            "restrictions": restrictions,
            "endorsements": endorsements,
            "sex": sex,
            "height": height,
            "weight": weight,
            "hair": hair,
            "eyes": eyes,
            "units": units,
            "issued": issued,
            "suffix": nameSuffix,
            "prefix": None,
            "document": fields["DCF"].strip(),
            "arrival_dates": arrival_dates,
            "card_type": card_type,
            "version": 9,
            "standards": (len(warnings) == 0),
            "warnings": warnings,
        }
        return rv

    @staticmethod
    def _parse_date(date, fmt="ISO"):
        fmt = fmt.upper()
        if fmt == "USA":
            return datetime.date(int(date[4:8]), int(date[0:2]), int(date[2:4]))
        elif fmt == "ISO" or fmt == "CAN":
            return datetime.date(int(date[0:4]), int(date[4:6]), int(date[6:8]))


class ReadError(Exception):
    pass


class HeightError(Exception):
    pass


class WeightError(Exception):
    pass


class Subfile:
    """
    Subfile abstraction to help organize parsing of raw PDF417 data.
    Not intended for external use
    """

    type = None
    offset = None
    length = None
    data = {}


class Height:
    """
    Represents the physical description of height in an unit-netural way.
    Since not all MRT formats and barcode versions express height in an
    international format, this class makes it easy to convert between the
    units provided by AAMVA physical descriptions between inches (USA) and
    centimetres (Canada)
    """

    def __init__(self, height, format="ISO"):
        self.format = format
        if format == "ISO" or format == "CAN":  # use metric (cm)
            self.units = METRIC
        elif format == "USA":
            self.units = IMPERIAL
        else:
            raise HeightError("Invalid format: '%s'" % format)

        self.height = height

    def as_metric(self):
        """
        Returns height as integer in centimetres
        """
        if self.units == METRIC:
            return self.height
        else:
            return int(round(self.height * 0.393700787))  # convert to cm

    def as_imperial(self):
        """
        Returns height as integer in inches
        """
        if self.units == IMPERIAL:
            return self.height
        else:
            return int(round(self.height * 2.54))  # convert to inches

    def __eq__(self, other):
        if other.units == self.units:
            return self.height == other.height

    def __repr__(self):
        return "%s(%s, format='%s')" % (
            self.__class__.__name__,
            self.height,
            self.format,
        )

    def __str__(self):
        if self.units == IMPERIAL:
            return str(self.height) + " in"
        else:
            return str(self.height) + " cm"


class Weight:
    """
    Represents the physical description of weight in an unit-neutral way.
    """

    def __init__(self, weight_range, weight=None, format="ISO"):
        self.format = format
        if format == "ISO" or format == "CAN":  # use metric
            self.units = METRIC
        elif format == "USA":  # use imperial
            self.units = IMPERIAL
        else:
            raise WeightError("Invalid format: '%s'" % format)

        if weight_range is None:  # Defined by exact weight (lbs or kg)
            self.exact = True
            assert weight != None and type(weight) == int, "Invalid weight"
            self.weight = weight
            if self.units == METRIC:
                self.weightRange = self._get_metric_range(weight)
            else:
                self.weightRange = self._get_imperial_range(weight)

        else:  # Defined by weight range
            self.exact = False
            assert type(weight_range) == int
            self.weightRange = weight_range
            if self.units == METRIC:
                self.weight = self._metric_approximation(weight_range)
            else:
                self.weight = self._imperial_approximation(weight_range)

    def as_metric(self):  # Returns integer
        if self.units == METRIC:
            return self.weight
        else:
            return int(round(self.weight / 2.2))

    def as_imperial(self):  # Returns integer
        if self.units == IMPERIAL:
            return self.weight
        else:
            return int(round(self.weight * 2.2))

    def _get_metric_range(self, weight):
        """
        Returns the integer weight range given a weight in kilograms
        """
        # TODO: Make this more pythonic
        if weight <= 31:
            return 0
        elif weight > 31 and weight <= 45:
            return 1
        elif weight > 45 and weight <= 59:
            return 2
        elif weight > 59 and weight <= 70:
            return 3
        elif weight > 70 and weight <= 86:
            return 4
        elif weight > 86 and weight <= 100:
            return 5
        elif weight > 100 and weight <= 113:
            return 6
        elif weight > 113 and weight <= 127:
            return 7
        elif weight > 127 and weight <= 145:
            return 8
        elif weight > 146:
            return 9
        else:
            return None

    def _metric_approximation(self, weight):
        """
        Return an approximation of the weight given a weight range
        """
        table = {
            0: 20,
            1: 38,
            2: 53,
            3: 65,
            4: 79,
            5: 94,
            6: 107,
            7: 121,
            8: 137,
            9: 146,
        }
        return table[weight]

    def _get_imperial_range(self, weight):
        """
        Returns the integer weight range given a weight in pounds
        """
        if weight <= 70:
            return 0
        elif weight > 70 and weight <= 100:
            return 1
        elif weight > 100 and weight <= 130:
            return 2
        elif weight > 130 and weight <= 160:
            return 3
        elif weight > 160 and weight <= 190:
            return 4
        elif weight > 190 and weight <= 220:
            return 5
        elif weight > 220 and weight <= 250:
            return 6
        elif weight > 250 and weight <= 280:
            return 7
        elif weight > 280 and weight <= 320:
            return 8
        elif weight > 320:
            return 9
        else:
            return None

    def _imperial_approximation(self, weight):
        table = {
            0: 50,
            1: 85,
            2: 115,
            3: 145,
            4: 175,
            5: 205,
            6: 235,
            7: 265,
            8: 300,
            9: 320,
        }
        return table[weight]

    def __str__(self):
        if self.exact:
            if self.units == METRIC:
                return "%s kg" % self.weight
            else:
                return "%s lbs" % self.weight
        else:
            if self.units == METRIC:
                return METRIC_WEIGHTS[self.weightRange]
            else:
                return IMPERIAL_WEIGHTS[self.weightRange]

    def __eq__(self, other):
        if other is None:
            return False
        if self.units == other.units:
            return self.weight == other.weight
        else:
            return self.weightRange == other.weightRange

    # Not sure why you'd ever need to do this
    def __add__(self, other):
        if self.units == METRIC:
            return Weight(None, self.weight + other.as_metric(), format="ISO")
        else:
            return Weight(None, self.weight + other.as_imperial(), format="USA")

    def __repr__(self):
        return "%s(weightRange=%s, weight=%s, format=%s)" % (
            self.__class__.__name__,
            self.weightRange,
            self.weight,
            self.format,
        )


def log(string):
    """Barebones logging"""
    if debug:
        print(string)


if __name__ == "__main__":
    import pprint

    parser = AAMVA()

    # ~ while True:
    # ~ try: #Reading from an HID card reader (stdin)
    # ~ pprint.pprint(parser.decode(raw_input("Swipe a card")))
    # ~ except ReadError as e:
    # ~ print e
    # ~ print "Read error.  Try again."

    # reading from a serial barcode reader
    import serial

    ser = serial.Serial("/dev/ttyACM0")
    while True:
        charbuffer = ""
        print("Scan a license")
        while charbuffer[-2:] != "\r\n":
            char = ser.read(1)
            charbuffer += char
        try:
            print("Got string: " + repr(charbuffer) + "\n\n\n\n")
            pprint.pprint(parser.decode_barcode(str(charbuffer)))
        except Exception as e:
            print("Parse error. Try again")
            print(e)

    ser.close()
