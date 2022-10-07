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

#Demander la fréquence : device.query("FREQ?")

def set_sweep(start = "1GHZ", stop = "4GHZ", amp = "-136DBM") :
    device.write("FREQ "+start+";POW "+amp)

class Sweep :
    startfreq = "1GHZ"
    stopfreq = "4GHZ"
    startamp = "-136DBM"
    stopamp = "-136DBM"
        
