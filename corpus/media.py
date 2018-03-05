import os

from mwt import mwt

from appglobals import ROOT_DIR

path = os.path.join('assets', 'files')
all_media = os.listdir(path)


@mwt(120)
def get_file_by_media_id(media_id):
    try:
        file = next(x for x in all_media if os.path.splitext(x)[0] == media_id.lower())
        return os.path.join(path, file)
    except StopIteration:
        return None
