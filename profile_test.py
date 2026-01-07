#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick profiling test to find bottlenecks"""

import cProfile
import pstats
from io import StringIO
import sys
import importlib.util

# Import anon7.2
spec = importlib.util.spec_from_file_location("anon72", "anon7.2 - s padama.py")
anon72 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(anon72)

Anonymizer = anon72.Anonymizer
load_names_library = anon72.load_names_library
CZECH_FIRST_NAMES = anon72.CZECH_FIRST_NAMES

def run_anonymization():
    """Run anonymization with profiling"""
    global CZECH_FIRST_NAMES
    CZECH_FIRST_NAMES = load_names_library("cz_names.v1.json")

    anonymizer = Anonymizer(verbose=False)
    anonymizer.anonymize_docx(
        "smlouva32.docx",
        "smlouva32_anon_profile.docx",
        "smlouva32_map_profile.json",
        "smlouva32_map_profile.txt"
    )

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    run_anonymization()

    profiler.disable()

    # Print stats
    stats = pstats.Stats(profiler, stream=sys.stdout)
    stats.strip_dirs()
    stats.sort_stats('cumulative')

    print("\n" + "="*80)
    print("TOP 30 SLOWEST FUNCTIONS (by cumulative time):")
    print("="*80)
    stats.print_stats(30)

    print("\n" + "="*80)
    print("TOP 30 SLOWEST FUNCTIONS (by total time):")
    print("="*80)
    stats.sort_stats('tottime')
    stats.print_stats(30)
