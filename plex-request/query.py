import requests
import json
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)


class Movie:

    def __init__(self, **metadata):
        self.title = metadata.get('title', None)
        print(f'Found Movie: {self.title}') ###DEL
        self.image = metadata.get('image', {})
        self.titleType = metadata.get('titleType', 'NA')
        self.year = metadata.get('year', 'NA')
        self.principals = metadata.get('principals', [{}])
        self.image_url = self.image.get('url', None)
        self.actors = [actor.get('name', 'NA') for actor in self.principals]
        self.runtime_total = metadata.get('runningTimeInMinutes', 0)
        self.runtime_hour = self.runtime_total // 60
        self.runtime_min = self.runtime_total % 60



class MediaClient:

    def __init__(self, **kwargs):
        load_dotenv()

        self.content_type = kwargs.get('content_type', None)
        self.keywords = kwargs.get('keywords', None)
        assert len(self.keywords) >= 1
        assert len(self.keywords) > 1 or len(self.keywords[0]) > 1

        print(f'Querying Media with keywords: {self.keywords}')
        query = ' '.join(self.keywords)

        url = os.getenv('RAPID_API_URL')
        querystring = {"q": query}

        headers = {
            'x-rapidapi-host': os.getenv('RAPID_API_HOST'),
            'x-rapidapi-key': os.getenv('RAPID_API_KEY')
            }

        response = requests.request("GET", url, headers=headers, params=querystring)
        if response.status_code == 200:
            self.data = json.loads(response.text)
            self.results = [{**result} for result in self.data['results']]
            self.movies, self.tvshows = self.parse_results()

        else:
            print(f'Error Response {response.status_code}')

    def parse_results(self):
        print('parsing results')
        movies = []
        tvshows = []
        for result in self.results:
            if result.get('titleType', False):
                ttype = result.get('titleType')
                if ttype == 'movie':
                    movies.append(Movie(**result))
                elif ttype == 'tvSeries':
                    tvshows.append(result)
                else:
                    continue
        return movies, tvshows



if __name__ == '__main__':
    keywords = {'content_type': 'movie', 'keywords' : ['invention', 'of', 'lying']}
    mymovie = MediaClient(**keywords)
