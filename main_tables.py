import datajoint as dj
import os

drive_path = os.environ["DJ_DRIVE_PATH"]
data_path = os.environ["DATA_PATH"]
environment = {}

dj.config['stores'] = {
    'facecam': dict(
        protocol='file',
        location=os.path.join(drive_path, r'blobs/facecam'),  # A copy of the data will be stored here
    ),
    'external_neuropixels': dict(
        protocol='file',
        location=os.path.join(drive_path, r'blobs/neuropixels')
    )
}

schema = dj.schema('Ephys', locals())


@schema
class Experiment(dj.Manual):
    definition = """
        experiment_id: varchar(16)
        ---
        description: varchar(255)
        experimenters: varchar(255)   # name of the experimenters
    """


@schema
class Mouse(dj.Manual):
    definition = """
        -> Experiment
        mouse_id = "M1" : varchar(16)
        ---
        sex: varchar(5)
        mouse_number: varchar(16)
    """


@schema
class Session(dj.Manual):
    definition = """
        -> Experiment
        -> Mouse
        session_id: varchar(16)
        ---
        session_date: date            # session date
    """


@schema
class TrialGroup(dj.Imported):
    definition = """
        -> Session
        trialgroup_id: varchar(16)
        ---
        stimulus_type: varchar(16)
        iteration: int
    """

    def make(self, key):
        base_path = os.path.join(data_path, "{experiment_id}/{mouse_id}/{session_id}".format(**key)) # could also be experiment_id/neuropixels/session_id
        stimgroup_files = [os.path.splitext(f)[0] for f in os.listdir(base_path) if f.endswith('.h5')]
        for stimgroup in stimgroup_files:
            key['stimgroup_id'] = stimgroup
            stimulus_type, iteration = stimgroup.split('_')
            key['stimulus_type'] = stimulus_type
            key['iteration'] = int(iteration)
            self.insert1(key)


from ephys import ephys_tables
from behavior import behavior_tables
from stimulus import stimulus_tables