# reveng-misc
Misc. Reverse Engineering Projects

gtasa.py - GTA:SA Trainer (Framework) for Linux
hp_bas.py - Cracking HP UEFI admin password
hp_hdd.py - Decode HP UEFI Automatic DriveLock password (xor rol xor)

HP Probook 470 G1 UEFI L74 Ver. 01.47 from 2018-07-30 (latest, as of 2019-05-11):
HP's Automatic DriveLock is vulnerable to a hotplug attack. The DriveLock password gets sent to the harddisk before an user enters his password.
HP's Automatic DriveLock password is stored in the NVRAM variable "HP_AUTODL" (offset 0x14, len 0x20) and encoded with a weak "cipher". (xor 0x5a, rol 4, xor 0x66)
HP's UEFI admin password is converted to scancodes, hashed with SHA1 and stored in the NVRAM variable "HP_BIOSAdminScanCode"

