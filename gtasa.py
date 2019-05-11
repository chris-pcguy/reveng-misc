#!/usr/bin/env python3

"""
sysctl -w kernel.yama.ptrace_scope=0
playerAddress: 0x2f500d0
"""

import sys, glob, struct, time, math, builtins, subprocess

GAME_BASEDIR='/home/wine/win_steam_dir/Steam/steamapps/common/Grand Theft Auto San Andreas/'
EXE_NAME=b'gta-sa.exe'

# offsets
OFFSET_OBJECT_HANDLERS = 0x0 # pointer, twowheel and car wheel status function is [0x0][0xb0]
OFFSET_OBJECT_POSITION = 0x14 # pointer
OFFSET_OBJECT_ID = 0x22 # word

OFFSET_MOVEMENT_VELOCITY_X = 0x44 # float
OFFSET_MOVEMENT_VELOCITY_Y = 0x48 # float
OFFSET_MOVEMENT_VELOCITY_Z = 0x4c # float
OFFSET_SPIN_VELOCITY_X = 0x50 # float
OFFSET_SPIN_VELOCITY_Y = 0x54 # float
OFFSET_SPIN_VELOCITY_Z = 0x58 # float
OFFSET_PLAYER_MISC_BASE_POINTER = 0x480 # pointer of pointer
OFFSET_PERSON_LIFE = 0x540 # float, default 100?
OFFSET_PERSON_MAXLIFE = 0x544 # float, default 100?
OFFSET_PERSON_VEST = 0x548 # float
OFFSET_PLAYER_ANGLE = 0x558 # unknown
OFFSET_PLAYER_ANGLE2 = OFFSET_PLAYER_ANGLE+0x4
OFFSET_PERSON_VEHICLE_OBJECT = 0x58c # pointer
OFFSET_PERSON_WEAPON_BASE = 0x5a0 # pointer
OFFSET_MOVEMENT_VELOCITY_X2 = 0x610 # float
OFFSET_MOVEMENT_VELOCITY_Y2 = 0x614 # float
OFFSET_MOVEMENT_VELOCITY_Z2 = 0x618 # float
OFFSET_PLAYER_TIME_SPEED = 0x620 # integer, default CONSTANT_TIME_SPEED
OFFSET_PERSON_WEAPON_INDEX = 0x718 # byte

# from OFFSET_PLAYER_MISC_BASE_POINTER [0x480]
OFFSET_PLAYER_MISC_BASE_WANTEDLEVEL_PTR = 0x0 # pointer
OFFSET_PLAYER_MISC_BASE_OXYGEN = 0x44 # float

MAX_OBJECT_LENGTH_PERSON = 0x7c4
MAX_OBJECT_LENGTH_CAR = 0xa18

# begin of base is OFFSET_OBJECT_POSITION
OFFSET_OBJECT_POSITION_X = 0x30 # float
OFFSET_OBJECT_POSITION_Y = 0x34 # float
OFFSET_OBJECT_POSITION_Z = 0x38 # float
# end of base is OFFSET_OBJECT_POSITION

OFFSET_CAR_UNKNOWN_SIREN_HONK_1 = 0x1f6 # byte ; maybe something different
OFFSET_CAR_UNKNOWN_SIREN_HONK_2 = 0x1f7 # byte ; maybe something different ; 1 if normal siren is enabled
OFFSET_CAR_UNKNOWN_SIREN_HONK_3 = 0x1f8 # byte ; maybe something different ; 1 if special siren is enabled
OFFSET_CAR_SIREN_SOUND_OBJECT = 0x2b4 # pointer ; offset from something is 0x17c, so base seems to be +0x138
OFFSET_CAR_TOP_LIGHTS = 0x42d # byte ; top lights, e.g. police car ; normal 0x50, enabled 0xd0 (|0x80)
OFFSET_VEHICLE_LIFE = 0x4c0 # float, default 1000
OFFSET_VEHICLE_TYPE = 0x590 # dword, car==0x0, motorcycle==0x9
OFFSET_CAR_STATUS_BASE = 0x5a0
OFFSET_CAR_STATUS_BASE_TIRE_BROKEN_INDEX = 0x5
OFFSET_CAR_STATUS_TWOWHEEL_TIRE_BROKEN_INDEX = 0x65c

# clubs
# 0x1 == blocks weapon scrolling in one direction
# 0x2 == invisible baton enabled
WEAPON_TYPES_CLUBS_GOLF = 0x2
WEAPON_TYPES_CLUBS_POLICEBATON = 0x3
WEAPON_TYPES_CLUBS_KNIFE = 0x4
WEAPON_TYPES_CLUBS_BASEBALLBAT = 0x5
WEAPON_TYPES_CLUBS_SHOVEL = 0x6
WEAPON_TYPES_CLUBS_CHAINSAW = 0x9

WEAPON_TYPES_CLUBS2_GIANTDILDO = 0xa
WEAPON_TYPES_CLUBS2_FLOWERS = 0xe

WEAPON_TYPES_PISTOLS_9MM = 0x16
WEAPON_TYPES_PISTOLS_9MM_WITH_SURPRESSOR = 0x17
WEAPON_TYPES_SHOTGUNS_SHOTGUN = 0x19
WEAPON_TYPES_SHOTGUNS_SHOTGUN_SAWED_OFF = 0x1a
WEAPON_TYPES_MACHINEPISTOLS_MICROSMG = 0x1c
WEAPON_TYPES_MACHINEPISTOLS_SMG = 0x1d
WEAPON_TYPES_MACHINEPISTOLS_TEC9 = 0x20
WEAPON_TYPES_MACHINEGUNS_AK47 = 0x1e
WEAPON_TYPES_MACHINEGUNS_M4 = 0x1f

WEAPON_TYPES_SPRAYS_SPRAYCAN = 0x29
WEAPON_TYPES_SPRAYS_FIREEXTINGUISHER = 0x2a
WEAPON_TYPES_SPRAYS_CAMERA = 0x2b

WEAPON_TYPES_GRENADES_GRENADES = 0x10
WEAPON_TYPES_GRENADES_MOLOTOV = 0x12

WEAPON_SLOT_INDEX_CLUBS = 1
WEAPON_SLOT_INDEX_PISTOLS = 2
WEAPON_SLOT_INDEX_SHOTGUNS = 3
WEAPON_SLOT_INDEX_MACHINEPISTOLS = 4
WEAPON_SLOT_INDEX_MACHINEGUNS = 5
WEAPON_SLOT_INDEX_GRENADES = 8
WEAPON_SLOT_INDEX_SPRAYS = 9
WEAPON_SLOT_INDEX_CLUBS2 = 10

WEAPON_INDEX_TYPE = 0x0 # used for clubs etc.
WEAPON_INDEX_VAL2 = 0x8
WEAPON_INDEX_VAL1_VAL2 = 0xc # only this if there's only one number
WEAPON_INDEX_SKILL = 0x10

WEAPON_SINGLE_NUMBER_SLOTS = (WEAPON_SLOT_INDEX_CLUBS, WEAPON_SLOT_INDEX_SHOTGUNS, WEAPON_SLOT_INDEX_GRENADES)

WANTED_LEVELS = [0, 50, 180, 550, 1200, 2400, 4600]

CAR_TIRE_FRONT_LEFT_INDEX = 0
CAR_TIRE_BACK_LEFT_INDEX = 1
CAR_TIRE_FRONT_RIGHT_INDEX = 2
CAR_TIRE_BACK_RIGHT_INDEX = 3

CAR_TIRE_INDEXES = [CAR_TIRE_FRONT_LEFT_INDEX, CAR_TIRE_BACK_LEFT_INDEX, CAR_TIRE_FRONT_RIGHT_INDEX, CAR_TIRE_BACK_RIGHT_INDEX]
CAR_TIRE_INDEXES_NAMES = ['front left', 'back left', 'front right', 'back right']

TWOWHEEL_TIRE_FRONT_INDEX = 0
TWOWHEEL_TIRE_BACK_INDEX = 1

TWOWHEEL_TIRE_INDEXES = [TWOWHEEL_TIRE_FRONT_INDEX, TWOWHEEL_TIRE_BACK_INDEX]
TWOWHEEL_TIRE_INDEXES_NAMES = ['front', 'back']

TIRE_OK = 0
TIRE_BROKEN = 1

ADDR_EXE_BASE = 0x400000
ADDR_MAXIMUM_WANTEDLEVEL_POINTS = ADDR_EXE_BASE+0x540884 # default value CONSTANT_MAXIMUM_WANTEDLEVEL_POINTS
ADDR_TIME_SPEED = ADDR_EXE_BASE+0x80fd74 # default value CONSTANT_TIME_SPEED
ADDR_MONEY_HAVE = ADDR_EXE_BASE+0x810188 # [0x8100d0+0xb8], type float
ADDR_MONEY_COUNTER = ADDR_EXE_BASE+0x81018c # [0x8100d0+0xbc], type float

ADDR_LAUFBAND_LEVEL_REAL = ADDR_EXE_BASE+0x6C9B88 # dword
ADDR_LAUFBAND_STRENGTH_SHOW = ADDR_EXE_BASE+0x6C9B8C # dword
ADDR_LAUFBAND_DISTANCE_SHOW = ADDR_EXE_BASE+0x6C9B94 # dword
#ADDR_LAUFBAND_STRENGTH_REAL = ADDR_EXE_BASE+0x706A80 # float
ADDR_LAUFBAND_STRENGTH_REAL = ADDR_EXE_BASE+0x706e00 # float
ADDR_LAUFBAND_UNKNOWN1 = ADDR_EXE_BASE+0x706A90 # float
ADDR_LAUFBAND_DISTANCE_REAL = ADDR_EXE_BASE+0x706A94 # float
ADDR_LAUFBAND_LEVEL_SHOW = ADDR_EXE_BASE+0x706AA4 # float

ADDR_LAUFRAD_LEVEL_REAL = ADDR_EXE_BASE+0x6C9B08 # dword
ADDR_LAUFRAD_DISTANCE_SHOW = ADDR_EXE_BASE+0x6C9b0c # dword
ADDR_LAUFRAD_DISTANCE_REAL = ADDR_EXE_BASE+0x6c9b14 # float
ADDR_LAUFRAD_STRENGTH_SHOW = ADDR_EXE_BASE+0x6C9B04 # dword
ADDR_LAUFRAD_STRENGTH_REAL = ADDR_EXE_BASE+0x706534 # float

LAUFBANDRAD_SLEEP_TIME = 0.1


ADDR_LANGHANTEL_WIEDERHOLUNGEN_REAL = ADDR_EXE_BASE+0x6c6664 # float
ADDR_LANGHANTEL_WIEDERHOLUNGEN_SHOW = ADDR_EXE_BASE+0x6c9b58 # dword
ADDR_LANGHANTEL_STRENGTH_REAL = ADDR_EXE_BASE+0x706e04 # float
ADDR_HANTEL_STRENGTH_SHOW = ADDR_EXE_BASE+0x6c2f38 # dword

ADDR_KURZHANTEL_WIEDERHOLUNGEN_SHOW1 = ADDR_EXE_BASE+0x6c9bbc # dword
ADDR_KURZHANTEL_WIEDERHOLUNGEN_SHOW2 = ADDR_EXE_BASE+0x6c9bcc # float ; set from show1
ADDR_KURZHANTEL_STRENGTH_REAL = ADDR_EXE_BASE+0x6c9bc8 # float

ADDR_CURRENT_UNKNOWN = ADDR_EXE_BASE+0x8077a0 # base
ADDR_OBJECTS = ADDR_EXE_BASE+0x808b00 # base

ADDR_PLAYER_INDEX = ADDR_EXE_BASE+0x8100bc # index, byte
ADDR_PLAYER_BASE = ADDR_EXE_BASE+0x8100d0 # base

ADDR_OBJECTS_MAX_INDEX = 1001 # 0xfa4

ADDR_MINUTE = ADDR_EXE_BASE+0x7fd4c6 # byte
ADDR_HOUR = ADDR_EXE_BASE+0x7fd4c7 # byte

ADDR_VIGILANTE_TIME_LEFT_ENCODED = ADDR_EXE_BASE+0x6c9348 # dword
ADDR_VIGILANTE_LEFTCAR_TIME_LEFT = ADDR_EXE_BASE+0x6c03b0 # dword, milliseconds

ADDR_CURRENT_RADIO_CHANNEL = ADDR_EXE_BASE+0x53BA8D # byte, 2==K-Rose

HANTEL_SET_STRENGTH = 130
HANTEL_SLEEP_TIME = 1.3

VEHICLE_TYPE_CAR = 0x0
VEHICLE_TYPE_TRAIN = 0x6 # like VEHICLE_TYPE_CAR, but activates cinematic camera
VEHICLE_TYPE_TWOWHEEL = 0x9

VEHICLE_TYPE_NAMES = {VEHICLE_TYPE_CAR: "car", VEHICLE_TYPE_TRAIN: "train", VEHICLE_TYPE_TWOWHEEL: "twowheel"}
#VEHICLE_TYPE_NAMES = {VEHICLE_TYPE_CAR: "car", VEHICLE_TYPE_TRAIN: "train"}

CONSTANT_MAXIMUM_WANTEDLEVEL_POINTS = 1800
#CONSTANT_TIME_SPEED = 3091
CONSTANT_TIME_SPEED = 5581

class BaseObject:
    def __init__(self, trainer, base):
        self.trainer = trainer
        self.base = base

    def __getattribute__(self, name):
        if (name in ('trainer', 'base')):
            return builtins.object.__getattribute__(self, name)
        if (not self.base):
            return
        elif (name == 'id'):
            return self.trainer.readInteger(self.base+OFFSET_OBJECT_ID, 2)
        elif (name in ('position', 'positionX', 'positionY', 'positionZ')):
            positionBase = self.trainer.readInteger(self.base+OFFSET_OBJECT_POSITION, 4)
            if (not positionBase):
                return
            positionX = self.trainer.readFloat(positionBase+OFFSET_OBJECT_POSITION_X)
            positionY = self.trainer.readFloat(positionBase+OFFSET_OBJECT_POSITION_Y)
            positionZ = self.trainer.readFloat(positionBase+OFFSET_OBJECT_POSITION_Z)
            if (name == 'position'):
                return [positionX, positionY, positionZ]
            elif (name == 'positionX'):
                return positionX
            elif (name == 'positionY'):
                return positionY
            elif (name == 'positionZ'):
                return positionZ
        elif (name in ('movementVelocity', 'movementVelocityX', 'movementVelocityY', 'movementVelocityZ')):
            movementVelocityX = self.trainer.readFloat(self.base+OFFSET_MOVEMENT_VELOCITY_X)
            movementVelocityY = self.trainer.readFloat(self.base+OFFSET_MOVEMENT_VELOCITY_Y)
            movementVelocityZ = self.trainer.readFloat(self.base+OFFSET_MOVEMENT_VELOCITY_Z)
            if (name == 'movementVelocity'):
                return [movementVelocityX, movementVelocityY, movementVelocityZ]
            elif (name == 'movementVelocityX'):
                return movementVelocityX
            elif (name == 'movementVelocityY'):
                return movementVelocityY
            elif (name == 'movementVelocityZ'):
                # player's value of OFFSET_MOVEMENT_VELOCITY_Z won't get set correctly by the game if the player is in a vehicle.
                return movementVelocityZ
        elif (name in ('spinVelocity', 'spinVelocityX', 'spinVelocityY', 'spinVelocityZ')):
            spinVelocityX = self.trainer.readFloat(self.base+OFFSET_SPIN_VELOCITY_X)
            spinVelocityY = self.trainer.readFloat(self.base+OFFSET_SPIN_VELOCITY_Y)
            spinVelocityZ = self.trainer.readFloat(self.base+OFFSET_SPIN_VELOCITY_Z)
            if (name == 'spinVelocity'):
                return [spinVelocityX, spinVelocityY, spinVelocityZ]
            elif (name == 'spinVelocityX'):
                return spinVelocityX
            elif (name == 'spinVelocityY'):
                return spinVelocityY
            elif (name == 'spinVelocityZ'):
                return spinVelocityZ

    def __setattr__(self, name, value):
        if (name in ('trainer', 'base')):
            return builtins.object.__setattr__(self, name, value)
        if (not self.base):
            return
        elif (name == 'id'):
            return self.trainer.writeInteger(self.base+OFFSET_OBJECT_ID, 2, value) # Don't do this. The game will crash!
        elif (name in ('position', 'positionX', 'positionY', 'positionZ')):
            # moving a vehicle also moves the passengers accordingly
            positionBase = self.trainer.readInteger(self.base+OFFSET_OBJECT_POSITION, 4)
            if (not positionBase):
                return
            if (name == 'position'):
                self.trainer.writeFloat(positionBase+OFFSET_OBJECT_POSITION_X, value[0])
                self.trainer.writeFloat(positionBase+OFFSET_OBJECT_POSITION_Y, value[1])
                self.trainer.writeFloat(positionBase+OFFSET_OBJECT_POSITION_Z, value[2])
                return
            elif (name == 'positionX'):
                return self.trainer.writeFloat(positionBase+OFFSET_OBJECT_POSITION_X, value)
            elif (name == 'positionY'):
                return self.trainer.writeFloat(positionBase+OFFSET_OBJECT_POSITION_Y, value)
            elif (name == 'positionZ'):
                return self.trainer.writeFloat(positionBase+OFFSET_OBJECT_POSITION_Z, value)
        elif (name in ('movementVelocity', 'movementVelocityX', 'movementVelocityY', 'movementVelocityZ')):
            # moving a vehicle also moves the passengers accordingly
            if (name == 'movementVelocity'):
                self.trainer.writeFloat(self.base+OFFSET_MOVEMENT_VELOCITY_X, value[0])
                self.trainer.writeFloat(self.base+OFFSET_MOVEMENT_VELOCITY_Y, value[1])
                self.trainer.writeFloat(self.base+OFFSET_MOVEMENT_VELOCITY_Z, value[2])
                return
            elif (name == 'movementVelocityX'):
                return self.trainer.writeFloat(self.base+OFFSET_MOVEMENT_VELOCITY_X, value)
            elif (name == 'movementVelocityY'):
                return self.trainer.writeFloat(self.base+OFFSET_MOVEMENT_VELOCITY_Y, value)
            elif (name == 'movementVelocityZ'):
                return self.trainer.writeFloat(self.base+OFFSET_MOVEMENT_VELOCITY_Z, value)
        elif (name in ('spinVelocity', 'spinVelocityX', 'spinVelocityY', 'spinVelocityZ')):
            # moving a vehicle also moves the passengers accordingly
            if (name == 'spinVelocity'):
                self.trainer.writeFloat(self.base+OFFSET_SPIN_VELOCITY_X, value[0])
                self.trainer.writeFloat(self.base+OFFSET_SPIN_VELOCITY_Y, value[1])
                self.trainer.writeFloat(self.base+OFFSET_SPIN_VELOCITY_Z, value[2])
                return
            elif (name == 'spinVelocityX'):
                return self.trainer.writeFloat(self.base+OFFSET_SPIN_VELOCITY_X, value)
            elif (name == 'spinVelocityY'):
                return self.trainer.writeFloat(self.base+OFFSET_SPIN_VELOCITY_Y, value)
            elif (name == 'spinVelocityZ'):
                return self.trainer.writeFloat(self.base+OFFSET_SPIN_VELOCITY_Z, value)
        elif (name == 'angle'):
            positionBase = self.trainer.readInteger(self.base+OFFSET_OBJECT_POSITION, 4)
            if (not positionBase):
                return
            x, y, z = value
            # euler rotation matrix, my math skills aren't good enough to understand it
            x_cos = math.cos(x)
            x_sin = math.sin(x)
            y_cos = math.cos(y)
            y_sin = math.sin(y)
            z_cos = math.cos(z)
            z_sin = math.sin(z)
            self.trainer.writeFloat(positionBase+0x00, y_cos*z_cos)
            self.trainer.writeFloat(positionBase+0x04, -z_sin)
            self.trainer.writeFloat(positionBase+0x08, y_sin)
            self.trainer.writeFloat(positionBase+0x10, z_sin)
            self.trainer.writeFloat(positionBase+0x14, x_cos*z_cos)
            self.trainer.writeFloat(positionBase+0x18, -x_sin)
            self.trainer.writeFloat(positionBase+0x20, -y_sin)
            self.trainer.writeFloat(positionBase+0x24, x_sin)
            self.trainer.writeFloat(positionBase+0x28, x_cos*y_cos)

class Vehicle(BaseObject):
    def __init__(self, trainer, base):
        BaseObject.__init__(self, trainer, base)

    def __getattribute__(self, name):
        if (name not in ('trainer', 'base') and not self.base):
            return
        elif (name == 'life'):
            return self.trainer.readFloat(self.base+OFFSET_VEHICLE_LIFE)
        elif (name == 'type'):
            return self.trainer.readInteger(self.base+OFFSET_VEHICLE_TYPE, 4)
        else:
            return BaseObject.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if (name not in ('trainer', 'base') and not self.base):
            return
        elif (name == 'life'):
            return self.trainer.writeFloat(self.base+OFFSET_VEHICLE_LIFE, value)
        elif (name == 'type'):
            return self.trainer.writeInteger(self.base+OFFSET_VEHICLE_TYPE, 4, value)
        else:
            return BaseObject.__setattr__(self, name, value)

class Person(BaseObject):
    def __init__(self, trainer, base):
        BaseObject.__init__(self, trainer, base)

    def __getattribute__(self, name):
        if (name not in ('trainer', 'base') and not self.base):
            return
        elif (name == 'life'):
            return self.trainer.readFloat(self.base+OFFSET_PERSON_LIFE)
        elif (name == 'maxLife'):
            return self.trainer.readFloat(self.base+OFFSET_PERSON_MAXLIFE) # seems to be read-only
        elif (name == 'vest'):
            return self.trainer.readFloat(self.base+OFFSET_PERSON_VEST)
        elif (name == 'oxygen'):
            miscBase = self.trainer.readInteger(self.base+OFFSET_PLAYER_MISC_BASE_POINTER, 4)
            if (not miscBase):
                return
            return self.trainer.readFloat(miscBase+OFFSET_PLAYER_MISC_BASE_OXYGEN)
        elif (name == 'vehicleBase'):
            return self.trainer.readInteger(self.base+OFFSET_PERSON_VEHICLE_OBJECT, 4)
        elif (name == 'vehicle'):
            vehicle = self.trainer.readInteger(self.base+OFFSET_PERSON_VEHICLE_OBJECT, 4)
            return Vehicle(self.trainer, vehicle)
        elif (name == 'weaponIndex'): # TODO?: use signed integer instead of unsigned integer?
            return self.trainer.readInteger(self.base+OFFSET_PERSON_WEAPON_INDEX, 1)
        elif (name == 'weapon'):
            return Weapon(self.trainer, self.base, self.weaponIndex)
        else:
            return BaseObject.__getattribute__(self, name)

    def __setattr__(self, name, value):
        if (name not in ('trainer', 'base') and not self.base):
            return
        elif (name == 'life'):
            return self.trainer.writeFloat(self.base+OFFSET_PERSON_LIFE, value)
        elif (name == 'vest'):
            return self.trainer.writeFloat(self.base+OFFSET_PERSON_VEST, value)
        elif (name == 'oxygen'):
            miscBase = self.trainer.readInteger(self.base+OFFSET_PLAYER_MISC_BASE_POINTER, 4)
            if (not miscBase):
                return
            return self.trainer.writeFloat(miscBase+OFFSET_PLAYER_MISC_BASE_OXYGEN, value)
        elif (name == 'vehicle'):
            return self.trainer.writeInteger(self.base+OFFSET_PERSON_VEHICLE_OBJECT, 4, value)
        elif (name == 'weaponIndex'): # use signed integer instead of unsigned integer
            return self.trainer.writeInteger(self.base+OFFSET_PERSON_WEAPON_INDEX, 1, value)
        else:
            return BaseObject.__setattr__(self, name, value)

class Weapon:
    def __init__(self, trainer, personBase, index):
        self.trainer = trainer
        self.index = index
        index = (index*8)-index
        self.base = personBase+OFFSET_PERSON_WEAPON_BASE+(index*4)

    def __getattribute__(self, name):
        if (name in ('trainer', 'base', 'index')):
            return builtins.object.__getattribute__(self, name)
        if (not self.base or not self.index):
            return
        elif (name == 'type'):
            return self.trainer.readInteger(self.base+WEAPON_INDEX_TYPE, 4)
        elif (name == 'ammo'):
            val1_val2 = self.trainer.readInteger(self.base+WEAPON_INDEX_VAL1_VAL2, 4)
            if (self.index in WEAPON_SINGLE_NUMBER_SLOTS):
                val2 = None
            else:
                val2 = self.trainer.readInteger(self.base+WEAPON_INDEX_VAL2, 4)
                val1_val2 -= val2
            return val1_val2, val2

    def __setattr__(self, name, value):
        if (name in ('trainer', 'base', 'index')):
            return builtins.object.__setattr__(self, name, value)
        if (not self.base or not self.index):
            return
        elif (name == 'type'):
            return self.trainer.writeInteger(self.base+WEAPON_INDEX_TYPE, 4, value)
        elif (name == 'ammo'):
            if (self.index not in WEAPON_SINGLE_NUMBER_SLOTS):
                value[0] += value[1]
                self.trainer.writeInteger(self.base+WEAPON_INDEX_VAL2, 4, value[1])
            else:
                self.trainer.writeInteger(self.base+WEAPON_INDEX_VAL2, 4, 1)
            self.trainer.writeInteger(self.base+WEAPON_INDEX_VAL1_VAL2, 4, value[0])

class Trainer:
    def __init__(self):
        self.pedsTypes, self.pedsIds = self.getTypes('peds')
        self.vehicleTypes, self.vehicleIds = self.getTypes('vehicles')
        self.debugEnabled = False
        #self.debugEnabled = True
        self.getPid(EXE_NAME)
        self.getMaps()

    def message(self, msg, *args):
        print(msg.format(*args))

    def debug(self, msg, *args):
        if (self.debugEnabled):
            self.message('DEBUG: '+msg, *args)

    def error(self, msg, *args):
        self.message('ERROR: '+msg, *args)
        sys.exit(1)

    def speak(self, msg, *args, **kwargs):
        if (not self.debugEnabled):
            return
        s = msg.format(*args)
        self.message('Spoken: {0:s}', s)
        voice = kwargs['voice'] if 'voice' in kwargs else 'en-us'
        speed = str(kwargs['speed']) if 'speed' in kwargs else '175' # '140'
        pitch = str(kwargs['pitch']) if 'pitch' in kwargs else '50' # '40'
        l = ['espeak', '-v', voice, '-s', speed, '-p', pitch, s]
        subprocess.call(l)
        time.sleep(10)

    def timeDecode(self, timeVal):
        minute, second = divmod(timeVal//1000, 60)
        minute %= 100 # no mod 60 after that
        return '{0:02d}:{1:02d}'.format(minute, second)

    def readInteger(self, addr, length):
        if (length == 1):
            sf = '<B'
        elif (length == 2):
            sf = '<H'
        elif (length == 4):
            sf = '<L'
        elif (length == 8):
            sf = '<Q'
        self.memFp.seek(addr)
        d = self.memFp.read(struct.calcsize(sf))
        return struct.unpack(sf, d)[0]

    def readFloat(self, addr):
        sf = '<f'
        self.memFp.seek(addr)
        d = self.memFp.read(struct.calcsize(sf))
        return struct.unpack(sf, d)[0]

    def readDouble(self, addr):
        sf = '<d'
        self.memFp.seek(addr)
        d = self.memFp.read(struct.calcsize(sf))
        return struct.unpack(sf, d)[0]

    def writeInteger(self, addr, length, val):
        if (length == 1):
            sf = '<B'
        elif (length == 2):
            sf = '<H'
        elif (length == 4):
            sf = '<L'
        elif (length == 8):
            sf = '<Q'
        self.memFp.seek(addr)
        d = struct.pack(sf, val)
        self.memFp.write(d)

    def writeFloat(self, addr, val):
        sf = '<f'
        self.memFp.seek(addr)
        d = struct.pack(sf, val)
        self.memFp.write(d)

    def writeDouble(self, addr, val):
        sf = '<d'
        self.memFp.seek(addr)
        d = struct.pack(sf, val)
        self.memFp.write(d)

    def readBin(self, fn):
        fp = open(fn, 'rb')
        d = fp.read()
        fp.close()
        return d

    def dumpBin(self, addr, length, fn=''):
        self.memFp.seek(addr)
        d = self.memFp.read(length)
        if (not fn):
            fn = 'gtasa_dump_{0:d}.bin'.format(int(time.time()))
            #fn = 'gtasa_dump_pistol_and_machinepistol.bin'
            #fn = 'gtasa_dump_pistol_machinepistol_and_shotgun.bin'
            #fn = 'gtasa_dump_locked_car_2.bin'
            #fn = 'gtasa_dump_locked_car_2_unlocked.bin'
            #fn = 'gtasa_dump_my_unlocked_car.bin'
            #fn = 'gtasa_dump_my_car_color_lightgray.bin'
        fp = open(fn, 'w+b')
        fp.write(d)
        fp.flush()
        fp.close()

    def restoreBin(self, addr, fn):
        d = self.readBin(fn)
        #offset = 0x4e0
        #length = 0x200
        #offset = 0x5e0
        #length = 0x80
        #offset = 0x5e0
        #length = 0x40
        #offset = 0x5e0
        #length = 0x20
        offset = 0x5c0
        length = 0x80
        d = d[offset:offset+length]
        addr += offset
        self.memFp.seek(addr)
        self.memFp.write(d)

    def same_same_diff(self, fn1, fn2, fn3):
        d1, d2, d3 = self.readBin(fn1), self.readBin(fn2), self.readBin(fn3)
        l1, l2, l3 = len(d1), len(d2), len(d3)
        if (l1 != l2 or l1 != l3):
            self.error('same_same_diff: lengths are not equal')
        for i in range(l1):
            if (d1[i] == d2[i] and d1[i] != d3[i]):
                self.message('same_same_diff: Found: i:{0:#x}: d1=d2={1:#04x}, d3={2:#04x}', i, d1[i], d3[i])

    def same_diff_all(self, same_fns, diff_fns):
        same_ds = [self.readBin(i) for i in same_fns]
        diff_ds = [self.readBin(i) for i in diff_fns]
        all_ls = [len(i) for i in same_ds+diff_ds]
        first_l = all_ls[0]
        for i in range(1, len(all_ls)):
            if (first_l != all_ls[i]):
                self.error('same_diff_all: lengths are not equal')
        for i in range(first_l):
            found = True
            for j in range(1, len(same_ds)):
                if (same_ds[0][i] != same_ds[j][i]):
                    found = False
                    break
            for j in range(1, len(diff_ds)):
                if (diff_ds[0][i] != diff_ds[j][i]):
                    found = False
                    break
            for j in range(1, len(diff_ds)):
                if (same_ds[0][i] == diff_ds[j][i]):
                    found = False
                    break
            if (found):
                self.message('same_diff_all: Found: i:{0:#x}: sd={1:#04x}, dd={2:#04x}', i, same_ds[0][i], diff_ds[0][i])

    def getPid(self, name):
        for i in glob.glob('/proc/[0-9]*/cmdline'):
            fp = open(i, 'rb')
            argv = list(filter(None, fp.read().split(bytes(1))))
            fp.close()
            if (name in argv[0]):
                self.pid = int(i.split('/')[2])
                return
        self.error('PID not found!')

    def getMaps(self):
        fn = '/proc/{0:d}/maps'.format(self.pid)
        fp = open(fn, 'rb')
        l = list(filter(None, [b'rwxp' in i and b' 00000000 ' in i and i.strip().endswith(b' 0') and i.strip() for i in fp.readlines()]))
        fp.close()
        self.maps = []
        for i in l:
            il = i.split(b' ')[0].split(b'-')
            il = int(il[0], 16), int(il[1], 16)
            il = il[0], il[1]-il[0]
            self.maps.append(il)

    def openMem(self):
        fn = '/proc/{0:d}/mem'.format(self.pid)
        try:
            self.memFp = open(fn, 'r+b')
        except PermissionError:
            self.error('Are you sure that you\'ve disabled ptrace_scope?')
        except FileNotFoundError:
            self.error('Are you sure that you\'ve started the game?')

    def closeMem(self):
        self.memFp.flush()
        self.memFp.close()

    def searchPlayerObject(self):
        index = self.readInteger(ADDR_PLAYER_INDEX, 1)*0x190
        playerObjectAddress = self.readInteger(ADDR_PLAYER_BASE+index, 4)
        self.player = Person(self, playerObjectAddress)

    def getTypes(self, name):
        types = {}
        ids = {}
        fp = open('{0:s}/data/{1:s}.ide'.format(GAME_BASEDIR, name), 'rt')
        for line in fp.readlines():
            line = line.replace(' ', '')
            line = line.replace('\t', '')
            linearr = line.split(',')
            #print(line)
            if (line[0] != '#' and len(linearr) >= 4):
                entryId = int(linearr[0])
                entryType = linearr[3]
                if (entryType in types):
                    types[entryType].append(entryId)
                else:
                    types[entryType] = [entryId]
                ids[entryId] = entryType
        fp.close()
        return types, ids

    def searchPersonObjects(self):
        #people = [0x02f5e9c8, 0x02f60114, 0x02f62024, 0x02f627e8, 0x02f62fac, 0x02f63770, 0x02f64ebc, 0x02f65680, 0x02f65e44, 0x02f66608, 0x02f66dcc, 0x02f67590, 0x02f68518, 0x02f68cdc, 0x02f694a0, 0x02f69c64, 0x02f6a428, 0x02f6abec, 0x02f6b3b0, 0x02f6bb74, 0x02f6c338, 0x02f6cafc, 0x02f6d2c0, 0x02f6da84, 0x02f6e248]
        #people = [0x3193f78, 0x31a019c, 0x31a0960, 0x319282c, 0x31937b4, 0x31956c4, 0x319473c, 0x3192ff0]
        people = [0x3193f78]
        if 0:
        #if 1:
            for i in people:
                pass
                #self.teleportPersonCar(i)
                person = Person(self, i)
                person.positionZ += 2
                person.life = 999999
            exit()
        r = []
        self.openMem()
        for i in range(ADDR_OBJECTS_MAX_INDEX):
            base = self.readInteger(ADDR_OBJECTS+(i*4), 4)
            if (not base):
                continue
            found = True
            baseoffsets = [0x1cc, 0x298, 0x438, 0x50c]
            for baseoffset in baseoffsets:
                baseval = self.readInteger(base+baseoffset, 4)
                if (base != baseval):
                    found = False
                    break
            if (found):
                #r.append(base)
                #self.message('Possible Person Object: {0:#010x}', base)
                if (base != self.player.base):
                #if (base == self.player.base):
                    r.append(base)
                    person = Person(self, base)
                    #self.message('Possible Person Object Id: {0:d}', person.id)
                    #self.message('Possible Person Object Life: {0:f}', person.life)
                    #person.life = 999999
                    #print(person.weapon.ammo)
                    #person.life = 100
                    #self.teleport(base)
                    #self.teleportPersonCar(base)
                    if (not person.life):
                        pass
                        #self.speak("murder death kill") #, voice='mb-us1', speed=100, pitch=55) # sry, nothing really matches the voice in the movie
                    #if (person.id == 102 and not person.life):
                    #    self.speak("found dead ballas")
                    #elif (person.id == 102 and person.vehicle):
                    #    self.speak("found ballas in car")
                    #elif (person.id == 102):
                    #    self.speak("found ballas")
                    if 0:
                    #if 1:
                        for baseoffset in range(0, MAX_OBJECT_LENGTH_PERSON, 4):
                            maybetype = self.readInteger(base+baseoffset, 4)
                            if (maybetype and maybetype != 255 and maybetype in self.pedsIds):
                                self.message('maybe found type {0:d} offset {1:#06x}', maybetype, baseoffset)
                        self.message('')
                    if (person.id is None):
                        continue
                    #continue
                    #print(self.pedsIds)
                    #print(person.id)
                    #if (self.pedsIds[person.id] == 'GANG1'):
                    #    self.speak("found ballas")
                    #if (self.pedsIds[person.id] == 'GANG2'):
                    #    self.speak("found grove street families")
                    #if (self.pedsIds[person.id] == 'GANG3'):
                    #    self.speak("found los santos vagos")
                    #if (self.pedsIds[person.id] == 'GANG4'):
                    #    self.speak("found gang4 san fierro rifa")
                    #if (self.pedsIds[person.id] == 'GANG5'):
                    #    self.speak("found gang5 da nang boys")
                    #if (self.pedsIds[person.id] == 'GANG6'):
                    #    self.speak("found gang6 italian mafia")
                    #if (self.pedsIds[person.id] == 'GANG7'):
                    #    self.speak("found gang7 san fierro triads")
                    #if (self.pedsIds[person.id] == 'GANG8'):
                    #    self.speak("found varrios los aztecas")
                    #if (self.pedsIds[person.id] == 'PROSTITUTE'):
                    #    self.speak("found prostitute")
                    #if (self.pedsIds[person.id] == 'COP'):
                    #    self.speak("found cop")
                    #if (self.pedsIds[person.id] == 'FIREMAN'):
                    #    self.speak("found fireman")
                    #if (self.pedsIds[person.id] == 'MEDIC'):
                    #    self.speak("found sanitoeter") # typo intended
                    #if (person.life in (100, 120)):
                    #if (person.life in (120,)):
                    #if 1:
                    if 0:
                        person.weapon.ammo = [0, 0]
                        person.weaponIndex = 0
                        person.life = 0
                        person.positionZ += 10
                        if (person.vehicle.positionZ):
                            person.vehicle.positionZ += 10
                        pass
        self.closeMem()
        #exit()
        #if 1:
        if 0:
            for i in range(0, len(r)-1):
                i2 = r[i+1]-r[i]
                print(hex(i2))
        #if 1:
        if 0:
            #print(r)
            print('[', end='')
            for i in r:
                print('{0:#x}, '.format(i), end='')
            print(']')
            #for i in range(0, len(r)-1):
            #    i2 = r[i+1]-r[i]
            #    print(hex(i2))

    def searchVehicleObjects(self):
        #SEARCH_CARID = 596 # los santos pd copcar
        #SEARCH_CARID = 599 # ranger copcar
        #cars = [0x02fac9b0]
        #cars = ...
        #time.sleep(10)
        #while True:
        #if 1:
        if 0:
            for base in cars:
                vehicle = Vehicle(self, base)
                #i = self.readInteger(ADDR_CURRENT_UNKNOWN, 4)
                #self.message('Possible Car Index: {0:#010x}', i)
                #i = self.readInteger(ADDR_OBJECTS+(i*4), 4)
                pass
                #self.message('Possible Car Object: {0:#010x}', base)
                #self.message('Possible Car Object Life: {0:f}', vehicle.life)
                vehicle.positionZ += 10
                vehicle.life = 1000
                #vehicle.position = self.player.position
                #vehicle.angle = [0, 0, 0]
                #self.player.vehicle = base
                #self.dumpBin(base, MAX_OBJECT_LENGTH_CAR)
                #self.dumpBin(base, MAX_OBJECT_LENGTH_CAR, 'gtasa_dump_locked_car_red.bin')
                #self.dumpBin(base, MAX_OBJECT_LENGTH_CAR, 'gtasa_dump_locked_car_red_unlocked.bin')
                #self.dumpBin(base, MAX_OBJECT_LENGTH_CAR, 'gtasa_dump_locked_car_red_locked_again.bin')
                #self.dumpBin(base, MAX_OBJECT_LENGTH_CAR, 'gtasa_dump_locked_car_yellow_unlocked.bin')
                if (vehicle.id == SEARCH_CARID):
                    self.message('Possible Car Object: {0:#010x}', base)
                    pass
                    #self.dumpBin(base, MAX_OBJECT_LENGTH_CAR, 'gtasa_dump_locked_car_copcar_7.bin')
                    #self.dumpBin(base, MAX_OBJECT_LENGTH_CAR, 'gtasa_dump_locked_car_copcar_6_unlocked.bin')
                    #self.dumpBin(base, MAX_OBJECT_LENGTH_CAR, 'gtasa_dump_locked_car_copcar_6_unlocked2.bin')
            exit()
            time.sleep(1)
        #exit()
        r = []
        self.openMem()
        for i in range(ADDR_OBJECTS_MAX_INDEX):
            base = self.readInteger(ADDR_OBJECTS+(i*4), 4)
            if (not base):
                continue
            vehicle = Vehicle(self, base)
            found = True
            baseoffsets = [0x13c]
            for baseoffset in baseoffsets:
                baseval = self.readInteger(base+baseoffset, 4)
                if (base != baseval):
                    found = False
                    break
            magicval1 = self.readInteger(base+0x9c, 4)
            if (magicval1 != 0x3d4ccccd):
                found = False
            #if (vehicle.id != SEARCH_CARID):
            #    found = False
            if (found):
                #r.append(base)
                #self.message('Possible Car Object: {0:#010x}', base)
                if (base != self.player.vehicleBase):
                #if 1:
                    r.append(base)
                    #self.message('Possible Car Object Life: {0:f}', vehicle.life)
                    #self.dumpBin(base, MAX_OBJECT_LENGTH_CAR, 'gtasa_dump_locked_car_copcar_3.bin')
                    #self.writeFloat(base+OFFSET_VEHICLE_LIFE, 1000)
                    #self.teleport(base)
                    #carPositionObjectAddress = self.readInteger(base+OFFSET_OBJECT_POSITION, 4)
                    #self.setPositionAngle(carPositionObjectAddress, 0, 0, 0)
                    #vehicle.angle = [0, 0, 0]
                    #vehicle.positionZ += 20
                    if (vehicle.type is None):
                        continue
                    vehicleType = vehicle.type
                    vehicleTypeName = VEHICLE_TYPE_NAMES[vehicleType] if (vehicleType in VEHICLE_TYPE_NAMES) else "unknown"
                    if (vehicleTypeName == "unknown"):
                        self.speak("found unknown vehicle type number {0:d}", vehicleType)
                    if 1:
                        pass
                    elif (vehicle.id in self.vehicleTypes['train']):
                        print('Found Train XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                        #vehicle.movementVelocity = [0, 0, 0]
                        #vehicle.movementVelocityZ = 2
                        #vehicle.positionX += 20
                        #vehicle.positionY += 20
                        #vehicle.positionZ += 20
                    elif (vehicle.id in self.vehicleTypes['plane']):
                        print('Found Plane XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                        #vehicle.movementVelocityZ = -2


        self.closeMem()
        #if 1:
        if 0:
            #print(r)
            print('[', end='')
            for i in r:
                print('{0:#x}, '.format(i), end='')
            print(']')
            #for i in range(0, len(r)-1):
            #    i2 = r[i+1]-r[i]
            #    print(hex(i2))
        pass
        #exit()

    def searchMiscObjects(self):
        self.openMem()
        for i in range(ADDR_OBJECTS_MAX_INDEX):
            base = self.readInteger(ADDR_OBJECTS+(i*4), 4)
            if (not base):
                continue
            baseObject = BaseObject(self, base)
            #self.message('Possible Misc Object: {0:#010x}', base)
            if (baseObject.position):
                pass
                #self.message('Possible Misc Object: {0:#010x}', base)
                #self.message('Position: {0:s}', repr(baseObject.position))
                #baseObject.position[2] -= 10
            else:
                pass
                #self.message('Position not found.')
        self.closeMem()

    def getWantedLevelBase(self):
        base = self.readInteger(self.player.base+OFFSET_PLAYER_MISC_BASE_POINTER, 4)
        base = self.readInteger(base+OFFSET_PLAYER_MISC_BASE_WANTEDLEVEL_PTR, 4)
        #print('wantedlevel base:', hex(base))
        return base

    def getWantedLevel(self):
        base = self.getWantedLevelBase()
        points = self.readInteger(base+0x00, 4)
        level = self.readInteger(base+0x2c, 4)
        return points, level

    def setWantedLevel(self, level):
        base = self.getWantedLevelBase()
        points = WANTED_LEVELS[level]
        self.writeInteger(base+0x00, 4, points)
        self.writeInteger(base+0x2c, 4, level)

    def getMaximumWantedLevelPoints(self):
        value = self.readInteger(ADDR_MAXIMUM_WANTEDLEVEL_POINTS, 4)
        return value

    def setMaximumWantedLevelPoints(self, value=CONSTANT_MAXIMUM_WANTEDLEVEL_POINTS):
        self.writeInteger(ADDR_MAXIMUM_WANTEDLEVEL_POINTS, 4, value)

    def getTimeSpeed(self):
        value = self.readInteger(ADDR_TIME_SPEED, 4)
        value2 = self.readInteger(self.player.base+OFFSET_PLAYER_TIME_SPEED, 4)
        return value, value2

    def setTimeSpeed(self, value=CONSTANT_TIME_SPEED):
        self.writeInteger(ADDR_TIME_SPEED, 4, value)
        self.writeInteger(self.player.base+OFFSET_PLAYER_TIME_SPEED, 4, 0)

    def getTime(self):
        minute = self.readInteger(ADDR_MINUTE, 1)
        hour = self.readInteger(ADDR_HOUR, 1)
        return hour, minute

    def setTime(self, hour, minute):
        if (minute is not None):
            self.writeInteger(ADDR_MINUTE, 1, minute%60)
        if (hour is not None):
            self.writeInteger(ADDR_HOUR, 1, hour%24)

    def getVehicleTires(self):
        # on six-wheels (barracks, military troop transportation vehicle), the values for the back tires are for both sets (four back tires)
        carObjectAddress = self.player.vehicleBase
        if (not carObjectAddress):
            return
        if (self.player.vehicle.type == VEHICLE_TYPE_CAR):
            for index in CAR_TIRE_INDEXES:
                statusVal = self.readInteger(carObjectAddress+OFFSET_CAR_STATUS_BASE+OFFSET_CAR_STATUS_BASE_TIRE_BROKEN_INDEX+index, 1)
                position = CAR_TIRE_INDEXES_NAMES[index]
                print('{0:s} tire: {1:s}'.format(position, 'broken' if (statusVal == TIRE_BROKEN) else 'OK'))
        elif (self.player.vehicle.type == VEHICLE_TYPE_TWOWHEEL):
            for index in TWOWHEEL_TIRE_INDEXES:
                statusVal = self.readInteger(carObjectAddress+OFFSET_CAR_STATUS_TWOWHEEL_TIRE_BROKEN_INDEX+index, 1)
                position = TWOWHEEL_TIRE_INDEXES_NAMES[index]
                print('{0:s} tire: {1:s}'.format(position, 'broken' if (statusVal == TIRE_BROKEN) else 'OK'))

    def setVehicleTires(self, status=[TIRE_OK, TIRE_OK, TIRE_OK, TIRE_OK]):
        carObjectAddress = self.player.vehicleBase
        if (not carObjectAddress):
            return
        if (self.player.vehicle.type == VEHICLE_TYPE_CAR):
            for index in CAR_TIRE_INDEXES:
                statusVal = status[index]
                self.writeInteger(carObjectAddress+OFFSET_CAR_STATUS_BASE+OFFSET_CAR_STATUS_BASE_TIRE_BROKEN_INDEX+index, 1, statusVal)
                position = CAR_TIRE_INDEXES_NAMES[index]
                #print('{0:s} tire: {1:s}'.format(position, 'broken' if (statusVal == TIRE_BROKEN) else 'OK'))
        elif (self.player.vehicle.type == VEHICLE_TYPE_TWOWHEEL):
            for index in TWOWHEEL_TIRE_INDEXES:
                statusVal = status[index]
                self.writeInteger(carObjectAddress+OFFSET_CAR_STATUS_TWOWHEEL_TIRE_BROKEN_INDEX+index, 1, statusVal)
                position = TWOWHEEL_TIRE_INDEXES_NAMES[index]
                #print('{0:s} tire: {1:s}'.format(position, 'broken' if (statusVal == TIRE_BROKEN) else 'OK'))

    def spin(self):
        self.openMem()
        self.searchPlayerObject()
        if (not self.player.vehicle):
            return
        self.player.vehicle.angle = [0, 0, 0]
        self.closeMem()
        #return
        time.sleep(5)
        i = 0.0
        while True:
            if (i >= 360.0):
                break
            self.openMem()
            self.player.vehicle.angle = [0, 0, i]
            self.closeMem()
            i += 0.001
            #i += 0.01
            #i += 0.1
            #time.sleep(0.001)
            time.sleep(0.01)

    def fly(self):
        self.openMem()
        self.searchPlayerObject()
        if (not self.player.vehicle):
            return
        self.closeMem()
        #return
        #time.sleep(5)
        while True:
            self.openMem()
            self.player.vehicle.life = 1000
            self.setVehicleTires()
            velocity = self.player.vehicle.movementVelocity
            #print(velocity)
            self.player.vehicle.movementVelocity = [0, 0, 0]
            position = self.player.vehicle.position
            #if 1:
            if 0:
                for i in range(3):
                    if (velocity[i] > 0):
                        #position[i] += 1
                        position[i] += 0.1
                    elif (velocity[i] < 0):
                        #position[i] -= 1
                        position[i] -= 0.1
            #position[0] += 0.1
            #position[1] += 1
            position[1] += 0.01
            self.player.vehicle.position = position
            self.player.vehicle.angle = [0, 0, 0]
            self.closeMem()
            #break
            time.sleep(0.001)
            #time.sleep(0.01)
            #time.sleep(0.1)
            #time.sleep(1)

    def rcCar(self):
        self.openMem()
        self.searchPlayerObject()
        self.closeMem()
        #return
        #time.sleep(5)
        MOVEMENT_SPEED = 20
        while True:
            self.openMem()
            self.player.vehicle.life = 1000
            self.setVehicleTires()
            if (self.player.vehicle):
                playerPosition = self.player.position
                velocity = self.player.vehicle.movementVelocity
                if (any(velocity[0:2])):
                    print(velocity)
                self.player.movementVelocity = [0, 0, 0]
                self.player.vehicle.movementVelocity = [0, 0, 0]
                position = self.player.vehicle.position
                if 1:
                #if 0:
                    #if 1:
                    if 0:
                        if (velocity[2] != 0):
                            for i in range(3):
                                pos = position[i]-playerPosition[i]-5
                                pos2 = playerPosition[i]-position[i]-5
                                if (pos > 0):
                                    position[i] -= MOVEMENT_SPEED
                                elif (pos2 > 0):
                                    position[i] += MOVEMENT_SPEED
                    if 1:
                    #if 0:
                        for i in range(2):
                            #if (velocity[i] != 0):
                            #    position[2] += 0.05
                            if (velocity[i] >= 0.01):
                                position[i] += MOVEMENT_SPEED
                            elif (velocity[i] <= -0.01):
                                position[i] -= MOVEMENT_SPEED
                #position[0] += 0.1
                #position[1] += 1
                #position[1] += 0.01
                self.player.vehicle.position = position
                self.player.vehicle.angle = [0, 0, 0]
                playerPosition[0] = position[0]
                playerPosition[1] = position[1]
                playerPosition[2] = position[2]+2
                self.player.position = playerPosition
            self.closeMem()
            #break
            #time.sleep(0.001)
            #time.sleep(0.01)
            #time.sleep(0.1)
            time.sleep(0.2)
            #time.sleep(0.4)
            #time.sleep(0.5)
            #time.sleep(1)

    def onlyDaylight(self):
        time_hour, time_minute = self.getTime()
        if (time_hour < 8 or time_hour >= 18):
            time_hour = 8
        self.setTime(time_hour, None)

    def run(self):
        self.openMem()
        self.searchPlayerObject()
        print('playerAddress:', hex(self.player.base))
        print('playerVehicleAddress:', hex(self.player.vehicle.base))
        #self.spin()
        #self.fly()
        #self.rcCar()
        self.searchPersonObjects()
        #exit()
        if 0:
        #while True:
            self.openMem()
            time_hour, time_minute = self.getTime()
            #time_hour += 6
            if (time_hour >= 18):
                time_hour = 8
            #time_minute += 4
            #self.setTime(time_hour, time_minute)
            self.setTime(time_hour, None)
            #print('all set')
            #time.sleep(0.1)
            time.sleep(1)
            self.closeMem()
        if 0:
        #while True:
            #self.writeInteger(ADDR_LAUFBAND_LEVEL_REAL, 4, 10)
            #self.writeInteger(ADDR_LAUFRAD_LEVEL_REAL, 4, 10)
            #self.writeFloat(ADDR_LAUFBAND_STRENGTH_REAL, 100)
            self.writeFloat(ADDR_LAUFRAD_STRENGTH_REAL, 100)
            #print(self.readFloat(ADDR_LAUFBAND_STRENGTH_REAL))
            time.sleep(LAUFBANDRAD_SLEEP_TIME)
            #time.sleep(1.3)
            #self.writeFloat(ADDR_KURZHANTEL_STRENGTH_REAL, HANTEL_SET_STRENGTH)
            #self.writeFloat(ADDR_LANGHANTEL_STRENGTH_REAL, HANTEL_SET_STRENGTH)
            #time.sleep(HANTEL_SLEEP_TIME)
        if 0:
        #if 1:
            #self.same_same_diff('gtasa_dump_locked_car_0.bin', 'gtasa_dump_locked_car_1.bin', 'gtasa_dump_locked_car_1_unlocked.bin')
            self.same_same_diff('gtasa_dump_locked_car_red.bin', 'gtasa_dump_locked_car_red_locked_again.bin', 'gtasa_dump_locked_car_red_unlocked.bin')
            #self.same_diff_all(['gtasa_dump_locked_car_0.bin', 'gtasa_dump_locked_car_1.bin', 'gtasa_dump_locked_car_2.bin', 'gtasa_dump_locked_car_red.bin', 'gtasa_dump_locked_car_yellow2.bin', 'gtasa_dump_locked_car_yellow.bin'], ['gtasa_dump_locked_car_1_unlocked.bin', 'gtasa_dump_my_unlocked_car.bin'])
        #self.searchVehicleObjects()
        #self.searchMiscObjects()
        #exit()
        #return
        self.openMem()
        #"""
        if (1):
        #if (0):
            self.setMaximumWantedLevelPoints(0)
            self.setWantedLevel(0)
        else:
            self.setMaximumWantedLevelPoints(999999)
            self.setWantedLevel(6)
        self.player.life = 999999
        self.player.vest = 999999
        self.player.oxygen = 999999
        self.writeFloat(ADDR_MONEY_HAVE, 999999999)
        self.writeFloat(ADDR_MONEY_COUNTER, 999999999)
        if 1:
        #if 0:
            Weapon(self, self.player.base, WEAPON_SLOT_INDEX_CLUBS).ammo = [30000, None]
            Weapon(self, self.player.base, WEAPON_SLOT_INDEX_PISTOLS).ammo = [29500, 500]
            Weapon(self, self.player.base, WEAPON_SLOT_INDEX_SHOTGUNS).ammo = [30000, None]
            Weapon(self, self.player.base, WEAPON_SLOT_INDEX_MACHINEPISTOLS).ammo = [29500, 500] # 100 instead of 50 on hitman level
            Weapon(self, self.player.base, WEAPON_SLOT_INDEX_MACHINEGUNS).ammo = [29500, 500]
            Weapon(self, self.player.base, WEAPON_SLOT_INDEX_SPRAYS).ammo = [29500, 500]
            Weapon(self, self.player.base, WEAPON_SLOT_INDEX_GRENADES).ammo = [30000, None]
            #self.writeInteger(self.player.base+0x12c, 4, 0x3efffef4)
            #self.writeInteger(self.player.base+0x12c, 4, 0x3efffffe)
            #self.writeInteger(self.player.base+0x12c, 2, 0xdead)
            #self.writeInteger(self.player.base+0x5c8, 4, 0xc)
            #self.writeInteger(self.player.base+0x5fc, 4, 0x1)
            #self.writeInteger(self.player.base+0x600, 4, 0x1f4)
            #self.writeInteger(self.player.base+0x604, 4, 0x4ca7a)
            #self.writeInteger(self.player.base+0x620, 4, 0x4aeea)
            #if 1:
            if 0:
                Weapon(self, self.player.base, WEAPON_SLOT_INDEX_CLUBS).type = WEAPON_TYPES_CLUBS_POLICEBATON # works directly
                Weapon(self, self.player.base, WEAPON_SLOT_INDEX_PISTOLS).type = WEAPON_TYPES_PISTOLS_9MM
                Weapon(self, self.player.base, WEAPON_SLOT_INDEX_MACHINEPISTOLS).type = WEAPON_TYPES_MACHINEPISTOLS_TEC9
                #Weapon(self, self.player.base, WEAPON_SLOT_INDEX_SPRAYS).type = WEAPON_TYPES_SPRAYS_SPRAYCAN
                #Weapon(self, self.player.base, WEAPON_SLOT_INDEX_CLUBS2).type = WEAPON_TYPES_CLUBS2_GIANTDILDO
                pass
        self.player.vehicle.life = 999999
        #self.player.vehicle.life = 1000
        #self.player.vehicle.life = 0
        #self.setVehicleTires()
        #self.setVehicleTires([TIRE_BROKEN, TIRE_BROKEN, TIRE_BROKEN, TIRE_BROKEN])
        #"""
        #print('playerAddress:', hex(self.player.base))
        #print('current wantedlevel:', self.getWantedLevel())
        #print('position:', self.player.position)
        #self.player.position = [1790.400390625, 573.1087036132812, -0.6294232606887817]
        #self.player.positionX += 100
        #self.player.positionZ += 50
        #print('weapon type club:', hex(self.getWeaponType(WEAPON_SLOT_INDEX_CLUBS)))
        #return
        #print('Time Speed:', self.getTimeSpeed())
        #self.setTimeSpeed()
        time_hour, time_minute = self.getTime()
        self.message('Time: {0:02d}:{1:02d}', time_hour, time_minute)
        print('Life:', self.player.life)
        print('Oxygen:', self.player.oxygen)
        #print('shotgunErrorValue:', hex(self.readInteger(self.player.base+0x5f4, 4)))
        #print('baton addr:', hex(self.player.base+0x5bc))
        #print('misc machinepistol addr:', hex(self.player.base+0x610))
        print('current weapon index:', self.player.weaponIndex)
        print('current weapon addr:', hex(self.player.weapon.base))
        print('current weapon type:', self.player.weapon.type)
        print('current weapon ammo:', self.player.weapon.ammo)
        print('current wantedlevel:', self.getWantedLevel())
        print('maximum_wantedlevel_points:', self.getMaximumWantedLevelPoints())
        print('current radio channel:', self.readInteger(ADDR_CURRENT_RADIO_CHANNEL, 1))
        self.message('mission?/vigilante time left: {0:s}', self.timeDecode(self.readInteger(ADDR_VIGILANTE_TIME_LEFT_ENCODED, 4)))
        self.message('mission?/vigilante leftcar time left: {0:d}', self.readInteger(ADDR_VIGILANTE_LEFTCAR_TIME_LEFT, 4)//1000)
        vehicleType = self.player.vehicle.type
        if (vehicleType is not None):
            vehicleTypeName = VEHICLE_TYPE_NAMES[vehicleType] if (vehicleType in VEHICLE_TYPE_NAMES) else "unknown"
            self.message('current VehicleType: {0:d}, name: {1:s}', vehicleType, vehicleTypeName)
            if (vehicleTypeName == "unknown"):
                self.speak("current vehicle type number {0:d} unknown", vehicleType)
            self.getVehicleTires()
            self.setVehicleTires()
        #self.setTimeSpeed(CONSTANT_TIME_SPEED//2)
        #self.setTimeSpeed()
        if 0:
        #if 1:
            for i in range(0, 0x1000, 4):
                print('i:', hex(i), hex(self.readInteger(self.player.base+i, 4)))
        if 0:
        #if 1:
            cl = []
            cl.extend([0x490, 0x494, 0x498, 0x49c])
            cl.extend([0x4a4, 0x4a8, 0x4ac])
            cl.extend([0x4b0, 0x4b4, 0x4b8, 0x4bc])
            cl.extend([0x4c0, 0x4c4, 0x4c8])
            cl.extend([0x4d0])
            cl.extend([0xc50, 0xc54, 0xc58, 0xc5c])
            cl.extend([0xc60, 0xc64, 0xc68, 0xc6c])
            cl.extend([0xc70, 0xc74, 0xc78, 0xc7c])
            cl.extend([0xc80, 0xc84, 0xc88, 0xc8c])
            cl.extend([0xc90, 0xc94])
            for i in cl:
                self.writeInteger(self.player.base+i, 4, 0)
        if 0:
        #if 1:
            #time.sleep(5)
            for i in range(256):
            #for i in range(40, 50):
            #for i in range(45, 50):
                print(i)
                Weapon(self, self.player.base, WEAPON_SLOT_INDEX_CLUBS).type = i
                time.sleep(0.1)
        print('playerAddress:', hex(self.player.base))
        #print(self.player.vehicle.movementVelocity)
        #self.player.vehicle.movementVelocity = [0, 0, 5]
        #print(self.player.movementVelocity)
        #self.player.movementVelocity = [0, 0, 5]
        #self.player.vehicle.movementVelocity = [0, 0, -500]
        #self.player.movementVelocity = [40, 20, -500]
        #self.dumpBin(0x02f6cafc, 0x1000)
        #self.dumpBin(0x02fb6118, 0x1000)
        #self.dumpBin(0x2fadde0, 0x1000)
        #self.dumpBin(self.player.car.base, MAX_OBJECT_LENGTH_CAR)
        self.onlyDaylight()
        #self.player.vehicle.position = self.player.position
        self.closeMem()
        #exit()
        if 0:
        #if 1:
            while (True):
                self.openMem()
                print('player position:', self.player.position)
                #break
                #time.sleep(0.01)
                #self.player.position = [245, 70, 1005] # pershing square inside of the p.d.
                #self.player.position = [1551, -1674, 16] # pershing square outside of the p.d.
                #self.player.position = [2495, -1684, 14] # infront of cj's house
                #self.player.position = [1040, -1334, 14] # infront of crash cops donut shop
                #self.player.position = [1361, -1282, 14] # in front of ammu nation
                #self.player.position = [799, -1630, 14] # ogloc burger shot
                #self.player.position = [415, -1431, 34] # girlfriend restaurant
                #self.player.position = [245, 70, 1505]
                #self.player.position = [20, 20, 200]
                #self.player.position = [245, 70, 205]
                #self.player.position = [262, 38, 3] # position of a submachinegun unterneath pershing square inside of the p.d.
                self.player.position = [1595, -2584, 50] # airport runway
                #self.player.positionX += 10
                #self.player.positionZ += 50
                #self.player.positionZ += 10
                #self.player.vehicle.positionZ += 10
                velocity = [0, 0, 0]
                #velocity = [0, 0, -0.5]
                #self.player.vehicle.movementVelocity = velocity
                #velocity = self.player.vehicle.movementVelocity
                #if (velocity[2] < 0):
                #    velocity[2] = -velocity[2]
                #velocity[0] *= 2
                #velocity[1] *= 2
                #velocity[2] *= 2
                #self.player.vehicle.movementVelocity = velocity
                #self.player.vehicle.angle = [0, 0, 0]
                pass
                self.closeMem()
                break
        #self.dumpBin(self.player.base, 0x1000)
        #fn = 'gtasa_dump_1546735634.bin'
        #fn = 'gtasa_dump_1546735652.bin'
        #fn = 'gtasa_dump_1546735665.bin'
        #fn = 'gtasa_dump_pistol.bin'
        #fn = 'gtasa_dump_pistol_machinepistol_and_shotgun.bin'
        #self.restoreBin(self.player.base, fn)

if (__name__ == '__main__'):
    trainer = Trainer()
    #trainer.run()
    #exit()

    while (True):
        trainer.run()
        #time.sleep(0.001)
        #time.sleep(0.01)
        #time.sleep(0.1)
        time.sleep(1)
        #time.sleep(2)
        #time.sleep(5)


