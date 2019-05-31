import os
import json
import time
import requests
from operator import itemgetter
from collections import namedtuple, OrderedDict
from fuzzywuzzy import fuzz
import settings
from utils import Token

token = Token()

token.response = token.get_token()

headers = {
    'Authorization': 'Bearer %s' % token.response['access_token']
}

class SpotifySong:

    def __init__(self, song_name, artist_name_zh, artist_name_en, *args, **kwargs):
        self.song_name = song_name
        self.artist_name_zh = artist_name_zh
        self.artist_name_en = artist_name_en
        self.audio_features = ['danceability','energy','key','loudness','mode','speechiness','acousticness','instrumentalness','liveness','valence','tempo','duration_ms','time_signature']
        self.audio_analysis_features = ['bars', 'beats', 'tatums', 'sections', 'segments']
        self.headers = headers

        self._song_id_get()
        self._song_attr_getter()

    def _song_artist_matcher(self, kk_song_name, kk_artist_name_zh, kk_artist_name_en, spoti_song_name, spoti_artist_name):
        song_name_similarity = fuzz.partial_ratio(kk_song_name, spoti_song_name) * 0.01
        aritst_name_similartiy_zh = fuzz.partial_ratio(kk_artist_name_zh, spoti_artist_name) * 0.01
        aritst_name_similartiy_en = fuzz.partial_ratio(kk_artist_name_en, spoti_artist_name) * 0.01
        aritst_name_similartiy = max(aritst_name_similartiy_en,aritst_name_similartiy_zh)
        return song_name_similarity * aritst_name_similartiy

    def _song_attr_getter(self):
        ret_array = []
        idx_simi = []
        SpotifyMetadata = namedtuple('SpotifyMetadata',['id','name','artist_name'])

        try:
            data_array = itemgetter('items')(itemgetter('tracks')(json.loads(self._response.text)))
            
            for item in data_array:
                result = SpotifyMetadata(
                    id = item['id'],
                    name = item['name'],
                    artist_name = itemgetter('artists')(item)[0]['name']
                )._asdict()
                ret_array.append(result)

            for i, d in enumerate(ret_array):
                s = self._song_artist_matcher(self.song_name, self.artist_name_zh, self.artist_name_en, d['name'], d['artist_name'])
                idx_simi.append((i,s))

            if idx_simi == []:
                self._spotify_search_result = OrderedDict(
                    [('id',None),
                    ('name',None),
                    ('artist_name',None)]
                )

            else:    
                idx_simi = sorted(idx_simi, key = itemgetter(1),reverse = True)
                max_simi = idx_simi[0][1]
                
                if max_simi < settings.SIMILARITY_THRESHOLD:
                    self._spotify_search_result = OrderedDict(
                        [('id', None),
                        ('name', None),
                        ('artist_name', None)]
                    )
                else:
                    max_simi_index = idx_simi[0][0]
                    self._spotify_search_result = ret_array[max_simi_index]

        except:
            self._spotify_search_result = OrderedDict(
                [('id', None),
                 ('name', None),
                 ('artist_name', None)]
            )

    def _song_id_get(self):
        search_url = os.path.join(settings.API_URL, 'search')
        response = requests.get(
            search_url, 
            params = {
                'q':self.song_name,
                'type':'track',
                'market':'TW'
                },
            headers = self.headers
            )
        self._response = response

    def _request_audio_features(self):
        audio_feature_headers = {
            "Authorization": "Bearer %s" % token.response['access_token'],
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        api_path = os.path.join(settings.API_URL,'audio-features')
        response = requests.get(
            api_path,
            params={
                'ids': self._spotify_search_result['id']
            },
            headers=audio_feature_headers
        )

        if response.status_code == 200:
            try:
                ret = json.loads(response.text)
                ret = OrderedDict(zip(self.audio_features,itemgetter(*self.audio_features)(ret['audio_features'][0])))
                return {
                    'results': dict(ret),
                    'meta':dict(self._spotify_search_result),
                }

            except:
                return {
                    'results': '',
                    'meta': dict(OrderedDict(zip(self.audio_features, [None] * len(self.audio_features)))),
                }

        elif response.status_code == 429:
            time.sleep(settings.TIMESLEEP_FOR_401)
            self._request_audio_features()

        elif response.status_code == 401:
            token.response = token.get_token()
            self._request_audio_features()

        else:
            raise Exception("Response <%s>" % response.status_code)

    def _request_audio_analysis(self):
        audio_analysis_headers = {
            "Authorization": "Bearer %s" % token.response['access_token'],
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        api_path = os.path.join(settings.API_URL, 'audio-analysis')
        response = requests.get(
            os.path.join(api_path, self._spotify_search_result['id']),
            headers = audio_analysis_headers
        )
        if response.status_code == 200:
            try:
                ret = json.loads(response.text)
                ret = OrderedDict(zip(self.audio_analysis_features, itemgetter(*self.audio_analysis_features)(ret)))
                return {
                    'results': dict(ret),
                    'meta': dict(self._spotify_search_result),
                }
            except:
                return {
                    'results': '',
                    'meta':OrderedDict(zip(self.audio_analysis_features, [None] * len(self.audio_analysis_features)))
                }

        elif response.status_code == 429:
            time.sleep(settings.TIMESLEEP_FOR_401)
            self._request_audio_analysis()
        
        elif response.status_code == 401:
            token.response = token.get_token()
            self._request_audio_analysis()

        elif response.status_code == 504:
            self._request_audio_analysis()

        else:
            raise Exception("Response <%s>" % response.status_code)

    def get_audio_features(self):
        return self._request_audio_features()

    def get_audio_analysis(self):
        return self._request_audio_analysis()


