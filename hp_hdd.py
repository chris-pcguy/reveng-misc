#!/usr/bin/env python3

import codecs

def rol(n):
    return ((n&0xf)<<4)|((n&0xf0)>>4)

def cipher(s, enc=False):
    val1, val2 = 0x66, 0x5a
    if (enc):
        val1, val2 = val2, val1
    r = b''
    for i in s:
        r += bytes([(rol(i^val1))^val2])
    return r
    

# HP_AUTODL
encval = b'<hexdump of UEFI NVRAM variable HP_AUTODL>'
encval = codecs.decode(encval, 'hex')
decval = cipher(encval)
model = decval[:0x14].strip().decode()
enckey = decval[0x14:0x14+0x20]
enckeyhex = 'hex:'+codecs.encode(enckey, 'hex').decode()
#print(model)
print(enckeyhex)

