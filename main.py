import os
import sys
from pathlib import Path
from collections import defaultdict
import shutil
from multiprocessing import Process

dir_src = Path(sys.argv[1])
assert dir_src.exists()

dir_root = dir_src.parent
dir_dest = dir_root / 'Renamed_{}'.format(dir_src.stem)
dir_error = dir_root / 'Error_{}'.format(dir_src.stem)

print(dir_src, dir_dest)

list_date_patterns = [
    'Date/Time Original',
    'Create Date',
    'Date Created'
]


def read_exif_date(filename: str):

    txt_time = 'time.txt'

    for pattern in list_date_patterns:

        os.system('exiftool %s | grep %s | head -1 > %s' % (filename, pattern.replace(' ', '\\ '), txt_time))

        with open(txt_time, 'r', encoding='utf-8') as f:

            line = None
            try:
                line = f.readlines()[0]
                hit_pattern = True
            except IndexError:
                hit_pattern = False

            if hit_pattern:

                try:
                    assert line.startswith(pattern)
                except AssertionError:
                    print('exif date prefix wrong %s' % filename)
                    return None

                exif_date = line.split(pattern)[-1].strip(' :').strip().replace(':', '_')
                return exif_date

    return None


def worker(list_pics, list_movs):

    num_pics = len(list_pics)
    for i, filename in enumerate(list_pics):
        prefix = filename.split('.')[0]
        postfix = filename.split('.')[-1]
        full_file = dir_src / filename

        exif_date = read_exif_date(full_file)

        if exif_date is not None:

            shutil.copyfile(full_file, os.path.join(dir_dest.as_posix(), '%s.%s' % (exif_date, postfix)))

            if prefix in list_movs:
                shutil.copyfile(
                    os.path.join(dir_src.as_posix(), '%s.mov' % prefix),
                    os.path.join(dir_dest.as_posix(), '%s.mov' % exif_date)
                )

        else:

            shutil.copyfile(full_file, dir_error / filename)

        print('%d/%d' % (i + 1, num_pics))


def parse_photos():

    if not os.path.exists(dir_dest):
        os.mkdir(dir_dest)

    if not os.path.exists(dir_error):
        os.mkdir(dir_error)

    list_pics = []
    list_mp4s = []
    list_movs = defaultdict(int)
    list_unknown = []

    for filename in os.listdir(dir_src):
        filename = filename.lower()

        if '.heic' in filename or '.jpg' in filename or '.png' in filename:
            list_pics.append(filename)
        elif '.mov' in filename:
            list_movs[filename.strip('.mov')] = 1
        elif '.mp4' in filename:
            list_mp4s.append(filename)
        else:
            print('unknown type %s' % filename)
            list_unknown.append(filename)

    for i, filename in enumerate(list_pics):
        prefix = filename.split('.')[0]

        if prefix in list_movs:
            list_movs[prefix] = 0

    num_pics = len(list_pics)
    num_workers = 5
    unit_size = num_pics // num_workers
    list_workers = []

    for i in range(num_workers):
        start = i * unit_size
        end = start + unit_size

        if i == num_workers - 1:
            end = num_pics

        p = Process(target=worker, args=(list_pics[start: end], list_movs))
        p.start()
        list_workers.append(p)

    for p in list_workers:
        p.join()

    for mp4 in list_mp4s:
        print(mp4)
        shutil.copyfile(dir_src / mp4, dir_error / mp4)

    for unk in list_unknown:
        print('unk', unk)
        shutil.copyfile(dir_src / unk, dir_error / unk)

    for mov in list_movs:
        if list_movs[mov] != 0:
            print('failed match mov %s.mov' % mov)
            shutil.copyfile(
                os.path.join(dir_src, '%s.mov' % mov),
                os.path.join(dir_error, '%s.mov' % mov)
            )


if __name__ == '__main__':

    # a = 'Create Date                     : 2018:10:30 18:19:38'
    # print(a.split(list_date_patterns[-1])[-1].strip(' :').strip())
    parse_photos()