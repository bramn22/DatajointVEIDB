import os
import datajoint as dj
from main_tables import Experiment, Session, Subsession
from behavior import data_video
from behavior.data_tiff import DataTiff
from behavior.data_deeplabcut import DataDLC
import pandas as pd
import numpy as np
import pickle
import configs

drive_path = os.environ["DJ_DRIVE_PATH"]
data_path = os.environ["DATA_PATH"]
schema = dj.schema('VEIDB', locals())


@schema
class FaceCamRecording(dj.Imported):
    definition = """
        -> Subsession
        part = 0: smallint
        ---
        recording: blob@facecam
        n_frames: int
        width: int
        height: int
      """

    def make(self, key):
        stimulus_type, iteration = (Subsession() & key).fetch1('stimulus_type', 'iteration')
        print("Importing stimulus", stimulus_type, str(iteration))
        config_type = (Experiment() & key).fetch1('config_type')

        cfg = configs.get_config(config_type)

        recs_path = os.path.join(data_path, cfg['facecam_path'].format(**key), stimulus_type)
        if not os.path.exists(recs_path):
            print('Face recording for {session_id} {experiment_id}, {stimulus_type} {iteration} NOT found!'.format(stimulus_type=stimulus_type, iteration=iteration, **key))
            return
        runs = [os.path.splitext(f.split('_')[1])[0] for f in os.listdir(recs_path) if f.endswith('.camlog')]
        session_date = (Session() & key).fetch1('session_date')
        trial_run = sorted(runs)[0]  # Iterations start from index 1
        print("{session_date:%Y%m%d}_{trial_run}".format(trial_run=trial_run, session_date=session_date))

        tiffs = [f for f in os.listdir(recs_path) if
                 f.startswith("{session_date:%Y%m%d}_{trial_run}".format(trial_run=trial_run, session_date=session_date)) and f.endswith('.tif')]
        tiffs = sorted(tiffs)
        print(tiffs)
        max_merged_tiffs = 15
        i = 0
        while i*max_merged_tiffs < len(tiffs):
            data_tiff = DataTiff(os.path.join(recs_path, tiffs[i*max_merged_tiffs]))
            for tiff in tiffs[i*max_merged_tiffs+1:(i+1)*max_merged_tiffs]:
                print(f"Loading {tiff}")
                temp = DataTiff(os.path.join(recs_path, tiff))
                try:
                    data_tiff.merge_tiff(temp)
                except ValueError as err:
                    print(f"Was not able to load {tiff} with error: {err}")
            print("Merged tiffs")
            key['part'] = i
            key['recording'] = data_tiff.data
            n_frames, height, width = data_tiff.data.shape
            key['n_frames'] = n_frames
            key['width'] = width
            key['height'] = height
            print(f"Inserting part {i} for {stimulus_type}, {iteration}")
            self.insert1(key)
            i += 1

        print('Populated a face recording for {session_id} in {experiment_id}'.format(**key))


@schema
class FaceCamRecording_avi(dj.Computed):
    definition = """
        -> Subsession
        ---
        avi_path: varchar(256)
    """

    def make(self, key):
        print("Key: ", key)
        parts, recordings = (FaceCamRecording() & key).fetch('part', 'recording')
        # Save file
        print(f"Parts order: {parts}")
        if parts.size != 0:
            data = DataTiff(data=recordings[0])
            for recording in recordings[1:]:
                data.merge_tiff(DataTiff(data=recording))

            # write path
            avi_path = os.path.join("videos", "{experiment_id}_{mouse_id}_{session_id}_{subsession_id}.avi".format(**key))
            data.write_avi(out_path=os.path.join(drive_path, avi_path), fps=30)
            key['avi_path'] = avi_path
            self.insert1(key)
            
@schema
class BallReadout(dj.Imported):   # it's half imported, but also computed, not sure which dj is better for that
   definition = """
       -> Subsession
       ---
       ball_readout: longblob   # extracts the ball readout from wavesurfer channel
   """

   def make(self, key):
       import h5py
       config_type = (Experiment() & key).fetch1('config_type')
       cfg = configs.get_config(config_type)

       wavesurfer_path = os.path.join(data_path, cfg['wavesurfer_path'].format(**key))
       print("Wavesurfer path", wavesurfer_path)
       if not os.path.isdir(wavesurfer_path):
           print('Ball recordings for {session_id} in {experiment_id} are not found'.format(**key))
           return
       wavesurfer_files = [f for f in os.listdir(wavesurfer_path) if f.endswith('.h5') and key['subsession_id'] in f] # Assumes subsession_ids are not overlapping!!!
       print(wavesurfer_files)
       # speedV0 = 16800 # analog signal when the animal is not moving
       # sweep = '0001'
       with h5py.File(os.path.join(wavesurfer_path, wavesurfer_files[0]), "r") as ws_file:
           sweep = [sub for sub in ws_file.keys() if 'sweep' in sub][0]
           trigger_traces = np.array(ws_file.get(sweep + '/analogScans'))
           # ball_speed = (trigger_traces[2, :]-speedV0)/speedV0 # recorded with 20kHz
           key['ball_readout'] = trigger_traces  # ball_speed
           self.insert1(key)

         # channels from wavesurfer file:
         # 0: frame triggers, 1: stim triggers, 2: imagin triggers,  4: ball speed, 5: camera triggers

