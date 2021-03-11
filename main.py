import os

def load(drive_path, data_path):
    os.environ["DJ_DRIVE_PATH"] = drive_path
    os.environ["DATA_PATH"] = data_path
    import main_tables as mt
    return mt
