import os
import numpy as np
from pathlib import Path
from main_tables import Experiment, Session, Subsession
from ephys.ephys_tables import EphysRaw
import datajoint as dj
from ephys import neuropixels_utils
from events import event_types

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
    """

    def make(self, key):
        experiment_id, session_id, subsession_type, sync_trace, start, length, iteration = \
            (EphysRaw() & key).fetch1('experiment_id', 'session_id', 'subsession_type', 'sync_trace', 'start', 'length', 'iteration')
        key['subsession_type'] = subsession_type
        key['start_abs'] = start
        stimlog_iter = iteration
        stimlog_folder_path = os.path.join(data_path,
                                   "{experiment_id}/{mouse_id}/{session_id}/StimLog".format(**key))
        if not os.path.isdir(stimlog_folder_path):
            print('Neural recordings for {session_id} in {experiment_id} are not found'.format(**key))
            return
        subsession_triggers, trials = event_types.extract(subsession_type, sync_trace, stimlog_folder_path, stimlog_iter)
        # info = neuropixels_utils.get_trialgroup_stimulus_info(sync_trace)
        key['trials'] = trials
        key['subsession_triggers'] = subsession_triggers
        # key.update(info)

        self.insert1(key)

        print('Populated a trial for {session_id} in {experiment_id}'.format(**key))

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