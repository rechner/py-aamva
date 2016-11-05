
# From https://github.com/winfinit/aamvajs/tree/master/test

# Interestingly MD has "AAMVA" filetype instead of ANSI per 2000 and later standard.
# Reports as version number 1 otherwise
class PDF417:
    md_aamva = '@\n\u001e\rAAMVA6360030101DL00290192DLDAQK-134-123-145-103\nDAAJOHNSON,JACK,,3RD\nDAG1234 BARNEYS INN PL\nDAIBALTIMORE\nDAJMD\nDAK21230 \nDARC \nDAS \nDAT \nDAU505\nDAW135\nDBA20170209\nDBB19910209\nDBC1\nDBD20120210\nDBHN\r';
a
class Magstripe:
    tx = '%TXAUSTIN^DOE$JOHN^12345 SHERBOURNE ST^?;63601538774194=150819810101?#" 78729      C               1505130BLKBLK?'
    al = '%ALPRATTVILLE^STURGEON$ZACHARY$WILLIAM^518 WEATHERBY TRL^?;6360338359411=131019930513=?+10360673851  D A             M510120BROBRO?'
    fl = '%FLDELRAY BEACH^DOE$JOHN$^4818 S FEDERAL BLVD^           ?;6360100462172082009=2101198799080=?#! 33435      I               1600                                   ECCECC00000?'
    fl2 = '%FLDELRAY BEACH^JURKOV$ROMAN$^4818 N CLASSICAL BLVD^                            ?;6360100462172082009=2101198799080=?#! 33435      I               1600                                   ECCECC00000'
