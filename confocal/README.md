The nanomax_control_examples subfolder contains multiple examples to test communication between python and KSG|KPZ101 module, and to control nanomax.
The python package `apt_interface` is available [here](https://github.com/benoitlx/APT-interface) with instruction to install it.

The folder contains:
- `identify_devices.py` that scan for KSG and KPZ with serial "29501986" and "59000407"
- `kpz101x_test.py` that send a sinusoidal signal to control kpz voltage of the x axis or send a signal given in input
- `ksg101x_test.py` that permanently retrieve the value given by the gauge of x axis
