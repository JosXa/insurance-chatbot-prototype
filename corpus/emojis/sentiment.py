import csv

import os
from pathlib import Path

DIR = Path(os.path.dirname(os.path.abspath(__file__)))


def get_emoji_sentiments():
    with open(DIR / 'Emoji_Sentiment_Data_v1.0.csv', mode='r') as data:
        reader = csv.reader(data)
        results = {}
        for row in reader:
            try:
                negative = int(row[4])
                neutral = int(row[5])
                positive = int(row[6])
            except ValueError:
                continue

            emoji = row[0]

            total = sum((negative, neutral, positive))
            results[emoji] = dict(
                negative=negative / total,
                neutral=neutral / total,
                positive=positive / total
            )
        return results
