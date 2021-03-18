from skimage import io
import matplotlib.pyplot as plt
import cv2
import numpy as np
import os

class DataTiff:

    def __init__(self, file_path=None, data=None):
        if data is None:
            self.data = self.open_tiff(file_path)
        else:
            self.data = data

    def open_tiff(self, file_path):
        im = io.imread(file_path)
        print(im.shape)
        if im.shape[2] == 3:
            im = np.moveaxis(im, -1, 0)
            print("Changed image shape to: ", im.shape)
        return im

    def merge_tiff(self, data_tiff):
        self.data = np.concatenate([self.data, data_tiff.data])

    def write_avi(self, out_path, fps=60, fourcc_str='DIVX'):
        n, height, width = self.data.shape
        fourcc = cv2.VideoWriter_fourcc(*fourcc_str)
        out = cv2.VideoWriter(out_path, fourcc, fps, (width, height), 0)
        for frame in self.data:
            out.write(frame)
        out.release()

    def subtract_mean(self, mean=None):
        pass

    def disp_data(self, data):
        pass

    def d3_2_d2(self):
        pass

    def d2_2_d3(self):
        pass

# path = r'Y:\Data\subhash\20-02-2020_Dome_rec\Camera\20_02_2020\good\20200220_run000_00000001.tif'
# folders = [
#     r'Y:\Data\01323\20200531\Cams',
#     r'Y:\Data\01323\20200602\Cams',
#     r'Y:\Data\01324\20200531\Cams',
#     r'Y:\Data\01324\20200602\Cams',
#     r'Y:\Data\01325\20200531\Cams',
#     r'Y:\Data\01325\20200602\Cams'
# ]
# folders = [
#     r'E:\data\WF_neurons\behavior\01325_20200531\Cams',
# ]
#
# for folder in folders:
#     folder = os.path.normpath(folder)
#     folder_path_list = folder.split(os.sep)
#     exp_sess = f'{folder_path_list[2]}_{folder_path_list[3]}'
#     os.mkdir(os.path.join(r'E:\data\WF_neurons\behavior', exp_sess))
#     subfolders = [subf for subf in os.listdir(folder) if os.path.isdir(os.path.join(folder, subf))]
#     for subfolder in subfolders:
#         tiffs = [tiff for tiff in os.listdir(os.path.join(folder, subfolder)) if tiff.endswith('.tif')]
#         tiffs.sort()
#         data_tiff = DataTiff(os.path.join(folder, subfolder, tiffs[0]))
#         for tiff in tiffs[1:]:
#             print(f"Loading {tiff}")
#             temp = DataTiff(os.path.join(folder, subfolder, tiff))
#             try:
#                 data_tiff.merge_tiff(temp)
#             except ValueError as err:
#                 print(f"Was not able to load {tiff} with error: {err}")
#
#         print(f"Writing video for {os.path.join(folder, subfolder)}")
#         data_tiff.write_avi(out_path=os.path.join(r'E:\data\WF_neurons\behavior', exp_sess, f'{subfolder}.avi'))


# tiff = DataTiff(r'Y:\Data\01324\20200602\Cams\EXPA\20200602_run017_00000000.tif')
# tiff2 = DataTiff(r'Y:\Data\01324\20200602\Cams\EXPA\20200602_run017_00000001.tif')
# tiff.merge_tiff(tiff2)
# tiff2 = None
# tiff.write_avi(out_path=r'E:\data\WF_neurons\behavior\CHPE_00001_00001.avi')