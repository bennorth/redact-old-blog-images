"""
Requires these env.vars to be set:

HOME — home directory of user, e.g., "/home/jrandomhacker"; this is
        usually set by the shell automatically

SITE_NAME — domain name of site, e.g., "mycoolsite.com"

Emits JSON to stdout for an array of records; each record having
properties "fullpath", "x", and "y".

Emits diagnostics and warnings to stderr.
"""

import glob
import os
import stat
import json
import sys
from pathlib import Path
from subprocess import run, PIPE


########################################################################

homedir = os.getenv("HOME")
site_name = os.getenv("SITE_NAME")
if home is None or site_name is None:
    print(
        "please set HOME and SITE_NAME",
        file=sys.stderr
    )
    sys.exit(1)


########################################################################

def cmd_text_output(cmd):
    out = run(cmd, stdout=PIPE)
    return out.stdout.decode(errors="replace")

def handle_jpg(path):
    text_output = cmd_text_output(["jhead", str(path)])
    for line in text_output.split("\n"):
        if line.startswith("Resolution"):
            pcs = line.split()
            res = {"fullpath": str(path), "x": int(pcs[2]), "y": int(pcs[4])}
            records.append(res)

def handle_png(path):
    cmd = ["file", str(path)]
    text_output = cmd_text_output(cmd)
    pcs = text_output.split()
    res = {"fullpath": str(path), "x": int(pcs[4]), "y": int(pcs[6][:-1])}
    records.append(res)


########################################################################

records = []
pattern = f"{homedir}/{site_name}/wp-content/uploads/**"
for fname in glob.iglob(pattern, recursive=True):
    s = os.stat(fname)
    if stat.S_ISREG(s.st_mode):
        path = Path(fname)
        extension = path.suffix
        if extension in [".jpeg", ".jpg"]:
            handle_jpg(path)
        elif extension == ".png":
            handle_png(path)
        elif extension in [".pdf", ".pptx"]:
            # Ignore these files.
            pass
        else:
            print(f"unknown extension: {path}", file=sys.stderr)

print(json.dumps(records))
