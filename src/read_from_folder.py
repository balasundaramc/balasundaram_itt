import os
from src import image_preprocesing
from PIL import Image
import pdf2image
import pytesseract
from pytesseract import Output
import cv2
import numpy as np
from src.pre_processor import ImagePreProcessing
from src.thyrocare import process_df
from template_match import template_match
from src.db_layer import *

BASE_PATH = os.getcwd()
print(BASE_PATH)
INPUT_FOLDER = os.path.join(BASE_PATH, "data/img")
TMP_FOLDER = os.path.join(BASE_PATH, "data/tmp")
OUTPUT_FOLDER = os.path.join(BASE_PATH, "data/txt")


# If you don't have tesseract executable in your PATH, include the following:
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
# Example tesseract_cmd = r'C:\Program Files (x86)\Tesseract-OCR\tesseract'


class OCREngine(object):
    def __init__(self):
        self.template_name = None
        pass

    def create_folders(self):
        """
        :return: void
            Creates necessary folders
        """

        for folder in [
            INPUT_FOLDER, TMP_FOLDER, OUTPUT_FOLDER
        ]:
            if not os.path.exists(folder):
                os.makedirs(folder)

    # def get_string(img_path):
    #  # Read image using opencv
    #  img = cv2.imread(img_path)
    #
    #  # Extract the file name without the file extension
    #  file_name = os.path.basename(img_path).split('.')[0]
    #  file_name = file_name.split()[0]
    #
    #  # Create a directory for outputs
    #  output_path = os.path.join(output_dir, file_name)
    #  if not os.path.exists(output_path):
    #      os.makedirs(output_path)


    def find_images(self, folder):
        """
        :param folder: str
            Path to folder to search
        :return: generator of str
            List of images in folder
        """

        for file in os.listdir(folder):
            full_path = os.path.join(folder, file)
            if os.path.isfile(full_path):
                try:
                    _ = Image.open(full_path)  # if constructor succeeds
                    yield file
                except Exception as e:
                    print("Exception in find_images: ", e.__class__)

    def rotate_image(self, input_file, output_file, angle=90):
        """
        :param input_file: str
            Path to image to rotate
        :param output_file: str
            Path to output image
        :param angle: float
            Angle to rotate
        :return: void
            Rotates image and saves result
        """

        cmd = "convert -rotate " + "' " + str(angle) + "' "
        cmd += "'" + input_file + "' '" + output_file + "'"
        print("Running", cmd)
        os.system(cmd)  # sharpen


    def sharpen_image(self, input_file, output_file):
        """
        :param input_file: str
            Path to image to prettify
        :param output_file: str
            Path to output image
        :return: void
            Prettifies image and saves result
        """

        # rotate_image(input_file, output_file)  # rotate
        cmd = "convert -auto-level -sharpen 0x4.0 -contrast "
        cmd += "'" + output_file + "' '" + output_file + "'"
        print("Running", cmd)
        os.system(cmd)  # sharpen


    def run_tesseract(self, input_file, output_file):
        """
        :param input_file: str
            Path to image to OCR
        :param output_file: str
            Path to output file
        :return: void
            process image and saves result
        """

        cmd = "tesseract -l eng "
        cmd += "'" + input_file + "' '" + output_file + "'"+' --psm 1 --dpi 300'
        print("Running", cmd)
        os.system(cmd)

    def convert_pdf_to_image(self, folder, file_name):
        """
        :param folder:str
            path of the input folder
        :param file_name:
        :return: list
            It retruns list of Image object
        """

        path = os.path.join(folder,file_name)
        pdf_to_image_result = []
        file_name = os.path.join(folder,file_name)
        if os.name == 'posix':
            pd = pdf2image.convert_from_path(path)
        else:
            pd = pdf2image.convert_from_path(path,poppler_path =r'C:\Users\Administrator\Downloads\OCR_BASE\OCR_BASE\poppler-0.68.0\bin')
        return pd


    def main(self, folder):
        """
        we need to check whether folder contains tesseract supported file
        formats. PDF, jpg, JPEG, png, tiff

        :param folder: str
            path of the input folder
        :return: void
        """
        filepaths = []
        for file in os.listdir(folder):
            full_path = os.path.join(folder, file)
            if os.path.isfile(full_path):
                try:
                    #_ = Image.open(full_path)  # if constructor succeeds
                    file_extension = os.path.splitext(file)[-1].lower()
                    # Now we can simply check for equality, no need for wildcards.
                    if file_extension.lower().endswith(('.png', '.jpg', '.jpeg')):
                        filepaths.append(file)
                        image_object = cv2.imread(full_path)
                        self.process_with_ocr_engine(image_object)
                        print("found image file", file_extension)
                    elif file_extension.lower().endswith(('.pdf')):
                        '''
                        if it is pdf file , get images from pdf file and process tesseract and save files in  output folder.
                        make folder based on file inside output folder.
                        '''
                        filepaths.append(file)
                        image_object = self.convert_pdf_to_image(folder,file)
                        for i, page in enumerate(image_object):
                            image_name = '{}_{}.png'.format(file[:-4], i)
                            #page.save(TMP_FOLDER+"\\"+image_name, 'png')
                            #img_from_temp_path = TMP_FOLDER+"\\"+image_name
                            ocr_result = self.process_with_ocr_engine(page)
                            self.make_dir_and_save_ocr_result(image_name, ocr_result)
                        print("found pdf file", file_extension)
                    else:
                        pass
                except Exception as e:
                    print(e)
                    print("Exception occured in main function:", e.__class__)


    def process_with_ocr_engine(self, image_file):
        """

        :param image_file: str
            input image for OCR process
        :return: dataframe
            OCR engine returns result as pandas dataframe
        """

        get_template_name = template_match.match_template(image_file)
        if get_template_name != None:
            self.template_name = get_template_name
        else:
            pass

        img = ImagePreProcessing.resize_image(image_file)
        gray_image = ImagePreProcessing.get_grayscale(image_file)
        #noise_removed = ImagePreProcessing.remove_noise(gray_image)
        threshold_image = ImagePreProcessing.thresholding(gray_image)
        custom_config = '--dpi 300 --psm 1 -l eng+equ+enm'
        data = pytesseract.image_to_data(threshold_image, config=custom_config, output_type=Output.DATAFRAME)
        return data

    def process_ocr_dataframe(self, data_frame):
        """

        :param data_frame:
        :return:
        """
        data_frame.dropna(inplace=True)
        data_frame.reset_index(inplace=True)
        data_frame.drop('index', axis=1, inplace=True)

        template_name = self.template_name
        result = None
        if template_name =="thyrocare":
            result = process_df(data_frame)
        elif template_name == "appollo":
            pass
        else:
            pass

        # #data_frame.to_csv('ocr_dump.csv')
        # new_lines = []
        # line_ref = 0
        # for i in range(len(data_frame)):
        #     n = data_frame['word_num'][i]
        #     if n == 1:
        #         line_ref += 1
        #         new_lines.append(line_ref)
        #     else:
        #         new_lines.append(line_ref)
        # data_frame['new_line'] = np.array(new_lines)
        # max_line = data_frame['new_line'].max()
        # min_line = data_frame['new_line'].min()
        #
        # result = ''
        #
        # for i in range(min_line, max_line):
        #     df = data_frame[data_frame['new_line'] == i]
        #     df = df.sort_values(by=['left'], ascending=True)
        #     text = ' '.join(df.text.values)
        #     result = result+(text + '\n')

        return result



    def make_dir_and_save_ocr_result(self, image, ocr_result):
        """

        :param image: str
            name of the image file
        :param ocr_result: dataframe
            dataframe contains OCR results
        :return: void
            process the OCR result and saved into output folder
        """
        output_dir = OUTPUT_FOLDER
        # Extract the file name without the file extension
        file_name = image.split('.')[0]

        # Create a directory for outputs
        output_path = os.path.join(output_dir, file_name)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        out_file_name = output_path + '//'+file_name+'.txt'
        with open(out_file_name, 'w+', encoding='utf-8') as output:
            result = self.process_ocr_dataframe(ocr_result)
            output.write(result)

    def main1(self):
        self.create_folders()
        images = list(self.find_images(INPUT_FOLDER))
        print("Found the following images in", INPUT_FOLDER)
        print(images)
        for image in images:
            input_path = os.path.join(
                INPUT_FOLDER,
                image
            )
            tmp_path = os.path.join(
                TMP_FOLDER,
                image
            )
            out_path = os.path.join(
                OUTPUT_FOLDER,
                image + ".out.txt"
            )
            #sharpen_image(input_path, tmp_path)
            image_preprocesing.pre_processing(input_path, OUTPUT_FOLDER)
            self.run_tesseract(input_path, out_path)


if __name__ == '__main__':
        #main()
        engine_object = OCREngine()
        engine_object.main(INPUT_FOLDER)