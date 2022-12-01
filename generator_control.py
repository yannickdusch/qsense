# GENERATOR : Agilent E4438C
#   Type : ESG
#   Communication :
#	    LAN (10BASE-T ; 100BASE-T Ethernet) [prot. VXI-11, Sockets, TELNET, FTP]
#		GPIB
#		RS-232 

import pyvisa

rm = pyvisa.ResourceManager()
device = rm.open_resource('TCPIP::169.254.243.104::INSTR')
print('Detected : '+device.query("*IDN?")+'Alias : device')

#Ask for frequency : device.query("FREQ?")

def set_sweep(center = "3GHZ", span = "1GHZ", dwell = "100 ms", amp = "-136DBM") :
    device.write("POW -136DBM")
    device.write("SOUR:FREQ:MODE SWEEP")
    device.write("SOUR:FREQ:CENTER "+center)
    device.write("SOUR:FREQ:SPAN "+span)
    device.write("SOUR:SWEEP:DWELL "+dwell)
    

class Sweep :
    
    def __init__(self, center = "3GHZ", span = "1GHZ", dwell = "100 ms", amp = "-136DBM") :
        self.c = center
        self.s = span
        self.d = dwell
        self.a = amp
    
    def set_sweep(self) :
        device.write("POW -136DBM")
        device.write("SOUR:FREQ:MODE SWEEP")
        device.write("SOUR:FREQ:CENTER "+self.c)
        device.write("SOUR:FREQ:SPAN "+self.s)
        device.write("SOUR:SWEEP:DWELL "+self.d)
    
    # def run() :
    #     device.write("SOUR:SWEEP:EXECUTE")
