# Python program to illustrate
# template matching
import cv2
import numpy as np


import cv2
import os

template_path = "../src/data/tmp"



def match_template(source_image):
    # Read the main image
    img_rgb = source_image

    # Convert it to grayscale
    img_gray = cv2.cvtColor(np.asarray(img_rgb), cv2.COLOR_BGR2GRAY)
    for filename in os.listdir(template_path):
        img = cv2.imread(os.path.join(template_path,filename), 0)
        if img is not None:
            # Read the template
            template = img

            # Store width and height of template in w and h
            w, h = template.shape[::-1]

            # Perform match operations.
            res = cv2.matchTemplate(img_gray,template,cv2.TM_CCOEFF_NORMED)

            # Specify a threshold
            threshold = 0.8

            # Store the coordinates of matched area in a numpy array
            loc = np.where( res >= threshold)

            if len(loc[0]) != 0:

                #Draw a rectangle around the matched region.
                for pt in zip(*loc[::-1]):
                    cv2.rectangle(img_gray, pt, (pt[0] + w, pt[1] + h), (0,255,255), 2)
                cv2.imshow('Detected',img_gray)
                cv2.waitKey(0)
                template_name = filename.split('.')[-2]
                return  template_name

            else:
                return None


if __name__ == '__main__':
    print(match_template('../template_match/main.png'))

