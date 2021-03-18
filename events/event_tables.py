import os
import numpy as np
from pathlib import Path
from main_tables import Experiment, Session, TrialGroup
from ephys.ephys_tables import EphysRaw
import datajoint as dj
from ephys import neuropixels_utils

drive_path = os.environ["DJ_DRIVE_PATH"]
data_path = os.environ["DATA_PATH"]
schema = dj.schema('VEIDB', locals())

@schema
class TrialGroupEvents(dj.Computed):
    definition = """
            -> EphysRaw
            ---
            stimulus_type: varchar(128)
            start_abs: int
            stims_start: int
            stims_end: int
            stim_triggers: longblob
    """

    def make(self, key):
        experiment_id, session_id, stimulus_type, sync_trace, start, length = \
            (EphysRaw() & key).fetch1('experiment_id', 'session_id', 'stimulus_type', 'sync_trace', 'start', 'length')
        key['stimulus_type'] = stimulus_type
        key['start_abs'] = start
        info = neuropixels_utils.get_trialgroup_stimulus_info(sync_trace)
        key.update(info)

        self.insert1(key)

        print('Populated a trial for {session_id} in {experiment_id}'.format(**key))


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