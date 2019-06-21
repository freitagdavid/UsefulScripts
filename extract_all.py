import os
import argparse
import subprocess
from pathlib import Path
parser = argparse.ArgumentParser()
parser.add_argument('-r', '--recursive', action='store_true',
                    help="Recurses through subfolders")
parser.add_argument('-s', '--seven-zip', action='store_true',
                    help="Process seven zip files")
parser.add_argument('-z', '--zip', action='store_true',
                    help="Process zip files")
parser.add_argument('-d', '--delete', action='store_true',
                    help="Delete after extraction")
parser.add_argument('-di', '--directory',
                    default="./", help="Directory to process")
args = parser.parse_args()


def is_zip(file):
    return file.suffix == ".zip"


def is_szip(file):
    return file.suffix == ".7z"


def get_files():
    output = []
    if args.recursive:
        for dir_name, subdir_list, file_list in os.walk(args.directory):
            for fname in file_list:
                file = Path(dir_name) / fname
                if is_zip(file):
                    output.append(file)
                if is_szip(file):
                    output.append(file)
    else:
        for fname in os.listdir(args.directory):
            file = Path(args.directory) / fname
            if is_zip(file):
                output.append(file)
            if is_szip(file):
                output.append(file)

    return output


def extract_file(file):
    szip_args = ["7z", "e", None, "-y", None]
    szip_args[2] = str(file.absolute())
    szip_args[4] = f'-o{str(file.parent / file.stem)}'
    return subprocess.call(szip_args, stdin=None, stdout=None,
                           stderr=None, shell=False)


def delete_file(file):
    os.remove(file)
    print(f"Deleted: {file.name}")
    pass


def process_files(files):
    for file in files:
        status = extract_file(file)
        print(f"Extracted: {file.name}")
        if args.delete:
            if status == 0:
                delete_file(file)
            else:
                print(
                    "There was a problem with extraction this file will not be deleted")


def main():
    files = get_files()
    process_files(files)


main()
