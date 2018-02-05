import os
import subprocess

import ffmpy
import speech_recognition as sr


class VoiceRecognitionClient:
    def __init__(self):
        self.recognizer = sr.Recognizer()

    # def convert_ogg_to_flac_cloudconvert(self, handle):
    #     reader = io.BufferedReader(handle)
    #     process = self.converter.convert({
    #         'inputformat': 'ogg',
    #         'outputformat': 'flac',
    #         'input': 'upload',
    #         'file': reader
    #     })
    #     process.wait()  # wait until conversion finished
    #     filename = 'voice.flac'
    #     process.download(filename)  # download output file
    #     return filename

    @staticmethod
    def convert_audio_ffmpeg(in_file, out_file):
        if os.path.exists(out_file):
            os.remove(out_file)
        ff = ffmpy.FFmpeg(
            inputs={in_file: None},
            outputs={out_file: None}
        )
        ff.run(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return out_file

    def recognize(self, filepath):
        with sr.AudioFile(filepath) as source:
            audio = self.recognizer.record(source)  # read the entire audio file
        return self.recognizer.recognize_google_cloud(audio, None, language='de_DE')
