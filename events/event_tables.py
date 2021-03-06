import os
import numpy as np
from pathlib import Path
from main_tables import Experiment, Session, Subsession
from ephys.ephys_tables import EphysRaw, EphysRawHelper
import datajoint as dj
from ephys import neuropixels_utils
from events import event_types
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
            stimlog_folder_path = os.path.join(session_path, [f for f in os.listdir(session_path) if 'stimlog' in f.lower()][0])
            if not os.path.isdir(stimlog_folder_path):
                print('Neural recordings for {session_id} in {experiment_id} are not found'.format(**key))
                return
        try:
            subsession_triggers, trials, trials_starts, trials_ends, trial_stimtypes = event_types.extract(subsession_type, sync_trace, stimlog_folder_path, stimlog_iter)
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