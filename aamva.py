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

import datetime

""" Constants and signals """ #Better way to do this?
ANY = 0
MAGSTRIPE = 1
PDF417 = 2
SMARTCARD = 4
METRIC = 8
IMPERIAL = 16
EYECOLOURS = ['BLK', 'BLU', 'BRO', 'GRY', 'HAZ', 'MAR', 'PNK', 'DIC',
              'UNK']
HAIRCOLOURS = ['BAL', 'BLK', 'BLN', 'BRO', 'GRY', 'RED', 'SDY', 'WHI',
               'UNK']

#PDF417 format specifications and validations
PDF_LINEFEED = '\x0A'  # '\n' (line feed)
PDF_RECORDSEP = '\x1E' # record seperator
PDF_SEGTERM = '\x0D'   # '\r' segment terminator (carriage return)
PDF_FILETYPE = 'ANSI ' # identifies the file as an AAMVA compliant 
PDF_VERSIONS = range(64) # decimal between 0 - 63
PDF_ENTRIES = range(1, 100) #decimal number of subfile identifiers


class AAMVA:
  def __init__(self, data=None, format=[ANY]):
    self.format = format
    assert not isinstance(format, str)
    self.data = data
        
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
          raise ReadError(e)

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
      address = fields[2].split('$')
      remaining = fields[3] #track 2 & 3
      
    assert len(name_pre) > 0, "Empty name field"
    assert '$' in name_pre, "Name field missing delimiter ($)"
    #entire name field is 35 characters with delimiters
    name = name_pre.split('$')
    
    remaining = remaining.split('?')[1:3] #remove prepended end sentinel
    print remaining[0]
    
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
    
    assert 'F' in sex or 'M' in sex, "Invalid sex"
    assert height.isdigit() or height == '', "Invalid height"
    assert weight.isdigit() or weight == '', "Invalid weight"
    assert hair in HAIRCOLOURS, "Invalid hair colour"
    assert eyes in EYECOLOURS, "Invalid eye colour"
    
    return { 'first' : name[1], 'last' : name[0], 
             'middle' : name[2], 'city' : city, 'state' : state,
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
    #check for compliance character:
    assert data[0] == '@', 'Missing compliance character (@)'
    assert data[1] == PDF_LINEFEED, 'Missing data element separator (LF)'
    assert data[2] == PDF_RECORDSEP, 'Missing record separator (RS)'
    assert data[3] == PDF_SEGTERM, 'Missing segment terminator (CR)'
    assert data[4:9] == PDF_FILETYPE, 
      'Wrong file type (got "%s", should be "ANSI ")' % data[4:9]
    issueIdentifier = data[9:15]
    assert issueIdentifier.isdigit(), 'Issue Identifier is not an integer'
    version = data[15:17]
    assert version in PDF_VERSIONS, 
      'Invalid data version number (got %s, should be 0 - 63)' % version
    nEntries = data[17:19]
    assert nEntries.isdigit(), 'Number of entries is not an integer'
    #/header
    #subfile designator
    assert data[19:21] == 'DL', 
      "Not a driver's license (Got '%s', should be 'DL')" % data[19:21]
    offset = data[21:25]
    assert offset.isdigit(), 'Subfile offset is not an integer'
    length = data[25:29]
    assert length.isdigit(), 'Subfile length is not an integer'
    
    subfile = data[offset:(offset+length)]
    subfile = subfile.split('\n')
    assert subfile[0][:2] == 'DL', "Not a driver's license"
    subfile[0] = subfile[0][2:] #remove prepended "DL"
    subfile[-1] = subfile[-1].strip('\r')
    
    #Decode fields as a dictionary
    fields = dict((key[0:3], key[3:])  for key in subfile)
    
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
    exipry = datetime.date(dba[0:4], dba[4:6], dba[6:8])
    dbb = fields['DBB'] #Date of Birth REQUIRED 12
    dob = datetime.date(dbb[0:4], dbb[4:6], dbb[6:8])
    dbd = fields['DBD'] #Document issue date REQUIRED 14
    issued = datetime.date(dbd[0:4], dbd[4:6], dbd[6:8])
    
    sex = fields['DBC'] #REQUIRED 13
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
      hair = fields['DAZ']
      eyes = fields['DAY']
      assert hair in HAIRCOLOURS, "Invalid hair colour"
      assert eyes in EYECOLOURS, "Invalid eye colour"
    except KeyError:
      hair = None
      eyes = None
    
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
    
    
class ReadError(Exception):
    pass

if __name__ == '__main__':
  import pprint
  
  parser = AAMVA()
  while True:
    try:
      pprint.pprint(parser.decode(raw_input("Swipe a card")))
    except ReadError:
      print "Read error.  Try again."
