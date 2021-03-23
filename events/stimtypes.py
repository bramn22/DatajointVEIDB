import numpy as np


class EXPA:

    def extract(self, stimtriggers, trigger_idxs):
        # These are the channels used by Katja in her recordings
        start_idx = trigger_idxs[7]
        start_stop_post = tuple(stimtriggers[7][start_idx:start_idx+3])
        new_trigger_idxs = trigger_idxs[7] + 3
        return start_stop_post, new_trigger_idxs


class DIMM:

    def extract(self, stimtriggers, trigger_idxs):
        # These are the channels used by Katja in her recordings
        start_idx = trigger_idxs[7]
        start_stop_post = tuple(stimtriggers[7][start_idx:start_idx+3])
        new_trigger_idxs = trigger_idxs[7] + 3
        return start_stop_post, new_trigger_idxs