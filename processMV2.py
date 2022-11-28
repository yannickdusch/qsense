import serial
import time
import math as m
import cv2  # after having installed opencv-python
import numpy as np

ref = '32816,32817,32562,17971'  # Values returned by the sensor away from any source of magnetic field (in digital mode)
#ref ='32608,32976,32768,14464'  # Ref values for A mode
MV2range = 240  # Converts pin values to mT (for ±100 mT, the ADC saturates at a field roughly 20% larger than the range so : 0 <=> ~ -120mT | 65535 <=> ~ +120 mT)
alpha = m.pi/4  # Angle between the axis of the sensor and those of the electromagnet
height, width = 256, 256  # Shape of the window displaying the data
col = 200  # Color of the window displaying the data (0 <=> black | 255 <=> white)

def extract(port) :  # Gets raw data from the sensor (returns pin values)
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = 115200
    ser.timeout = 0
    c = 0
    ser.open()
    while c == 0 :
        lines = ser.readlines()
        if (len(lines) > 0) :
            line = lines[0].decode().strip('\n\r')
            if len(line) > 8 :
                if (line[0] == '_') and (line[-1] == '_') :
                    MV2data = line[1:-1].split(',')
                    c += 1
    print('finished')
    ser.close()
    return(MV2data)

def RawToField(MV2data) :  # Converts pin values to mT by calculating the difference with ref values and dividing with MV2range
    data0 = ref.split(',')
    MV2field = []
    for i in range(len(data0)-1) :
        MV2field += [(float(MV2data[i])-float(data0[i]))/MV2range]
    return MV2field

def ChangeBase(MV2field) :  # Changes base by using the projection of the sensor axis on those of the electromagnet
    Bx, By, Bz = MV2field[0], MV2field[1], MV2field[2]
    BX = m.cos(alpha)*Bx - m.sin(alpha)*By
    BY = -m.sin(alpha)*Bx - m.cos(alpha)*By
    BZ = -Bz
    field = [BX,BY,BZ]
    return field

def GetSphericalCoord(field) :  # Calculates the spherical coordinates
    Bx, By, Bz = field[0], field[1], field[2]
    B = (Bx**2 + By**2 + Bz**2)**0.5
    if B == 0 :
        # print("No Field")
        return [0.0,0.0,0.0]
    theta = m.acos(Bz/B)
    if By == 0 :
        if Bx < 0 :
            phi = m.pi
        else :
            phi = 0
    else :
        phi = m.acos(Bx/((Bx**2+By**2)**0.5))*By/abs(By) + m.pi*(1 - By/abs(By))
    coord = [B,theta,phi]
    # print("Field : B = "+str(round(B,2))+" mT | θ = "+str(round(theta/m.pi,2))+"π | φ = "+str(round(phi/m.pi,2))+"π")
    return(coord)

def ProcessField(port) :  # All of the above at once
    MV2data = extract(port)
    MV2field = RawToField(MV2data)
    field = ChangeBase(MV2field)
    coord = GetSphericalCoord(field)
    return(coord)

def newbckground() :
    bckground = np.zeros((height,width,3), np.uint8)
    bckground[:,:] = (col,col,col)
    for k in range(3) :
        a = int(height/12)
        i = a-1 + 4*a*k
        bckground[i:i+2*a+1,a-1] = (0,0,0)
        bckground[i:i+2*a+2,-a] = (0,0,0)
        bckground[i,a-1:-a] = (0,0,0)
        bckground[i+2*a+1,a-1:-a] = (0,0,0)
        bckground[i+1:i+2*a,a:-(a+1)] = (col+20,col+20,col+20)
        bckground[i+1:i+2*a+1,a] = (150,150,150)
        bckground[i+1,a:-a] = (150,150,150)
        bckground[i+1:i+2*a+1,-(a+1)] = (150,150,150)
        bckground[i+2*a,a:-a] = (150,150,150)
    return bckground

def displaytext(bckground, data) :  # Prints text on the given background
    c = ['B = ','th = ','ph = ']   # PIL module could display special characters : θ, φ and π
    u = [' mT','pi','pi']
    font = cv2.FONT_HERSHEY_PLAIN
    fontScale = 1.4
    color = (0,0,0)
    thickness = 1
    a = int(height/12)
    for k in range(3) :
        if k == 0 :
            val = str(round(data[k],2))
        else :
            val = str(round(data[k]/m.pi,2))
        text = c[k]+val+u[k]
        coordinates = (int(4*a/3),int(5*a/2+4*a*k))
        imgdata = cv2.putText(bckground, text, coordinates, font, fontScale, color, thickness, cv2.LINE_AA)
    return imgdata

def displayMF(port) :  # Displays the live data in a separate window
    print('Press q to exit..')
    ser = serial.Serial()
    ser.port = port
    ser.baudrate = 115200
    ser.timeout = 0
    ser.open()
    while True :
        lines = ser.readlines()
        if (len(lines) > 0) :
            line = lines[0].decode().strip('\n\r')
            if len(line) > 8 :
                if (line[0] == '_') and (line[-1] == '_') :
                    MV2data = line[1:-1].split(',')
                    MV2field = RawToField(MV2data)
                    field = ChangeBase(MV2field)
                    coord = GetSphericalCoord(field)
                    bckground = newbckground()
                    imgdata = displaytext(bckground,coord)
                    cv2.imshow("Field", imgdata)
        time.sleep(0.05)
        if cv2.waitKey(1) & 0xFF == ord('q') :
            break
    print('exit')
    cv2.destroyAllWindows()
    ser.close()
