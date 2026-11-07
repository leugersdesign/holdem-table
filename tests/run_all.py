"""Run the whole suite:  python3 tests/run_all.py   (no pytest needed; the test files are also pytest-compatible).

Exit code 0 means every test passed. Known failures (documented defects not fixed yet) are listed separately and do
not fail the run, but they are never hidden. Seeds are fixed inside the tests, so a failure reproduces.
"""
import importlib, os, sys, time, traceback
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
MODULES = ['test_evaluator', 'test_equity', 'test_ranges', 'test_ev', 'test_engine', 'test_opponents', 'test_strategy', 'test_coaching', 'test_reliability', 'test_adversarial', 'test_rules']

def main(only=None):
    passed = []; failed = []; known = []; t0 = time.time()
    for m in MODULES:
        if only and m not in only: continue
        mod = importlib.import_module(m)
        for name in sorted(n for n in dir(mod) if n.startswith('test_')):
            fn = getattr(mod, name); t = time.time()
            try:
                fn(); passed.append((m, name, time.time() - t)); print('PASS   %s.%s  (%.1fs)' % (m, name, time.time() - t), flush=True)
            except Exception as ex:
                if hasattr(fn, 'known_failure'):
                    known.append((m, name, fn.known_failure)); print('KNOWN  %s.%s' % (m, name), flush=True)
                else:
                    failed.append((m, name, ex)); print('FAIL   %s.%s\n%s' % (m, name, ''.join(traceback.format_exception_only(type(ex), ex)).strip()[:600]), flush=True)
    print('\n%d passed, %d failed, %d known failures, %.0fs' % (len(passed), len(failed), len(known), time.time() - t0))
    for m, n, why in known: print('  known: %s.%s: %s' % (m, n, why))
    return 1 if failed else 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:] or None))
