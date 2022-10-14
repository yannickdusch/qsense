import pyvisa

rm = pyvisa.ResourceManager()
device = rm.open_resource('TCPIP::169.254.243.104::INSTR')

""" 2 méthodes pour l'ODMR """

""" Méthode pas à pas """

def stepODMR(start,stop,npts) :
    step = (stop - start)/(npts-1)
    odmr = []
    for i in range(npts) :
        freq = start + i*step
        device.write("FREQ "+str(int(freq)))
        # PWR Antenna
        # frame = getframe()
        # data = getdata(frame,pixel)
        # odmr += [data]
    # Plot odmr

""" Méthode continue """      

def sweepODMR(start,stop,dwelt,npts) :
    # set the mode on SWEEP (frequency step)
    # set the START and STOP FREQUENCIES
    # set the DWELL TIME (1 ms to 60 s)
    # set the number of POINTS (2 to 65535 points)

