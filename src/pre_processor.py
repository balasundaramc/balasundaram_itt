import os, sys
import cv2
import numpy as np

class ImagePreProcessing():
    def __init__(self):
        pass



    @staticmethod
    def read_image(image):

        return cv2.imread(image)

    @staticmethod
    def resize_image(image):
        image = np.asarray(image)
        print('Original Dimensions : ', image.shape)

        scale_percent = 250  # percent of original size
        width = int(image.shape[1] * scale_percent / 100)
        height = int(image.shape[0] * scale_percent / 100)
        dim = (width, height)
        # resize image
        resized = cv2.resize(image, dim, interpolation=cv2.INTER_LINEAR)

        print('Resized Dimensions : ', resized.shape)

        cv2.imshow("Resized image", resized)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        #resized = cv2.resize(image, (100, 100), interpolation=cv2.INTER_LINEAR)
        return resized

    # get grayscale image
    @staticmethod
    def get_grayscale(image):

        return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2GRAY)

    # noise removal
    @staticmethod
    def remove_noise(image):
        return cv2.medianBlur(image, 5)

    # thresholding
    @staticmethod
    def thresholding(image):
        return cv2.threshold(image,0,255,cv2.THRESH_BINARY+cv2.THRESH_OTSU)[1]