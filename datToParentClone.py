# from collections import defaultdict
from xml.etree import cElementTree as ET
from xml.dom import minidom
from pathlib import Path
import argparse
# import json

parser = argparse.ArgumentParser()
parser.add_argument("inputDat", help="Dat file that you wish to process")
args = parser.parse_args()
inputDat = Path(args.inputDat)
outDat = inputDat.parent / (str(inputDat.stem) +
                            "_processed" + str(inputDat.suffix))
outTxt = inputDat.parent / (str(inputDat.stem) +
                            "_processed.txt")

with open(inputDat, "r") as datFile:
    rawXML = datFile.read()
tree = ET.XML(rawXML)


class Dat:
    def __init__(self, tree):
        self.header = None
        self.roms = None
        self.games = None
        self.dupes = {}
        self.dedup = ""
        self.add_header(tree)
        self.find_dupes(tree)
        self.mark_dupes(tree)

    def add_header(self, tree):
        header = {}
        for child in tree.find("header"):
            header[child.tag] = child.text
        self.header = header

    def find_dupes(self, tree):
        for game in tree.findall("game"):
            for rom in game.findall(".//rom"):
                if rom.attrib["sha1"] not in self.dupes:
                    self.dupes[rom.attrib["sha1"]] = []
                self.dupes[rom.attrib["sha1"]].append(game)

    def mark_dupes(self, tree):
        marked = []
        for romHash, games in self.dupes.items():
            if len(games) > 1:
                for game in games:
                    if game not in marked:
                        marked.append(game)
                        if game is not games[0]:
                            if "cloneof" in games[0].attrib:
                                game.attrib["cloneof"] = games[0].attrib["cloneof"]
                                self.dedup += f'{game.attrib["name"]} -> {games[0].attrib["name"]}\n'
                            else:
                                game.attrib["cloneof"] = games[0].attrib["name"]
        with open(outTxt, "w") as file:
            file.write(self.dedup)
        xmlString = ET.tostring(tree, encoding='unicode', method='xml')
        with open(outDat, "w") as file:
            file.write(xmlString)


def prettifyXML(elem):
    # Slightly modified from here
    # https://pymotw.com/2/xml/etree/ElementTree/create.html#pretty-printing-xml
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")


if __name__ == '__main__':
    data = Dat(tree)
