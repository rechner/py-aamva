py-aamva
========

A python library for decoding and working with AAMVA-complaint driver's 
licensees and identity cards, taken from a magstripe or PDF417 barcode
(or potentially a SmartCard, although no implementations currently exist).

Pure python and with no dependencies, though your mileage may vary because
it is difficult to find very many test cases to validate this with.

Copyright © 2022 Rechner Fox <rechner@totallylegit.agency>

__WARNING__:  Use of the information from machine-legible formats on a North-American identification card is subject to
compliance with 18 U.S.C. chapter 123, §2721, available [here](http://uscode.house.gov/download/pls/18C123.txt). The
author of this code claims no responsibility for its use contrary to this or any later act, law, or jurisdiction. In
most cases you must obtain written permission from the license holder to compile or /share/ a database of information
obtained from their machine-readable information. For example, it is legal to make a private database of this
information to prevent check fraud or process credit-cards, but it may not be used to create a mailing list without
permission. You are responsible for maintaining compliance or risk fines of up to $5,000 per day of non-compliance in
the US. Individual states may have their own restrictions on swiping as well: at the time of
writing,  [S.B. No. 1445 applies to the state of Texas](http://www.legis.state.tx.us/tlodocs/78R/billtext/html/SB01445F.htm)
.


## License ##
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
MA 02110-1301, USA.
