#!/usr/bin/env python
# *-* coding: utf-8 *-*

import datetime

# 3 versions in circulation (no version 0?)
PDF_VERSIONS = list(range(1, 4))
PERSON_DESIGNATOR_TYPES = {
    "S": "Social Security Number",
    "N": "Non-SSN Identifier",
    "P": "Pre-SSN Identifier",
    "D": "Temporary Identifier Number",
    "F": "Forgein Identifier Number",
    "T": "Test Identification Number",
    "I": "Taxpayer ID",
}
PERSON_DESIGNATOR_TYPES_TOOLTIPS = {
    "S": "Social Security Number",
    "N": "Nine-digit code that looks like an SSN, but is not in a valid SSN range.",
    "P": "Special nine-digit code created for U.S. military personnel "
         + "from Service numbers before the switch to SSNs.",
    "D": "Special nine-digit code created for individuals (i.e., babies) "
         + "who do not have or have not provided an SSN when the person is "
         + "added to DEERS (dependents only). Known as a Temporary "
         + "Identifier Number (TIN).",
    "F": "Special nine-digit code created for foreign military and "
         + "nationals. Known as a Foreign Identifier Number (FIN).",
    "T": "Test (858 series)",
    "I": "Individual Taxpayer Identification Number",
}
BRANCH_CODES = {
    "A": "USA",
    "C": "USCG",
    "D": "DoD",
    "F": "USAF",
    "H": "USPHS",
    "M": "USMC",
    "N": "USN",
    "O": "NOAA",
    "1": "Forgein Army",
    "2": "Forgein Navy",
    "3": "Forgein Marine Corps",
    "4": "Forgein Air Force",
    "X": "Other",
}
PERSON_IDENTIFIER_CODES = {
    "A": "Active Duty",
    "B": "Presidential Appointee",
    "C": "DoD civil service employee",
    "D": "100% disabled American veteran",
    "E": "DoD contract employee",
    "F": "Former member",
    "P": "Former member",
    "N": "National Guard member",
    "G": "National Guard member",
    "H": "Medal of Honour recipient",
    "I": "Non-DoD civil service employee",
    "J": "Academy student",
    "K": "NAF DoD employee",
    "L": "Lighthouse service",
    "M": "NGO personnel",
    "O": "Non-DoD contract employee",
    "Q": "Non-eligible Reserve retiree",
    "R": "Retired",
    "V": "Active duty Reserve",
    "S": "Active duty Reserve",
    "T": "Foreign military member",
    "U": "Foreign national employee",
    "V": "Reserve member",
    "W": "DoD beneficiary",
    "Y": "Retired DoD Civil Service",
}
PERSON_ENTITLEMENT_CONDITIONS = {
    "00": "Unknown",  # This is undocumented, but found in real-world cards
    "01": "Active duty",
    "02": "Mobilization",
    "03": "On appellate leave",
    "04": "Military prisoner",
    "05": "POW/MIA",
    "06": "Separated from Selected Reserve",
    "07": "Permanently disabled",
    "08": "Non-CONUS assignment",
    "09": "Living in Guam or Puerto Rico",
    "10": "Living in government quarters",
    "11": "Death from injury, illness, or disease on active duty",
    "12": "Discharged due to misconduct involving family member abuse. "
          + "(Sponsors who are eligible for retirement)",
    "13": "Granted retired pay",
    "14": "DoD sponsored in U.S. (foreign military)",
    "15": "DoD non-sponsored in U.S. (foreign military)",
    "16": "DoD sponsored overseas",
    "17": "Deserter",
    "18": "Discharged due to misconduct involving family member abuse. "
          + "(Sponsors who are not eligible for retirement)",
    "19": "Reservist who dies after receiving their 20 year letter",
    "20": "Transitional assistance (TA-30)",
    "21": "Transitional assistance (TA-Res)",
    "22": "Transitional assistance (TA-60)",
    "23": "Transitional assistance (TA-120)",
    "24": "Transitional assistance (SSB program)",
    "25": "Transitional assistance (VSI program)",
    "26": "Transitional assistance (composite)",
    "27": "Senior Executive Service",
    "28": "Emergency Essential — overseas only",
    "29": "Emergency Essential – CONUS",
    "30": "2 Emergency Essential – CONUS living in quarters, living "
          + "on base, and not drawing a basic allowance for quarters",
    "31": "Reserve Component TA-120 Reserve Component Transition "
          + "Assistance TA 120 (Jan 1, 2002 or later)",
    "32": "On MSC owned and operated vessels Deployed to foreign "
          + "countries on Military Sealift Command owned and operated vessels",
    "33": "Guard/Reserve Alert Notification Period",
    "34": "Reserve Component TA-180 – 180 days TAMPS for reserve "
          + "return from named contingencies (was 60 before Nov 5 2003)",
    "35": "Reserve Component TA-180 – 180 days TAMPS for reserve "
          + "return from named contingencies (was 120 before Nov 5 2003)",
    "36": "TA-180 – 180 days TAMP for involuntary separation",
    "37": "TA-180 — 180 days TAMPS for involuntary separation",
    "38": "Living in Government Quarters in Guam or Puerto Rico, "
          + "Living on base and not drawing an allowance for quarters in "
          + "Guam or Puerto Rico.",
    "39": "Reserve Component TA-180 – TAMP – Mobilized for Contingency",
    "40": "TA – 180 TAMP – SPD Code Separation",
    "41": "TA-180 – TAMP – Stop/Loss Separation",
    "42": "DoD Non-Sponsored Overseas – Foreign Military personnel "
          + "serving OCONUS not sponsored by DoD",
}
PAY_PLAN_CODES = {
    "AF": "American Family Members",
    "AD": "Administratively determined not elsewhere specified",
    "AJ": "Administrative judges, Nuclear Regulatory Commission",
    "AL": "Administrative Law judges",
    "BB": "Non supervisory negotiated pay employees",
    "BL": "Leader negotiated pay employees",
    "BP": "Printing and Lithographic negotiated pay employees",
    "BS": "Supervisory negotiated pay employees",
    "CA": "Board of contract appeals",
    "CC": "Commissioned Corps of Public Heath Service",
    "CE": "Contract education",
    "CG": "Corporate graded Federal Deposit Insurance Corp",
    "CP": "Compensation program Office of the Comptroller of the currency",
    "CS": "Skill Based Pay demonstration employees, DLA",
    "CU": "Credit Union employees",
    "CY": "Contract education Bureau of Indian Affairs",
    "CZ": "Canal Area General Schedule type positions",
    "DA": "Demonstration administrative Director of Laboratory Programs (Navy)",
    "DG": "Demonstration general Director of Laboratory Programs (Navy)",
    "DH": "Demonstration hourly Air Force logistics command",
    "DN": "Defense Nuclear facilities safety board",
    "DP": "Demonstration professional Director of Laboratory Programs (Navy)",
    "DS": "Demonstration specialist Director of Laboratory Programs (Navy)",
    "DT": "Demonstration technician Director of Laboratory Programs (Navy)",
    "DW": "Demonstration salaried Air Force and DLA",
    "DX": "Demonstration Supervisory Air Force and DLA",
    "EA": "Administrative schedule (excluded) Tennessee Valley Authority",
    "EB": "Clerical schedule (excluded) Tennessee Valley Authority",
    "EC": "Engineering and Computing schedule (excluded) Tennessee Valley Authority",
    "ED": "Expert",
    "EE": "Expert (other)",
    "EF": "Consultant",
    "EG": "Consultant (other)",
    "EH": "Advisory committee member",
    "EI": "Advisory committee member (other)",
    "EM": "Executive schedule Office of the Controller of the currency",
    "EO": "FDIC executive pay",
    "EP": "Defense Intelligence Senior Executive Service",
    "ES": "Senior Executive Service (SES)",
    "ET": "General Accounting Office Senior Executive Service",
    "EX": "Executive pay",
    "FA": "Foreign Service Chiefs of Mission",
    "FC": "Foreign compensation Agency for International Development",
    "FD": "Foreign defense",
    "FE": "Senior Foreign Service",
    "FO": "Foreign Service Officers",
    "FP": "Foreign Service personnel",
    "FZ": "Consular Agent Department of State",
    "GD": "Skill based pay demonstration project managers (DLA)",
    "GG": "Grades similar to General Schedule",
    "GH": "GG employees converted to performance and management recognition system",
    "GM": "Performance Management and Recognition system",
    "GN": "Nurse at Warren G. Magnuson Clinical Center",
    "GS": "General Schedule",
    "GW": "Employment under schedule A paid at GS rate Stay-In-School program",
    "JG": "Graded tradesmen and craftsmen United States Courts",
    "JL": "Leaders of tradesmen and craftsmen United States Courts",
    "JP": "Non supervisory lithographers and printers United States Courts",
    "JQ": "Lead lithographers and printers United States Courts",
    "JR": "Supervisory lithographers and printers United States Courts",
    "JT": "KA Kleas Act Government Printing Office",
    "KA": "Kleas Act Government Printing Office",
    "KG": "Non-Craft non supervisory Bureau of Engraving and Printing",
    "KL": "Non-Craft leader Bureau of Engraving and Printing",
    "KS": "Non-Craft supervisory Bureau of Engraving and Printing",
    "LE": "United States Secret Service uniformed division Treasury",
    "LG": "Liquidation graded FDIC",
    "MA": "Milk Marketing Department of Agriculture",
    "MC": "Cadet",
    "ME": "Enlisted",
    "MO": "Officer",
    "MW": "Warrant officer",
    "NA": "Non appropriated funds, non supervisory, non leader Federal Wage System",
    "NS": "Non appropriated funds, supervisory, Federal Wage System",
    "OC": "Office of the Comptroller of the Currency",
    "PA": "Attorneys and law clerks General Accounting Office",
    "PE": "Evaluator and evaluator related General Accounting Office",
    "PG": "Printing Office grades",
    "RS": "Senior Biomedical Service",
    "SA": "Administrative schedule Tennessee Valley Authority",
    "SB": "Clerical schedule (excluded) Tennessee Valley Authority",
    "SC": "Engineering and Computing schedule Tennessee Valley Authority",
    "SD": "Scientific and Programming schedule Tennessee Valley Authority",
    "SE": "Aide and Technician schedule Tennessee Valley Authority",
    "SF": "Custodial schedule Tennessee Valley Authority",
    "SG": "Public Safety schedule Tennessee Valley Authority",
    "SH": "Physicians schedule Tennessee Valley Authority",
    "SJ": "Scientific and Programming schedule (excluded) Tennessee Valley Authority",
    "SL": "Senior Level Positions",
    "SM": "Management Schedule Tennessee Valley Authority",
    "SN": "Senior Level System Nuclear Regulatory Commission",
    "SP": "Park Police Department of the Interior",
    "SR": "Statutory rates not elsewhere specified",
    "SS": "Senior Staff positions",
    "ST": "Scientific and professional",
    "SZ": "Canal Area Special category type positions",
    "TA": "Construction schedule",
    "TB": "Operating and Maintenance (power facilities) Tennessee Valley Authority",
    "TC": "Chemical Operators Tennessee Valley Authority",
    "TD": "Plant Operators schedule Tennessee Valley Authority",
    "TE": "Operating and Maintenance (nonpower facilities) Tennessee Valley Authority",
    "TM": "Federal Housing Finance board Executive level",
    "TP": "Teaching positions DoD schools only",
    "TR": "Police Forces US Mint and Bureau of Engraving and Printing",
    "TS": "Step System Federal Housing Finance board",
    "VC": "Canteen Service Department of Veterans Affairs",
    "VG": "Clerical and Administrative support Farm Credit",
    "VH": "Professional, Administrative, and Managerial Farm Credit",
    "VM": "Medical and Dental Department of Veterans Affairs",
    "VN": "Nurses Department of Veterans Affairs",
    "VP": "Clinical Podiatrists and Optometrists Department of Veterans Affairs",
    "WA": "Navigation Lock and Dam Operation and maintenance Supervisory USACE",
    "WB": "Wage positions under Federal Wage System otherwise not designated",
    "WD": "Production facilitating non supervisory Federal Wage System",
    "WE": "Currency manufacturing Department of the Treasury",
    "WG": "Non supervisory pay schedule Federal Wage System",
    "WJ": "Hopper Dredge Schedule Supervisory Federal Wage System Dept of Army",
    "WK": "Hopper Dredge Schedule non supervisory Federal Wage System Dept of Army",
    "WL": "Leader pay schedules Federal Wage System",
    "WM": "Maritime pay schedules",
    "WN": "Production facilitating supervisory Federal Wage System",
    "WO": "Navigation Lock and Dam Operation and maintenance leader USACE",
    "WQ": "Aircraft Electronic Equipment and Optical Inst. repair supervisory",
    "WR": "Aircraft Electronic Equipment and Optical Inst. repair leader",
    "WS": "Supervisor Federal Wage System",
    "WT": "Apprentices and Shop trainees Federal Wage System",
    "WU": "Aircraft Electronic Equipment and Optical Inst. repair non supervisory",
    "WW": "Wage type excepted Stay-In-School Federal Wage System",
    "WY": "Navigation Lock and Dam Operation and maintenance non supervisory USACE",
    "WZ": "Canal Area Wage System type positions",
    "XA": "Special Overlap Area Rate Schedule non supervisory Dept of the Interior",
    "XB": "Special Overlap Area Rate Schedule leader Dept of the Interior",
    "XC": "Special Overlap Area Rate Schedule supervisory Dept of the Interior",
    "XD": "Non supervisory production facilitating special schedule printing employees",
    "XF": "Floating Plant Schedule non supervisory Dept of Army",
    "XG": "Floating Plant Schedule leader Dept of Army",
    "XH": "Floating Plant Schedule supervisory Dept of Army",
    "XL": "Leader special schedule printing employees",
    "XN": "Supervisory production facilitating special schedule printing employees",
    "XP": "Non supervisory special schedule printing employees",
    "XS": "Supervisory special schedule printing employees",
    "YV": "Temporary summer aid employment",
    "YW": "Student aid employment Stay-In-School",
    "ZA": "Administrative National Institute of Standards and Technology",
    "ZP": "Scientific and Engineering Professional National Institute of Standards and Technology",
    "ZS": "Administrative Support National Institute of Standards and Technology",
    "ZT": "Scientific and Engineering Technician National Institute of Standards and Technology",
    "ZZ": "Not applicable (use only with pay basis without compensation when others N/A)",
}


class DoD:
    def __init__(self):
        pass

    def decode_cac_barcode(self, data):
        # CAC barcodes are less identifiable, with no header or length info.
        # Details outlined on PDF page 21
        version = data[0]
        assert version in "N1", "Unimplemented barcode version: {0}".format(version)

        if version == "1":
            parsedData = self._decode_cac_barcode_v1(data)
        elif version == "N":
            parsedData = self._decode_cac_barcode_v_n(data)

        return parsedData

    def _decode_cac_barcode_v1(self, data):
        # Person Identifier (Usually SSN, etc.)
        try:
            person_identifier = base32_to_int(data[1:7])
        except KeyError as e:
            raise ParseError(e)

        # Describes type of Person Identifier
        person_designator = data[7]  # See appendix C (PDF page 58)
        assert person_designator in list(
            PERSON_DESIGNATOR_TYPES.keys()
        ), "Invalid person designator type '{0}'".format(person_designator)

        # DEERS-specific ID number
        try:
            edi_person_identifier = base32_to_int(data[8:15])
        except KeyError as e:
            raise ParseError(e)
        # Longs apparently don't have a len() function, so:
        assert len(str(edi_person_identifier)) == 10

        # First name (20 chars)
        first_name = data[15:35].strip()

        # Surname:
        surname = data[35:61].strip()

        # DOB is compressed (4 chars)
        DOB = date_from_julian(data[61:65])

        person_category_code = data[65]
        branch_code = data[66]
        entitlement_type = data[67:69]
        rank = data[69:75].strip()
        pay_plan_code = data[75:77]
        pay_grade_code = data[77:79]

        issue_date = date_from_julian(data[79:83])
        expiration_date = date_from_julian(data[83:87])

        card_instance = data[87]

        # FIXME: Add _type elements
        return {
            "version": "N",
            "pdi": person_identifier,
            "designator_code": person_designator,
            "designator_type": PERSON_DESIGNATOR_TYPES[person_designator],
            "edipi": edi_person_identifier,
            "first": first_name,
            "last": surname,
            "middle": "",
            "dob": DOB,
            "category_code": person_category_code,
            "branch_code": branch_code,
            "branch_type": BRANCH_CODES[branch_code],
            "entitlement_code": entitlement_type,
            "entitlement_type": PERSON_ENTITLEMENT_CONDITIONS[entitlement_type],
            "rank": rank,
            "payplan_code": pay_plan_code,
            # ~ 'payplan_type' : PAY_PLAN_CODES[pay_plan_code],
            "paygrade_code": pay_grade_code,
            # ~ 'playgrade_type' : ?
            "issued": issue_date,
            "expiry": expiration_date,
            "instance": card_instance,
        }

    def _decode_cac_barcode_v_n(self, data):
        """
        Basically the same as v1, but with one extra field at the end.
        We could combine these to save bits, but meh.
        """
        try:
            person_identifier = base32_to_int(data[1:7])
        except KeyError as e:
            raise ParseError(e)

        # Describes type of Person Identifier
        person_designator = data[7]  # See appendix C (PDF page 58)
        assert person_designator in list(
            PERSON_DESIGNATOR_TYPES.keys()
        ), "Invalid person designator type '{0}'".format(person_designator)

        # DEERS-specific ID number
        try:
            edi_person_identifier = base32_to_int(data[8:15])
        except KeyError as e:
            raise ParseError(e)
        # Longs apparently don't have a len() function, so:
        assert len(str(edi_person_identifier)) == 10

        # First name (20 chars)
        first_name = data[15:35].strip()

        # Surname:
        surname = data[35:61].strip()

        # DOB is compressed (4 chars)
        DOB = date_from_julian(data[61:65])

        person_category_code = data[65]
        branch_code = data[66]
        entitlement_type = data[67:69]
        rank = data[69:75].strip()
        pay_plan_code = data[75:77]
        pay_grade_code = data[77:79]

        issue_date = date_from_julian(data[79:83])
        expiration_date = date_from_julian(data[83:87])

        card_instance = data[87]
        middle_initial = data[88]

        # FIXME: Add _type elements
        return {
            "version": "N",
            "pdi": person_identifier,
            "designator_code": person_designator,
            "designator_type": PERSON_DESIGNATOR_TYPES[person_designator],
            "edipi": edi_person_identifier,
            "first": first_name,
            "last": surname,
            "middle": middle_initial,
            "dob": DOB,
            "category_code": person_category_code,
            "branch_code": branch_code,
            "branch_type": BRANCH_CODES[branch_code],
            "entitlement_code": entitlement_type,
            "entitlement_type": PERSON_ENTITLEMENT_CONDITIONS[entitlement_type],
            "rank": rank,
            "payplan_code": pay_plan_code,
            # ~ 'payplan_type' : PAY_PLAN_CODES[pay_plan_code],
            "paygrade_code": pay_grade_code,
            # ~ 'playgrade_type' : ?
            "issued": issue_date,
            "expiry": expiration_date,
            "instance": card_instance,
        }

    def _decode_barcode(self, data):
        # Extract header and run sanity checks
        header = data[0:9]
        assert len(header) == 9, "Header record too short ({0})".format(len(header))

        # PDF417 DoD ID format always starts with the string "IDUS"
        id_code = header[0:4]
        assert (
                id_code == "IDUS"
        ), "Invalid Identification code '{0}'. Not a DoD ID card.".format(id_code)

        # Check barcode version
        version = int(header[4])
        assert version in PDF_VERSIONS, "Unimplemented barcode version: {0}".format(
            version
        )

        size = int(header[5:7]) + 7
        check_sum = int(header[7])
        rapids_size = int(header[8])


class NotImplemented(Exception):
    pass


class ReadError(Exception):
    pass


class ParseError(Exception):
    pass


def date_from_julian(inp):
    """
    Convert a base32-hex (Triacontakaidecimal) encoded Julian date to a
    python datetime object.
    """
    julian = base32_to_int(inp)
    return datetime.timedelta(julian) + datetime.date(1000, 1, 1)


def base32_to_int(inp):
    """
    Converts a base32-hex (Triacontakaidecimal) encoded string to an integer
    """
    base32dict = dict(
        (c, int(c, 32)) for c in ("0123456789abcdefghijklmnopqrstuv")[:32]
    )
    inp = inp.lower()  # convert to lowercase

    out = 0
    place = 1

    for i in inp[::-1]:  # little endian
        digit = base32dict[i]  # lookup corresponding value of current digit
        out += digit * place  # multiply by place value
        place *= 32  # incrament the place value

    return out


def int_to_base32(inp):
    """
    Encodes an integer as base32-hex (Triacontakaidecimal) as used by some DoD
    date and number compressions.  Ignores sign and returns a string.
    """
    if inp == 0:
        return "0"
    base32 = "0123456789abcdefghijklmnopqrstuv"
    digits = []
    while inp:
        digits.append(base32[inp % 32])
        inp /= 32
    digits.reverse()
    return "".join(digits)


if __name__ == "__main__":
    import pprint

    decoder = DoD()
    # reading from a serial barcode reader
    import serial

    ser = serial.Serial("/dev/ttyUSB0")
    while True:
        charbuffer = ""
        print("Scan an ID")
        while charbuffer[-2:] != "\r\n":
            char = ser.read(1)
            charbuffer += char
        # try:
        print("Got string: " + charbuffer + "\n\n\n\n")

        pprint.pprint(decoder.decode_cac_barcode(charbuffer))
