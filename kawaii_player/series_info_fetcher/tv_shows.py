import os
import time
import json
import pickle
import hashlib
import re
import traceback
from html import unescape
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

    def sanitize_title(self, title):
        # Step 1: Remove bracketed content
        cleaned = re.sub(r'[\[\(\{].*?[\]\)\}]', '', title)

        # Step 2: Remove season indicators
        cleaned = re.sub(r'\b(?:season|series|s|part|pt)\s*\d{0,2}\b', '', cleaned, flags=re.IGNORECASE)

        # Step 3: Handle special characters
        cleaned = re.sub(r'[-_]+', ' ', cleaned)

        # Step 4: Clean up spacing
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned

    def extract_season_number(self, title):
        # Combined pattern for all numeric season indicators
        pattern = r'(?:\b(?:season|series|part|pt)\s*|[\[\(\{]?s)(\d{1,2})(?:[\]\)\}]|\b)'
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            try:
                season_num = int(match.group(1))
                return season_num if 1 <= season_num <= 99 else None
            except ValueError:
                pass

        return None
    
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

    def fetch_best_candidates(self, title: str, series_type: str) -> Dict:
        """Search for shows and return the best match"""
        search_url = f"{self.base_url}/search/shows"
        search_params = {"q": title}
        show_type_mapping = {'cartoons': 'animation', 'tv shows': 'scripted'}
        show_type_required = show_type_mapping.get(series_type, 'N/A')

        try:
            response = self.vnt.get(search_url, params=search_params)
            if response.status != 200:
                self.ui.logger.error(f"Search failed with status: {response.status}")
                return {}
 
            search_results = json.loads(response.html)
            self.ui.logger.info(f"{title} => {search_results}")
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
                show_type = show.get('type', 'N/A')
                show_type = show_type.lower()
                if show_type != show_type_required:
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
            self.ui.logger.error(f"Error in fetching best candidates: {err}")
            return {}

    def fetch_season_info(self, show_id: int, season_number: Optional[int] = None) -> Dict:
        """
        Fetch season-specific information including episode count and poster.
        
        Args:
            show_id: TVmaze show ID
            season_number: Specific season number to fetch (None for all seasons)
            
        Returns:
            Dict with season info: {
                'season_number': int,
                'episode_count': int,
                'season_poster': str,
                'premiere_date': str,
                'end_date': str
            }
        """
        try:
            self._rate_limit()
            seasons_url = f"{self.base_url}/shows/{show_id}/seasons"
            
            response = self.vnt.get(seasons_url)
            if response.status != 200:
                self.ui.logger.error(f"Seasons fetch failed with status: {response.status}")
                return {}
            
            seasons_data = json.loads(response.html)
            if not seasons_data:
                return {}
            
            # If specific season requested, find it
            if season_number is not None:
                target_season = None
                for season in seasons_data:
                    if season.get('number') == season_number:
                        target_season = season
                        break
                
                if not target_season:
                    self.ui.logger.warning(f"Season {season_number} not found for show {show_id}")
                    return {}
                
                return self._process_season_data(target_season)
            
            # Return info for all seasons
            all_seasons = {}
            for season in seasons_data:
                season_num = season.get('number')
                if season_num is not None:
                    all_seasons[season_num] = self._process_season_data(season)
            
            return all_seasons
            
        except Exception as err:
            self.ui.logger.error(f"Error fetching season info for show {show_id}: {err}")
            return {}
    
    def _process_season_data(self, season_data: Dict) -> Dict:
        """Process individual season data into standardized format."""
        return {
            'season_number': season_data.get('number'),
            'episode_count': season_data.get('episodeOrder', 0),
            'season_poster': self._get_large_poster(season_data.get('image')),
            'premiere_date': season_data.get('premiereDate'),
            'end_date': season_data.get('endDate'),
            'network': season_data.get('network', {}).get('name') if season_data.get('network') else None,
            'web_channel': season_data.get('webChannel', {}).get('name') if season_data.get('webChannel') else None,
            'summary': season_data.get('summary')
        }

    def build_local_image_file_name(self, url: str) -> str:
        """Generate local filename for image URL"""
        url_bytes = bytes(url, 'utf-8')
        h = hashlib.sha256(url_bytes)
        digest = h.hexdigest()
        local_path = os.path.join(self.thumbnail_dir, f"poster-{digest}.jpg")
        return local_path
    
    def _download_image(self, img_url: str) -> Optional[str]:
        """Download image and return local URL path."""
        if not img_url:
            return None
            
        try:
            img_path = self.build_local_image_file_name(img_url)
            
            self._rate_limit()
            response = self.vnt.get(img_url, out=img_path)
            if response.status == 200:
                img = os.path.split(img_path)[-1]
                return f"/images/{img}"
            else:
                self.ui.logger.warning(f"Failed to download image: {img_url}")
                return None
        except Exception as err:
            self.ui.logger.error(f"Error downloading image: {err}")
            return None
    
    def _extract_year_from_date(self, date_string):
        """Extract year from date string."""
        try:
            return datetime.strptime(date_string[:10], '%Y-%m-%d').year
        except (ValueError, TypeError):
            return None

    def _clean_html_summary(self, summary):
        """Remove HTML tags from summary text."""
        if not summary:
            return ""
        
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', summary)
        
        # Decode HTML entities (&amp; &lt; etc.)
        clean_text = unescape(clean_text)
        
        # Clean up extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        return clean_text

    def get_series_info(self, title: str, cache: bool, series_type: str) -> Optional[Dict]:
        """
        Get TV series info by title with season-specific information
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
            'url': str,
            'season_info': {
                'season_number': int,
                'episode_count': int,
                'season_poster': str,
                'premiere_date': str,
                'end_date': str
            }
        }
        """
        try:
            season_number = self.extract_season_number(title)
            sanitized_title = self.sanitize_title(title)
            self.ui.logger.info(f"searching: {sanitized_title}, S-{season_number}")

            # Create cache key that includes season info
            cache_key = f"{sanitized_title}_s{season_number}" if season_number else sanitized_title

            # Check cache first
            if cache and self.cache and self.cache.get(cache_key):
                self.ui.logger.info(f"Returning from cache: {cache_key}")
                return self.cache.get(cache_key)
            
            # Search for the show
            self._rate_limit()
            best_match = self.fetch_best_candidates(sanitized_title, series_type)
            
            if not best_match:
                self.ui.logger.warning(f"No match found for: {sanitized_title}")
                return None
            
            self.ui.logger.info(f"Best-matched: {best_match}")
            # Get detailed info
            show_id = best_match.get('id')
            if not show_id:
                return None
            
            self._rate_limit()
            detail_url = f"{self.base_url}/shows/{show_id}"
            
            response = self.vnt.get(detail_url)
            self.ui.logger.info(f"{detail_url} => {response.html}")
            if response.status != 200:
                self.ui.logger.error(f"Detail fetch failed with status: {response.status}")
                return None
            
            data = json.loads(response.html)
            self.ui.logger.info(f"JSON: {detail_url} => {data}")
            
            # Extract premiere year
            premiered = self._extract_year_from_date(data.get('premiered'))
            
            # Process network information
            network_name = 'N/A'
            country_name = 'N/A'
            network_info = data.get('network', {}) or data.get('webChannel', {})
            if network_info:
                network_name = network_info.get('name', 'N/A')
                country_name_info = network_info.get('country', {})
                if country_name_info:
                    country_name = country_name_info.get('name', 'N/A')
            
            # Build series details
            series_details = {
                'id': data.get('id'),
                'title': data.get('name'),
                'title_english': data.get('name'),  # TVmaze doesn't separate English titles
                'title_synonyms': [],  # TVmaze doesn't provide synonyms in main endpoint
                'type': data.get('type', 'Scripted'),
                'status': data.get('status'),
                'aired': premiered,
                'ended': data.get('ended'),
                'year': premiered,
                'duration': data.get('runtime'),
                'rating': data.get('rating', {}).get('average') if data.get('rating') else None,
                'language': data.get('language'),
                'summary': data.get('summary'),
                'synopsis': data.get('summary'),  # Alias for compatibility
                'genres': data.get('genres', []),
                'network': network_name,
                'country': country_name,
                'url': data.get('url'),
                'officialSite': data.get('officialSite'),
                'schedule': data.get('schedule', {}),
                'weight': data.get('weight'),
                'image_poster_large': self._get_large_poster(data.get('image')),
                'externals': data.get('externals', {}),
                'updated': data.get('updated'),
                'season_info': None  # Will be populated below
            }
            
            # Fetch season-specific information
            
            if season_number:
                season_info = self.fetch_season_info(show_id, season_number)
                if season_info:
                    # Overwrite with season data if available
                    series_details.update({
                        'premiered': season_info.get('premiere_date') or series_details.get('premiered'),
                        'year': self._extract_year_from_date(season_info.get('premiere_date')) or series_details.get('year'),
                        'episodes': season_info.get('episode_count') or series_details.get('episodes'),
                        'summary': season_info.get('summary') or series_details.get('summary'),
                        'synopsis': season_info.get('summary') or series_details.get('synopsis'),
                        'title': f"{data.get('name')} (Season {season_number})",
                        'season_info': season_info
                    })
                    
                    self.ui.logger.info(f"Updated with season {season_number} data: {season_info.get('episode_count', 0)} episodes")

            # Determine best poster URL (season poster or show poster)
            poster_url = None
            if season_number and series_details.get('season_info'):
                poster_url = series_details['season_info'].get('season_poster')

            if not poster_url:
                poster_url = self._get_large_poster(data.get('image'))

            # Download the chosen poster
            if poster_url:
                series_details['image_poster_large'] = self._download_image(poster_url)

            cleaned_summary = self._clean_html_summary(series_details.get("summary", ""))

            series_details["synopsis"] = cleaned_summary
            
            # Cache the result
            if cache:
                self.cache[cache_key] = series_details
                self._save_cache()
            
            return series_details
            
        except Exception as err:
            self.ui.logger.error(f"Error fetching series info for '{title}': {err}")
            self.ui.logger.exception(f"Traceback:\n {traceback.format_exc()}")
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
