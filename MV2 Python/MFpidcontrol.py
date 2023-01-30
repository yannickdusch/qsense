# /!\ THIS FILE IS INCOMPLETE. IT MUST STILL SEND THE CALCULATED CURRENT VALUES TO A GENERATOR.
# /!\ THE PID CONSTANTS HAVE TO BE SET.

import math as m
import serial
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt

ref = '32816,32817,32562,17971'  # Values returned by the sensor away from any source of magnetic field (in digital mode)
sens_x, sens_y, sens_z = 267, 267, 289  # Values of sensitivity (in LSB/mT) given by the MV2 datasheet (p. 16)
MV2sens = [sens_x, sens_y, sens_z]  # Converts pin values to mT (for ±100 mT, the ADC saturates at a field roughly 20% larger than the range so : 0 <=> ~ -120mT | 65535 <=> ~ +120 mT)
alpha = m.pi/4  # Angle between the axis of the sensor and those of the electromagnet

Kpb, Kib, Kdb = 0.5, 0.2, 0.4  # PID constants for B (I) regulation
Kpt, Kit, Kdt = 0.5, 0.2, 0.4  # PID constants for theta regulation
Kpp, Kip, Kdp = 0.5, 0.2, 0.4  # PID constants for phi regulation

B0 = 20/2**0.5
tau = 20 # Interval time in ms

##########################################################################################################

def Cartesian(B,theta,phi) :
    BX = B*m.sin(theta)*m.cos(phi)
    BY = B*m.sin(theta)*m.sin(phi)
    BZ = B*m.cos(theta)
    return(BX,BY,BZ)

def RawToField(MV2data) :  # Converts pin values to mT by calculating the difference with ref values and dividing with MV2range
    data0 = ref.split(',')
    MV2field = []
    for i in range(len(data0)-1) :
        MV2field += [(float(MV2data[i])-float(data0[i]))/MV2sens[i]]
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

def deps_dt(EPS) :  # Derivative computation
    return((EPS[0] - EPS[-1])/(tau/1000))

def Sepsdt(EPS, Seps) :  # Integral computation
    return(Seps + tau*(EPS[-1] + EPS[0])/2000)

##########################################################################################################

class RegulFieldPID :
    
    def __init__(self, cB, ctheta, cphi, port = 'COM3') : 
        self.ser = serial.Serial()
        self.ser.port = 'COM3'
        self.ser.baudrate = 115200
        self.ser.timeout = 0
        self.ser.open()
        
        self.fig = plt.figure(figsize = (8,14))
        self.ax1 = plt.subplot2grid((3, 2), (0, 0), colspan=2, rowspan=2, projection='3d')
        self.ax2 = plt.subplot2grid((3, 2), (2, 0))
        self.ax3 = plt.subplot2grid((3, 2), (2, 1))
        #self.ax2.axis('off')
        #self.ax3.axis('off')
        self.ax1.set_xlim([-50,50])
        self.ax1.set_ylim([-50,50])
        self.ax1.set_zlim([-50,50])
        self.ax1.view_init(15,-60)  # Args = angles (°)
        
        self.cB, self.ctheta, self.cphi = cB, ctheta, cphi  # Command values
        self.mB, self.mtheta, self.mphi = 0, 0, 0  # Measured values
        self.cBx, self.cBy, self.cBz = Cartesian(cB, ctheta, cphi)
        
        self.epsB, self.epsth, self.epsph = cB, ctheta, cphi  # Initialization of the error
        self.SepsB, self.Sepsth, self.Sepsph = 0, 0, 0  # Initialization of the error integral
        self.EPSB, self.EPSth, self.EPSph = [cB,cB], [ctheta,ctheta], [cphi,cphi]  # Initialization of the error last values (for derivative computation)
        
        self.I, self.theta, self.phi = cB/B0, ctheta, cphi
        
        self.I1, self.I2, self.I3, self.I4 = 0, 0, 0, 0
        
        self.anim = FuncAnimation(self.fig, self.animate, frames=100, interval=tau)
    
    def ComputeEpsilon(self) :
        self.epsB = self.cB - self.mB
        self.epsth = self.ctheta - self.mtheta
        self.epsph = self.cphi - self.mphi
        self.EPSB = [self.epsB, self.EPSB[0]]
        self.EPSth = [self.epsth, self.EPSth[0]]
        self.EPSph = [self.epsph, self.EPSph[0]]
        return(0)
    
    def ComputePID(self) :
        self.SepsB = Sepsdt(self.EPSB,self.SepsB)
        self.Sepsth = Sepsdt(self.EPSth,self.Sepsth)
        self.Sepsph = Sepsdt(self.EPSph,self.Sepsph)
        self.I = Kpb*self.epsB + Kib*self.SepsB + Kdb*deps_dt(self.EPSB)
        self.theta = Kpt*self.epsth + Kit*self.Sepsth + Kdt*deps_dt(self.EPSth)
        self.phi = Kpp*self.epsph + Kip*self.Sepsph + Kdp*deps_dt(self.EPSph)
        return(0)
    
    def ComputeCurrent(self) :
        self.I1 = -self.I*(m.sin(self.phi)*m.sin(self.theta)+m.cos(self.theta)/2)
        self.I2 = self.I*(m.sin(self.phi)*m.sin(self.theta)-m.cos(self.theta)/2)
        self.I3 = self.I*(m.cos(self.phi)*m.sin(self.theta)-m.cos(self.theta)/2)
        self.I4 = -self.I*(m.cos(self.phi)*m.sin(self.theta)+m.cos(self.theta)/2)
        return(0)
    
    def plot(self, Bmoy) :
        self.ax1.cla()
        self.ax2.clear()
        self.ax3.clear()
        
        self.ax1.set_xlim([-50,50])
        self.ax1.set_ylim([-50,50])
        self.ax1.set_zlim([-50,50])
        self.ax1.quiver(0,0,0,10,0,0,color = 'b')  # X axis
        self.ax1.quiver(0,0,0,0,10,0,color = 'k')  # Y axis
        self.ax1.quiver(0,0,0,0,0,10,color = 'k')  # Z axis
        self.ax1.quiver(0,0,0,Bmoy[0],Bmoy[1],Bmoy[2],color = 'r')
        self.ax1.quiver(0,0,0,self.cBx,self.cBy,self.cBz)
        self.ax1.quiver(self.cBx,self.cBy,self.cBz,Bmoy[0] - self.cBx,Bmoy[1] - self.cBy,Bmoy[2] - self.cBz, color = 'g')
        
        self.ax2.text(0.1, 0.8, "epsB = "+str(round(self.epsB,2))+" ; SepsB = "+str(round(self.SepsB,2)))
        self.ax2.text(0.1, 0.5, "epsth = "+str(round(self.epsth,2))+" ; Sepsth = "+str(round(self.Sepsth,2)))
        self.ax2.text(0.1, 0.2, "epsph = "+str(round(self.epsph,2))+" ; Sepsph = "+str(round(self.Sepsph,2)))
        self.ax3.text(0.2, 0.8, "I1 = "+str(round(self.I1,2))+" mA")
        self.ax3.text(0.2, 0.6, "I2 = "+str(round(self.I2,2))+" mA")
        self.ax3.text(0.2, 0.4, "I3 = "+str(round(self.I3,2))+" mA")
        self.ax3.text(0.2, 0.2, "I4 = "+str(round(self.I4,2))+" mA")
    
    def animate(self, i) :
        lines = self.ser.readlines()
        if (len(lines) > 0) :
            line = lines[0].decode().strip('\n\r')
            if len(line) > 8 :
                if (line[0] == '_') and (line[-1] == '_') :
                    MV2data = line[1:-1].split(',')
                    MV2field = RawToField(MV2data)
                    field = ChangeBase(MV2field)
                    #self.Bx, self.By, self.Bz = field[0], field[1], field[2]
                    spheric = GetSphericalCoord(field)
                    self.mB, self.mtheta, self.mphi = spheric[0], spheric[1], spheric[2]
                    #self.errB = 100*((self.cBx - self.Bx)**2 + (self.cBy - self.By)**2 + (self.cBz - self.Bz)**2)**0.5/self.cB
                    self.ComputeEpsilon()
                    self.ComputePID()
                    self.ComputeCurrent()
                    self.plot(field)  # This function is about to turn into a function which commands current generator (sending the values of I1, I2, I3 and I4)

    def close(self) :
        self.ser.close()
        plt.close(self.fig)
