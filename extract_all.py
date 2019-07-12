import os
import argparse
import subprocess
from pathlib import Path
from multiprocessing import Process, Value, Queue, Manager, active_children
from time import sleep
import zipfile
from collections import deque
import progressbar
import time
import rx
from rx import operators as ops

parser = argparse.ArgumentParser()
parser.add_argument('-r', '--recursive', action='store_true',
                    help="Recurses through subfolders")
parser.add_argument('-s', '--seven-zip', action='store_true',
                    help="Process seven zip files")
parser.add_argument('-z', '--zip', action='store_true',
                    help="Process zip files")
parser.add_argument('-g', '--g-zip', action='store_true',
                    help="Process gzip files")
parser.add_argument('-d', '--delete', action='store_true',
                    help="Delete after extraction")
parser.add_argument('-m', '--multi-threading',
                    help='Enable or disable multi-threading', default="1")
parser.add_argument('-di', '--directory',
                    default="./", help="Directory to process")
args = parser.parse_args()

workers = args.multi_threading - 1
directory_scan_complete = False
files_scanned = Value('i')
files_to_process = Value('i')
files_processed = Value('i')
processed_progressbar = progressbar.ProgressBar(max_value=progressbar.UnknownLength)

def is_zip(file):
    return file.suffix == ".zip" and args.zip


def is_szip(file):
    return file.suffix == ".7z" and args.seven_zip


def is_gzip(file):
    return file.suffix == ".gz" and args.g_zip

def extract_zip(file, out_dir, extract_progress):
    try:
        z = zipfile.ZipFile(file.absolute())
        zip_entries = z.infolist()
        zip_size = file.stat().st_size
        extracted = 0
        for entry in zip_entries:
            z.extract(entry, out_dir)
            extracted += entry.compress_size
        return 0
    except:
        return 1


def get_files(files_scanned, files_to_process, q):
    if args.recursive:
        for dir_name, subdir_list, file_list in os.walk(args.directory):
            for fname in file_list:
                file = Path(dir_name) / fname
                if is_zip(file):
                    q.put(file)
                    files_to_process.value += 1
                if is_szip(file):
                    q.put(file)
                    files_to_process.value += 1
                if is_gzip(file):
                    q.put(file)
                    files_to_process.value += 1
                files_scanned.value += 1
    else:
        for fname in os.listdir(args.directory):
            file = Path(args.directory) / fname
            if is_zip(file):
                q.put(file)
                files_to_process.value += 1
            if is_szip(file):
                q.put(file)
                files_to_process.value += 1
            if is_gzip(file):
                q.put(file)
                files_to_process.value += 1
            files_scanned.value += 1
    directory_scan_complete = True


def extract_file(file, extract_progress):
    if zipfile.is_zipfile(file.absolute()):
        return extract_zip(file, str(file.parent / file.stem), extract_progress)
    else:
        szip_args = ["7z", "e", None, "-y", None]
        szip_args[2] = str(file.absolute())
        szip_args[4] = f'-o{str(file.parent / file.stem)}'
        return subprocess.call(szip_args, stdin=None, stdout=None, stderr=None, shell=False)


def delete_file(file):
    os.remove(file)
    print(f"Deleted: {file.name}")

def process_file(file, files_processed):
    extraction_result = extract_file(file, extract_progress)
    if args.delete:
        if extract_file(file, extract_progress) == 0:
            delete_file(file)
        else:
            print("There was a problem with extraction this file will not be deleted")
    files_processed.value += 1

def clear(): 
  
    # for windows 
    if os.name == 'nt': 
        _ = os.system('cls') 
  
    # for mac and linux(here, os.name is 'posix') 
    else: 
        _ = os.system('clear')

# def print_extract_progress(extract_progress, progress_bars):
#     for key, value in extract_progress.items():
#         print(value["name"])
#         progress_bars[value["name"]] = progressbar.ProgressBar(max_value=value["size"])
#         progress_bars[value["name"]].update(value["extracted"])


def update_screen(files_scanned, files_to_process, files_processed, extract_progress, progress_bars):
    clear()
    print("Files Scanned:", files_scanned.value)
    print("Files to Process:", files_to_process.value)
    print("Files Processed:", files_processed.value)

def screen(files_scanned, files_to_process, files_processed, extract_progress, progress_bars):
    while True:
        update_screen(files_scanned, files_to_process, files_processed, extract_progress, progress_bars)
        sleep(1)

if __name__ == '__main__':
    manager = Manager()
    progress_bars = manager.dict()
    extract_progress = manager.dict()
    files_processed = manager.Value()
    q = manager.Queue()
    get_files = Process(target=get_files, args=[files_scanned, files_to_process, q]).start()
    Process(target=screen, args=[files_scanned, files_to_process, files_processed, extract_progress, progress_bars]).start()
    process_count = int(args.multi_threading)
    threads = []
    while q or directory_scan_complete is False:
        if q and len(active_children()) < process_count + 3:
            Process(target=process_file, args=(q.get(), files_processed, extract_progress)).start()
        # if q and threading.active_count() < process_count + 3:
        #     threading.Thread(target=process_files, args=(q.get(),files_processed, extract_progress)).start()
