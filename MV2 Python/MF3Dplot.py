# This file works together with the dataMV2.ino file.

# This file allows to plot the field as a live vector in a 3D window.

# To activate plot animations in Spyder: Tools > Preferences > IPython Console > Graphics > Backend and change it from "Inline" to "Automatic".

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import math as m
import serial

# plt.style.use('seaborn-pastel')  # other choice : 'Solarize_Light2'

ref = '32816,32817,32562,17971'  # Values returned by the sensor away from any source of magnetic field (in digital mode)
sens_x, sens_y, sens_z = 267, 267, 289  # Values of sensitivity (in LSB/mT) given by the MV2 datasheet (p. 16)
MV2sens = [sens_x, sens_y, sens_z]  # Converts pin values to mT (for ±100 mT, the ADC saturates at a field roughly 20% larger than the range so : 0 <=> ~ -120mT | 65535 <=> ~ +120 mT)
#alpha = m.pi/4  # Angle between the axis of the sensor and those of the electromagnet
alpha = -m.pi/2 # Angle between the axis of the sensor and those of the antenna
start = [0,0,0]  # Set origin
lim = 50 # Axes limit on plots

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

class MF3D :  # Real time 3D plot of the magnetic field vector
    
    def __init__(self, port = 'COM3', multi = False) :  # 'multi = True' activates the multiplotting (3D and 2D spherical angles)
        self.multi = multi
        self.lim = lim
        self.ser = serial.Serial()
        self.ser.port = 'COM3'
        self.ser.baudrate = 115200
        self.ser.timeout = 0
        self.ser.open()
        if self.multi :
            self.fig = plt.figure(figsize = (8,14))
            self.ax1 = plt.subplot2grid((3, 2), (0, 0), colspan=2, rowspan=2, projection='3d')
            self.ax2 = plt.subplot2grid((3, 2), (2, 0), polar = True)
            self.ax3 = plt.subplot2grid((3, 2), (2, 1), polar = True)
            self.ax1.set_xlim([-self.lim,self.lim])
            self.ax1.set_ylim([-self.lim,self.lim])
            self.ax1.set_zlim([-self.lim,self.lim])
            self.ax2.set_rlim([0,self.lim])
            self.ax2.set_theta_zero_location("E")
            self.ax3.set_rlim([0,self.lim])
            self.ax3.set_thetalim([0,m.pi])
            self.ax3.set_theta_zero_location("N")  # Put 0° on the right
            self.ax3.set_theta_direction(-1)  # Set clockwise direction
            self.ax1.view_init(15,-60)  # Args = angles (°)
            self.ax2.grid(True)
            self.ax3.grid(True)
        else :
            self.fig = plt.figure(figsize = (10,10))
            self.ax = plt.axes(projection = '3d')
            self.ax.set_xlim([-self.lim,self.lim])
            self.ax.set_ylim([-self.lim,self.lim])
            self.ax.set_zlim([-self.lim,self.lim])
            self.ax.quiver(start[0],start[1],start[2],10,0,0,color = 'b')  # X axis (colored version : R)
            self.ax.quiver(start[0],start[1],start[2],0,10,0,color = 'k')  # Y axis (colored version : G)
            self.ax.quiver(start[0],start[1],start[2],0,0,10,color = 'k')  # Z axis (colored version : B)
            self.ax.view_init(15,-60)  # Args = angles (°)
        self.anim = FuncAnimation(self.fig, self.animate, frames=100, interval=50)
    
    def MF3Dplot(self, Bmoy) :  # Plots only the 3D field (higher frame rate)
        self.ax.cla()  # Clear the content already plotted without closing the figure (NB : plt.clf() clears the figure without closing the window)
        self.ax.set_xlim([-self.lim,self.lim])
        self.ax.set_ylim([-self.lim,self.lim])
        self.ax.set_zlim([-self.lim,self.lim])
        self.ax.set_title("3D Magnetic Field : B = "+str(self.B)+" mT | θ = "+str(self.theta)+"π | φ = "+str(self.phi)+"π")
        self.ax.quiver(start[0],start[1],start[2],10,0,0,color = 'b')
        self.ax.quiver(start[0],start[1],start[2],0,10,0,color = 'k')
        self.ax.quiver(start[0],start[1],start[2],0,0,10,color = 'k')
        self.ax.quiver(start[0],start[1],start[2],Bmoy[0],Bmoy[1],Bmoy[2],color = 'r')
        self.ax.quiver(start[0],start[1],start[2],Bmoy[0],Bmoy[1],0)  # Projection of B on xy-plane
    
    def MFmultiplot(self, Bmoy) :  # Plots the field in 3D and shows the spherical coordinates in 2D plots
        self.Bxy = (Bmoy[0]**2 + Bmoy[1]**2)**0.5
        self.ax1.cla()  # Clear axes for the 3D figure
        self.ax2.cla()  # Clear axes for the first 2D figure
        self.ax3.cla()  # Clear axes for the second 2D figure
        self.ax1.set_xlim([-self.lim,self.lim])
        self.ax1.set_ylim([-self.lim,self.lim])
        self.ax1.set_zlim([-self.lim,self.lim])
        self.ax2.set_rlim([0,self.lim])
        self.ax2.set_theta_zero_location("E")
        self.ax3.set_rlim([0,self.lim])
        self.ax3.set_thetalim([0,m.pi])
        self.ax3.set_theta_zero_location("N")  # Put 0° on the right
        self.ax3.set_theta_direction(-1)  # Set clockwise direction
        self.ax1.set_title("3D Magnetic Field | B = "+str(self.B)+" mT")
        self.ax2.set_title("Spherical φ = "+str(self.phi)+"π")
        self.ax3.set_title("Spherical θ = "+str(self.theta)+"π")
        self.ax1.quiver(start[0],start[1],start[2],10,0,0,color = 'b')  # X axis
        self.ax1.quiver(start[0],start[1],start[2],0,10,0,color = 'k')  # Y axis
        self.ax1.quiver(start[0],start[1],start[2],0,0,10,color = 'k')  # Z axis
        self.ax1.quiver(start[0],start[1],start[2],Bmoy[0],Bmoy[1],Bmoy[2],color = 'r')
        self.ax1.quiver(start[0],start[1],start[2],Bmoy[0],Bmoy[1],0)  # Projection of B on xy-plane
        self.ax2.quiver(0,0,10,0,color = 'b',scale_units='y',scale=2)  # X axis
        self.ax2.quiver(0,0,0,10,color = 'k',scale_units='y',scale=2)  # Y axis
        self.ax2.quiver(start[0],start[1],Bmoy[0],Bmoy[1],color = 'c',scale_units='y',scale=2)    
        self.ax3.quiver(0,0,self.Bxy,0,color = 'c',scale_units='y',scale=2)  # Bxy
        self.ax3.quiver(0,0,0,10,color = 'k',scale_units='y',scale=2)  # Z axis
        self.ax3.quiver(start[0],start[1],self.Bxy,Bmoy[2],color = 'r',scale_units='y',scale=2)
        self.ax2.grid(True)
        self.ax3.grid(True)
    
    def animate(self, i) :
        lines = self.ser.readlines()
        if (len(lines) > 0) :
            line = lines[0].decode().strip('\n\r')
            if len(line) > 8 :
                if (line[0] == '_') and (line[-1] == '_') :
                    MV2data = line[1:-1].split(',')
                    MV2field = RawToField(MV2data)
                    field = ChangeBase(MV2field)
                    spheric = GetSphericalCoord(field)
                    self.B, self.theta, self.phi = round(spheric[0],2), round(spheric[1]/m.pi,2), round(spheric[2]/m.pi,2)
                    if self.multi :
                        self.MFmultiplot(field)
                    else :
                        self.MF3Dplot(field)
    
    def close(self) :
        self.ser.close()
        plt.close(self.fig)
