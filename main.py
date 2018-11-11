import os
import sys
from pathlib import Path
from collections import defaultdict
import exifread
import shutil
from pprint import pprint
# from subprocess import call


dir_src = Path(sys.argv[1])
assert dir_src.exists()

dir_root = dir_src.parent
dir_dest = dir_root / 'Renamed_{}'.format(dir_src.stem)
dir_error = dir_root / 'Error_{}'.format(dir_src.stem)

print(dir_src, dir_dest)

date_prefix = 'Date/Time Original              : '


def read_exif_date(filename: str):

    txt_time = 'time.txt'

    os.system('exiftool %s | grep Date/Time\ Original | head -1 > %s' % (filename, txt_time))

    with open(txt_time, 'r', encoding='utf-8') as f:
        try:
            line = f.readlines()[0]
            assert line.startswith(date_prefix)
        except AssertionError:
            print('exif date prefix wrong %s' % filename)
            return None
        except IndexError:
            print('exif info missed %s' % filename)
            return None

        exif_date = line.strip(date_prefix).replace(':', '_').strip()

    return exif_date


def parse_photos():

    os.mkdir(dir_dest)
    os.mkdir(dir_error)

    list_pics = []
    list_jpgs = []
    list_heics = []
    list_mp4s = []
    list_movs = defaultdict(int)
    list_unknown = []

    for filename in os.listdir(dir_src):
        filename = filename.lower()

        if '.heic' in filename or '.jpg' in filename:
            list_pics.append(filename)
        elif '.mov' in filename:
            list_movs[filename.strip('.mov')] += 1
        elif '.mp4' in filename:
            list_mp4s.append(filename)
        else:
            print('unknown type %s' % filename)
            list_unknown.append(filename)

    num_pics = len(list_pics)

    for i, filename in enumerate(list_pics):
        prefix = filename.split('.')[0]
        postfix = filename.split('.')[-1]
        full_file = dir_src / filename

        exif_date = read_exif_date(full_file)

        if exif_date is not None:

            shutil.copyfile(full_file, os.path.join(dir_dest.as_posix(), '%s.%s' % (exif_date, postfix)))

            if prefix in list_movs:
                assert list_movs[prefix] == 1
                list_movs[prefix] -= 1
                shutil.copyfile(
                    os.path.join(dir_src.as_posix(), '%s.mov' % prefix),
                    os.path.join(dir_dest.as_posix(), '%s.mov' % exif_date)
                )

        else:

            shutil.copyfile(full_file, dir_error / filename)

        print('%d/%d' % (i + 1, num_pics))

    for mp4 in list_mp4s:
        shutil.copyfile(dir_src / mp4, dir_error / mp4)

    for unk in list_unknown:
        shutil.copyfile(dir_src / unk, dir_error / unk)

    for mov in list_movs:
        if list_movs[mov] != 0:
            shutil.copyfile(dir_src / mov, dir_error / mov)


if __name__ == '__main__':

    parse_photos()