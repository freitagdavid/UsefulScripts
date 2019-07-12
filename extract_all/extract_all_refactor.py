import argparse
from pathlib import Path
from multiprocessing import Manager, Process, active_children
import subprocess
from time import sleep
import zipfile
import os
from tqdm import tqdm
import asyncio

# parser = argparse.ArgumentParser()
# parser.add_argument('-r', '--recursive', action='store_true',
#                     help="Recurses through subfolders")
# parser.add_argument('-s', '--seven-zip', action='store_true',
#                     help="Process seven zip files")
# parser.add_argument('-z', '--zip', action='store_true',
#                     help="Process zip files")
# parser.add_argument('-g', '--g-zip', action='store_true',
#                     help="Process gzip files")
# parser.add_argument('-d', '--delete', action='store_true',
#                     help="Delete after extraction")
# parser.add_argument('-m', '--multi-threading',
#                     help='Enable or disable multi-threading', default="1")
# parser.add_argument('-di', '--directory',
#                     default="./", help="Directory to process")
# args = parser.parse_args()


def is_zip(file):
    return file.suffix == ".zip" and args.zip


def is_szip(file):
    return file.suffix == ".7z" and args.seven_zip


def is_gzip(file):
    return file.suffix == ".gz" and args.g_zip


def filter_file(file, files):
    if is_zip(file):
        pass
    if is_szip(file):
        pass
    if is_gzip(file):
        pass


def process_directory(files, files_to_process, scan_complete, files_scanned):
    if args.recursive:
        for dir_name, subdir_list, file_list in os.walk(args.directory):
            for fname in file_list:
                file = Path(dir_name) / fname
                if is_zip(file):
                    files.put(file)
                    files_to_process.value += 1
                if is_szip(file):
                    files.put(file)
                    files_to_process.value += 1
                if is_gzip(file):
                    files.put(file)
                    files_to_process.value += 1
                files_scanned.value += 1
    else:
        for fname in os.listdir(args.directory):
            file = Path(args.directory) / fname
            if is_zip(file):
                files.put(file)
                files_to_process.value += 1
            if is_szip(file):
                files.put(file)
                files_to_process.value += 1
            if is_gzip(file):
                files.put(file)
                files_to_process.value += 1
            files_scanned.value += 1
    scan_complete.value = 1


def extract_zip(file):
    try:
        z = zipfile.ZipFile(file.absolute())
        zip_entries = z.infolist()
        extracted = 0
        for entry in zip_entries:
            z.extract(entry, file.parent / file.stem)
            extracted += entry.compress_size
        return 0
    except:
        return 1


def extract_file(file, extract_progress):
    if zipfile.is_zipfile(file.absolute()):
        return extract_zip(file)
    else:
        szip_args = ["7z", "e", None, "-y", None]
        szip_args[2] = str(file.absolute())
        szip_args[4] = f'-o{str(file.parent / file.stem)}'
        proc = subprocess.Popen(
            szip_args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        extract_progress[file.name] = proc.communicate()
        proc.wait()
        del extract_progress[file.name]
        return proc.returncode
        # return subprocess.call(szip_args, stdin=None, stdout=None, stderr=None, shell=False)


def delete_file(file):
    os.remove(file)
    # print(f"Deleted: {file.name}")


def process_file(file, files_processed, extract_progress):
    if args.delete:
        if extract_file(file, extract_progress) == 0:
            delete_file(file)
        # else:
        #     print("There was a problem with extraction this file will not be deleted")
    files_processed.value += 1


def clear():
    if os.name == 'nt':
        _ = os.system('cls')
    else:
        _ = os.system('clear')


def screen(files_to_process, files_processed, files_scanned, files, extract_progress):
    prev_processed = 0
    files_processed_pb = tqdm(desc="Files Processed",
                              total=files_to_process.value)
    while True:
        # clear()
        # print("Files Scanned:", files_scanned.value)
        current_value = files_processed.value
        files_processed_pb.update(current_value - prev_processed)
        prev_processed = current_value
        files_processed_pb.total = files_to_process.value
        for key, value in extract_progress.items():
            print(value)
        sleep(1)


if __name__ == '__main__':
    manager = Manager()
    files = manager.Queue()
    files_processed = manager.Value('i', 0)
    files_to_process = manager.Value('i', 0)
    files_scanned = manager.Value('i', 0)
    scan_complete = manager.Value('i', 0)
    extract_progress = manager.dict({})
    print("test")
    root_dir = Path(args.directory)
    workers = int(args.multi_threading) + 3
    Process(target=process_directory, args=[
            files, files_to_process, scan_complete, files_scanned]).start()
    Process(target=screen, args=[files_to_process,
                                 files_processed, files_scanned, files, extract_progress]).start()
    while files or scan_complete != 1:
        if len(active_children()) < workers:
            Process(target=process_file, args=(
                files.get(), files_processed, extract_progress)).start()
