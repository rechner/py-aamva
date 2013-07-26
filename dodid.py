#!/usr/bin/env python
#*-* coding: utf-8 *-*

import datetime

#3 versions in circulation (no version 0?)
PDF_VERSIONS = range(1, 4)
PERSON_DESIGNATOR_TYPES = { 'S' : 'Social Security Number',
  'N' : 'Non-SSN Identifier', 'P' : 'Pre-SSN Identifier',
  'D' : 'Temporary Identifier Number',
  'F' : 'Forgein Identifier Number', 
  'T' : 'Test Identification Number',
  'I' : 'Taxpayer ID' }
PERSON_DESIGNATOR_TYPES_TOOLTIPS = { 'S' : 'Social Security Number',
  'N' : 'Nine-digit code that looks like an SSN, but is not in a valid SSN range.',
  'P' : 'Special nine-digit code created for U.S. military personnel ' +
    'from Service numbers before the switch to SSNs.',
  'D' : 'Special nine-digit code created for individuals (i.e., babies) ' +
    'who do not have or have not provided an SSN when the person is ' +
    'added to DEERS (dependents only). Known as a Temporary ' +
    'Identifier Number (TIN).',
  'F' : 'Special nine-digit code created for foreign military and ' +
    'nationals. Known as a Foreign Identifier Number (FIN).',
  'T' : 'Test (858 series)',
  'I' : 'Individual Taxpayer Identification Number' }
BRANCH_CODES = { 'A' : 'USA', 'C' : 'USCG', 'D' : 'DoD', 'F' : 'USAF',
  'H' : 'USPHS', 'M' : 'USMC', 'N' : 'USN', 'O' : 'NOAA', 
  '1' : 'Forgein Army', '2' : 'Forgein Navy', '3' : 'Forgein Marine Corps',
  '4' : 'Forgein Air Force', 'X' : 'Other' }
PERSON_IDENTIFIER_CODES = { 'A' : 'Active Duty', 
  'B' : 'Presidential Appointee', 'C' : 'DoD civil service employee',
  'D' : '100% disabled American veteran',
  'E' : 'DoD contract employee',
  'F' : 'Former member', 'P' : 'Former member',
  'N' : 'National Guard member', 'G' : 'National Guard member',
  'H' : 'Medal of Honour recipient',
  'I' : 'Non-DoD civil service employee',
  'J' : 'Academy student',
  'K' : 'NAF DoD employee',
  'L' : 'Lighthouse service',
  'M' : 'NGO personnel',
  'O' : 'Non-DoD contract employee', 
  'Q' : 'Non-eligible Reserve retiree',
  'R' : 'Retired',
  'V' : 'Active duty Reserve', 'S' : 'Active duty Reserve',
  'T' : 'Foreign military member',
  'U' : 'Foreign national employee',
  'V' : 'Reserve member',
  'W' : 'DoD beneficiary',
  'Y' : 'Retired DoD Civil Service' }
PERSON_ENTITLEMENT_CONDITIONS = { 
  '00' : 'Unknown', #This is undocumented, but found in real-world cards
  '01' : 'Active duty',
  '02' : 'Mobilization', '03' : 'On appellate leave',
  '04' : 'Military prisoner', '05' : 'POW/MIA',
  '06' : 'Separated from Selected Reserve',
  '07' : 'Permanently disabled',
  '08' : 'Non-CONUS assignment', 
  '09' : 'Living in Guam or Puerto Rico',
  '10' : 'Living in government quarters',
  '11' : 'Death from injury, illness, or disease on active duty',
  '12' : 'Discharged due to misconduct involving family member abuse. ' +
    '(Sponsors who are eligible for retirement)',
  '13' : 'Granted retired pay',
  '14' : 'DoD sponsored in U.S. (foreign military)',
  '15' : 'DoD non-sponsored in U.S. (foreign military)',
  '16' : 'DoD sponsored overseas',
  '17' : 'Deserter',
  '18' : 'Discharged due to misconduct involving family member abuse. ' +
    '(Sponsors who are not eligible for retirement)',
  '19' : 'Reservist who dies after receiving their 20 year letter',
  '20' : 'Transitional assistance (TA-30)',
  '21' : 'Transitional assistance (TA-Res)',
  '22' : 'Transitional assistance (TA-60)',
  '23' : 'Transitional assistance (TA-120)',
  '24' : 'Transitional assistance (SSB program)',
  '25' : 'Transitional assistance (VSI program)',
  '26' : 'Transitional assistance (composite)',
  '27' : 'Senior Executive Service',
  '28' : u'Emergency Essential — overseas only',
  '29' : u'Emergency Essential – CONUS',
  '30' : u'2 Emergency Essential – CONUS living in quarters, living ' +
    'on base, and not drawing a basic allowance for quarters',
  '31' : 'Reserve Component TA-120 Reserve Component Transition ' +
    'Assistance TA 120 (Jan 1, 2002 or later)',
  '32' : 'On MSC owned and operated vessels Deployed to foreign ' +
    'countries on Military Sealift Command owned and operated vessels',
  '33' : 'Guard/Reserve Alert Notification Period',
  '34' : u'Reserve Component TA-180 – 180 days TAMPS for reserve ' +
    'return from named contingencies (was 60 before Nov 5 2003)',
  '35' : u'Reserve Component TA-180 – 180 days TAMPS for reserve ' +
    'return from named contingencies (was 120 before Nov 5 2003)',
  '36' : u'TA-180 – 180 days TAMP for involuntary separation',
  '37' : u'TA-180 — 180 days TAMPS for involuntary separation',
  '38' : 'Living in Government Quarters in Guam or Puerto Rico, ' +
    'Living on base and not drawing an allowance for quarters in ' +
    'Guam or Puerto Rico.',
  '39' : u'Reserve Component TA-180 – TAMP – Mobilized for Contingency',
  '40' : u'TA – 180 TAMP – SPD Code Separation',
  '41' : u'TA-180 – TAMP – Stop/Loss Separation',
  '42' : u'DoD Non-Sponsored Overseas – Foreign Military personnel ' +
    'serving OCONUS not sponsored by DoD' }
PAY_PLAN_CODES = { 'AF' : 'American Family Members',
  'AD' : 'Administratively determined not elsewhere specified',
  'AJ' : 'Administrative judges, Nuclear Regulatory Commission',
  'AL' : 'Administrative Law judges',
  'BB' : 'Non supervisory negotiated pay employees',
  'BL' : 'Leader negotiated pay employees',
  'BP' : 'Printing and Lithographic negotiated pay employees',
  'BS' : 'Supervisory negotiated pay employees',
  'CA' : 'Board of contract appeals',
  'CC' : 'Commissioned Corps of Public Heath Service',
  'CE' : 'Contract education',
  'CG' : 'Corporate graded Federal Deposit Insurance Corp',
  'CP' : 'Compensation program Office of the Comptroller of the currency',
  'CS' : 'Skill Based Pay demonstration employees, DLA',
  'CU' : 'Credit Union employees',
  'CY' : 'Contract education Bureau of Indian Affairs',
  'CZ' : 'Canal Area General Schedule type positions',
  'DA' : 'Demonstration administrative Director of Laboratory Programs (Navy)',
  'DG' : 'Demonstration general Director of Laboratory Programs (Navy)',
  'DH' : 'Demonstration hourly Air Force logistics command',
  'DN' : 'Defense Nuclear facilities safety board',
  'DP' : 'Demonstration professional Director of Laboratory Programs (Navy)',
  'DS' : 'Demonstration specialist Director of Laboratory Programs (Navy)',
  'DT' : 'Demonstration technician Director of Laboratory Programs (Navy)',
  'DW' : 'Demonstration salaried Air Force and DLA',
  'DX' : 'Demonstration Supervisory Air Force and DLA',
  'EA' : 'Administrative schedule (excluded) Tennessee Valley Authority',
  'EB' : 'Clerical schedule (excluded) Tennessee Valley Authority',
  'EC' : 'Engineering and Computing schedule (excluded) Tennessee Valley Authority',
  'ED' : 'Expert', 'EE' : 'Expert (other)', 'EF' : 'Consultant', 
  'EG' : 'Consultant (other)', 'EH' : 'Advisory committee member',
  'EI' : 'Advisory committee member (other)', 
  'EM' : 'Executive schedule Office of the Controller of the currency',
  'EO' : 'FDIC executive pay',
  'EP' : 'Defense Intelligence Senior Executive Service',
  'ES' : 'Senior Executive Service (SES)' } #FIXME: Finish this from PDF page 67
  

  
  

class DoD:
  def __init__(self):
    pass
    
  def _decodeCACBarcode(self, data):
    #CAC barcodes are less identifiable, with no header or length info.
    #Details outlined on PDF page 21
    version = data[0]
    assert version in "N1", \
      "Unimplemented barcode version: {0}".format(version)
      
    if version == '1':
      parsedData = self._decodeCACBarcode_v1(data)
    elif version == 'N':
      parsedData = self._decodeCACBarcode_vN(data)
      
    return parsedData
    
    
  def _decodeCACBarcode_v1(self, data):
    #Person Identifier (Usually SSN, etc.)
    try:
      personIdentifier = base32toint(data[1:7])
    except KeyError as e:
      raise ParseError(e)
      
    #Describes type of Person Identifier
    personDesignator = data[7] #See appendix C (PDF page 58)
    assert personDesignator in PERSON_DESIGNATOR_TYPES.keys(), \
      "Invalid person designator type '{0}'".format(personDesignator)
      
    #DEERS-specific ID number
    try:
      EDIPersonIdentifier = base32toint(data[8:15])
    except KeyError as e:
      raise ParseError(e)
    #Longs apparently don't have a len() function, so:
    assert len(str(EDIPersonIdentifier)) == 10
    
    #First name (20 chars)
    firstName = data[15:35].strip()
    
    #Surname:
    surname = data[35:61].strip()
    
    #DOB is compressed (4 chars)
    DOB = dateFromJulian(data[61:65])
    
    personCategoryCode = data[65]
    branchCode = data[66]
    EntitlementType = data[67:69]
    rank = data[69:75].strip()
    payPlanCode = data[75:77]
    payGradeCode = data[77:79]
    
    issueDate = dateFromJulian(data[79:83])
    expirationDate = dateFromJulian(data[83:87])
    
    cardInstance = data[87]
    
    #FIXME: Add _type elements
    return { 'version' : 'N', 'pdi' : personIdentifier,
      'designator_code' : personDesignator,
      'designator_type' : PERSON_DESIGNATOR_TYPES[personDesignator],
      'edipi' : EDIPersonIdentifier, 
      'first' : firstName, 'last' : surname, 'middle' : '',
      'dob' : DOB, 'category_code' : personCategoryCode,
      'branch_code' : branchCode, 'branch_type' : BRANCH_CODES[branchCode],
      'entitlement_code' : EntitlementType, 
      'entitlement_type' : PERSON_ENTITLEMENT_CONDITIONS[EntitlementType],
      'rank' : rank, 'payplan_code' : payPlanCode, 
      #~ 'payplan_type' : PAY_PLAN_CODES[payPlanCode],
      'paygrade_code' : payGradeCode,
      #~ 'playgrade_type' : ?
      'issued' : issueDate, 'expiry' : expirationDate,
      'instance' : cardInstance }
    
  def _decodeCACBarcode_vN(self,data):
    """
    Basically the same as v1, but with one extra field at the end.
    We could combine these to save bits, but meh.
    """
    try:
      personIdentifier = base32toint(data[1:7])
    except KeyError as e:
      raise ParseError(e)
      
    #Describes type of Person Identifier
    personDesignator = data[7] #See appendix C (PDF page 58)
    assert personDesignator in PERSON_DESIGNATOR_TYPES.keys(), \
      "Invalid person designator type '{0}'".format(personDesignator)
      
    #DEERS-specific ID number
    try:
      EDIPersonIdentifier = base32toint(data[8:15])
    except KeyError as e:
      raise ParseError(e)
    #Longs apparently don't have a len() function, so:
    assert len(str(EDIPersonIdentifier)) == 10
    
    #First name (20 chars)
    firstName = data[15:35].strip()
    
    #Surname:
    surname = data[35:61].strip()
    
    #DOB is compressed (4 chars)
    DOB = dateFromJulian(data[61:65])
    
    personCategoryCode = data[65]
    branchCode = data[66]
    EntitlementType = data[67:69]
    rank = data[69:75].strip()
    payPlanCode = data[75:77]
    payGradeCode = data[77:79]
    
    issueDate = dateFromJulian(data[79:83])
    expirationDate = dateFromJulian(data[83:87])
    
    cardInstance = data[87]
    middleInitial = data[88]
    
    #FIXME: Add _type elements
    return { 'version' : 'N', 'pdi' : personIdentifier,
      'designator_code' : personDesignator,
      'designator_type' : PERSON_DESIGNATOR_TYPES[personDesignator],
      'edipi' : EDIPersonIdentifier, 
      'first' : firstName, 'last' : surname, 'middle' : middleInitial,
      'dob' : DOB, 'category_code' : personCategoryCode,
      'branch_code' : branchCode, 'branch_type' : BRANCH_CODES[branchCode],
      'entitlement_code' : EntitlementType, 
      'entitlement_type' : PERSON_ENTITLEMENT_CONDITIONS[EntitlementType],
      'rank' : rank, 'payplan_code' : payPlanCode, 
      #~ 'payplan_type' : PAY_PLAN_CODES[payPlanCode],
      'paygrade_code' : payGradeCode,
      #~ 'playgrade_type' : ?
      'issued' : issueDate, 'expiry' : expirationDate,
      'instance' : cardInstance }
    
          
    
  def _decodeBarcode(self, data):
    #Extract header and run sanity checks
    header = data[0:9]
    assert len(header) == 9, "Header record too short ({0})".format(len(header))
    
    #PDF417 DoD ID format always starts with the string "IDUS"
    id_code = header[0:4]
    assert id_code == "IDUS",  \
      "Invalid Identification code '{0}'. Not a DoD ID card.".format(id_code)
    
    #Check barcode version  
    version = int(header[4])
    assert version in PDF_VERSIONS, \
      "Unimplemented barcode version: {0}".format(version)
    
    size = int(header[5:7]) + 7
    checkSum = int(header[7])
    rapids_size = int(header[8])
    
    
class NotImplemented(Exception):
  pass
  
class ReadError(Exception):
  pass
  
class ParseError(Exception):
  pass
    
def dateFromJulian(inp):
  """
  Convert a base32-hex (Triacontakaidecimal) encoded Julian date to a
  python datetime object.
  """
  julian = base32toint(inp)
  return datetime.timedelta(julian) + datetime.date(1000, 1, 1)
  

def base32toint(inp):
  """
  Converts a base32-hex (Triacontakaidecimal) encoded string to an integer
  """
  base32dict = dict((c,int(c,32)) for c in ('0123456789abcdefghijklmnopqrstuv')[:32])
  inp = inp.lower() #convert to lowercase
  
  out = 0
  place = 1
  
  for i in inp[::-1]: #little endian
    digit = base32dict[i]  #lookup corresponding value of current digit
    out += (digit * place) #multiply by place value
    place *= 32 #incrament the place value
    
  return out
  

def inttobase32(inp):
  """
  Encodes an integer as base32-hex (Triacontakaidecimal) as used by some DoD
  date and number compressions.  Ignores sign and returns a string.
  """
  if inp == 0: return '0'
  base32 = '0123456789abcdefghijklmnopqrstuv'
  digits = []
  while inp:
    digits.append(base32[inp % 32])
    inp /= 32
  digits.reverse()
  return ''.join(digits)
  
  
if __name__ == '__main__':
  import pprint
  decoder = DoD()
  #reading from a serial barcode reader
  import serial
  ser = serial.Serial('/dev/ttyUSB0')
  while True:
    charbuffer = ""
    print "Scan an ID"
    while charbuffer[-2:] != '\r\n':
      char = ser.read(1)
      charbuffer += char
    #try:
    print "Got string: " + charbuffer + "\n\n\n\n"
    
    pprint.pprint(decoder._decodeCACBarcode(charbuffer))
    
    
    
