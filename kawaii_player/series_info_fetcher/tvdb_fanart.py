import sys
import re
from PyQt5 import QtWidgets
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtCore import QUrl, pyqtSlot, pyqtSignal, QTimer


class TheTVDBPage(QWebEnginePage):
    page_loaded = pyqtSignal(str)
    js_result = pyqtSignal(object)
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent_view = parent
        self.load_count = 0
        self.loadFinished.connect(self._on_load_finished)
        
    def javaScriptConsoleMessage(self, level, msg, line, source):
        pass

    def _on_load_finished(self, ok):
        if ok:
            self.load_count += 1
            QTimer.singleShot(2000, lambda: self.page_loaded.emit("ready"))


class TVDBFanart(QtWidgets.QWidget):
    
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
        self.app = None

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
        self.callback = callback
        self.images = []
        self.series_url = ""
        self.step = 0
        self.is_processing = True
        
        self.app = QtWidgets.QApplication.instance()
        if self.app is None:
            self.app = QtWidgets.QApplication(sys.argv)
        
        if self.browser is None:
            self.browser = QWebEngineView()
            self.page = TheTVDBPage(self)
            self.browser.setPage(self.page)
            
            self.page.page_loaded.connect(self._handle_page_loaded)
            self.page.js_result.connect(self._handle_js_result)
            
            self.browser.hide()
        
        search_term = self._sanitize_title(search_term)

        formatted_search = search_term.lower().replace(" ", "+")

        if 'movie' in formatted_search or series_type.lower() == 'movie':
            base_url = f"https://thetvdb.com/search?query={formatted_search}&menu[type]=movie"
        else:
            base_url = f"https://thetvdb.com/search?query={formatted_search}&menu[type]=series"
        print(base_url)
        self.browser.load(QUrl(base_url))
        
        count = 0
        while self.is_processing:
            self.app.processEvents()
            count += 1
            if count > 3000000:
                print('not-found')
                break

        print(count, "cc")
        
        return self.images
    
    @pyqtSlot()
    def _handle_page_loaded(self):
        self.on_page_ready()
    
    @pyqtSlot(object)
    def _handle_js_result(self, result):
        self.on_js_result(result)
    
    def on_page_ready(self):
        if not self.is_processing:
            return
        
        if self.step == 0:
            self.step = 1
            
            js_code = """
            (function() {
                try {
                    var link = document.querySelector('.ais-Hits-list a');
                    if (link) {
                        var href = link.href;
                        link.click();
                        return {
                            success: true,
                            series_url: href
                        };
                    } else {
                        return { success: false, error: 'First result not found' };
                    }
                } catch(e) {
                    return { success: false, error: e.message };
                }
            })();
            """
            self.page.runJavaScript(js_code, self._on_js_complete)
            
        elif self.step == 1:
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
        
        QTimer.singleShot(3000, lambda: None)
    
    def on_js_result(self, result):
        if isinstance(result, dict) and result.get('success') and result.get('images'):
            images = result.get('images', [])
            self.images = [img['url'] for img in images]
        
        self.is_processing = False
        
        if self.callback:
            error = None if self.images else "No images found"
            self.callback(self.images, self.series_url, error)
