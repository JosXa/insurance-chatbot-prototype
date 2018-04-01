import os
from pprint import pprint

from mwt import mwt

from appglobals import ROOT_DIR

media_path = os.path.join(ROOT_DIR, 'assets', 'files')
all_media = os.listdir(media_path)

phone_images_path = os.path.join(ROOT_DIR, 'corpus', 'phonedata', 'photo')
all_phone_images = os.listdir(phone_images_path)


@mwt(120)
def get_file_by_media_id(media_id):
    try:
        file = next(x for x in all_media if os.path.splitext(x)[0].lower() == media_id.lower())
        return os.path.join(media_path, file)
    except StopIteration:
        pass

    try:
        file = next(x for x in all_phone_images if os.path.splitext(x)[0].lower() == media_id.lower())
        return os.path.join(phone_images_path, file)
    except StopIteration:
        return None
