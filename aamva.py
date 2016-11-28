#!/usr/bin/env python
#*-* coding: utf-8 *-*

# aamva.py
#
# Copyright © 2013 Zachary Sturgeon <jkltechinc@gmail.com>
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

#TODO: Implement reading in straight from the device instead of just
# keyboard support: http://blog.flip-edesign.com/_rst/MagTek_USB_Card_Reader_Hacking_with_Python.html
#TODO: Add federal commercial driving codes "DCH" to all versions.

import datetime

debug = True

if debug: import pprint

""" Constants and signals """ #Better way to do this?
ANY = 0
MAGSTRIPE = 1
PDF417 = 2
SMARTCARD = 4
METRIC = 8
IMPERIAL = 16
MALE = 'M'
FEMALE = 'F'
DRIVER_LICENSE = 128
IDENTITY_CARD = 256
EYECOLOURS = ['BLK', 'BLU', 'BRO', 'GRY', 'HAZ', 'MAR', 'PNK', 'DIC',
              'UNK', 'GRN']
HAIRCOLOURS = ['BAL', 'BLK', 'BLN', 'BRO', 'GRY', 'RED', 'SDY', 'WHI',
               'UNK']
#Human-readable weight ranges
METRIC_WEIGHTS = { 0 : '0 - 31 kg', 1 : '32 - 45 kg', 2 : '46 - 59 kg',
                   3 : '60 - 70 kg', 4 : '71 - 86 kg', 5 : '87 - 100 kg',
                   6 : '101 - 113 kg', 7 : '114 - 127 kg',
                   8 : '128 - 145 kg', 9 : '146+ kg' }
IMPERIAL_WEIGHTS = { 0 : '0 - 70 lbs', 1 : '71 - 100 lbs',
                     2 : '101 - 130 lbs', 3 : '131 - 160 lbs',
                     4 : '161 - 190 lbs', 5 : '191 - 220 lbs',
                     6 : '221 - 250 lbs', 7 : '251 - 280 lbs',
                     8 : '281 - 320 lbs', 9 : '321+ lbs' }

#PDF417 format specifications and validations
PDF_LINEFEED = '\x0A'  # '\n' (line feed)
PDF_RECORDSEP = '\x1E' # record seperator
PDF_SEGTERM = '\x0D'   # '\r' segment terminator (carriage return)
PDF_FILETYPE = 'ANSI ' # identifies the file as an AAMVA compliant
PDF_VERSIONS = range(64) # decimal between 0 - 63
PDF_ENTRIES = range(1, 100) #decimal number of subfile identifiers


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
    if data == None:
      data = self.data
    if data == None:
      raise ValueError('No data to parse')

    for form in self.format:
      if form == ANY or form == MAGSTRIPE:
        try:
          return self._decodeMagstripe(data)
        except (IndexError, AssertionError) as e:
          if form == MAGSTRIPE: raise ReadError(e)
          #fail silently and continue to the next format
      if form == ANY or form == PDF417:
        #~ pprint.pprint(data)
        #~ return self._decodeBarcode(data)
        try:
          return self._decodeBarcode(data)
        except (IndexError, AssertionError, ReadError) as e:
          log(e)
          raise ReadError("Unable to decode as barcode")


  def _decodeMagstripe(self, data):
    fields = data.split('^') #split the field seperators
    #check for start of sentinel character
    assert fields[0][0] == '%', 'Missing start sentinel character (%)'
    assert fields[0][0:3] != '%E?', 'Error reading card'

    state = fields[0][1:3]
    city = fields[0][3:16]
    if len(city) == 13 and '^' not in city:
      #City maxes out at 13 characters, and excludes the field
      #separator.  Thus, name will be in the first field.
      #city+name+address together should be no longer than 77 chars.
      name_pre = fields[0][16:]
      address = fields[1].split('$')
      remaining = fields[2] #track 2 data will be one behind in this case
    else:
      name_pre = fields[1]
      address = fields[2].split('$')[0]
      remaining = fields[3] #track 2 & 3

    assert len(name_pre) > 0, "Empty name field"
    assert '$' in name_pre, "Name field missing delimiter ($)"
    #entire name field is 35 characters with delimiters
    name = name_pre.split('$')
    middle = None
    if len(name) == 3:
      middle = name[2]

    remaining = remaining.split('?')[1:3] #remove prepended end sentinel

    #track 2 start sentinel character
    assert remaining[0][0] == ';', "Missing track 2 start sentinel (;)"
    track2 = remaining[0].strip(';')
    track2 = track2.split('=')
    track3 = remaining[1]

    assert len(track2) == 2 or len(track2) == 3, "Invalid track 2 length"
    issueIdentifier = track2[0][0:6]
    if len(track2) == 3:
      #up to 13 digits, overflow for more at end of track 2.
      #in this case there's no overflow, indicated by the extra = seperator.
      licenseNumber = track2[0][6:20]
    else:
      licenseNumber = track2[0][6:20] + track2[1][13:25]

    expiryStr = track2[1][0:4] #e.g. 1310 for 31 October 2013
    expiry = datetime.date(2000 + int(expiryStr[0:2]),
                  int(expiryStr[2:4])+1, 1) - datetime.timedelta(days=1)

    dobStr = track2[1][4:12] #e.g. 19850215
    dob = datetime.date(int(dobStr[0:4]), int(dobStr[4:6]), int(dobStr[6:8]))

    #parse track3:
    template = track3[1:2] #FIXME: according to A.4.3 should only be 0,2 but mine says 1
    security = track3[2:3] #FIXME: docs says 1 character long but says 00-63 are valid values.
    postalCode = track3[3:14].strip() #remove space padding
    licenseClass = track3[14:16].strip()
    restrictions = track3[16:26].strip()
    endorsements = track3[26:30].strip() #according to ANSI-20 4.11.7
    sex = track3[30:31]
    height = track3[31:34].strip()
    weight = track3[34:37].strip() #lbs for US, kg for CA/MX
    hair = track3[37:40]
    eyes = track3[40:43]

    #assert 'F' in sex or 'M' in sex, "Invalid sex %s" % sex
    assert height.isdigit() or height == '', "Invalid height"
    assert weight.isdigit() or weight == '', "Invalid weight"
    #assert hair in HAIRCOLOURS, "Invalid hair colour %s" % hair
    #assert eyes in EYECOLOURS, "Invalid eye colour %s" % eyes

    #Since there's no way to determine if a magstripe is for USA or
    #Canada, we'll just have to set a default and assume units:
    #cast weight to Weight() type:
    if weight != '':
      weight = Weight(None, int(weight), 'USA')
    else:
      weight == None
    #cast height (Also assumes no one is taller than 9'11"
    height = Height((int(height[0])*12)+int(height[1:]), 'USA')

    return { 'first' : name[1], 'last' : name[0],
             'middle' : middle, 'city' : city, 'state' : state,
             'address' : address, 'IIN' : issueIdentifier,
             'licenseNumber' : licenseNumber, 'expiry' : expiry,
             'dob' : dob, 'ZIP' : postalCode, 'class' : licenseClass,
             'restrictions' : restrictions,
             'endorsements' : endorsements, 'sex' : sex,
             'height' : height, 'weight' : weight, 'hair' : hair,
             'eyes' : eyes, 'issued' : None, 'units' : IMPERIAL,
             'suffix' : None, 'prefix' : None }


  def _decodeBarcode(self, data):
    #header
    segterm = PDF_SEGTERM
    #check for compliance character:
    assert data[0] == '@', 'Missing compliance character (@)'
    assert data[1] == PDF_LINEFEED, 'Missing data element separator (LF)'
    if data[2] == '\x1C':
      #SCDMV sample deviates from standard here
      log("RECORDSEP (0x1E) missing, got FS instead (0x1C, SCDMV)")
      #segterm = '\x0a' # Have to override to work with SC old format
    else:
      assert data[2] == PDF_RECORDSEP, 'Missing record separator (RS)'
    assert data[3] == PDF_SEGTERM, 'Missing segment terminator (CR)'
    assert data[4:9] == PDF_FILETYPE, \
      'Wrong file type (got "%s", should be "ANSI ")' % data[4:9]
    issueIdentifier = data[9:15]
    assert issueIdentifier.isdigit(), 'Issue Identifier is not an integer'
    version = int(data[15:17])
    assert version in PDF_VERSIONS, \
      'Invalid data version number (got %s, should be 0 - 63)' % version

    log("Format version: " + str(version))
    #import pdb; pdb.set_trace()

    parsedData = ""
    revOffset = 0
    if version in (0, 1):
      nEntries = data[17:19]
      assert nEntries.isdigit(), 'Number of entries is not an integer'
      nEntries = int(nEntries)
      log("Entries: " + str(nEntries))
      #subfile designator
      # FIXME could also be 'ID'
      assert data[19:21] == 'DL', \
        "Not a driver's license (Got '%s', should be 'DL')" % data[19:21]
      offset = data[21:25]
      assert offset.isdigit(), 'Subfile offset is not an integer'
      offset = int(offset)
      length = data[25:29]
      assert length.isdigit(), 'Subfile length is not an integer'
      length = int(length)
      decodeFunction = self._decodeBarcode_v1

      #parse subfile designators
      readOffset = 0
      recordType = None

      for fileId in range(nEntries):
        #Read each subfile designator
        log("=== Subfile {0} ===".format(fileId))
        if recordType is None: #Subfile type determines document type
          recordType = data[readOffset+19:readOffset+21]
        offset = data[readOffset+21:readOffset+25]
        length = data[readOffset+25:readOffset+29]
        assert offset.isdigit(), 'Subfile offset is not an integer'
        assert length.isdigit(), 'Subfile length is not an integer'
        offset = int(offset) - 1
        length = int(length) +2
        log("Offset: {0}".format(offset))
        log("Length: {0}".format(length))
        parsedData += data[offset:offset+length] #suck in all of record
        log(data[offset:offset+length])
        log("=== End Subfile ===")
        readOffset += 10


    elif version in (2, 3, 4, 5, 6):
      #version 2 and later add a jurisdiction field
      jurisdictionVersion = data[17:19]
      assert jurisdictionVersion.isdigit(), \
        'Jurisidiction version number is not an integer'
      nEntries = data[19:21]
      assert nEntries.isdigit(), 'Number of entries is not an integer'
      nEntries = int(nEntries)
      log("Entries: " + str(nEntries))

      #parse subfile designators
      readOffset = 0
      recordType = None
      import pdb; pdb.set_trace()

      for fileId in range(nEntries):
        #Read each subfile designator
        log("=== Subfile {0} ===".format(fileId))
        if recordType is None: #Subfile type determines document type
          recordType = data[readOffset+21:readOffset+23]
        offset = data[readOffset+23:readOffset+27]
        length = data[readOffset+27:readOffset+31]
        assert offset.isdigit(), 'Subfile offset is not an integer'
        assert length.isdigit(), 'Subfile length is not an integer'
        offset = int(offset)
        length = int(length)
        log("Offset: {0}".format(offset))
        log("Length: {0}".format(length))
        parsedData += data[offset:offset+length]  #suck in all of record
        log(data[offset:offset+length])
        log("=== End Subfile ===")
        readOffset += 10

      #~ assert data[21:23] == 'DL', \
        #~ "Not a driver's license (Got '%s', should be 'DL')" % data[21:23]
      #~ offset = data[23:27]
      #~ assert offset.isdigit(), 'Subfile offset is not an integer'
      #~ offset = int(offset)
      #~ print "Offset: " + str(offset)
      #~ length = data[27:31]
      #~ assert length.isdigit(), 'Subfile length is not an integer'
      #~ length = int(length)
      #~ print "Length: " + str(length)

      if version == 3: decodeFunction = self._decodeBarcode_v3
      if version == 4: decodeFunction = self._decodeBarcode_v4
      if version == 5: decodeFunction = self._decodeBarcode_v5
      if version == 6: decodeFunction = self._decodeBarcode_v6

    #Seperate out subfiles, removing trailing empty list
    parsedData = parsedData.split(segterm)[:-1]

    # FIXME: Munging record separator here
    # should probably give subfiles their own encapsulation treatment to better match
    # format of barcode and allow for duplicate subfile fields
    parsedData = [ i.strip('\n') for i in parsedData ] #remove trailing \n's
    parsedData = "".join(parsedData)

    log(parsedData)
    subfile = parsedData.split(PDF_LINEFEED)
    if debug: pprint.pprint(subfile)

    assert subfile[0][:2] == 'DL', "Not a driver's license"
    subfile[0] = subfile[0][2:] #remove prepended "DL"
    subfile[-1] = subfile[-1].strip(segterm)
    #Decode fields as a dictionary
    fields = dict((key[0:3], key[3:].strip()) for key in subfile)

    try:
      return decodeFunction(fields, issueIdentifier)
    except UnboundLocalError as e:
      raise NotImplemented("ERROR: Version {0} decoding not implemented!".format(version))


  def _decodeBarcode_v0(self, data):
    """Decodes a version 0 barcode specification (prior to 2000)"""
    pass #TODO

  def _decodeBarcode_v1(self, fields, issueIdentifier):
    #Version 1 (AAMVA DL/ID-2000 standard)
    try: #Prefer the optional, field-seperated values
      name = []
      name[0] = fields['DAB'] #Lastname, OPTIONAL 31
      name[1] = fields['DAC'] #Firstname, OPTIONAL 32
      name[2] = fields['DAD'] #Middle name/initial, OPTIONAL 33
      nameSuffix = fields['DAE'] #OPTIONAL 34
      namePrefix = fields['DAF'] #OPTIONAL 35
    except KeyError: #fall back on the required field
      name = fields['DAA'].split(',') #REQUIRED 1
      nameSuffix = None
      namePrefix = None

    #Convert datetime objects
    dba = fields['DBA'] #Expiry date REQUIRED 11
    expiry = datetime.date(int(dba[0:4]), int(dba[4:6]), int(dba[6:8]))
    dbb = fields['DBB'] #Date of Birth REQUIRED 12
    dob = datetime.date(int(dbb[0:4]), int(dbb[4:6]), int(dbb[6:8]))
    dbd = fields['DBD'] #Document issue date REQUIRED 14
    issued = datetime.date(int(dbd[0:4]), int(dbd[4:6]), int(dbd[6:8]))

    sex = fields['DBC'] #REQUIRED 13
    if sex == '1':  #SCDMV v1 discrepancy
      sex = 'M'
    elif sex == '2':
      sex = 'F'
    assert 'F' in sex or 'M' in sex, "Invalid sex"

    #Optional fields:
    try:
        height = fields['DAV'] #Prefer metric units OPTIONAL 42
        weight = fields['DAX'] #OPTIONAL 43
        units = METRIC
    except KeyError:
      try:
        height = fields['DAU'] #U.S. imperial units OPTIONAL 20
        weight = fields['DAW'] #OPTIONAL 21
        units = IMPERIAL
      except KeyError:
        #No height/weight defined (these fields are optional by the standard)
        height = None
        weight = None
        units = None
    finally:
      assert height.isdigit() or height is not None, "Invalid height"
      assert weight.isdigit() or height is not None, "Invalid weight"

    try:
      hair = fields['DAZ'].strip()
      eyes = fields['DAY'].strip()
    except KeyError:
      hair = None
      eyes = None

    #assert hair in HAIRCOLOURS, "Invalid hair colour"
    #assert eyes in EYECOLOURS, "Invalid eye colour"

    return { 'first' : name[1], 'last' : name[0],
             'middle' : name[2], 'city' : fields['DAI'], #REQUIRED 3
             'state' : fields['DAJ'], #REQUIRED 4
             'address' : fields['DAG'], 'IIN' : issueIdentifier, #REQUIRED 2
             'licenseNumber' : fields['DAQ'], 'expiry' : expiry, #REQUIRED 6
             'dob' : dob, 'ZIP' : fields['DAK'].strip(), #REQUIRED 5
             'class' : fields['DAR'].strip(), #REQUIRED 8
             'restrictions' : fields['DAS'].strip(), #REQUIRED 9
             'endorsements' : fields['DAT'].strip(), 'sex' : sex, #REQUIRED 10
             'height' : height, 'weight' : weight, 'hair' : hair,
             'eyes' : eyes, 'units' : units, 'issued' : issued,
             'suffix' : nameSuffix, 'prefix' : namePrefix}


  def _decodeBarcode_v3(self, fields, issueIdentifier):

    if debug: pprint.pprint(fields)
    #required fields
    country = fields['DCG'] #USA or CAN

    #convert dates
    dba = fields['DBA'] #expiry (REQUIRED REF d.)
    expiry = self._parseDate(dba, country)
    dbd = fields['DBD'] #issue date (REQUIRED REF g.)
    issued = self._parseDate(dbd, country)
    dbb = fields['DBB'] #date of birth (REQUIRED REF h.)
    dob = self._parseDate(dbb, country)

    #jurisdiction-specific (required for DL only):
    try:
      vehicleClass = fields['DCA'].strip()
      restrictions = fields['DCB'].strip()
      endorsements = fields['DCD'].strip()
      cardType = DRIVER_LICENSE
    except KeyError:
      #not a DL, use None instead
      vehicleClass = None
      restrictions = None
      endorsements = None
      cardType = IDENTITY_CARD

    #Physical description
    sex = fields['DBC']
    assert sex in '12', "Invalid sex"
    if sex == '1': sex = MALE
    if sex == '2': sex = FEMALE

    #Some v.03 barcodes (Indiana) [wrongly, and stupidly] omit
    # the mandatory height (DAU) field.
    try:
      #Normal v.03 barcodes:
      height = fields['DAU']
      if height[-2:] == 'in': #inches
        height = int(height[0:3])
        units = IMPERIAL
        height = Height(height, format='USA')
      elif height[-2:].lower() == 'cm': #metric
        height = int(height[0:3])
        units = METRIC
        height = Height(height)
      else:
        raise AssertionError("Invalid unit for height")
    except KeyError:
      try: #Indiana puts it in the jurisdiction field ZIJ
        height = fields['ZIJ'].split('-')
        units = IMPERIAL
        height = Height((int(height[0])*12)+int(height[1]), format='USA')
      except KeyError:
        #Give up on parsing height
        log("ERROR: Unable to parse height.")
        height = None

    #Eye colour is mandatory
    eyes = fields['DAY']
    assert eyes in EYECOLOURS, "Invalid eye colour: {0}".format(eyes)

    #But hair colour is optional for some reason in this version
    try:
      hair = fields['DAZ']
      assert hair in HAIRCOLOURS, "Invalid hair colour: {0}".format(hair)
    except KeyError:
      try: #Indiana
        hair = fields['ZIL']
        assert hair in HAIRCOLOURS, "Invalid hair colour: {0}".format(hair)
      except KeyError:
        hair = None

    #name suffix optional. No prefix field in this version.
    try: nameSuffix = fields['DCU']
    except KeyError: nameSuffix = None

    #Try weight range
    try:
      weight = fields['DCE']
      if units == METRIC:
        weight = Weight(int(weight), format='ISO')
      elif units == IMPERIAL:
        weight = Weight(int(weight), format='USA')
    except KeyError:
      try: #Indiana again
        weight = fields['ZIK']
        assert weight.isdigit(), 'Weight is non-integer: {0}'.format(weight)
        weight = Weight(int(weight), format='USA')
      except KeyError:
        weight = None #Give up

    #Abstract the name field:
    names = fields['DCT'].split(',')
    firstName = names[0].strip()
    if len(names) == 1: #No middle name
      middleName = None
    else:
      middleName = ', '.join(names[1:]).strip()

    #Indiana, again, uses spaces instead
    if ',' not in fields['DCT']:
      names = fields['DCT'].split(' ')
      firstName = names[0].strip()
      if len(names) == 1:
        middleName = None
      else:
        middleName = ' '.join(names[1:]).strip()


    return { 'first' : firstName, 'last' : fields['DCS'].strip(),
             'middle' : middleName, 'city' : fields['DAI'].strip(),
             'state' : fields['DAJ'].strip(), 'country' : country.strip(),
             'address' : fields['DAG'].strip(), 'IIN' : issueIdentifier.strip(),
             'licenseNumber' : fields['DAQ'].strip(), 'expiry' : expiry,
             'dob' : dob, 'ZIP' : fields['DAK'].strip(),
             'class' : vehicleClass, 'restrictions' : restrictions,
             'endorsements' : endorsements, 'sex' : sex,
             'height' : height, 'weight' : weight, 'hair' : hair,
             'eyes' : eyes, 'units' : units, 'issued' : issued,
             'suffix' : nameSuffix, 'prefix' : None,
             'document' : fields['DCF'].strip() }



  def _decodeBarcode_v4(self, fields, issueIdentifier):
    #required fields
    country = fields['DCG'] #USA or CAN

    #convert dates
    dba = fields['DBA'] #expiry (REQUIRED REF d.)
    expiry = self._parseDate(dba, country)
    dbd = fields['DBD'] #issue date (REQUIRED REF g.)
    issued = self._parseDate(dbd, country)
    dbb = fields['DBB'] #date of birth (REQUIRED REF h.)
    dob = self._parseDate(dbb, country)

    #jurisdiction-specific (required for DL only):
    try:
      vehicleClass = fields['DCA'].strip()
      restrictions = fields['DCB'].strip()
      endorsements = fields['DCD'].strip()
      cardType = DRIVER_LICENSE
    except KeyError:
      #not a DL, use None instead
      vehicleClass = None
      restrictions = None
      endorsements = None
      cardType = IDENTITY_CARD

    #Physical description
    sex = fields['DBC']
    assert sex in '12', "Invalid sex"
    if sex == '1': sex = MALE
    if sex == '2': sex = FEMALE

    height = fields['DAU']
    if height[-2:].lower() == 'cm': #metric
      height = int(height[0:3])
      units = METRIC
      height = Height(height)
    elif height [-1] == '"':
      # US height encoding for some implementations of this version is feet and inches
      # (e.g. 6'-01"")
      feet = int(height[0])
      inches = int(height[3:5])
      units = IMPERIAL
      height = Height((feet*12 + inches), format='USA')
    elif height [-2:].lower() == 'in':
      height = int(height[0:3])
      units = IMPERIAL
      height = Height(height, format='USA')
    else:
      raise AssertionError("Invalid unit for height")

    #weight is optional
    if units == METRIC:
      try: weight = Weight(None, int(fields['DAX']))
      except KeyError:
        weight = None
    elif units == IMPERIAL:
      try:
        weight = Weight(None, int(fields['DAW']), 'USA')
      except KeyError:
        weight = None
    if weight == None:
      #Try weight range
      try:
        weight = fields['DCE']
        if units == METRIC:
          weight = Weight(int(weight), format='ISO')
        elif units == IMPERIAL:
          weight = Weight(int(weight), format='USA')
      except KeyError:
        weight = None

    #Hair/eye colour are mandatory
    hair = fields['DAZ']
    eyes = fields['DAY']
    assert hair in HAIRCOLOURS, "Invalid hair colour: {0}".format(hair)
    assert eyes in EYECOLOURS, "Invalid eye colour: {0}".format(eyes)

    #name suffix optional. No prefix field in this version.
    try: nameSuffix = fields['DCU'].strip()
    except KeyError: nameSuffix = None

    first = fields['DAC'].strip()

    return { 'first' : fields['DAC'], 'last' : fields['DCS'],
             'middle' : fields['DAD'], 'city' : fields['DAI'],
             'state' : fields['DAJ'], 'country' : country,
             'address' : fields['DAG'], 'IIN' : issueIdentifier,
             'licenseNumber' : fields['DAQ'].strip(), 'expiry' : expiry,
             'dob' : dob, 'ZIP' : fields['DAK'].strip(),
             'class' : vehicleClass, 'restrictions' : restrictions,
             'endorsements' : endorsements, 'sex' : sex,
             'height' : height, 'weight' : weight, 'hair' : hair,
             'eyes' : eyes, 'units' : units, 'issued' : issued,
             'suffix' : nameSuffix, 'prefix' : None,
             'document' : fields['DCF'].strip(), 'version' : 4 }


  def _decodeBarcode_v5(self, fields, issueIdentifier):
    #required fields
    country = fields['DCG'] #USA or CAN

    #convert dates
    dba = fields['DBA'] #expiry (REQUIRED REF d.)
    expiry = self._parseDate(dba, country)
    dbd = fields['DBD'] #issue date (REQUIRED REF g.)
    issued = self._parseDate(dbd, country)
    dbb = fields['DBB'] #date of birth (REQUIRED REF h.)
    dob = self._parseDate(dbb, country)

    #jurisdiction-specific (required for DL only):
    #FIXME - check if fields are empty
    try:
      vehicleClass = fields['DCA'].strip()
      restrictions = fields['DCB'].strip()
      endorsements = fields['DCD'].strip()
      cardType = DRIVER_LICENSE
    except KeyError:
      #not a DL, use None instead
      vehicleClass = None
      restrictions = None
      endorsements = None
      cardType = IDENTITY_CARD

    #Physical description
    sex = fields['DBC']
    assert sex in '12', "Invalid sex"
    if sex == '1': sex = MALE
    if sex == '2': sex = FEMALE

    height = fields['DAU']
    if height[-2:] == 'in': #inches
      height = int(height[0:3])
      units = IMPERIAL
      height = Height(height, format='USA')
    elif height[-2:].lower() == 'cm': #metric
      height = int(height[0:3])
      units = METRIC
      height = Height(height)
    else:
      raise AssertionError("Invalid unit for height")

    #weight is optional
    if units == METRIC:
      try: weight = Weight(None, int(fields['DAX']))
      except KeyError:
        weight = None
    elif units == IMPERIAL:
      try:
        weight = Weight(None, int(fields['DAW']), 'USA')
      except KeyError:
        weight = None
    if weight == None:
      #Try weight range
      try:
        weight = fields['DCE']
        if units == METRIC:
          weight = Weight(int(weight), format='ISO')
        elif units == IMPERIAL:
          weight = Weight(int(weight), format='USA')
      except KeyError:
        weight = None

    #Hair/eye colour are mandatory
    hair = fields['DAZ']
    eyes = fields['DAY']
    assert hair in HAIRCOLOURS, "Invalid hair colour: {0}".format(eyes)
    assert eyes in EYECOLOURS, "Invalid eye colour: {0}".format(hair)

    #name suffix optional. No prefix field in this version.
    try: nameSuffix = fields['DCU']
    except KeyError: nameSuffix = None

    # v5 adds optional date fields DDH, DDI, and DDJ (Under 18/19/21 until)
    arrival_dates = {}
    #arrival_dates['under_18_until'] = _parseDate(fields['DDH'])
    #arrival_dates['under_19_until'] = _parseDate(fields['DDI'])
    #arrival_dates['under_21_until'] = _parseDate(fields['DDJ'])

    return { 'first' : fields['DAC'], 'last' : fields['DCS'],
             'middle' : fields['DAD'], 'city' : fields['DAI'],
             'state' : fields['DAJ'], 'country' : country,
             'address' : fields['DAG'], 'IIN' : issueIdentifier,
             'licenseNumber' : fields['DAQ'].strip(), 'expiry' : expiry,
             'dob' : dob, 'ZIP' : fields['DAK'].strip(),
             'class' : vehicleClass, 'restrictions' : restrictions,
             'endorsements' : endorsements, 'sex' : sex,
             'height' : height, 'weight' : weight, 'hair' : hair,
             'eyes' : eyes, 'units' : units, 'issued' : issued,
             'suffix' : nameSuffix, 'prefix' : None,
             'document' : fields['DCF'].strip(),
             'arrival_dates' : arrival_dates }


  def _decodeBarcode_v6(self, fields, issueIdentifier): # 2011 standard
    #required fields
    country = fields['DCG'] #USA or CAN

    # 2011 e, f, g, are required name fields
    lastname = fields['DCS']   #(REQUIRED 2011 e)
    firstname = fields['DAC']  #(REQUIRED 2011 f)
    middlename = fields['DAD'] #(REQUIRED 2011 g)

    # 2011 t, u, and v indicate if names are truncated:
    if fields['DDE'] == 'T':
      lastname += "…"
    if fields['DDF'] == 'T':
      firstname += "…"
    if fields['DDG'] == 'T':
      middlename += "…"

    #convert dates
    dba = fields['DBA'] #expiry (REQUIRED 2011 d.)
    expiry = self._parseDate(dba, country)
    dbd = fields['DBD'] #issue date (REQUIRED 2011 h.)
    issued = self._parseDate(dbd, country)
    dbb = fields['DBB'] #date of birth (REQUIRED 2011 i.)
    dob = self._parseDate(dbb, country)

    #jurisdiction-specific (required for DL only):
    #FIXME - check if fields are empty
    try:
      vehicleClass = fields['DCA'].strip() #(REQUIRED 2011 a.)
      restrictions = fields['DCB'].strip() #(REQUIRED 2011 b.)
      endorsements = fields['DCD'].strip() #(REQUIRED 2011 c.)
      cardType = DRIVER_LICENSE
    except KeyError:
      #not a DL, use None instead
      vehicleClass = None
      restrictions = None
      endorsements = None
      cardType = IDENTITY_CARD

    #Physical description
    sex = fields['DBC'] #(REQUIRED 2011 j.)
    assert sex in '12', "Invalid sex"
    if sex == '1': sex = MALE
    if sex == '2': sex = FEMALE

    eyes = fields['DAY'] #(REQUIRED 2011 k.)
    assert eyes in EYECOLOURS, "Invalid eye colour: {0}".format(hair)

    height = fields['DAU'] #(REQUIRED 2011 l.)
    if height[-2:] == 'in': #inches
      height = int(height[0:3])
      units = IMPERIAL
      height = Height(height, format='USA')
    elif height[-2:].lower() == 'cm': #metric
      height = int(height[0:3])
      units = METRIC
      height = Height(height)
    else:
      raise AssertionError("Invalid unit for height")

    # 2011 m, n, o, p, are required address elements


    #weight is optional
    if units == METRIC:
      try: weight = Weight(None, int(fields['DAX']))
      except KeyError:
        weight = None
    elif units == IMPERIAL:
      try:
        weight = Weight(None, int(fields['DAW']), 'USA')
      except KeyError:
        weight = None
    if weight == None:
      #Try weight range
      try:
        weight = fields['DCE']
        if units == METRIC:
          weight = Weight(int(weight), format='ISO')
        elif units == IMPERIAL:
          weight = Weight(int(weight), format='USA')
      except KeyError:
        weight = None


    #optional fields:
    address2 = None #(OPTIONAL 2011 a.)
    if 'DAH' in fields.keys():
      address2 = fields['DAH']

    hair = None #(OPTIONAL 2011 b.)
    if 'DAZ' in fields.keys():
      hair = fields['DAZ'] #Optional
      assert hair in HAIRCOLOURS, "Invalid hair colour: {0}".format(hair)

    #TODO: OPTIONAL 2011 fields c - h

    #name suffix optional. No prefix field in this version.
    try: nameSuffix = fields['DCU'] #(OPTIONAL 2011 i.)
    except KeyError: nameSuffix = None

    #TODO: OPTIONAL 2011 fields j - u

    # v6 adds optional date fields DDH, DDI, and DDJ (Under 18/19/21 until)
    arrival_dates = {}
    if 'DDH' in fields.keys():
      arrival_dates['under_18_until'] = _parseDate(fields['DDH'])
    if 'DDI' in fields.keys():
      arrival_dates['under_19_until'] = _parseDate(fields['DDI'])
    if 'DDJ' in fields.keys():
      arrival_dates['under_21_until'] = _parseDate(fields['DDJ'])

    #TODO: OPTIONAL 2011 field a.a.

    return { 'first' : firstname, 'last' : lastname,
             'middle' : middlename, 'city' : fields['DAI'],
             'state' : fields['DAJ'], 'country' : country,
             'address' : fields['DAG'], 'IIN' : issueIdentifier,
             'licenseNumber' : fields['DAQ'].strip(), 'expiry' : expiry,
             'dob' : dob, 'ZIP' : fields['DAK'].strip(),
             'class' : vehicleClass, 'restrictions' : restrictions,
             'endorsements' : endorsements, 'sex' : sex,
             'height' : height, 'weight' : weight, 'hair' : hair,
             'eyes' : eyes, 'units' : units, 'issued' : issued,
             'suffix' : nameSuffix, 'prefix' : None,
             'document' : fields['DCF'].strip(),
             'arrival_dates' : arrival_dates }



  def _parseDate(self, date, format='ISO'):
    format = format.upper()
    if format == 'USA':
      return datetime.date(int(date[4:8]), int(date[0:2]), int(date[2:4]))
    elif format == 'ISO' or format == 'CAN':
      return datetime.date(int(date[0:4]), int(date[4:6]), int(date[6:8]))


class ReadError(Exception):
  pass

class HeightError(Exception):
  pass

class WeightError(Exception):
  pass

class NotImplemented(Exception):
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
  def __init__(self, height, format='ISO'):
    self.format = format
    if format == 'ISO' or format == 'CAN': #use metric (cm)
      self.units = METRIC
    elif format == 'USA':
      self.units = IMPERIAL
    else:
      raise HeightError("Invalid format: '%s'" % format)

    self.height = height

  def asMetric(self):
    """
    Returns height as integer in centimetres
    """
    if self.units == METRIC:
      return self.height
    else:
      return int(round(self.height * 0.393700787)) #convert to cm

  def asImperial(self):
    """
    Returns height as integer in inches
    """
    if self.units == IMPERIAL:
      return self.height
    else:
      return int(round(self.height * 2.54)) #convert to inches

  def __repr__(self):
    return "%s(%s, format='%s')" % (self.__class__.__name__, \
      self.height, self.format)

  def __str__(self):
    if self.units == IMPERIAL:
      return str(self.height) + " in"
    else:
      return str(self.height) + " cm"


class Weight:
  """
  Represents the physical description of weight in an unit-neutral way.
  """
  def __init__(self, weightRange, weight=None, format='ISO'):
    self.format = format
    if format == 'ISO' or format == 'CAN': #use metric
      self.units = METRIC
    elif format == 'USA': #use imperial
      self.units = IMPERIAL
    else:
      raise WeightError("Invalid format: '%s'" % format)

    if weightRange == None: #Defined by exact weight (lbs or kg)
      self.exact = True
      assert weight != None and type(weight) == int, "Invalid weight"
      self.weight = weight
      if self.units == METRIC:
        self.weightRange = self._getMetricRange(weight)
      else:
        self.weightRange = self._getImperialRange(weight)

    else: #Defined by weight range
      self.exact = False
      assert type(weightRange) == int
      self.weightRange = weightRange
      if self.units == METRIC:
        self.weight = self._metricApproximation(weightRange)
      else:
        self.weight = self._imperialApproximation(weightRange)


  def asMetric(self): #Returns integer
    if self.units == METRIC:
      return self.weight
    else:
      return int(round(self.weight / 2.2))

  def asImperial(self): #Returns integer
    if self.units == IMPERIAL:
      return self.weight
    else:
      return int(round(self.weight * 2.2))

  def _getMetricRange(self, weight):
    """
    Returns the integer weight range given a weight in kilograms
    """
    #TODO: Make this more pythonic
    if weight <= 31: return 0
    elif weight > 31 and weight <= 45: return 1
    elif weight > 45 and weight <= 59: return 2
    elif weight > 59 and weight <= 70: return 3
    elif weight > 70 and weight <= 86: return 4
    elif weight > 86 and weight <= 100: return 5
    elif weight > 100 and weight <= 113: return 6
    elif weight > 113 and weight <= 127: return 7
    elif weight > 127 and weight <= 145: return 8
    elif weight > 146: return 9
    else: return None

  def _metricApproximation(self, weight):
    """
    Return an approximation of the weight given a weight range
    """
    table = { 0 : 20, 1 : 38, 2 : 53, 3 : 65, 4 : 79, 5 : 94,
              6 : 107, 7 : 121, 8 : 137, 9 : 146 }
    return table[weight]

  def _getImperialRange(self, weight):
    """
    Returns the integer weight range given a weight in pounds
    """
    if weight <= 70: return 0
    elif weight > 70 and weight <= 100: return 1
    elif weight > 100 and weight <= 130: return 2
    elif weight > 130 and weight <= 160: return 3
    elif weight > 160 and weight <= 190: return 4
    elif weight > 190 and weight <= 220: return 5
    elif weight > 220 and weight <= 250: return 6
    elif weight > 250 and weight <= 280: return 7
    elif weight > 280 and weight <= 320: return 8
    elif weight > 320: return 9
    else: return None

  def _imperialApproximation(self, weight):
    table = { 0 : 50, 1 : 85, 2 : 115, 3 : 145, 4 : 175, 5 : 205,
              6 : 235, 7 : 265, 8 : 300, 9 : 320 }
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

  #Not sure why you'd ever need to do this
  def __add__(self, other):
    if self.units == METRIC:
      return Weight(None, self.weight + other.asMetric(), format='ISO')
    else:
      return Weight(None, self.weight + other.asImperial(), format='USA')

  def __repr__(self):
    return "%s(weightRange=%s, weight=%s, format=%s)" % \
      (self.__class__.__name__, self.weightRange, self.weight, self.format)

def log(string):
  """Barebones logging"""
  if debug: print string

if __name__ == '__main__':
  import pprint

  parser = AAMVA()

  #~ while True:
    #~ try: #Reading from an HID card reader (stdin)
      #~ pprint.pprint(parser.decode(raw_input("Swipe a card")))
    #~ except ReadError as e:
      #~ print e
      #~ print "Read error.  Try again."

  #reading from a serial barcode reader
  import serial
  ser = serial.Serial('/dev/ttyUSB0')
  while True:
    charbuffer = ""
    print "Scan a license"
    while charbuffer[-2:] != '\r\n':
      char = ser.read(1)
      charbuffer += char
    try:
      print "Got string: " + charbuffer + "\n\n\n\n"
      pprint.pprint(parser.decode(str(charbuffer)))
    except ReadError:
      print "Parse error. Try again"

  ser.close()
