import numpy as np
import matplotlib.pyplot as plt
import logging
from hamamatsu.dcam import dcam, Stream, copy_frame

"""
import cv2
from PIL import Image as im
"""

logging.basicConfig(level=logging.INFO)

plt.rcParams["figure.figsize"] = [10.00, 10.00]
plt.rcParams["figure.autolayout"] = True

with dcam:    
    camera = dcam[0]
    
    def getframe(nb_frames = 4, t_exp = 0.1):
        with camera:
            camera["exposure_time"] = t_exp
            final_frame = np.zeros((camera['image_width'].value, camera['image_height'].value))
            with Stream(camera, nb_frames) as stream:
                    logging.info(" START ACQUISITION ------------------------------------------")
                    camera.start()
                    for i, frame_buffer in enumerate(stream):
                        frame = copy_frame(frame_buffer)
                        final_frame += frame/nb_frames
                        logging.info(" Acquired frame #%d/%d", i+1, nb_frames)
                    logging.info(" FINISHED ACQUISITION ---------------------------------------")

        logging.info(" Final frame content :\n%s", final_frame)
        plt.imshow(final_frame)
    
    """
    def getstream():
        with camera:
            camera["exposure_time"] = 0.01
            with Stream(camera, 1) as stream:
                    camera.start()
                    while 1 :
                        for i, frame_buffer in enumerate(stream):
                            frame = im.fromarray(copy_frame(frame_buffer))
                            cv2.imshow('Frame',frame)
                            if cv2.waitKey(1) & 0xFF == ord('q') :
                                break
                    cv2.destroyAllWindows()
    """
    
