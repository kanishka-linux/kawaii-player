import time
import re
from difflib import SequenceMatcher
from typing import Dict, Optional, List
from vinanti import Vinanti
import hashlib
import json
import pickle
import os
import traceback
from datetime import datetime

class AnimeInfoFetcher:
    def __init__(self, ui):
        self.base_url = "https://api.jikan.moe/v4"
        self.last_request = 0
        self.cache = {}
        self.ui = ui
        self.pattern = r'[\[\(\{].*?[\]\)\}]'
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

    def _build_recommendation_cache_key(self, title, series_type, series_sub_type):
        cache_key = f"recommendation::{title}::{series_type}::{series_sub_type}"
        return cache_key

    def fetch_best_candidates(self, title: str, series_type: str, series_sub_type: str, use_cache: bool) -> Dict:
        cache_key = self._build_recommendation_cache_key(title, series_type, series_sub_type)
        search_url = f"{self.base_url}/anime"
        search_params = {"q": title, "limit": 10}
        if series_sub_type and series_sub_type.lower() != "any":
            search_params['type'] = series_sub_type
        
        self.ui.logger.info(f"search-params: {search_params}")
        
        if use_cache and self.cache.get(cache_key):
            candidates = self.cache.get(cache_key)
        else:
            response = self.vnt.get(search_url, params=search_params)
            if response.status != 200:
                return {}
            candidates = json.loads(response.html).get('data', [])
            if not candidates:
                return {}
            self.cache[cache_key] = candidates
        
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
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as err:
            self.ui.logger.error(f"Error saving cache: {err}")
    
    def _safe_extract_names(self, items):
        """Safely extract names from list of dictionaries."""
        if not items:
            return []

        names = []
        for item in items:
            if item and isinstance(item, dict):
                name = item.get('name')
                if name:  # Only add non-empty names
                    names.append(name)
        return names

    def sanitize_title(self, title):
        cleaned = re.sub(r'[\[\(\{].*?[\]\)\}]', '', title)
        cleaned = re.sub(r'[-_.]+', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned

    def get_anime_info(self, title: str, cache: bool, series_type: str, external_id: str, series_sub_type: str) -> Optional[Dict]:
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
            title = self.sanitize_title(title)
            self.ui.logger.info(f"searching: {title}")

            if cache and self.cache and external_id:
                detail_cache_url = f"{self.base_url}/anime/{external_id}"
                if self.cache.get(detail_cache_url):
                    self.ui.logger.info(f"returning from cache {detail_cache_url}")
                    return self.cache.get(detail_cache_url)

            if cache and self.cache and self.cache.get(title):
                self.ui.logger.info(f"returning from cache {title}")
                return self.cache.get(title)
            # Search for anime
            self._rate_limit()
            
            if external_id:
                mal_id = external_id
            else:
                best_match = self.fetch_best_candidates(title, series_type, series_sub_type, cache)
                self.ui.logger.info(f"best-matched for {title} => {best_match}")
                mal_id = best_match['mal_id']
            
            # Get detailed info
            self._rate_limit()
            detail_url = f"{self.base_url}/anime/{mal_id}"
            
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

                    'producers': self._safe_extract_names(data.get('producers', [])),
                    'licensors': self._safe_extract_names(data.get('licensors', [])),
                    'studios': self._safe_extract_names(data.get('studios', [])),
                    'genres': self._safe_extract_names(data.get('genres', [])),
                    'themes': self._safe_extract_names(data.get('themes', [])),
                    'demographics': self._safe_extract_names(data.get('demographics', [])),

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
                    self.ui.logger.error("error: {}, formating iso-date: {}".format(err, aired_from))
                anime_details['year'] = year
            img_url = anime_details.get("image_poster_large")
            if img_url:
                img_path = self.build_local_image_file_name(img_url)
                self.vnt.get(img_url, out=img_path)
                img = os.path.split(img_path)[-1]
                local_image_url = f"/images/{img}"
                anime_details["image_poster_large"] = local_image_url
            self.cache[title] = anime_details
            self.cache[detail_url] = anime_details
            self._save_cache()
            
            if mal_id:
                episode_details = self.get_all_episodes(int(mal_id), cache, False)
                anime_details["episode_details"] = episode_details
                self.cache[title] = anime_details
                self.cache[detail_url] = anime_details
                self._save_cache()

            return anime_details
            
        except Exception as err:
            self.ui.logger.error("error: {}, for fetching: {}".format(err, title))
            self.ui.logger.exception(f"Traceback:\n {traceback.format_exc()}")
            return None

    def _build_episodes_cache_key(self, mal_id: int) -> str:
        return f"episodes::{mal_id}"

    def get_episode_details(self, mal_id: int, episode_number: int, use_cache: bool = True) -> Optional[Dict]:
        """
        Fetch detailed info for a single episode (includes synopsis/summary).
        Jikan exposes this at /anime/{mal_id}/episodes/{episode_id}.

        Returns a dict with keys:
            mal_id, url, title, title_japanese, title_romanji,
            aired, score, filler, recap, synopsis
        """
        cache_key = f"episode_detail::{mal_id}::{episode_number}"

        if use_cache and self.cache.get(cache_key):
            self.ui.logger.info(f"returning episode detail from cache: {cache_key}")
            return self.cache[cache_key]

        self._rate_limit()
        url = f"{self.base_url}/anime/{mal_id}/episodes/{episode_number}"
        response = self.vnt.get(url)

        if response.status != 200:
            self.ui.logger.warning(
                f"Failed to fetch episode {episode_number} detail for mal_id={mal_id}: HTTP {response.status}"
            )
            return None

        data = json.loads(response.html).get('data', {})
        if not data:
            return None

        episode_detail = {
            'mal_id':          data.get('mal_id'),
            'url':             data.get('url'),
            'title':           data.get('title'),
            'title_japanese':  data.get('title_japanese'),
            'title_romanji':   data.get('title_romanji'),
            'aired':           data.get('aired'),
            'score':           data.get('score'),
            'filler':          data.get('filler', False),
            'recap':           data.get('recap', False),
            'synopsis':        data.get('synopsis'),        # full episode summary
            'forum_url':       data.get('forum_url'),
        }

        self.cache[cache_key] = episode_detail
        self._save_cache()
        return episode_detail

    def get_all_episodes(
        self,
        mal_id: int,
        use_cache: bool = True,
        fetch_details: bool = False,
    ) -> List[Dict]:
        """
        Fetch the full episode list for an anime by its MAL ID.

        Jikan returns episodes in pages of 100.  This method handles
        pagination automatically and collects every page.

        Args:
            mal_id:        MyAnimeList ID of the anime.
            use_cache:     Return cached result when available.
            fetch_details: If True, make an additional per-episode request
                           to retrieve the synopsis/summary for each episode.
                           This is much slower (one extra API call per episode)
                           but gives the richest data.

        Returns:
            List of episode dicts.  Without fetch_details each dict contains:
                mal_id, url, title, title_japanese, title_romanji,
                aired, score, filler, recap
            With fetch_details the 'synopsis' key is also populated.
        """
        episodes_cache_key = self._build_episodes_cache_key(mal_id)

        # Return from cache only when details are NOT needed or cache already
        # has the synopsis field (i.e. was built with fetch_details=True before).
        if use_cache and self.cache.get(episodes_cache_key):
            cached = self.cache[episodes_cache_key]
            if not fetch_details or (cached and cached[0].get('synopsis') is not None):
                self.ui.logger.info(f"returning all episodes from cache for mal_id={mal_id}")
                return cached

        episodes: List[Dict] = []
        page = 1

        while True:
            self._rate_limit()
            url = f"{self.base_url}/anime/{mal_id}/episodes"
            response = self.vnt.get(url, params={"page": page})

            if response.status != 200:
                self.ui.logger.warning(
                    f"Failed to fetch episodes page {page} for mal_id={mal_id}: HTTP {response.status}"
                )
                break

            body = json.loads(response.html)
            page_data = body.get('data', [])

            if not page_data:
                break  # No more episodes

            for ep in page_data:
                episode_entry = {
                    'mal_id':         ep.get('mal_id'),          # episode number
                    'url':            ep.get('url'),
                    'title':          ep.get('title'),
                    'title_japanese': ep.get('title_japanese'),
                    'title_romanji':  ep.get('title_romanji'),
                    'aired':          ep.get('aired'),
                    'score':          ep.get('score'),
                    'filler':         ep.get('filler', False),
                    'recap':          ep.get('recap', False),
                    'synopsis':       None,  # populated below if fetch_details=True
                }
                episodes.append(episode_entry)

            # Check if there are more pages
            pagination = body.get('pagination', {})
            has_next = pagination.get('has_next_page', False)
            if not has_next:
                break

            page += 1

        # Optionally enrich each episode with its full synopsis
        if fetch_details:
            for ep in episodes:
                ep_number = ep.get('mal_id')
                if ep_number is None:
                    continue
                detail = self.get_episode_details(mal_id, ep_number, use_cache=use_cache)
                if detail:
                    ep['synopsis']       = detail.get('synopsis')
                    ep['forum_url']      = detail.get('forum_url')

        # Persist to cache
        self.cache[episodes_cache_key] = episodes
        self._save_cache()

        return episodes
