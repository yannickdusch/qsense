from apt_interface.scan import Scan, ScanConfig
from time import sleep

def mesure(*args, **kwargs):
    sleep(.1)

    return 1

s = Scan((None, None), config_file="conf/scan.yaml")

print(s.conf)
print(s.coords)

s.visualize()
