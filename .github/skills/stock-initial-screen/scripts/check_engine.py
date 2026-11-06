#!/usr/bin/env python3
"""Engine guard (v4.11.2, Codex): the screen runs only on the engine files the user approved.

    python3 check_engine.py RUN_DIR            -> exit 0 when every engine file in RUN_DIR matches CHECKSUMS.txt, else exit 1

CHECKSUMS.txt sits next to this script (the skill's scripts/ folder) and lists the full SHA-256 of each engine file. Run it after copying
the engine into the run folder (Step 0), again right before `screener.py build`, and again right before `make_html.py`. A mismatch means
the engine was changed during the run: stop, restore the file from the skill folder, and report the problem to the user instead of patching
the code. Rules and code change only in a new skill version the user approved.
"""
import hashlib, os, sys
here = os.path.dirname(os.path.abspath(__file__))
run = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.getcwd()
ck = os.path.join(here, 'CHECKSUMS.txt')
if not os.path.exists(ck): sys.exit(f'CHECKSUMS.txt not found next to {__file__}')
bad, ok = [], 0
for line in open(ck):
    line = line.strip()
    if not line or line.startswith('#'): continue
    h, f = line.split(None, 1)
    p = os.path.join(run, f)
    if not os.path.exists(p): bad.append(f'{f}: missing in {run}'); continue
    got = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    if got != h: bad.append(f'{f}: changed (expected {h[:16]}, found {got[:16]})')
    else: ok += 1
if bad:
    print('ENGINE CHANGED — stop the run. Restore these files from the skill folder (scripts/ and references/) and tell the user what you wanted to change and why:')
    for b in bad: print('  ' + b)
    sys.exit(1)
print(f'engine ok: {ok} files match CHECKSUMS.txt')
