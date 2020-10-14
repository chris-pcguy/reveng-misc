#!/usr/bin/env python3

"""
leontp_fw.py /dev/hidraw0 LeoNTP.bin
"""

import sys, fcntl

class Leo:
    def __init__(self):
        self.fp = open(sys.argv[1], 'a+b', 0)
        self.fd = open(sys.argv[2], 'rb').read()
    def cmd(self, cmd, data=b''):
        cmd = cmd.ljust(8, bytes(1))
        data = data.ljust(52, bytes(1))
        fcntl.ioctl(self.fp, 0xc03d4806, bytes(1)+cmd+data)
    def loop(self):
        while self.fd:
            tmp, self.fd = self.fd[:40], self.fd[40:]
            self.cmd(b'\x02', tmp)
        self.cmd(b'\x02') # final zero block? might not be actually necessary.
    def flash(self):
        self.cmd(b'\x01') # initialize flash mode
        self.loop() # write firmware
        self.cmd(b'\x03') # reboot. if loop() isn't called, it'll reboot back to itself (bootloader mode). the only way to leave the bootloader mode seems to be flashing the firmware file.
    def run(self):
        self.flash()

leo = Leo()
leo.run()
