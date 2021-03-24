import numpy as np


class EXPA:

    def extract(self, stimtriggers, trigger_idxs):
        # These are the channels used by Katja in her recordings
        start_idx = trigger_idxs[7]
        # print("stimtriggers7: ", stimtriggers[7])
        # print("startidx: ", start_idx)
        start_stop_post = tuple(stimtriggers[7][start_idx:start_idx+3])
        trigger_idxs[7] += 3 # Original list is being modified!!

        # trigger_idxs[7] += 1
        return start_stop_post, trigger_idxs


class DIMM:

    def extract(self, stimtriggers, trigger_idxs):
        # These are the channels used by Katja in her recordings
        start_idx = trigger_idxs[7]
        # print("stimtriggers7: ", stimtriggers[7])
        # print("startidx: ", start_idx)
        start_stop_post = tuple(stimtriggers[7][start_idx:start_idx+3])
        trigger_idxs[7] += 3 # Original list is being modified!!

        return start_stop_post, trigger_idxs