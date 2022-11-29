# This file works together with the triggerMV2.ino file

import serial
import time
import math as m

fref = '32816,32817,32562'  # Values returned by the sensor away from any source of magnetic field (in 3 axis digital mode)
xref = '32880'  # X value returned by the sensor away from any source of magnetic field (in single axis digital mode)
yref = '32945'  # Y value returned by the sensor away from any source of magnetic field (in single axis digital mode)
zref = '32754'  # Z value returned by the sensor away from any source of magnetic field (in single axis digital mode)
MV2range = 240  # Converts pin values in mT (for ±100 mT, the ADC saturates at a field roughly 20% larger than the range so : 0 <=> ~ -120mT | 65535 <=> ~ +120 mT)
alpha = m.pi/4  # Angle between the axis of the sensor and those of the electromagnet

def AskMV2(port) :
    print("PRESS 'q' TO EXIT..\n")
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = 115200
    ser.timeout = 0
    cmd = ''
    firstAnalog = False
    ser.open()
    while 1 : 
        init = ser.readline()
        time.sleep(0.05)
        if len(init) > 0 :
            break
    log = init.decode().strip('\n\r')
    print(log)
    while cmd != 'q' :
        cmd = input('Send:')
        ser.write(str(cmd+'\n').encode())  # IMPORTANT : Add '\n' to the command entered. Otherwise Arduino does not understand the command and returns nothing (readlines() returns '[]').
        time.sleep(0.05) 
        line = ser.readline()
        data = line.decode().strip('\n\r')
        if (cmd == 'a') :
            AD = 1
            if firstAnalog == False :
                ser.close()
                aref = SetAnalogRef(port,10)
                print('Set ref for Analog mode :')
                print(aref)
                ser.open()
                while 1 : 
                    init = ser.readline()
                    time.sleep(0.05)
                    if len(init) > 0 :
                        break
                firstAnalog = True
        else :
            AD = 0
        if (cmd == 'x') :
            if (AD == 0) :
                Bx = round((float(data)-float(xref))/MV2range,2)
            elif (AD == 1) :
                Bx = round((float(data)-aref[0])/MV2range,2)
            print('Bx = '+str(Bx)+' mT')
        elif (cmd == 'y') :
            if (AD == 0) :
                By = round((float(data)-float(yref))/MV2range,2)
            elif (AD == 1) :
                By = round((float(data)-aref[1])/MV2range,2)            
            print('By = '+str(By)+' mT')
        elif (cmd == 'z') :
            if (AD == 0) :
                Bz = round((float(data)-float(zref))/MV2range,2)
            elif (AD == 1) :
                Bz = round((float(data)-aref[2])/MV2range,2)
            print('Bz = '+str(Bz)+' mT')
        elif (cmd == 'f') :
            field = data.split(',')
            refield = fref.split(',')
            if (AD == 0) :
                Bx = round((float(field[0])-float(refield[0]))/MV2range,2)
                By = round((float(field[1])-float(refield[1]))/MV2range,2)
                Bz = round((float(field[2])-float(refield[2]))/MV2range,2)
            elif (AD == 1) :
                Bx = round((float(field[0])-aref[3][0])/MV2range,2)
                By = round((float(field[1])-aref[3][1])/MV2range,2)
                Bz = round((float(field[2])-aref[3][2])/MV2range,2)
            print('Bx = '+str(Bx)+' mT')
            print('By = '+str(By)+' mT')
            print('Bz = '+str(Bz)+' mT')
        else :
            print(data)
    print('finished')
    ser.close()
    return 0

def SetAnalogRef(port,repet) :
    aref = [0,0,0,[0,0,0]]
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = 115200
    ser.timeout = 0
    ser.open()
    while 1 :
        if (len(ser.readline()) > 0) :
            break
    ser.write('a\n'.encode())
    time.sleep(0.05)
    for k in range(repet) :
        ser.write('x\n'.encode())
        time.sleep(0.05)
        ser.write('y\n'.encode())
        time.sleep(0.05)
        ser.write('z\n'.encode())
        time.sleep(0.05)
        ser.write('f\n'.encode())
        time.sleep(0.05)
        lines = ser.readlines()
        axref = lines[-4].decode().strip('\n\r')
        ayref = lines[-3].decode().strip('\n\r')
        azref = lines[-2].decode().strip('\n\r')
        afref = lines[-1].decode().strip('\n\r').split(',')
        aref[0] += float(axref)/repet
        aref[1] += float(ayref)/repet
        aref[2] += float(azref)/repet
        aref[3][0] += float(afref[0])/repet
        aref[3][1] += float(afref[1])/repet
        aref[3][2] += float(afref[2])/repet
    ser.close()
    return aref
