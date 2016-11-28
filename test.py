import unittest
import datetime
import aamva
import pprint
# Potential other sources for unit tests: https://github.com/c0shea/IdParser/tree/master/IdParser.Tests

# From https://github.com/winfinit/aamvajs/tree/master/test

# Interestingly MD has "AAMVA" filetype instead of ANSI per 2000 and later standard.
# Reports as version number 1 otherwise
class PDF417:
    md_aamva = '@\n\u001e\rAAMVA6360030101DL00290192DLDAQK-134-123-145-103\nDAAJOHNSON,JACK,,3RD\nDAG1234 BARNEYS INN PL\nDAIBALTIMORE\nDAJMD\nDAK21230 \nDARC \nDAS \nDAT \nDAU505\nDAW135\nDBA20170209\nDBB19910209\nDBC1\nDBD20120210\nDBHN\r';
    oh = "@\n\u001e\rANSI 636023080102DL00410280ZO03210024DLDBA05262020\nDCSLASTNAME\nDACFIRSTNAME\nDADW\nDBD05132016\nDBB05261991\nDBC1\nDAYBLU\nDAU072 IN\nDAG5115 TEST DR\nDAIPENNSITUCKY\nDAJOH\nDAK606061337  \nDAQTG834904\nDCF2520UQ7248040000\nDCGUSA\nDDEN\nDDFN\nDDGN\nDAZBRO\nDCIUS,CALIFORNIA\nDCJNONE\nDCUNONE\nDCE4\nDDAM\nDDB12042013\nDAW170\nDDK1\nDCAD\nDCBB\nDCDNONE\rZOZOAY\nZOBY\nZOE05262020\r"
    oh_missing_record_separator = "@\n\rANSI 636023080102DL00410280ZO03210024DLDBA05262020\nDCSLASTNAME\nDACFIRSTNAME\nDADW\nDBD05132016\nDBB05261991\nDBC1\nDAYBLU\nDAU072 IN\nDAG5115 TEST DR\nDAIPENNSITUCKY\nDAJOH\nDAK606061337  \nDAQTG834904\nDCF2520UQ7248040000\nDCGUSA\nDDEN\nDDFN\nDDGN\nDAZBRO\nDCIUS,CALIFORNIA\nDCJNONE\nDCUNONE\nDCE4\nDDAM\nDDB12042013\nDAW170\nDDK1\nDCAD\nDCBB\nDCDNONE\rZOZOAY\nZOBY\nZOE05262020\r"

class Magstripe:
    tx = '%TXAUSTIN^DOE$JOHN^12345 SHERBOURNE ST^?;63601538774194=150819810101?#" 78729      C               1505130BLKBLK?'
    fl = '%FLDELRAY BEACH^DOE$JOHN$^4818 S FEDERAL BLVD^           ?;6360100462172082009=2101198701010=?#! 33435      I               1600                                   ECCECC00000?'
    fl2 = '%FLDELRAY BEACH^JURKOV$ROMAN$^4818 N CLASSICAL BLVD^                            ?;6360100462172082009=2101198701010=?#! 33435      I               1600                                   ECCECC00000'

class MagstripeTestMethods(unittest.TestCase):
    def test_tx(self):
        parser = aamva.AAMVA()

        data = parser._decodeMagstripe(Magstripe.tx)
        self.assertEqual(data['first'], 'JOHN')
        self.assertEqual(data['last'], 'DOE')
        self.assertEqual(data['city'], 'AUSTIN')
        self.assertEqual(data['IIN'], '636015')
        self.assertEqual(data['dob'], datetime.date(1981, 1, 1))
        self.assertEqual(data['expiry'], datetime.date(2015, 8, 31))


    def test_fl(self):
        parser = aamva.AAMVA()

        data = parser._decodeMagstripe(Magstripe.fl)
        self.assertEqual(data['first'], 'JOHN')
        self.assertEqual(data['last'], 'DOE')
        self.assertEqual(data['city'], 'DELRAY BEACH')
        self.assertEqual(data['IIN'], '636010')
        self.assertEqual(data['dob'], datetime.date(1987, 1, 1))
        self.assertEqual(data['expiry'], datetime.date(2021, 1, 31))

if __name__ == '__main__':
    unittest.main()

