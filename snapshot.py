import os
import json
import mimetypes
from ads import list_ads_files

def create_snapshot(directory, use_ads):
    snapshot = {}
    for root, dirs, files in os.walk(directory):
        for dir_name in dirs:
            dir_path = os.path.join(root, dir_name)
            rel_path = os.path.relpath(dir_path, directory)
            snapshot[rel_path] = {'size': 0, 'type': 'directory'}
        for name in files:
            file_path = os.path.join(root, name)
            rel_path = os.path.relpath(file_path, directory)
            try:
                size = os.path.getsize(file_path)
                type, _ = mimetypes.guess_type(file_path)
                snapshot[rel_path] = {'size': size, 'type': type if type else "unknown"}
                if use_ads:
                    ads_files = list_ads_files(file_path)
                    for ads_file, ads_size in ads_files:
                        ads_rel_path = os.path.relpath(ads_file, directory)
                        snapshot[ads_rel_path] = {'size': ads_size, 'type': 'ADS'}
            except OSError as e:
                print(f"Error accessing file {file_path}: {e}")
    return snapshot

def save_snapshot(snapshot, filepath):
    with open(filepath, 'w') as f:
        json.dump(snapshot, f, indent=4)

def load_snapshot(filepath):
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None