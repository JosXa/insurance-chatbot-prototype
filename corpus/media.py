"""
Media are registered in the assets/files folder with any file ending supported by the bot clients.
They are referenced by their filename without extension, which is referred to as the `media_id`.
"""
import os

from mwt import mwt

from appglobals import ROOT_DIR

media_path = os.path.join(ROOT_DIR, 'assets', 'files')
all_media = os.listdir(media_path)

phone_images_path = os.path.join(ROOT_DIR, 'corpus', 'phonedata', 'photo')
all_phone_images = os.listdir(phone_images_path)


@mwt(120)
def get_file_by_media_id(media_id):
    """
    Searches for a media file or phone model image by its `media_id`
    :param media_id: Filename without extension
    :return: Absolute file path
    """

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
