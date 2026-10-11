#!/bin/bash
# usage: ./chk.sh tag t1 t2 ...  -> /tmp/chk_<tag>.png contact sheet of raw song frames
tag=$1; shift
../../.venv/bin/python engine.py cues/song.py --frames "$@" || exit 1
fs=""; for t in "$@"; do fs="$fs raw_full_$t.png"; done
../../.venv/bin/python sheet.py /tmp/chk_$tag.png $fs && rm -f $fs
