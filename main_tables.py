import datajoint as dj
import os
import configs

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

schema = dj.schema('VEIDB', locals())


@schema
class Experiment(dj.Manual):
    definition = """
        experiment_id: varchar(16)
        ---
        config_type = "Ania" : varchar(16)
        description: varchar(255)
        experimenters: varchar(255)   # name of the experimenters
    """


@schema
class Mouse(dj.Manual):
    definition = """
        -> Experiment
        mouse_id = "M01" : varchar(16)
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
class Subsession(dj.Imported):
    definition = """
        -> Session
        subsession_id: varchar(16)
        ---
        type: varchar(16)
        iteration: int
    """

    def make(self, key):
        config_type = (Experiment() & key).fetch1('config_type')
        cfg = configs.get_config(config_type)
        base_path = os.path.join(data_path, cfg['wavesurfer_path'].format(**key)) # could also be experiment_id/neuropixels/session_id
        subsession_files = [os.path.splitext(f)[0] for f in os.listdir(base_path) if f.endswith('.h5')]
        for subsession in subsession_files:
            key['subsession_id'] = subsession
            type, iteration = subsession.split('_')[:2]
            try:
                key['type'] = type
                key['iteration'] = int(iteration)
            except:
                key['type'] = iteration
                key['iteration'] = int(type)
            self.insert1(key)


from ephys import ephys_tables
from behavior import behavior_tables
from events import event_tables