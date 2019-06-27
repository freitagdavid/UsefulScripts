# UsefulScripts

### extract_all.py

This one is for bulk extracting archives it has a couple switches you can optionally extract zip or 7zip or both it can recurse through sub directories and it can optionally delete files after successful extraction. If you just run the script with the -h flag it will explain the rest.

### datToParentClone.py

This one is for creating a very rudimentary parent clone dat using an pre-existing dat file. It only works on roms that have multiple files the dat I had in mind was Redump's ps1 dat. Basically the way it works is that if it finds that there is a duplicate file between two games it adds a cloneof tag to one of the games. So far the only dat that I've tested is the redump ps1 dat though I don't see why it wouldn't work on other systems who's roms have multiple files where some are pure duplicates. It's also worth mentioning that you will only see benefits if you are using solid archives. The script also outputs a text file next to the output dat that lists which games got put into other archives like "game -> parent"
