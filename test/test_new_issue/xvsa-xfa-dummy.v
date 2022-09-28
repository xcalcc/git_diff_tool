 {
 "files": [
  {
   "fid": 1,
   "path":"/home/jun/xc5/test/c/true_positive/aob/case_0/case.c"
  },
  {
   "fid": 2,
   "path":"/usr/include/bits/stdio.h"
  },
  {
   "fid": 3,
   "path":"/usr/include/libio.h"
  },
  {
   "fid": 4,
   "path":"/usr/include/bits/sys_errlist.h"
  }
 ],
 "issues": [
  {
   "fid": 1,
   "sln": 16,
   "scn": 0,
   "k":"b@UIV@main@c",
   "rs":"BUILTIN",
   "rc":"UIV",
   "ec":null,
   "c":"M",
   "ic": 6,
   "vn":"b",
   "fn":"main",
   "m":"${UIV.1}",
   "paths": [
    {
     "fid": 1,
     "sln": 12,
     "scn": 0,
     "m":"Symbol declare line",
     "vn":"a",
     "fn":"main"
    },
    {
     "fid": 1,
     "sln": 13,
     "scn": 0,
     "m":"Function call",
     "vn":null,
     "fn":"main"
    },
    {
     "fid": 1,
     "sln": 5,
     "scn": 0,
     "m":"Value propagated",
     "vn":null,
     "fn":"assign"
    },
    {
     "fid": 1,
     "sln": 13,
     "scn": 0,
     "m":"Function return value",
     "vn":null,
     "fn":"main"
    },
    {
     "fid": 1,
     "sln": 16,
     "scn": 0,
     "m":"Vulnerable spot",
     "vn":"b",
     "fn":"main"
    }
   ]
  },
  {
   "fid": 1,
   "sln": 16,
   "scn": 0,
   "k":"b@AOB@main@5",
   "rs":"BUILTIN",
   "rc":"AOB",
   "ec":null,
   "c":"D",
   "ic": 25,
   "vn":"b",
   "fn":"main",
   "m":"${AOB.1}",
   "paths": [
    {
     "fid": 1,
     "sln": 5,
     "scn": 0,
     "m":"Value propagated",
     "vn":null,
     "fn":"assign"
    },
    {
     "fid": 1,
     "sln": 13,
     "scn": 0,
     "m":"Function return value",
     "vn":null,
     "fn":"main"
    },
    {
     "fid": 1,
     "sln": 16,
     "scn": 0,
     "m":"Vulnerable spot",
     "vn":"b",
     "fn":"main"
    }
   ]
  }
 ],
 "rulesets": [
  {
   "rs":"BUILTIN",
   "rv":"1"
  }
 ],
 "v": 1,
 "id":"@@scanTaskId@@",
 "s":"@@status@@",
 "m":"@@message@@",
 "eng":"Xcalibyte",
 "ev":"1",
 "er":"5697411055cd50103803d6c21a29b47d88ce70d9(develop)",
 "x1":"yv#@EHZ*qhlm.8#@GZIT*zyr.m35#cehz@cuz@wfnnb~x",
 "x2":"SLNV./slnv/qfm,OZMT.vm_FH~FGU@1,OW_ORYIZIB_KZGS./slnv/qfm/nzhgruu@rmhgzoo/yrm/~~/r313@kx@ormfc@tmf/c13_35@ormfc/ory*/slnv/qfm/nzhgruu@rmhgzoo/ory/8~9*/fhi/olxzo/ory,KZGS./slnv/qfm/SKV_Hvxfirgb/Uligrub_HXZ_zmw_Zkkh_82~89/yrm*/slnv/qfm/SKV_Hvxfirgb/Uligrub_HXZ_zmw_Zkkh_82~89/yrm*/slnv/qfm/yrm*/slnv,KDW./slnv/qfm/cx4/gvhg/x/gifv_klhrgrev/zly/xzhv_9,HSVOO./yrm/yzhs,FHVI.qfm",
 "ss": 1589377252914083,
 "se": 1589377252932337,
 "usr": 18380,
 "sys": 7352,
 "rss": 20396
 }