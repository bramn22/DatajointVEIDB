import pandas as pd
import os
import cv2
import numpy as np

class DataDLC:

    def __init__(self, df):
        self.bodyparts = list(df.columns.levels[0])
        self.df = df

    def visualize_on_video(self, video):
        def visualize_bodyparts(n, frame, prob_threshold=0.90):
            for key in self.bodyparts:
                x, y = int(self.df[key,'x'][n]), int(self.df[key,'y'][n])
                prob = self.df[key,'likelihood'][n]
                if prob > prob_threshold:
                    cv2.circle(frame, (x,y), 5, color=(255,0,0), thickness=2)
                else:
                    cv2.circle(frame, (x,y), 5, color=(0,0,255), thickness=2)

            return frame
        video.play_video(fn=visualize_bodyparts, prob_threshold=0.90)

    def visualize_standardized_on_video(self, video):
        df_stand = self.get_standardized()
        def visualize_bodyparts(n, frame, prob_threshold=0.90):
            mid = tuple(t//2 for t in frame.shape[1::-1])
            trans_x, trans_y = int(df_stand['trans_x'][n]), int(df_stand['trans_y'][n])
            angle = df_stand['angle'][n]

            frame = self.translate_image(frame, (mid[0] - trans_x, mid[1] - 1*trans_y))
            frame = self.rotate_image(frame, mid, angle*180/3.14)
            for key in self.bodyparts:
                x, y = int(df_stand[key, 'x'][n]), int(df_stand[key, 'y'][n])
                prob = df_stand[key, 'likelihood'][n]

                if prob < prob_threshold:
                    cv2.circle(frame, (mid[0]+x, mid[1]+y), 5, color=(255, 0, 0), thickness=2)
                else:
                    cv2.circle(frame, (mid[0]+x, mid[1]+y), 5, color=(0, 0, 255), thickness=2)

            return frame[mid[1]-150:mid[1]+150, mid[0]-150:mid[0]+150]
        return visualize_bodyparts
        # video.play_video(fn=visualize_bodyparts, prob_threshold=0.90)

    def translate_image(self, frame, shifts):
        tx, ty = shifts
        print(frame.shape)
        print(tx)
        print(ty)
        #     translation_matrix = np.float32([[1,0,pose_matrix[anchor_idx,1]],[0,1,pose_matrix[anchor_idx,0]]])
        translation_matrix = np.float32([[1, 0, tx], [0, 1, ty]])
        result = cv2.warpAffine(frame, translation_matrix, frame.shape[1::-1])
        return result

    def rotate_image(self, frame, anchor_point, angle):
        #     image_center = tuple(np.array(image.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(anchor_point, angle, 1.0)
        result = cv2.warpAffine(frame, rot_mat, frame.shape[1::-1], flags=cv2.INTER_LINEAR)
        return result

    def filter_temporal(self, fn, **fn_args):
        for key in self.bodyparts:
            self.df[key, 'x'] = fn(self.df[key, 'x'], **fn_args)
            self.df[key, 'y'] = fn(self.df[key, 'y'], **fn_args)

    def filter_likelihood(self, p):
        for part in self.bodyparts:
            for coord in ['x', 'y']:
                df_sub = self.df[part, coord]
                df_sub.loc[self.df[part]['likelihood'] < p] = np.nan
                if np.isnan(df_sub.iloc[0]):
                    if not df_sub.notnull().values.any():
                        continue
                    df_sub.iloc[0] = df_sub.iloc[df_sub.first_valid_index()]
                if np.isnan(df_sub.iloc[-1]):
                    df_sub.iloc[-1] = df_sub.iloc[df_sub.last_valid_index()]
                self.df[part, coord] = df_sub.interpolate(method="linear", order=None)

    def calc_velocity(self, data_x, data_y):
        dx2 = (data_x - data_x.shift())**2
        dy2 = (data_y - data_y.shift())**2

        return (dx2 + dy2) ** (1/2)

    # def calc_acceleration(self, data):
    #     dxdy = data[['distance']] - data[['distance']].shift()
    #     return dxdy

    def get_angle_from_xaxis(self, vector):
        axis = np.array([1, 0])
        unit_vector_1 = vector / np.linalg.norm(vector)
        unit_vector_2 = axis / np.linalg.norm(axis)
        cos_angle = np.dot(unit_vector_1, unit_vector_2)
        angle = np.arccos(cos_angle)
        if vector[1] < 0:
            return -angle
        return angle

    def get_standardized(self, ref_idx=0, anchor_idx=6):
        pose_matrix = np.zeros(shape=(9, 2))
        df_stand = self.df.copy()
        df_stand['trans_x'] = 0
        df_stand['trans_y'] = 0
        df_stand['angle'] = 0

        for idx, row in self.df.iterrows():
            for j, key in enumerate(self.bodyparts):
                pose_matrix[j, 0] = row[key, 'x']
                pose_matrix[j, 1] = row[key, 'y']
            # Translation
            translated = np.subtract(pose_matrix, pose_matrix[anchor_idx, :])
            df_stand.loc[idx, 'trans_x'] = pose_matrix[anchor_idx, 0]
            df_stand.loc[idx, 'trans_y'] = pose_matrix[anchor_idx, 1]

            # Rotation
            angle = self.get_angle_from_xaxis(translated[ref_idx, :])
            df_stand.loc[idx, 'angle'] = angle
            rot_matrix = np.array([[np.cos(angle), np.sin(angle)], [-np.sin(angle), np.cos(angle)]])
            rotated = np.matmul(translated, np.transpose(rot_matrix))
            for j, key in enumerate(self.bodyparts):
                df_stand.loc[idx, (key, 'x')] = rotated[j, 0]
                df_stand.loc[idx, (key, 'y')] = rotated[j, 1]
        return df_stand

    def calc_movement_measures(self):
        df_stand = self.get_standardized()
        df_stand['locomotion'] = (self.calc_velocity(df_stand['trans_x'], df_stand['trans_y'])).abs()

        df_stand['freeze'] = 0 # replace with L2 norm
        for i, key in enumerate(self.bodyparts):
            df_stand['freeze'] -= (self.calc_velocity(df_stand[key, 'x'], df_stand[key, 'y'])).abs()

        df_stand['rotation'] = (df_stand['angle'] - df_stand['angle'].shift()).abs()

        return df_stand

    def to_numpy(self, bodyparts_to_keep):
        df = self.get_standardized()
        positions = []
        for part in bodyparts_to_keep:
            positions.append(df[part].x.to_numpy())
            positions.append(df[part].y.to_numpy())
        # Add velocity column
        # positions.append(self.calc_velocity(df['trans_x'], df['trans_y']).abs().to_numpy())

        positions_np = np.vstack(positions)

        print(positions_np.shape)
        return positions_np

