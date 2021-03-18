import cv2
import numpy as np

class DataVideo:

    def __init__(self, file_path):
        self.file_path = file_path
        # self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def get_meta_data(self):
        cap = cv2.VideoCapture(self.file_path)
        return {'n_frames': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
         'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
         'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))}

    def play_video(self, fn=None, **fn_args):
        cap = cv2.VideoCapture(self.file_path)
        n = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                if fn is not None:
                    res = fn(n, frame, **fn_args)
                else:
                    res = frame
                cv2.imshow('frame', res)
                key = cv2.waitKey(0)
                if key == ord("q"):
                    break
            else:
                break
            n += 1
        cap.release()
        cv2.destroyAllWindows()

    def get_frame(self, index):
        cap = cv2.VideoCapture(self.file_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, index)
        ret, frame = cap.read()
        cap.release()
        return frame

    def get_all_frames(self):
        cap = cv2.VideoCapture(self.file_path)

        frames = np.zeros(shape=(int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))))
        n = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if ret:
                frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frames[n,:,:] = frame_gray
                n += 1
            else:
                break
        cap.release()
        return frames