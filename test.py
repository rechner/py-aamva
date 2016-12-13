import unittest
import datetime
import aamva
import pprint
# Potential other sources for unit tests: https://github.com/c0shea/IdParser/tree/master/IdParser.Tests

# From https://github.com/winfinit/aamvajs/tree/master/test

# Interestingly MD has "AAMVA" filetype instead of ANSI per 2000 and later standard.
# Reports as version number 1 otherwise
class PDF417:
    aamva_v1 = '@\n\x1e\rANSI 6360000102DL00390188ZV02270031DLDAQ0123456789ABC\nDAAPUBLIC,JOHN,Q\nDAG123 MAIN STREET\nDAIANYTOWN\nDAJVA\nDAK123459999  \nDARDM  \nDAS       \nDAT     \nDAU509\nDAW175\nDAYBL \nDAZBR \nDBA20011201\nDBB19761123\nDBCM\nDBD19961201\rZVZVAJURISICTIONDEFINEDELEMENT\r\\928\\111\\100\\180\\605\\739\\922\r\n'
    aamva_v2 = '@\n\x1e\rANSI 6360000102DL00390188ZV02270031DLDAQ0123456789ABC\nDAAPUBLIC,JOHN,Q\nDAG123 MAIN STREET\nDAIANYTOWN\nDAJVA\nDAK123459999  \nDARDM  \nDAS       \nDAT     \nDAU509\nDAW175\nDAYBL \nDAZBR \nDBA20011201\nDBB19761123\nDBCM\nDBD19961201\rZVZVAJURISICTIONDEFINEDELEMENT\r\\928\\111\\100\\180\\605\\739\\922\r\n'

    va = '@\n\x1e\rANSI 636000030001DL00310440DLDCANONE\nDCB158X9     \nDCDS    \nDBA08142017\nDCSMAURY                                   \nDCTJUSTIN,WILLIAM                                                                  \nDBD08142009\nDBB07151958\nDBC1\nDAYBRO\nDAU075 in\nDAG17 FIRST STREET                    \nDAISTAUNTON            \nDAJVA\nDAK244010000  \nDAQT16700185                \nDCF061234567                \nDCGUSA\nDCHS   \nDDC00000000\nDDB12102008\nDDDN\nDDAN\nDCK9060600000017843         \n\r\r\n'
    va_under21 = '@\n\x1e\rANSI 636000030001DL00310440DLDCANONE\nDCB158X9     \nDCDS    \nDBA08142017\nDCSMAURY                                   \nDCTJUSTIN,WILLIAM                                                                  \nDBD08142009\nDBB07151997\nDBC1\nDAYBRO\nDAU075 in\nDAG17 FIRST STREET                    \nDAISTAUNTON            \nDAJVA\nDAK244010000  \nDAQT16700185                \nDCF061234567                \nDCGUSA\nDCHS   \nDDC00000000\nDDB12102008\nDDDN\nDDAN\nDCK9060600000017843         \n\r\r\n'
    ga = '@\n\x1e\rANSI 636055060002DL00410288ZG03290093DLDCAC\nDCBB\nDCDNONE\nDBA07012017\nDCSSAMPLE\nDDEU\nDACJANICE\nDDFU\nDADNONE\nDDGU\nDBD07012012\nDBB07011957\nDBC2\nDAYBLU\nDAU064 in\nDAG123 MAIN STREET\nDAIANYTOWN\nDAJGA\nDAK303341234  \nDAQ123456789\nDAW120\nDCF1234509876543210987654321\nDCGUSA\nDCUNONE\nDCK1234567890123456789012345\nDDAF\nDDB01302012\nDDK1\n\rZGZGAN\nZGBN\nZGC5-04\nZGDROCKDALE\nZGEN\nZGFABC123456789-1234567\nZGG12345-67891234567ABC\nZGH000\n\r\r\n'
    indiana = '@\n\x1e\rANSI 636037040002DL00410514ZI05550117DLDCAX-1X-2\nDCBX-1X-2X-3X-4\nDCDX-1XY\nDBA07042010\nDCSSAMPLEFAMILYNAMEUPTO40CHARACTERSXYWXYWXY\nDACHEIDIFIRSTNAMEUPTO40CHARACTERSXYWXYWXYWX\nDADMIDDLENAMEUPTO40CHARACTERSXYWXYWXYWXYWXY\nDBD07042006\nDBB07041989\nDBC2\nDAYHAZ\nDAU5\'-04"\nDAG123 SAMPLE DRIVE                   \nDAHAPT B                              \nDAIINDIANAPOLIS        \nDAJIN\nDAK462040000  \nDAQ1234-56-7890             \nDCF07040602300001           \nDCGUSA\nDDEN\nDDFN\nDDGN\nDAZBLN         \nDCK12345678900000000000     \nDCUXYWXY\nDAW120\nDDAF\nDDBMMDDCCYY\nDDD1\n\rZIZIAMEDICAL CONDITION\nZIBMEDICAL ALERT\nZIC023\nZIDDONOR\nZIEUNDER 18 UNTIL 07/04/07\nZIFUNDER 21 UNTIL 07/04/10\nZIGOP\n\r\r\n'
    wa = '@\n\x1e\rANSI 636045030002DL00410239ZW02800053DLDCANONE\nDCBNONE\nDCDNONE\nDBA11042014\nDCSANASTASIA\nDCTPRINCESS MONACO\nDCU\nDBD09142010\nDBB11041968\nDBC2\nDAYGRN\nDAU063 in\nDCE2\nDAG2600 MARTIN WAY E\nDAIOLYMPIA\nDAJWA\nDAK985060000  \nDAQANASTPM320QD\nDCFANASTPM320QDL1102574D1643\nDCGUSA\nDCHNONE\n\rZWZWAL1102574D1643\nZWB\nZWC33\nZWD\nZWE\nZWFRev09162009\n\r\r\n'
    wa_edl = '@\n\x1e\rANSI 636045030002DL00410232ZW02730056DLDCSO REALTEST\nDCTDABE DEE\nDCUV\nDAG2600 MARTIN WAY\nDAIOLYMPIA\nDAJWA\nDAK985060000  \nDCGUSA\nDAQOREALDD521DS\nDCANONE\nDCBNONE\nDCDNONE\nDCFOREALDD521DSL1083014J1459\nDCHNONE\nDBA03102013\nDBB03101948\nDBC1\nDBD10272008\nDAU070 in\nDCE4\nDAYBLU\n\rZWZWAL1083014J1459\nZWB   \nZWC33\nZWD\nZWE\nZWFRev03122007\n\r\r\n'
    ca = ' @\n\x1e\rANSI 636014040002DL00410477ZC05180089DLDAQD1234562 XYXYXYXYXYXYXYXYX\nDCSLASTNAMEXYXYXYXYXYXYXYXYXXYXYXYXYXYXYXYX\nDDEU\nDACFIRSTXYXYXYXYXYXYXYXYXXYXYXYXYXYXYXYXXYX\nDDFU\nDADXYXYXYXYXYXYXYXYXXYXYXYXYXYXYXYXXYXYXYXY\nDDGU\nDCAA XYXY\nDCBNONEY1XY1XY1\nDCDNONEX\nDBD10312009\nDBB10311977\nDBA10312014\nDBC1\nDAU068 IN\nDAYBRO\nDAG1234 ANY STREET XY1XY1XY1XY1XY1XY1X\nDAICITY XY1XY1XY1XY1XY1\nDAJCA\nDAK000000000  \nDCF00/00/0000NNNAN/ANFD/YY X\nDCGUSA\nDCUSUFIX\nDAW150\nDAZBLK XY1XY1XY\nDCKXY1XY1XY1XY1XY1XY1XY1XY1X\nDDAF\nDDBMMDDCCYY\nDDD1\n\rZCZCAY\nZCBCORR LENS\nZCCBRN\nZCDXYX\nZCEXYXYXYXYXYXYXY\nZCFXY1XY1XY1XY1XY1XY1XYXYXYXYXYXYXY\n\r\r\n'
    ny = '@\n\x1e\rANSI 636001070002DL00410392ZN04330047DLDCANONE  \nDCBNONE        \nDCDNONE \nDBA08312013\nDCSMichael                                 \nDACM                                       \nDADMotorist                                \nDBD08312013\nDBB08312013\nDBC1\nDAYBRO\nDAU064 in\nDAG2345 ANYWHERE STREET               \nDAIYOUR CITY           \nDAJNY\nDAK123450000  \nDAQNONE                     \nDCFNONE                     \nDCGUSA\nDDEN\nDDFN\nDDGN\n\rZNZNAMDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTIzNDU2Nzg5\n\r\r\n'
    md_aamva = '@\n\x1e\rAAMVA6360030101DL00290192DLDAQK-134-123-145-103\nDAAJOHNSON,JACK,,3RD\nDAG1234 BARNEYS INN PL\nDAIBALTIMORE\nDAJMD\nDAK21230 \nDARC \nDAS \nDAT \nDAU505\nDAW135\nDBA20170209\nDBB19910209\nDBC1\nDBD20120210\nDBHN\r';
    sc = '@\n\x1c\rANSI 6360050101DL00300201DLDAQ102245737\nDAASAMPLE,DRIVER,CREDENTIAL,\nDAG1500 PARK ST\nDAICOLUMBIA\nDAJSC\nDAK292012731  \nDARD   \nDAS          \nDAT     \nDAU600\nDAW200\nDAY   \nDAZ   \nDBA20190928\nDBB19780928\nDBC1\nDBD20091026\nDBG2\nDBH1\r\r\n'
    oh = "@\n\x1e\rANSI 636023080102DL00410280ZO03210024DLDBA05262020\nDCSLASTNAME\nDACFIRSTNAME\nDADW\nDBD05132016\nDBB05261991\nDBC1\nDAYBLU\nDAU072 IN\nDAG5115 TEST DR\nDAIPENNSITUCKY\nDAJOH\nDAK606061337  \nDAQTG834904\nDCF2520UQ7248040000\nDCGUSA\nDDEN\nDDFN\nDDGN\nDAZBRO\nDCIUS,CALIFORNIA\nDCJNONE\nDCUNONE\nDCE4\nDDAM\nDDB12042013\nDAW170\nDDK1\nDCAD\nDCBB\nDCDNONE\rZOZOAY\nZOBY\nZOE05262020\r"
    oh_missing_record_separator = "@\n\rANSI 636023080102DL00410280ZO03210024DLDBA05262020\nDCSLASTNAME\nDACFIRSTNAME\nDADW\nDBD05132016\nDBB05261991\nDBC1\nDAYBLU\nDAU072 IN\nDAG5115 TEST DR\nDAIPENNSITUCKY\nDAJOH\nDAK606061337  \nDAQTG834904\nDCF2520UQ7248040000\nDCGUSA\nDDEN\nDDFN\nDDGN\nDAZBRO\nDCIUS,CALIFORNIA\nDCJNONE\nDCUNONE\nDCE4\nDDAM\nDDB12042013\nDAW170\nDDK1\nDCAD\nDCBB\nDCDNONE\rZOZOAY\nZOBY\nZOE05262020\r"

class Magstripe:
    tx = '%TXAUSTIN^DOE$JOHN^12345 SHERBOURNE ST^?;63601538774194=150819810101?#" 78729      C               1505130BLKBLK?'
    fl = '%FLDELRAY BEACH^DOE$JOHN$^4818 S FEDERAL BLVD^           ?;6360100462172082009=2101198701010=?#! 33435      I               1600                                   ECCECC00000?'
    fl2 = '%FLDELRAY BEACH^JURKOV$ROMAN$^4818 N CLASSICAL BLVD^                            ?;6360100462172082009=2101198701010=?#! 33435      I               1600                                   ECCECC00000'


class BarcodeTestMethods(unittest.TestCase):

    def test_va(self):
        parser = aamva.AAMVA()
        data = parser._decodeBarcode(PDF417.va)
        self.assertEqual(data['document'], '061234567')
        self.assertEqual(data['IIN'], '636000')
        self.assertEqual(data['address'], '17 FIRST STREET')
        self.assertEqual(data['city'], 'STAUNTON')
        self.assertEqual(data['class'] ,'NONE')
        self.assertEqual(data['dob'], datetime.date(1958, 7, 15))
        self.assertEqual(data['endorsements'], 'S')
        self.assertEqual(data['eyes'], 'BRO')
        self.assertEqual(data['first'], 'JUSTIN')
        self.assertEqual(data['middle'], 'WILLIAM')
        self.assertEqual(data['last'], 'MAURY')
        self.assertIs(data['prefix'], None)
        self.assertIs(data['hair'], None)
        self.assertEqual(data['height'], aamva.Height(75, format='USA'))
        self.assertEqual(data['expiry'], datetime.date(2017, 8, 14))
        self.assertEqual(data['issued'], datetime.date(2009, 8, 14))
        self.assertEqual(data['licenseNumber'], 'T16700185')
        self.assertEqual(data['restrictions'], '158X9')
        self.assertEqual(data['sex'], 'M')
        self.assertEqual(data['state'], 'VA')
        self.assertIs(data['suffix'], None)
        self.assertIs(data['weight'], None) # VA does not encode weight
        pprint.pprint(data)

    def test_ga(self):
        parser = aamva.AAMVA()
        data = parser._decodeBarcode(PDF417.ga)
        self.assertEqual(data['document'], '1234509876543210987654321')
        self.assertEqual(data['IIN'], '636055')
        self.assertEqual(data['address'], '123 MAIN STREET')
        self.assertEqual(data['city'], 'ANYTOWN')
        self.assertEqual(data['class'] ,'C')
        self.assertEqual(data['dob'], datetime.date(1957, 7, 1))
        self.assertEqual(data['endorsements'], 'NONE')
        self.assertEqual(data['eyes'], 'BLU')
        self.assertEqual(data['first'], 'JANICE')
        self.assertEqual(data['middle'], 'NONE')
        self.assertEqual(data['last'], 'SAMPLE')
        self.assertIs(data['prefix'], None)
        self.assertIs(data['hair'], None)
        self.assertEqual(data['height'], aamva.Height(64, format='USA'))
        self.assertEqual(data['expiry'], datetime.date(2017, 7, 1))
        self.assertEqual(data['issued'], datetime.date(2012, 7, 1))
        self.assertEqual(data['licenseNumber'], '123456789')
        self.assertEqual(data['restrictions'], 'B')
        self.assertEqual(data['sex'], 'F')
        self.assertEqual(data['state'], 'GA')
        self.assertEqual(data['suffix'], 'NONE')
        self.assertEqual(data['weight'], aamva.Weight(None, weight=120, format='USA'))
        pprint.pprint(data)

    def test_in(self):
        parser = aamva.AAMVA()
        data = parser._decodeBarcode(PDF417.indiana)
        self.assertEqual(data['document'], '07040602300001')
        self.assertEqual(data['IIN'], '636037')
        self.assertEqual(data['address'], '123 SAMPLE DRIVE')
        self.assertEqual(data['city'], 'INDIANAPOLIS')
        self.assertEqual(data['class'] ,'X-1X-2')
        self.assertEqual(data['dob'], datetime.date(1989, 7, 4))
        self.assertEqual(data['endorsements'], 'X-1XY')
        self.assertEqual(data['eyes'], 'HAZ')
        self.assertEqual(data['first'], 'HEIDIFIRSTNAMEUPTO40CHARACTERSXYWXYWXYWX')
        self.assertEqual(data['middle'], 'MIDDLENAMEUPTO40CHARACTERSXYWXYWXYWXYWXY')
        self.assertEqual(data['last'], 'SAMPLEFAMILYNAMEUPTO40CHARACTERSXYWXYWXY')
        self.assertIs(data['prefix'], None)
        self.assertEqual(data['hair'], 'BLN')
        self.assertEqual(data['height'], aamva.Height(64, format='USA'))
        self.assertEqual(data['expiry'], datetime.date(2010, 7, 4))
        self.assertEqual(data['issued'], datetime.date(2006, 7, 4))
        self.assertEqual(data['licenseNumber'], '1234-56-7890')
        self.assertEqual(data['restrictions'], 'X-1X-2X-3X-4')
        self.assertEqual(data['sex'], 'F')
        self.assertEqual(data['state'], 'IN')
        self.assertEqual(data['suffix'], 'XYWXY')
        self.assertEqual(data['weight'], aamva.Weight(None, 120, 'USA')) 
        pprint.pprint(data)

    def test_wa(self):
        parser = aamva.AAMVA()
        data = parser._decodeBarcode(PDF417.wa)
        self.assertEqual(data['document'], 'ANASTPM320QDL1102574D1643')
        self.assertEqual(data['IIN'], '636045')
        self.assertEqual(data['address'], '2600 MARTIN WAY E')
        self.assertEqual(data['city'], 'OLYMPIA')
        self.assertEqual(data['class'] ,'NONE')
        self.assertEqual(data['dob'], datetime.date(1968, 11, 4))
        self.assertEqual(data['endorsements'], 'NONE')
        self.assertEqual(data['eyes'], 'GRN')
        self.assertEqual(data['first'], 'PRINCESS')
        self.assertEqual(data['middle'], 'MONACO')
        self.assertEqual(data['last'], 'ANASTASIA')
        self.assertIs(data['prefix'], None)
        self.assertIs(data['hair'], None)
        self.assertEqual(data['height'], aamva.Height(63, format='USA'))
        self.assertEqual(data['expiry'], datetime.date(2014, 11, 4))
        self.assertEqual(data['issued'], datetime.date(2010, 9, 14))
        self.assertEqual(data['licenseNumber'], 'ANASTPM320QD')
        self.assertEqual(data['restrictions'], 'NONE')
        self.assertEqual(data['sex'], 'F')
        self.assertEqual(data['state'], 'WA')
        self.assertEqual(data['suffix'], '')
        self.assertEqual(data['weight'], aamva.Weight(None, weight=115, format='USA'))
        pprint.pprint(data)

    def test_wa_edl(self):
        parser = aamva.AAMVA()
        data = parser._decodeBarcode(PDF417.wa_edl)
        self.assertEqual(data['document'], 'OREALDD521DSL1083014J1459')
        self.assertEqual(data['IIN'], '636045')
        self.assertEqual(data['address'], '2600 MARTIN WAY')
        self.assertEqual(data['city'], 'OLYMPIA')
        self.assertEqual(data['class'] ,'NONE')
        self.assertEqual(data['dob'], datetime.date(1948, 3, 10))
        self.assertEqual(data['endorsements'], 'NONE')
        self.assertEqual(data['eyes'], 'BLU')
        self.assertEqual(data['first'], 'DABE')
        self.assertEqual(data['middle'], 'DEE')
        self.assertEqual(data['last'], 'O REALTEST')
        self.assertIs(data['prefix'], None)
        self.assertIs(data['hair'], None)
        self.assertEqual(data['height'], aamva.Height(70, format='USA'))
        self.assertEqual(data['expiry'], datetime.date(2013, 3, 10))
        self.assertEqual(data['issued'], datetime.date(2008, 10, 27))
        self.assertEqual(data['licenseNumber'], 'OREALDD521DS')
        self.assertEqual(data['restrictions'], 'NONE')
        self.assertEqual(data['sex'], 'M')
        self.assertEqual(data['state'], 'WA')
        self.assertEqual(data['suffix'], 'V')
        self.assertEqual(data['weight'], aamva.Weight(None, weight=175, format='USA'))
        pprint.pprint(data)

    def test_sc(self):
        parser = aamva.AAMVA()
        data = parser._decodeBarcode(PDF417.sc)
        self.assertEqual(data['IIN'], '636005')
        self.assertEqual(data['address'], '1500 PARK ST')
        self.assertEqual(data['city'], 'COLUMBIA')
        self.assertEqual(data['class'] , 'D')
        self.assertEqual(data['dob'], datetime.date(1978, 9, 28))
        self.assertEqual(data['endorsements'], '')
        self.assertEqual(data['eyes'], '')
        self.assertEqual(data['first'], 'DRIVER')
        self.assertEqual(data['middle'], 'CREDENTIAL')
        self.assertEqual(data['last'], 'SAMPLE')
        self.assertIs(data['prefix'], None)
        self.assertEqual(data['hair'], '')
        #self.assertEqual(data['height'], '600')
        self.assertEqual(data['expiry'], datetime.date(2019, 9, 28))
        self.assertEqual(data['issued'], datetime.date(2009, 10, 26))
        self.assertEqual(data['licenseNumber'], '102245737')
        self.assertEqual(data['restrictions'], '')
        self.assertEqual(data['sex'], 'M')
        self.assertEqual(data['state'], 'SC')
        self.assertIs(data['suffix'], None)
        pprint.pprint(data)

class MagstripeTestMethods(unittest.TestCase):
    def test_tx(self):
        parser = aamva.AAMVA()

        data = parser.decode(Magstripe.tx)
        self.assertEqual(data['first'], 'JOHN')
        self.assertEqual(data['last'], 'DOE')
        self.assertEqual(data['city'], 'AUSTIN')
        self.assertEqual(data['IIN'], '636015')
        self.assertEqual(data['dob'], datetime.date(1981, 1, 1))
        self.assertEqual(data['expiry'], datetime.date(2015, 8, 31))


    def test_fl(self):
        parser = aamva.AAMVA()

        data = parser.decode(Magstripe.fl)
        self.assertEqual(data['first'], 'JOHN')
        self.assertEqual(data['last'], 'DOE')
        self.assertEqual(data['city'], 'DELRAY BEACH')
        self.assertEqual(data['IIN'], '636010')
        self.assertEqual(data['dob'], datetime.date(1987, 1, 1))
        self.assertEqual(data['expiry'], datetime.date(2021, 1, 31))

    def test_fl2(self):
        parser = aamva.AAMVA()

        data = parser.decode(Magstripe.fl2)
        self.assertEqual(data['first'], 'ROMAN')
        self.assertEqual(data['last'], 'JURKOV')
        self.assertEqual(data['state'], 'FL')
        self.assertEqual(data['address'], '4818 N CLASSICAL BLVD')
        self.assertEqual(data['city'], 'DELRAY BEACH')
        self.assertEqual(data['IIN'], '636010')
        self.assertEqual(data['dob'], datetime.date(1987, 1, 1))
        self.assertEqual(data['expiry'], datetime.date(2021, 1, 31))

if __name__ == '__main__':
    unittest.main()

