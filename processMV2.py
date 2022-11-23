# This file works together with the dataMV2 Arduino files

import serial
import math as m

ref = '32816,32817,32562,17971'  # Values returned by the sensor away from any source of magnetic field (in digital mode)
MV2range = 240  # Converts pin values in mT (for ±100 mT, the ADC saturates at a field roughly 20% larger than the range so : 0 <=> ~ -120mT | 65535 <=> ~ +120 mT)
alpha = m.pi/4  # Angle between the axis of the sensor and those of the electromagnet

def extract(port) :
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = 115200
    ser.timeout = 0
    c = 0
    ser.open()
    while c == 0 :
        lines = ser.readlines()
        if (len(lines) > 0) and (len(lines[0]) == len(ref)) :
            line = lines[0].decode().strip('\n\r')
            if line[17] == ',' :
                MV2data = line.split(',')
                c += 1
    print('finished')
    ser.close()
    return(MV2data)

def RawToField(MV2data) :
    data0 = ref.split(',')
    MV2field = []
    for i in range(len(data0)-1) :
        MV2field += [(float(MV2data[i])-float(data0[i]))/MV2range]
    return MV2field

def ChangeBase(MV2field) :
    Bx, By, Bz = MV2field[0], MV2field[1], MV2field[2]
    BX = m.cos(alpha)*Bx - m.sin(alpha)*By
    BY = -m.sin(alpha)*Bx - m.cos(alpha)*By
    BZ = -Bz
    field = [BX,BY,BZ]
    return field

def GetSphericalCoord(field) :
    Bx, By, Bz = field[0], field[1], field[2]
    B = (Bx**2 + By**2 + Bz**2)**0.5
    if B == 0 :
        print("No Field")
        return [0,0,0]
    theta = m.acos(Bz/B)
    if By == 0 :
        if Bx < 0 :
            phi = m.pi
        else :
            phi = 0
    else :
        phi = m.acos(Bx/((Bx**2+By**2)**0.5))*By/abs(By) + m.pi*(1 - By/abs(By))
    coord = [B,theta,phi]
    print("Field : B = "+str(round(B,2))+" mT | θ = "+str(round(theta/m.pi,2))+"π | φ = "+str(round(phi/m.pi,2))+"π")
    return(coord)

def ProcessField(port) :
    MV2data = extract(port)
    MV2field = RawToField(MV2data)
    field = ChangeBase(MV2field)
    coord = GetSphericalCoord(field)
    return(coord)
