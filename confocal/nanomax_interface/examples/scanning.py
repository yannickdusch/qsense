from pylablib.devices import Thorlabs
import yaml
import sys
import logging
import numpy as np


def scan(generic_conf, scan_conf):

    # Generic Stage parameters
    stage_channels = generic_conf["stage"]["channels"]

    # Scan parameters
    ref_point_coords = scan_conf["zoi"]["ref_point"]
    dimensions = scan_conf["zoi"]["dimensions"]
    final_point_coords = map(lambda t : t[0] + t[1], zip(ref_point_coords, dimensions))
    step_res = scan_conf["step_res"]
    
    tau = scan_conf["acquisition_time"]

    res = np.zeros(list(map(lambda x : int(x[0]/x[1]), zip(dimensions, step_res))))
    estimated_time = res.size * tau

    logging.debug("estimated scanning time (s):"+str(estimated_time))

    
    # Il faudra rajouter le code pour le SPCM
    with Thorlabs.KinesisPiezoMotor(generic_conf["stage"]["serial_port"]) as stage:
        # Init SPCM ===================
        # send acquisition time
        
        # Init Stage ==================
        # Go into the zoi
        logging.debug(stage.get_full_info())
        for coord, chann in zip(ref_point_coords, stage_channels):
            stage.move_to(coord, False, chann)
            stage.wait_move()
            logging.debug("Starting point reached")
            stage.set_position_reference(coord, chann)


        for coord, chann, step in zip(final_point_coords, stage_channels, step_res):
            while stage.get_position(chann) < coord:
                # Acquisition

                # send start_acquisition signal
                # wait for the acquisition
                pixel_value = 1 # get data from the spcm
                logging.debug("position: " + str(stage.get_position()))
                logging.debug("number of photon: " + pixel_value)

                # Move by delta in the corresponding direction
                stage.move_by(step, False, chann)
                stage.wait_move()
    
        

def main():
    if len(sys.argv) <= 1:
        print("One argument needed, returning")
        return
    
    with open(sys.argv[1], 'r') as file:
        config = yaml.safe_load(file)

    
    if config["generic_conf"]["debug"]:
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    else:
        logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    logging.debug(config)

    scanned_area = scan(config["generic_conf"], config["scan_conf"])

if __name__ == "__main__":
    main()