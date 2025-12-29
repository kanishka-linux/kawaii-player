import os
import time
import json
import pickle
import hashlib
import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, Optional, List
from vinanti import Vinanti

class TvShowInfoFetcher:
    def __init__(self, ui):
        self.base_url = "https://api.tvmaze.com"
        self.last_request = 0
        self.cache = {}
        self.ui = ui
        self.cache_file = os.path.join(ui.home_folder, "tvshow_cache.pkl")
        self.thumbnail_dir = os.path.join(ui.home_folder, 'thumbnails', 'thumbnail_server')
        
        # Create thumbnail directory if it doesn't exist
        os.makedirs(self.thumbnail_dir, exist_ok=True)
        
        if os.name == 'posix':
            verify = True
        else:
            verify = False
        self.vnt = Vinanti(block=True, hdrs={'User-Agent': self.ui.user_agent}, verify=verify)
        
        # Load existing cache
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'rb') as f:
                    self.cache = pickle.load(f)
            except Exception as err:
                self.ui.logger.error(f"Error loading cache: {err}")
                self.cache = {}
    
    def _rate_limit(self):
        """Rate limiting - 20 requests per 10 seconds (0.5 seconds between requests)"""
        current_time = time.time()
        if current_time - self.last_request < 0.5:
            time.sleep(0.5 - (current_time - self.last_request))
        self.last_request = time.time()
    
    def _normalize_title(self, title: str) -> str:
        """Normalize title for comparison"""
        return ' '.join(re.sub(r'[^\w\s]', '', title.lower()).split())
    
    def _calculate_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between titles"""
        norm1 = self._normalize_title(title1)
        norm2 = self._normalize_title(title2)
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def _get_large_poster(self, image_data: Optional[Dict]) -> Optional[str]:
        """Extract large poster URL"""
        if image_data and isinstance(image_data, dict):
            return image_data.get('original') or image_data.get('medium')
        return None
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)
        except Exception as err:
            self.ui.logger.error(f"Error saving cache: {err}")

    def fetch_best_candidates(self, title: str) -> Dict:
        """Search for shows and return the best match"""
        search_url = f"{self.base_url}/search/shows"
        search_params = {"q": title}
        
        try:
            response = self.vnt.get(search_url, params=search_params)
            if response.status != 200:
                self.ui.logger.error(f"Search failed with status: {response.status}")
                return {}
            
            search_results = json.loads(response.html)
            if not search_results:
                return {}
            
            # Find best match based on title similarity
            best_match = {}
            best_similarity = 0.0
            title_lower = title.lower()
            
            for result in search_results:
                show = result.get('show', {})
                if not show:
                    continue
                
                # Check main title and aliases
                titles_to_check = [show.get('name', '')]
                
                # Add alternative titles if available
                if show.get('officialSite'):
                    titles_to_check.append(show.get('officialSite', ''))
                
                # Calculate similarity for all titles
                max_similarity = 0.0
                for check_title in titles_to_check:
                    if check_title:
                        similarity = self._calculate_similarity(title_lower, check_title.lower())
                        max_similarity = max(max_similarity, similarity)
                
                # Update best match if this is better
                if max_similarity > best_similarity:
                    best_similarity = max_similarity
                    best_match = show
            
            return best_match
            
        except Exception as err:
            self.ui.logger.error(f"Error in fetch_best_candidates: {err}")
            return {}

    def build_local_image_file_name(self, url: str) -> str:
        """Generate local filename for image URL"""
        url_bytes = bytes(url, 'utf-8')
        h = hashlib.sha256(url_bytes)
        digest = h.hexdigest()
        local_path = os.path.join(self.thumbnail_dir, f"poster-{digest}.jpg")
        return local_path
    
    def get_series_info(self, title: str, cache: bool = True) -> Optional[Dict]:
        """
        Get TV series info by title
        Returns: {
            'id': int,
            'title': str,
            'title_english': str,
            'genres': list,
            'summary': str,
            'large_poster': str,
            'year': int,
            'status': str,
            'network': str,
            'runtime': int,
            'rating': float,
            'premiered': str,
            'ended': str,
            'type': str,
            'language': str,
            'url': str
        }
        """
        try:
            # Check cache first
            if cache and self.cache and self.cache.get(title):
                self.ui.logger.info(f"Returning from cache: {title}")
                return self.cache.get(title)
            
            # Search for the show
            self._rate_limit()
            best_match = self.fetch_best_candidates(title)
            
            if not best_match:
                self.ui.logger.warning(f"No match found for: {title}")
                return None
            
            # Get detailed info
            show_id = best_match.get('id')
            if not show_id:
                return None
            
            self._rate_limit()
            detail_url = f"{self.base_url}/shows/{show_id}"
            
            response = self.vnt.get(detail_url)
            if response.status != 200:
                self.ui.logger.error(f"Detail fetch failed with status: {response.status}")
                return None
            
            data = json.loads(response.html)
            
            # Extract premiere year
            year = None
            premiered = data.get('premiered')
            if premiered:
                try:
                    year = datetime.strptime(premiered, '%Y-%m-%d').year
                except ValueError:
                    try:
                        year = int(premiered[:4])
                    except (ValueError, TypeError):
                        pass
            
            # Process network information
            network_info = data.get('network') or data.get('webChannel')
            network_name = network_info.get('name') if network_info else None
            
            # Build series details
            series_details = {
                'id': data.get('id'),
                'title': data.get('name'),
                'title_english': data.get('name'),  # TVmaze doesn't separate English titles
                'title_synonyms': [],  # TVmaze doesn't provide synonyms in main endpoint
                'type': data.get('type', 'Scripted'),
                'status': data.get('status'),
                'premiered': premiered,
                'ended': data.get('ended'),
                'year': year,
                'runtime': data.get('runtime'),
                'rating': data.get('rating', {}).get('average') if data.get('rating') else None,
                'language': data.get('language'),
                'summary': data.get('summary'),
                'synopsis': data.get('summary'),  # Alias for compatibility
                'genres': data.get('genres', []),
                'network': network_name,
                'country': network_info.get('country', {}).get('name') if network_info else None,
                'url': data.get('url'),
                'officialSite': data.get('officialSite'),
                'schedule': data.get('schedule', {}),
                'weight': data.get('weight'),
                'image_poster_large': self._get_large_poster(data.get('image')),
                'externals': data.get('externals', {}),
                'updated': data.get('updated')
            }
            
            # Handle image download
            img_url = series_details.get("image_poster_large")
            if img_url:
                try:
                    img_path = self.build_local_image_file_name(img_url)
                    self._rate_limit()
                    response = self.vnt.get(img_url, out=img_path)
                    if response.status == 200:
                        img = os.path.split(img_path)[-1]
                        local_image_url = f"/images/{img}"
                        series_details["image_poster_large"] = local_image_url
                    else:
                        self.ui.logger.warning(f"Failed to download image: {img_url}")
                except Exception as err:
                    self.ui.logger.error(f"Error downloading image: {err}")
            
            # Cache the result
            if cache:
                self.cache[title] = series_details
                self._save_cache()
            
            return series_details
            
        except Exception as err:
            self.ui.logger.error(f"Error fetching series info for '{title}': {err}")
            return None
    
    def search_shows(self, title: str) -> List[Dict]:
        """
        Search for multiple shows by title
        Returns a list of show dictionaries
        """
        try:
            self._rate_limit()
            search_url = f"{self.base_url}/search/shows"
            search_params = {"q": title}
            
            response = self.vnt.get(search_url, params=search_params)
            if response.status != 200:
                return []
            
            search_results = json.loads(response.html)
            shows = []
            
            for result in search_results:
                show = result.get('show', {})
                if show:
                    shows.append({
                        'id': show.get('id'),
                        'title': show.get('name'),
                        'year': show.get('premiered', '')[:4] if show.get('premiered') else None,
                        'status': show.get('status'),
                        'genres': show.get('genres', []),
                        'summary': show.get('summary'),
                        'score': result.get('score', 0)
                    })
            
            return shows
            
        except Exception as err:
            self.ui.logger.error(f"Error searching shows: {err}")
            return []
    
    def get_show_by_id(self, show_id: int) -> Optional[Dict]:
        """Get show info by TVmaze ID"""
        try:
            self._rate_limit()
            detail_url = f"{self.base_url}/shows/{show_id}"
            
            response = self.vnt.get(detail_url)
            if response.status != 200:
                return None
            
            data = json.loads(response.html)
            return data
            
        except Exception as err:
            self.ui.logger.error(f"Error fetching show by ID {show_id}: {err}")
            return None
