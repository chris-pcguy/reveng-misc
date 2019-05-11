#!/usr/bin/env python3

"""
hashcat -O -w 4 -m 100 -a 3 --hex-charset -1 '101112131415161718191e1f202122232425262c2d2e2f303132' biosadminscancode.txt '?1?1?1?1?1?1?1?1'
"""

import codecs, hashlib

# a-z, fetched from https://www.win.tue.nl/~aeb/linux/kbd/scancodes-1.html#ss1.4
s1 = b'qwertyuiopasdfghjklzxcvbnm'
s2 = codecs.decode('101112131415161718191e1f202122232425262c2d2e2f303132', 'hex')
st = bytes.maketrans(s1, s2)

# HP_BIOSAdminScanCode
hashval = '<hexdump of UEFI NVRAM variable HP_BIOSAdminScanCode>'

password = b'<original admin password>'
password = password.translate(st)
hashval2 = hashlib.sha1(password).hexdigest()

if (hashval == hashval2):
    print('Password correct.')
else:
    print('Password wrong.')

