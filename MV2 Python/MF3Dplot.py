# This file works together with the dataMV2.ino file.

# This file allows to plot the field as a live vector in a 3D window.

# /!\ This version does not include a closing of the serial communication.

# To activate 3D animation in Spyder: Tools > Preferences > IPython Console > Graphics > Backend and change it from "Inline" to "Automatic".

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import serial
from processMV2 import RawToField, ChangeBase

# plt.style.use('seaborn-pastel')

start = [0,0,0]  # Set origin

ser = serial.Serial()
ser.port = 'COM3'
ser.baudrate = 115200
ser.timeout = 0
ser.open()

fig = plt.figure(figsize = (10,10))
ax = plt.axes(projection = '3d')
ax.view_init(15,-60)  # Args = angles (°)

def MF3Dplot(Bmoy) :
    plt.cla()  # Clear the content already plotted without closing the figure (NB : plt.clf() clears the figure without closing the window)
    ax.set_xlim([-50,50])
    ax.set_ylim([-50,50])
    ax.set_zlim([-50,50])
    # plt.axis('scaled') -> Not in 3D
    ax.quiver(start[0],start[1],start[2],10,0,0,color = 'b')  # X axis (colored version : R)
    ax.quiver(start[0],start[1],start[2],0,10,0,color = 'k')  # Y axis (colored version : G)
    ax.quiver(start[0],start[1],start[2],0,0,10,color = 'k')  # Z axis (colored version : B)
    ax.quiver(start[0],start[1],start[2],Bmoy[0],Bmoy[1],Bmoy[2],color = 'r')
    ax.quiver(start[0],start[1],start[2],Bmoy[0],Bmoy[1],0)  # Projection of B on xy-plane

def animate(i):
    lines = ser.readlines()
    if (len(lines) > 0) :
        line = lines[0].decode().strip('\n\r')
        if len(line) > 8 :
            if (line[0] == '_') and (line[-1] == '_') :
                MV2data = line[1:-1].split(',')
                MV2field = RawToField(MV2data)
                field = ChangeBase(MV2field)
                MF3Dplot(field)

anim = FuncAnimation(fig, animate, frames=100, interval=50)
