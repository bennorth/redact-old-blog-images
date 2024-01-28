from subprocess import run
from glob import iglob

def file_iglob(pattern):
    return (
        path.removeprefix("images-out/")
        for path in iglob(pattern, recursive=True)
        if not path.endswith("/")
    )

for year in range(2008, 2024):
    files = []
    for month in range(8, 13):
        files.extend(file_iglob(f"images-out/{year}/{month:02d}/**"))
    for month in range(1, 8):
        files.extend(file_iglob(f"images-out/{year + 1}/{month:02d}/**"))
    files.sort()
    filelist_name = f"filenames-{year}-{year + 1}.null-terminated"
    tarname = f"symlinks-{year}-{year + 1}.tar.xz"
    with open(filelist_name, "w+t") as filelist:
        filelist.write("\0".join(files))
        filelist.write("\0")
        filelist.close()
        cmd = [
            "tar",
            "--create",
            "--xz",
            f"--file={tarname}",
            "--directory=images-out",
            "--null",
            "--verbatim-files-from",
            f"--files-from={filelist.name}"
        ]
        run(cmd)
