# reveng-misc <br />
Misc. Reverse Engineering Projects <br />
 <br />
gtasa.py - GTA:SA Trainer (Framework) for Linux <br />
hp_bas.py - Cracking HP UEFI admin password <br />
hp_hdd.py - Decode HP UEFI Automatic DriveLock password (xor rol xor) <br />
a86_unlock.txt - Asus "The new PadFone Infinity" A86 (T004) Unlock Instructions and Recovering from "QHSUSB__BULK (9008)" <br />
leontp_fw.py - Flash LeoNTP firmware <br />
philips_atv_mem.py - Root Philips Android TV by (mis)using a backdoor <br />
 <br />
HP Probook 470 G1 UEFI L74 Ver. 01.47 from 2018-07-30 (latest, as of 2019-05-11): <br />
HP's Automatic DriveLock is vulnerable to a hotplug attack. The DriveLock password gets sent to the harddisk before an user enters his password. <br />
HP's Automatic DriveLock password is stored in the NVRAM variable "HP_AUTODL" (offset 0x14, len 0x20) and encoded with a weak "cipher". (xor 0x5a, rol 4, xor 0x66) <br />
HP's UEFI admin password is converted to scancodes, hashed with SHA1 and stored in the NVRAM variable "HP_BIOSAdminScanCode" <br />

