import os
import time
import win32api
import win32con
import mimetypes

def calculate_directory_size(path):
    total_size = 0
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            total_size += calculate_directory_size(entry.path)
        else:
            total_size += entry.stat(follow_symlinks=False).st_size
    return total_size

def get_file_attributes(path):
    attributes = []
    attrs = win32api.GetFileAttributes(path)

    if attrs & win32con.FILE_ATTRIBUTE_ARCHIVE:
        attributes.append('A')
    else:
        attributes.append('-')
        
    if attrs & win32con.FILE_ATTRIBUTE_HIDDEN:
        attributes.append('H')
    else:
        attributes.append('-')
        
    if attrs & win32con.FILE_ATTRIBUTE_SYSTEM:
        attributes.append('S')
    else:
        attributes.append('-')
        
    if attrs & win32con.FILE_ATTRIBUTE_READONLY:
        attributes.append('R')
    else:
        attributes.append('-')

    return ''.join(attributes)

def get_last_modified(path):
    last_modified_timestamp = os.path.getmtime(path)
    last_modified_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_modified_timestamp))
    return last_modified_time

def compare_directories(dir1, dir2):
    entries1 = {e.name: e for e in os.scandir(dir1)}
    entries2 = {e.name: e for e in os.scandir(dir2)}

    files1 = {f: {
        'size': os.path.getsize(os.path.join(dir1, f)),
        'attributes': get_file_attributes(os.path.join(dir1, f)),
        'last_modified': get_last_modified(os.path.join(dir1, f))
    } for f in entries1 if not entries1[f].is_dir()}
    
    files2 = {f: {
        'size': os.path.getsize(os.path.join(dir2, f)),
        'attributes': get_file_attributes(os.path.join(dir2, f)),
        'last_modified': get_last_modified(os.path.join(dir2, f))
    } for f in entries2 if not entries2[f].is_dir()}

    dirs1 = {d: calculate_directory_size(os.path.join(dir1, d)) for d in entries1 if entries1[d].is_dir()}
    dirs2 = {d: calculate_directory_size(os.path.join(dir2, d)) for d in entries2 if entries2[d].is_dir()}

    size_diff_files = {f: {'size': files1[f]['size'] != files2[f]['size'],
                           'attributes': files1[f]['attributes'] != files2[f]['attributes'],
                           'last_modified': files1[f]['last_modified'] != files2[f]['last_modified']}
                       for f in files1 if f in files2 and (
                           files1[f]['size'] != files2[f]['size'] or
                           files1[f]['attributes'] != files2[f]['attributes'] or
                           files1[f]['last_modified'] != files2[f]['last_modified'])}
    
    size_diff_dirs = {d for d in dirs1 if d in dirs2 and dirs1[d] != dirs2[d]}
    only_in1_files = set(files1.keys()) - set(files2.keys())
    only_in2_files = set(files2.keys()) - set(files1.keys())
    only_in1_dirs = set(dirs1.keys()) - set(dirs2.keys())
    only_in2_dirs = set(dirs2.keys()) - set(dirs1.keys())

    return size_diff_files, only_in1_files, only_in2_files, only_in1_dirs, only_in2_dirs, size_diff_dirs