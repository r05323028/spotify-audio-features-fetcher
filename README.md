# Spotify Audio-features Fetcher

a simple tool to access spotify audio features and audio analysis.

## Install dependencies

```
pip install -r requirements.txt
```

## Usage

you need to set the `CLIENT_ID` and `CLIENT_SECRET` in the `settings.py` file.

```python
CLIENT_ID = '<YOUR_CLIENT_ID>'

CLIENT_SECRET = '<YOUR_CLIENT_SECRET>'
```

next, use `SpotifySong` to access the audio features.

```python

from spotify_tools import SpotifySong

song = SpotifySong('漂向北方', '黃明志', 'Namewee')

# for audio features
song.get_audio_features()

# for audio analysis
song.get_audio_analysis()

```