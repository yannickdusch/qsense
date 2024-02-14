The nanomax_control_examples subfolder contains multiple examples to test communication between python and KSG|KPZ101 module, and to control nanomax.
The python package `apt_interface` is available [here](https://github.com/benoitlx/APT-interface) with instruction to install it.

The folder contains:
- `identify_devices.py` that scan for KSG and KPZ with serial "29501986" and "59000407"
- `kpz101x_test.py` that send a sinusoidal signal to control kpz voltage of the x axis or send a signal given in input
- `ksg101x_test.py` that permanently retrieve the value given by the gauge of x axis
- `closed_loop_prompt.py` that make KPZ and KSG work together to control precisly the position of the stage, an input of the position will be asked
- `simulation.py` that generate an animation of the moving stage given a certain configuration using 3D plot from matplotlib
- `follow_configured_path.py` that send data to KPZ in order to follow a list of preconstructed coordinates