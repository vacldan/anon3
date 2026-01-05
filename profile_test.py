#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick profiling test to find bottlenecks"""

import cProfile
import pstats
from io import StringIO
import sys

# Import the optimized version
from anon_optimized import Anonymizer, load_names_library, CZECH_FIRST_NAMES

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
