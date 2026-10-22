#!/usr/bin/env python3
from pathlib import Path
import sys
p=Path(sys.argv[1])/'feeds/packages/lang/golang/golang-package.mk'
s=p.read_text()
start=s.index('GO_PKG_BUILD_VARS=')
end=s.index('\nGO_PKG_VARS=',start)
bs=chr(92)
lines=['GO_PKG_BUILD_VARS= '+bs,'\tGOPROXY="https://goproxy.cn" '+bs,'\tGOPATH="$(GO_PKG_BUILD_DIR)" '+bs,'\tGOCACHE="$(GO_BUILD_CACHE_DIR)" '+bs,'\tGOMODCACHE="$(GO_MOD_CACHE_DIR)" '+bs,'\tGOENV=off '+bs,'\tGOTOOLCHAIN=local','']
s=s[:start]+'\n'.join(lines)+s[end:]
p.write_text(s)
print('Go downloads use goproxy.cn only; checksum verification retained.')
