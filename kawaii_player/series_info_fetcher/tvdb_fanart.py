import re
from collections import deque

from PyQt6 import QtWidgets
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import QUrl, pyqtSlot, pyqtSignal, QTimer, QObject
from browser import Browser


class FanartQueue(QObject):
    
    def __init__(self, ui):
        super().__init__()
        self.ui = ui
        self.queue = deque()
        self.processing = False
        self.current_title = ""
        self.current_srch = ""
        
        self.ui.tvdb_fanart.fanart_done.connect(self._on_fanart_fetched)

    def add(self, fetch_for):
        print(self.processing,"ppp")
        self.queue.append(fetch_for)
        if not self.processing:
            self._process_next()

    def _process_next(self):
        if not self.queue:
            self.processing = False
            return
        
        self.processing = True
        fetch_for = self.queue.popleft()
        title, srch = fetch_for.split('::')
        if not srch:
            srch = title
        
        if not title:
            self._process_next()
            return
        
        self.current_title = title
        self.current_srch = srch
        
        print(self.queue, "qq")
        
        if self.ui.fanart_dict.get(srch):
            imgs = self.ui.fanart_dict[srch]
            rotation_index = (self.ui.fanart_dict_rotation_index.get(srch, 0) + 1) % len(imgs)
            self.ui.fanart_dict_rotation_index[srch] = rotation_index
            url = imgs[rotation_index]
            if url:
                self.ui.posterfound_new(
                    name=title, site="Video", url=url, direct_url=True,
                    copy_summary=False, copy_poster=False, copy_fanart=True
                )
            self._process_next()
        else:
            _, _, series_type = self.ui.media_data.fetch_series_metadata_for_desktop(title)
            self.ui.tvdb_fanart.fetch_fanart(srch, series_type.lower())

    @pyqtSlot(list)
    def _on_fanart_fetched(self, imgs):
        self.ui.logger.info(f"imgs: {imgs}")
        if imgs:
            self.ui.fanart_dict[self.current_srch] = imgs
            self.ui.fanart_dict_rotation_index[self.current_srch] = 0
            self.ui.posterfound_new(
                name=self.current_title, site="Video", url=imgs[0], direct_url=True,
                copy_summary=False, copy_poster=False, copy_fanart=True
            )
        self.processing = False
        self.ui.tvdb_fanart.is_processing = False
        self._process_next()


class TheTVDBPage(QWebEnginePage):
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.load_count = 0
        self.loadFinished.connect(self._on_load_finished)
        self.loadProgress.connect(self._on_load_progress)
        
    def javaScriptConsoleMessage(self, level, msg, line, source):
        pass

    def _on_load_finished(self, ok):
        self.parent.ui.logger.info(f"{ok}")
        self.parent.on_page_ready()

    def _on_load_progress(self, val):
        self.parent.ui.logger.info(val)


class TVDBFanart(QtWidgets.QWidget):
    fanart_done = pyqtSignal(list)
    
    def __init__(self, ui=None):
        super().__init__()
        self.ui = ui
        self.step = 0
        self.images = []
        self.series_url = ""
        self.is_processing = False
        self.browser = None
        self.page = None
        self.callback = None
        self.app = ui.app
        self.current_search_term = ""

    def _sanitize_title(self, title):
        # Step 1: Remove bracketed content
        cleaned = re.sub(r'[\[\(\{].*?[\]\)\}]', '', title)

        # Step 2: Remove season indicators
        cleaned = re.sub(r'\b(?:season|series|s|part|pt)\s*\d{0,2}\b', '', cleaned, flags=re.IGNORECASE)

        # Step 3: Handle special characters
        cleaned = re.sub(r'[-_.]+', ' ', cleaned)

        # Step 4: Clean up spacing
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()

        return cleaned
        
    def fetch_fanart(self, search_term, series_type = 'series', callback=None):
        self.is_processing = True
        self.callback = callback
        self.images = []
        self.series_url = ""
        self.step = 0
        self.is_processing = True
        
        if self.browser is None:

            self.browser = Browser(self.ui, self.ui.home_folder, self.ui.screen_size[0], self.ui.quality_val, "video", self.ui.epn_arr_list)
            self.page = TheTVDBPage(self)
            self.browser.setPage(self.page)
            self.browser.hide()
        
        search_term = self._sanitize_title(search_term)

        formatted_search = search_term.lower().replace(" ", "+")
        self.currrent_search_term = formatted_search.lower()

        if 'movie' in formatted_search or series_type.lower() == 'movie':
            base_url = f"https://thetvdb.com/search?query={formatted_search}&menu[type]=movie"
        else:
            base_url = f"https://thetvdb.com/search?query={formatted_search}&menu[type]=series"
        self.ui.logger.info(base_url)
        self.browser.load(QUrl(base_url))
        
    def on_page_ready(self):
        
        if self.step == 0:
            self.ui.logger.info(f"step 0, {self.page.url().toString()}")
            self.step = 1
            
           
            
            js_code = f"""
            (function() {{
                try {{
                    var searchTerm = {repr(self.current_search_term)};
                    
                    function levenshtein(a, b) {{
                        var dp = Array.from({{length: a.length + 1}}, (_, i) =>
                            Array.from({{length: b.length + 1}}, (_, j) => i === 0 ? j : j === 0 ? i : 0)
                        );
                        for (var i = 1; i <= a.length; i++)
                            for (var j = 1; j <= b.length; j++)
                                dp[i][j] = a[i-1] === b[j-1] ? dp[i-1][j-1] :
                                    1 + Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]);
                        return dp[a.length][b.length];
                    }}
                    
                    var items = document.querySelectorAll('.ais-Hits-item');
                    if (!items.length) return {{ success: false, error: 'No results found' }};
                    
                    var bestScore = Infinity;
                    var bestHref = null;
                    var bestTitle = null;
                    var bestIdx = 0;
                    
                    Array.from(items).forEach(function(item, idx) {{
                        var a = item.querySelector('h3.media-heading a');
                        if (!a) return;
                        var title = a.innerText.trim().toLowerCase();
                        var score = levenshtein(searchTerm, title);
                        if (score < bestScore) {{
                            bestScore = score;
                            bestHref = a.href;
                            bestTitle = title;
                            bestIdx = idx;
                        }}
                    }});
                    
                    if (!bestHref) return {{ success: false, error: 'No valid links found' }};
                    
                    items[bestIdx].querySelector('h3.media-heading a').click();
                    return {{ success: true, series_url: bestHref, matched_title: bestTitle, score: bestScore }};
                    
                }} catch(e) {{
                    return {{ success: false, error: e.message }};
                }}
            }})();
            """

            self.page.runJavaScript(js_code, self._on_js_complete)
            
        elif self.step == 1:
            self.ui.logger.info(f"step 1, {self.page.url().toString()}")
            self.step = 2
            
            js_code = """
            (function() {
                try {
                    var tab = document.querySelector('[role="tab"][href="#artwork"]');
                    if (tab) {
                        var images = Array.from(
                            document.querySelectorAll('#artwork-backgrounds .lightbox')
                        ).map(a => ({
                            url: a.href,
                            description: a.getAttribute('data-description')
                        }));

                        tab.click();

                        return {
                            success: true,
                            images: images,
                            count: images.length
                        };
                    } else {
                        return {
                            success: false,
                            error: 'Artwork tab not found',
                            images: []
                        };
                    }
                } catch(e) {
                    return {
                        success: false,
                        error: e.message,
                        images: []
                    };
                }
            })();
            """
            self.page.runJavaScript(js_code, self.on_js_result)
    
    def _on_js_complete(self, result):
        if isinstance(result, dict) and result.get('success'):
            self.series_url = result.get('series_url', '')
        else:
            self.ui.logger.error(f"failed to find relevant title: {self.page.url().toString()}")
            self.is_processing = False
            self.ui.fanart_queue.processing = False

        
    def on_js_result(self, result):
        if isinstance(result, dict) and result.get('success') and result.get('images'):
            images = result.get('images', [])
            self.images = [img['url'] for img in images]
        
        self.is_processing = False
        self.ui.fanart_queue.processing = False
        self.fanart_done.emit(self.images)
