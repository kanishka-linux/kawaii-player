import time
import re
from difflib import SequenceMatcher
from typing import Dict, Optional
from vinanti import Vinanti
import hashlib
import json
import pickle
import os
from datetime import datetime

class AnimeInfoFetcher:
    def __init__(self, ui):
        self.base_url = "https://api.jikan.moe/v4"
        self.last_request = 0
        self.cache = {}
        self.ui = ui
        self.cache_file = os.path.join(ui.home_folder, "anime_cache.pkl")
        self.thumbnail_dir = os.path.join(ui.home_folder, 'thumbnails', 'thumbnail_server')
        if os.name == 'posix':
            verify = True
        else:
            verify = False
        self.vnt = Vinanti(block=True, hdrs={'User-Agent':self.ui.user_agent}, verify=verify)
        if os.path.exists(self.cache_file):
             with open(self.cache_file, 'rb') as f:
                self.cache = pickle.load(f)
    
    def _rate_limit(self):
        """Basic rate limiting - 1 request per second"""
        current_time = time.time()
        if current_time - self.last_request < 1:
            time.sleep(1 - (current_time - self.last_request))
        self.last_request = time.time()
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        return ' '.join(re.sub(r'[^\w\s]', '', title.lower()).split())
    
    def _calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between titles"""
        norm1 = self._normalize_title(title1)
        norm2 = self._normalize_title(title2)
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def _get_large_poster(self, images_data: Dict) -> Optional[str]:
        """Extract large poster URL"""
        if 'jpg' in images_data:
            jpg = images_data['jpg']
            return jpg.get('large_image_url') or jpg.get('image_url')
        return None

    def fetch_best_candidates(self, title: str) -> Dict:
        search_url = f"{self.base_url}/anime"
        search_params = {"q": title, "limit": 10}
        
        response = self.vnt.get(search_url, params=search_params)
        if response.status != 200:
            return {}
        
        candidates = json.loads(response.html).get('data', [])
        if not candidates:
            return {}
        
        # Find best match
        best_match = {}
        best_similarity = 0.0

        title_lower = title.lower()
        for anime in candidates:
            anime_type = anime.get('type', 'tv')
            anime_type = anime_type.lower()
            titles_to_check = [anime['title']]
            if anime.get('title_english'):
                titles_to_check.append(anime['title_english'])
            titles_to_check.extend(anime.get('title_synonyms', []))
            titles_with_type = []
            for t in titles_to_check:
                t = t.lower()
                if anime_type in t:
                    titles_with_type.append(t)
                else:
                    titles_with_type.append(f"{t} {anime_type}")

            max_similarity = max(
                self._calculate_similarity(title_lower, t) for t in titles_to_check if t
            )
            
            if max_similarity > best_similarity:
                best_similarity = max_similarity
                best_match = anime
        
        return best_match

    def build_local_image_file_name(self, url: str) -> str:
        url_bytes = bytes(url, 'utf-8')
        h = hashlib.sha256(url_bytes)
        digest = h.hexdigest()
        local_path = os.path.join(self.thumbnail_dir, f"poster-{digest}.jpg")
        return local_path
    
    def get_anime_info(self, title: str, cache: bool) -> Optional[Dict]:
        """
        Get anime info by title
        Returns: {
            'mal_id': int,
            'title': str,
            'genres': list,
            'summary': str,
            'large_poster': str
        }
        """
        try:
            if cache and self.cache and self.cache.get(title):
                print(f"returning from cache {title}")
                return self.cache.get(title)
            # Search for anime
            self._rate_limit()
            
            best_match = self.fetch_best_candidates(title)
            
            # Get detailed info
            self._rate_limit()
            detail_url = f"{self.base_url}/anime/{best_match['mal_id']}"
            
            response = self.vnt.get(detail_url)
            if response.status != 200:
                return None
            
            data = json.loads(response.html).get('data', [])

            anime_details = {
                    'id': data['mal_id'],
                    'title': data['title'],
                    'title_english': data.get('title_english'),
                    'title_synonyms': data.get('title_synonyms', []),
                    'type': data.get('type'),
                    'episodes': data.get('episodes'),
                    'status': data.get('status'),
                    'aired': data.get('aired', {}),
                    'duration': data.get('duration'),
                    'rating': data.get('rating'),
                    'score': data.get('score'),
                    'scored_by': data.get('scored_by'),
                    'rank': data.get('rank'),
                    'popularity': data.get('popularity'),
                    'synopsis': data.get('synopsis'),
                    'background': data.get('background'),
                    'season': data.get('season'),
                    'year': data.get('year'),
                    'broadcast': data.get('broadcast', {}),
                    'producers': [p['name'] for p in data.get('producers', [])],
                    'licensors': [l['name'] for l in data.get('licensors', [])],
                    'studios': [s['name'] for s in data.get('studios', [])],
                    'genres': [g['name'] for g in data.get('genres', [])],
                    'themes': [t['name'] for t in data.get('themes', [])],
                    'demographics': [d['name'] for d in data.get('demographics', [])],
                    'url': data.get('url'),
                    'image_poster_large': self._get_large_poster(data.get('images', {})),
                    'trailer': data.get('trailer', {}),
                    'approved': data.get('approved'),
                    'titles': data.get('titles', [])
                }

            year = anime_details.get('year')
            aired = anime_details.get("aired")
            if aired and not year:
                aired_from = aired.get("from")
                try:
                    dt = datetime.fromisoformat(aired_from)
                    year = dt.year
                except Exception as err:
                    self.ui.logger("error: {}, formating iso-date: {}".format(err, aired_from))
                anime_details['year'] = year
            img_url = anime_details.get("image_poster_large")
            if img_url:
                img_path = self.build_local_image_file_name(img_url)
                self.vnt.get(img_url, out=img_path)
                img = os.path.split(img_path)[-1]
                local_image_url = f"/images/{img}"
                anime_details["image_poster_large"] = local_image_url
            self.cache[title] = anime_details

            return anime_details
            
        except Exception as err:
            self.ui.logger("error: {}, for fetching: {}".format(err, title))
            return None

