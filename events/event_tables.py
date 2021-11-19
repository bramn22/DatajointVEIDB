import os
import numpy as np
from pathlib import Path
from main_tables import Experiment, Session, Subsession
from ephys.ephys_tables import EphysRaw, EphysRawHelper, LFP
import datajoint as dj
from ephys import neuropixels_utils
from events import event_types_default, event_types_norma
import configs

drive_path = os.environ["DJ_DRIVE_PATH"]
data_path = os.environ["DATA_PATH"]
schema = dj.schema('VEIDB', locals())

@schema
class SubsessionEvents(dj.Computed):
    definition = """
            -> EphysRaw
            ---
            subsession_type: varchar(128)
            start_abs: int
            trials: longblob
            subsession_triggers: longblob
            trials_stimtypes: blob
            trials_starts: blob
            trials_ends: blob
    """

    def make(self, key):
        config_type = (Experiment() & key).fetch1('config_type')
        cfg = configs.get_config(config_type)

        experiment_id, session_id, subsession_type, sync_trace = \
            (EphysRaw() & key).fetch1('experiment_id', 'session_id', 'subsession_type', 'sync_trace')
        start, length = (EphysRawHelper() & key).fetch1('start', 'length')

        iteration = (Subsession() & key).fetch1('iteration')
        print(key)
        key['subsession_type'] = subsession_type
        key['start_abs'] = start
        stimlog_iter = iteration
        stimlog_folder_path = os.path.join(data_path, cfg['stimlog_path'].format(**key))
        if not os.path.isdir(stimlog_folder_path):
            session_path = os.path.join(data_path, cfg['session_path'].format(**key))
            print(session_path)
            if len([f for f in os.listdir(session_path) if 'stimlog' in f.lower()]) != 0:
                stimlog_folder_path = os.path.join(session_path, [f for f in os.listdir(session_path) if 'stimlog' in f.lower()][0])
                if not os.path.isdir(stimlog_folder_path):
                    print('Neural recordings for {session_id} in {experiment_id} are not found'.format(**key))
                    return
            else:
                print("No stimlog folder found for {session_id} in {experiment_id}!")
        try:
            if cfg['event_types'] =='norma':
                subsession_triggers, trials, trials_starts, trials_ends, trial_stimtypes = event_types_norma.extract(subsession_type, sync_trace, stimlog_folder_path, stimlog_iter)
            else:
                subsession_triggers, trials, trials_starts, trials_ends, trial_stimtypes = event_types_default.extract(subsession_type, sync_trace, stimlog_folder_path, stimlog_iter)
            # info = neuropixels_utils.get_trialgroup_stimulus_info(sync_trace)
            key['trials'] = trials
            key['trials_stimtypes'] = trial_stimtypes
            key['subsession_triggers'] = subsession_triggers
            key['trials_starts'] = trials_starts
            key['trials_ends'] = trials_ends
            # key.update(info)

            self.insert1(key)

            print('Populated a trial for {session_id} in {experiment_id}'.format(**key))
        except RuntimeError as e:
            print("Error with populating trial for {session_id} in {experiment_id}".format(**key))
            print(e)

@schema
class OptoEvents(dj.Computed):
    definition = """
                -> LFP
                ---
                pulse_starts: blob
                pulse_ends: blob 
        """
    def filter_pulses(self, transitions_below, transitions_upper):
        below_idx, upper_idx = 0, 0
        curr = 0
        transitions_below_filt = []
        transitions_upper_filt = []
        below = False

        while below_idx <= len(transitions_below) and upper_idx < len(transitions_upper):
            if below == True:
                v = transitions_upper[upper_idx]
                if v > curr:
                    transitions_upper_filt.append(v)
                    curr = v
                    below = False
                upper_idx += 1
            else:
                v = transitions_below[below_idx]
                if v > curr:
                    transitions_below_filt.append(v)
                    curr = v
                    below = True
                below_idx += 1
        return np.array(transitions_below_filt), np.array(transitions_upper_filt)

    def make(self, key):
        # Get LFPs
        lf_path, subsession_type = (LFP() & key).fetch1('lf_path', 'subsession_type')
        # Check if Optotagged recording
        if subsession_type != 'OPTS':
            return
        else:
            print("Opto trial found or {session_id} in {experiment_id}".format(**key))
        lfps = neuropixels_utils.extract_analog(Path(os.path.join(data_path, lf_path)), channels=range(384))

        # Artifact detection
        # mean_lfp = np.mean(lfps, axis=0) - np.mean(lfps)
        mean_lfp = np.mean((lfps.T - np.mean(lfps, axis=1)).T, axis=0)
        lfp_std = np.std(mean_lfp)

        lower_bound = -lfp_std * 6
        upper_bound = lfp_std * 6
        values_below = mean_lfp < lower_bound
        values_upper = mean_lfp > upper_bound
        transitions_below = np.where(np.diff(values_below.astype(int)) > 0)[0]
        transitions_upper = np.where(np.diff(values_upper.astype(int)) > 0)[0]
        if len(transitions_below) != 0 and len(transitions_upper) != 0:
            transitions_below, transitions_upper = self.filter_pulses(transitions_below, transitions_upper)
        # Store triggers
        key['pulse_starts'] = transitions_below
        key['pulse_ends'] = transitions_upper
        self.insert1(key)
        print('Populated a trial for {session_id} in {experiment_id}'.format(**key))


@schema
class TrialEvents(dj.Computed):
    definition = """
            -> SubsessionEvents
            trial_id: varchar(128)
            ---
            trial_iter: int
            stimtype: varchar(128)
            start: int
            end: int
            events: blob
    """

    def make(self, key):
        subsession_type, trials, trials_starts, trials_ends, trials_stimtypes = (SubsessionEvents() & key).fetch1('subsession_type', 'trials', 'trials_starts', 'trials_ends', 'trials_stimtypes')
        print(trials, trials_stimtypes, trials_starts, trials_ends)
        for i, (trial, stimtype, start, end) in enumerate(zip(trials, trials_stimtypes, trials_starts, trials_ends)):
            key['trial_id'] = f"{subsession_type}_T{i}"
            key['trial_iter'] = i
            key['stimtype'] = stimtype
            key['start'] = start
            key['end'] = end
            key['events'] = trial
            self.insert1(key)
        print(f"Inserted all trials for subsession {subsession_type}.")


#
# @schema
# class TrialEvents(dj.Computed):
#     definition = """
#             -> SubsessionEvents
#             trial_id: int
#             ---
#             trial_idx: int
#             trial_start: int
#             trial_end: int
#             trial_triggers: blob
#     """
#
#     def make(self, key):
#         (SubsessionEvents)


# @schema
# class TrialEvents(dj.Computed):
#     definition = """
#             -> TrialGroupEvents
#             ---
#             something: varchar(128)
#     """
#
#     def make(self, key):
#         pass