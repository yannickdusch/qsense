from apt_interface.KPZ101 import KPZ101, KPZ101Config
from time import sleep
from math import sin, pi

def voltage_prompt(kpz):
    while True:
        p = int(input("desired voltage 0..32767: "))
        kpz.set_output_voltage(p)

def sinus_voltage(kpz):
    i = 0
    while True: 
        v = int(32767/2+(32767/2)*sin(i*4*pi/100))
        kpz.set_output_voltage(v)
        i+=1
        sleep(.1)


with KPZ101(config_file="tests/config_KPZ.yaml") as kpz:
    print(kpz.conf)
    print(kpz.get_info())

    kpz.enable_output()

    voltage_prompt(kpz)
    # sinus_voltage(kpz)
