"""Test harness: loads index.html with ?test=1 in headless Chromium and evaluates engine code inside the app.

Everything runs against the real application code. Timers are replaced by a queue (engine_helpers.js), and all
randomness goes through RNG(), which tests seed with seedRNG(n), so every run is reproducible.
"""
import json, math, os, subprocess, sys, time, traceback
from playwright.sync_api import sync_playwright

TESTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TESTS)
INDEX = os.environ.get('HOLDEM_INDEX', os.path.join(ROOT, 'index.html'))   # tests can target a modified copy
URL = 'file://' + INDEX + '?test=1'
FIX = os.path.join(TESTS, 'fixtures', 'reference_equities.json')

class KnownFailure(Exception):
    """Raised by a test that documents a defect we have not fixed yet. Reported separately, never hidden."""

def known_failure(reason):
    def deco(fn):
        fn.known_failure = reason
        return fn
    return deco

class Engine:
    def __init__(self):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch()
        self.page = self._browser.new_page()
        self.errors = []
        self.page.on('pageerror', lambda e: self.errors.append(str(e)))
        self.reset()

    def reset(self):
        self.page.goto(URL)
        self.page.wait_for_function('typeof window.__dbg==="function"')
        helpers = open(os.path.join(TESTS, 'engine_helpers.js'), encoding='utf-8').read()
        self.page.evaluate('c=>window.__dbg(c)', helpers)

    def js(self, expr):
        """Evaluate a JS expression inside the app and return it as Python data (it must be JSON-friendly)."""
        r = self.page.evaluate('c=>{var v=window.__dbg(c);return JSON.stringify(v===undefined?null:v);}', expr)
        return json.loads(r)

    def run(self, body):
        """Run a JS function body (with `return`) inside the app."""
        return self.js('(function(){' + body + '})()')

    def close(self):
        self._browser.close(); self._pw.stop()

_ENGINE = None
def engine(fresh=False):
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = Engine()
    elif fresh:
        _ENGINE.reset()
    return _ENGINE

def fixtures():
    if not os.path.exists(FIX):
        raise FileNotFoundError('missing ' + FIX + '. Generate it with: python3 tests/make_fixtures.py')
    return json.load(open(FIX))

def card_id(s): return '23456789TJQKA'.index(s[0]) * 4 + 'shdc'.index(s[1])
