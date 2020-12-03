import cv2
import numpy as np
import pytesseract
import pandas as pd
from pytesseract import Output

import json
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'

def process_df(data_frame):
    """

    :param data_frame:
    :return:
    """
    data = data_frame
    new_lines = []
    line_ref = 0
    for i in range(len(data)):
        n = data['word_num'][i]
        if n == 1:
            line_ref += 1
            new_lines.append(line_ref)
        else:
            new_lines.append(line_ref)

    data['new_line'] = np.array(new_lines)
    data['tph'] = data['top'] + data['height']

    block_ref_num = 1
    prev_block_num = 0
    current_block_num = 1
    blockc_df = pd.DataFrame()
    breaker = False

    for i in range(data['block_num'].max()):

        dum_data = data[data['block_num'] == block_ref_num]

        def get_refpoints(df):
            ref_points = []
            if len(df) > 1:
                n = 3
            else:
                n = 2
            for j in range(1,n):
                ref_points.append(df.iloc[0-j, -1])

            return ref_points

        ref_height = max(get_refpoints(dum_data))

        if block_ref_num != data['block_num'].max():
            next_data = data[data['block_num'] == block_ref_num+1]
            next_top = next_data['top'].iloc[0]

            difference_height = next_top - ref_height

            if 0 < difference_height < 20:
                inc_block = prev_block_num + 1
                dum_data['block_num'] = inc_block
                next_data['block_num'] = inc_block

                blockc_df = pd.concat([blockc_df, dum_data, next_data], axis= 0)

                block_ref_num += 2

                if block_ref_num > data['block_num'].max():
                    break

                for k in range(0, 10):
                    dum_2 = blockc_df[blockc_df['block_num'] == inc_block]
                    ref_height_1 = max(get_refpoints(dum_2))
                    next_data_1 = data[data['block_num'] == block_ref_num]
                    next_top_1 = next_data_1['top'].iloc[0]

                    difference_height_1 = next_top_1 - ref_height_1

                    if 0 < difference_height_1 < 23:
                        next_data_1['block_num'] = inc_block
                        blockc_df = pd.concat([blockc_df, next_data_1], axis = 0)
                        block_ref_num += 1

                        if block_ref_num > data['block_num'].max():
                            breaker = True
                            break


                    else:
                        break

                if breaker:
                    break

                prev_block_num = current_block_num
                current_block_num += 1



            else:
                dum_data['block_num'] = prev_block_num + 1

                blockc_df = pd.concat([blockc_df, dum_data], axis= 0)
                prev_block_num = current_block_num
                current_block_num += 1
                block_ref_num += 1

                if block_ref_num > data['block_num'].max():
                    break

        else:
            dum_data['block_num'] = prev_block_num + 1
            blockc_df = pd.concat([blockc_df, dum_data], axis=0)
            break



    max_line = data['new_line'].max()
    min_line = data['new_line'].min()
    #=blockc_df.loc[blockc_df['block_num'] == 10]
    result = ''
    block_data = process_data_frame_by_block(blockc_df)
    table_data = get_table_data(block_data ,blockc_df)
    for i in range(min_line, max_line):
        df = data_frame[data_frame['new_line'] == i]
        df = df.sort_values(by=['left'], ascending=True)
        text = ' '.join(df.text.values)
        result = result+(text + '\n')

    return block_data


def process_data_frame_by_block(df):
    """

    :param df:
    :return:
    """
    block_detail = []
    data_frame = df
    for blocks in data_frame.groupby(by='block_num'):
        lines = (blocks[1]).groupby(by='new_line').groups

        for k ,v in lines.items():
            if len(v)==1:
                text = data_frame.loc[v[0]].text
            else:
                text = " ".join(data_frame.loc[v[0]:v[-1]].text.values)
            print(text)
            lines[k] = str(text)
        d = {"block_num": blocks[0], "lines": lines}
        block_detail.append(d)
    return json.dumps(block_detail)



def get_table_data(block_data, blockc_df):
    """

    :param block_data:
    :return:
    """
    table_headers = ["TEST NAME", "TECHNOLOGY", "VALUE", "UNITS", "REFERENCE", "RANGE"]
    table_df = blockc_df.loc[blockc_df['block_num'] == 10]

    #save table data
    table_df.to_csv('ocr_dump.csv')
    for i in block_data:
        print(i)


    # res = [ele for ele in table_headers if (ele in test_string)]





if __name__ == '__main__':
    process_df(r'C:\Users\Administrator\Downloads\OCR_BASE\OCR_BASE\Backup_Python_Files\Pathology_blood_test_2_0.png')


