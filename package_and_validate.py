#!/usr/bin/env python3
"""
Automated Packaging & Parity Validation Guard for Brand AI-Readiness Audit.
Ensures brand-ai-readiness-audit.zip is 100% in sync with brand-ai-readiness-audit/,
verifies zero byte-level divergence, runs pyflakes lint hygiene, and executes
full test and benchmark suites.
"""

import os
import sys
import zipfile
import subprocess
import filecmp
import tempfile

ADOBE_ROOT = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.path.join(ADOBE_ROOT, "brand-ai-readiness-audit")
ZIP_PATH = os.path.join(ADOBE_ROOT, "brand-ai-readiness-audit.zip")

EXCLUDED_DIRS = {"__pycache__", ".git", ".pytest_cache", ".idea", ".vscode"}
EXCLUDED_FILES = {".DS_Store", "*.pyc"}

def is_excluded(filename: str) -> bool:
    if filename in EXCLUDED_FILES:
        return True
    if filename.endswith(".pyc"):
        return True
    return False

def package_zip() -> int:
    """Build brand-ai-readiness-audit.zip with exact folder mirroring."""
    print(f"[*] Packaging {SOURCE_DIR} -> {ZIP_PATH}...")
    file_count = 0
    with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for root, dirs, files in os.walk(SOURCE_DIR):
            dirs[:] = [d for d in sorted(dirs) if d not in EXCLUDED_DIRS]
            
            # Record directory entry
            rel_dir = os.path.relpath(root, ADOBE_ROOT)
            if rel_dir != ".":
                z.write(root, arcname=rel_dir + "/")
            
            for f in sorted(files):
                if is_excluded(f):
                    continue
                abs_file = os.path.join(root, f)
                arc_name = os.path.relpath(abs_file, ADOBE_ROOT)
                z.write(abs_file, arcname=arc_name)
                file_count += 1
                
    zip_size_kb = os.path.getsize(ZIP_PATH) / 1024.0
    print(f"[✓] Successfully packaged {file_count} files ({zip_size_kb:.1f} KB) into {os.path.basename(ZIP_PATH)}.")
    return file_count

def validate_parity():
    """Extract zip to a temporary folder and assert 100% byte-for-byte parity."""
    print("[*] Validating 100% parity between working folder and zip archive...")
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(ZIP_PATH, "r") as z:
            z.extractall(tmpdir)
        
        extracted_source = os.path.join(tmpdir, "brand-ai-readiness-audit")
        
        # Compare all files
        mismatches = []
        missing_in_zip = []
        
        for root, dirs, files in os.walk(SOURCE_DIR):
            dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
            for f in files:
                if is_excluded(f):
                    continue
                src_file = os.path.join(root, f)
                rel_path = os.path.relpath(src_file, SOURCE_DIR)
                extracted_file = os.path.join(extracted_source, rel_path)
                
                if not os.path.exists(extracted_file):
                    missing_in_zip.append(rel_path)
                elif not filecmp.cmp(src_file, extracted_file, shallow=False):
                    mismatches.append(rel_path)
        
        if missing_in_zip or mismatches:
            print("[X] PARITY VALIDATION FAILED:")
            if missing_in_zip:
                print(f"    Missing in zip: {missing_in_zip}")
            if mismatches:
                print(f"    Content mismatches: {mismatches}")
            sys.exit(1)
        
        print("[✓] Parity Verified: Zip archive is byte-for-byte identical to the working directory.")

def run_hygiene_and_tests():
    """Run pyflakes linting and full test/benchmark suites."""
    print("[*] Running pyflakes code hygiene check...")
    res = subprocess.run(["pyflakes", SOURCE_DIR], capture_output=True, text=True)
    if res.returncode != 0:
        print("[X] pyflakes found code hygiene issues:")
        print(res.stdout or res.stderr)
        sys.exit(1)
    print("[✓] pyflakes: 0 errors / 0 warnings (100% clean).")

    print("[*] Running test_audit.py regression suite...")
    test_res = subprocess.run([sys.executable, os.path.join(SOURCE_DIR, "test_audit.py")], capture_output=True, text=True)
    if test_res.returncode != 0:
        print("[X] test_audit.py failed:")
        print(test_res.stdout)
        print(test_res.stderr)
        sys.exit(1)
    print(f"[✓] test_audit.py: PASSED (all tests clean).")

    print("[*] Running benchmark_suite.py validation...")
    bench_res = subprocess.run([sys.executable, os.path.join(SOURCE_DIR, "benchmark_suite.py")], capture_output=True, text=True)
    if bench_res.returncode != 0:
        print("[X] benchmark_suite.py failed:")
        print(bench_res.stdout)
        print(bench_res.stderr)
        sys.exit(1)
    print("[✓] benchmark_suite.py: PASSED (100% schema compliance & ground truth accuracy).")

if __name__ == "__main__":
    package_zip()
    validate_parity()
    run_hygiene_and_tests()
    print("\n" + "=" * 80)
    print(" ALL AUDIT & PARITY CHECKS PASSED: READY FOR COMPETITION SUBMISSION")
    print("=" * 80)
