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
EYECOLOURS = ['BLK', 'BLU', 'BRO', 'GRY', 'HAZ', 'MAR', 'PNK', 'DIC',
              'UNK']
HAIRCOLOURS = ['BAL', 'BLK', 'BLN', 'BRO', 'GRY', 'RED', 'SDY', 'WHI',
               'UNK']

class AAMVA:
  def __init__(self, data=None, format=[ANY]):
    self.format = format
    assert not isinstance(format, str)
    self.data = data
        
  """
  Decodes data from a string and returns a dictionary of values.
  Data is decoded in the format preference specified in the constructor.
  """
  def decode(self, data=None):
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
             'eyes' : eyes }
    
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
