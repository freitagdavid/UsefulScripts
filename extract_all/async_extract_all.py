import asyncio
import zipfile
import os
from pathlib import Path
import argparse

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


class Zip_Archive():
    def __init__(self, loop, path):
        self.path = path
        self.loop = loop
        print()
        self.archive_obj = zipfile.ZipFile(path.absolute())
        self.compressed_size = path.stat().st_size
        self.size_extracted = 0
        self.infolist = self.get_infolist()
        self.u_size = self.get_u_size()
        self.to_extract = len(self.infolist)
        self.num_extracted = 0

    def extract(self, path):
        self.loop.create_task(self._extract(path))

    def get_u_size(self):
        size = 0
        for i in self.infolist:
            size += i.compress_size
        return size

    def get_infolist(self):
        return self.archive_obj.infolist()

    async def _extract(self):
        try:
            for entry in self.infolist:
                self.archive_obj.extract(
                    entry, self.path.parent / self.path.stem)
                self.extracted += entry.compress_size
                self.num_extracted += 1
            return 0
        except:
            raise Exception("Unknown error occurred")


async def process_directory(directory, files_to_process, folders_to_process, workers):
    with workers.acquite():
        for item in directory.iterdir():
            if item.is_file():
                files_to_process.append(item)
                continue
            if item.is_dir():
                folders_to_process.append(item)


def is_zip(file):
    return file.suffix == ".zip" and args.zip


def is_szip(file):
    return file.suffix == ".7z" and args.seven_zip


def is_gzip(file):
    return file.suffix == ".gz" and args.g_zip


def is_wanted(file):
    return is_zip(file) or is_gzip(file) or is_szip(file)


async def handle_file(state, file):
    if is_zip(file):
        await state["files"].put(Zip_Archive(state["loop"], file))


async def get_files(state):
    async with state["workers"]:
        if args.recursive:
            for dir_name, subdir_list, file_list in os.walk(state["root_dir"]):
                for fname in file_list:
                    file = Path(dir_name) / fname
                    await handle_file(state, file)
                print("files:", state["files"].qsize())
        else:
            for fname in os.listdir(state["root_dir"]):
                file = Path(state["root_dir"] / fname)
                state["files"].put(handle_file(state, file))


def main():
    state = {
        "root_dir": args.directory,
        "files": asyncio.Queue(),
        "files_processed": 0,
        "workers": asyncio.Semaphore(int(args.multi_threading)),
        "tasks": asyncio.Queue(),
        "scan_complete": False,
        "loop": asyncio.get_event_loop()
    }
    state["loop"].create_task(get_files(state))
    state["loop"].run_forever()


if __name__ == '__main__':
    main()
