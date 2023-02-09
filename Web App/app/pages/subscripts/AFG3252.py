import pyvisa

class AFG3252():

    def __init__(self, usb_address):
        self.rm = pyvisa.ResourceManager()
        open_request = 'USB0::' + usb_address + '::INSTR'
        self.device = self.rm.open_resource(open_request)
        self.device.read_termination = '\n'
        self.device.write_termination = '\n'
        self.idn = self.device.write('*IDN?')

        self.waveform = self.device.query('SOURCE1:FUNCTION:SHAPE?')
        self.ramp_symmetry = self.device.query('SOURCE1:FUNCTION:RAMP:SYMMETRY?')
        self.amplitude = self.device.query('SOURCE1:VOLTAGE:AMPLITUDE?')
        self.frequency = self.device.query('SOURCE1:FREQUENCY?')
        self.offset = self.device.query('SOURCE1:VOLTAGE:OFFSET?')
        self.max_amplitude = 10
        self.max_offset = 5

    # Met à jour la forme du signal de sortie en fonction de la valeur de self.waveform
    # Valeurs possibles (Cf Doc) : SINusoid, SQUare, PULSe, RAMP, PRNoise,DC, SINC, GAUSsian, LORentz, ERISe, EDECay, HAVersine
    
    def update_waveform(self):
        update_request = 'SOURCE1:FUNCTION:SHAPE ' + str(self.waveform)
        self.device.write(update_request)

    def update_ramp_symmetry(self):
        update_request = 'SOURCE1:FUNCTION:RAMP:SYMMETRY ' + str(self.ramp_symmetry)
        self.device.write(update_request)

    # Met à jour la fréquence du signal de sortie en fonction de la valeur de self.frequency
    def update_frequency(self):
        update_request = 'SOURCE1:FREQUENCY ' + str(self.frequency)
        self.device.write(update_request)
    
    def get_period(self):
        return 1/float(self.device.query('SOURCE1:FREQUENCY?'))
    
    # Met à jour l'amplitude du signal de sortie en fonction de la valeur de self.amplitude
    def update_amplitude(self):
        update_request = 'SOURCE1:VOLTAGE:AMPLITUDE ' + str(self.amplitude/2)
        self.device.write(update_request)

    def update_offset(self):
        update_request = 'SOURCE1:VOLTAGE:OFFSET ' + str(self.offset/2) 
        self.device.write(update_request)
    
    def set_output(self, active=True):
        if active:
            self.device.write('OUTPUT1 ON')
        else:
            self.device.write('OUTPUT1 OFF')

    def close(self):
        self.device.close()
