#!/usr/bin/env python3
"""
fingerprint.py
--------------
• Parallel CPU MFCC fingerprinting + duplicate detection
• Logs every unreadable / too-short / mpg123-warning file
• Saves ALL fingerprints to fingerprints.npz
• Resume-safe duplicates.csv (original, duplicate)
"""

import os, csv, sys, warnings, io, contextlib, multiprocessing as mp
from multiprocessing import Pool, Lock
import numpy as np, torchaudio, librosa
from tqdm import tqdm

# ── suppress torchaudio fallback chatter ────────────────────────
warnings.filterwarnings("ignore", message="PySoundFile failed*")
warnings.filterwarnings("ignore", message=".*libmpg123.*")
# ────────────────────────────────────────────────────────────────

# Tunables ───────────────────────────────────────────────────────
SAMPLE_RATE       = 22_050
N_MFCC            = 20
MIN_DURATION_SEC  = 0.5
N_FFT_DEFAULT     = 2048
N_FFT_SMALL       = 512
HOP_LENGTH        = 256
DIST_THRESHOLD    = 45.0
CHUNKSIZE         = 8
FINGERPRINT_FILE  = "fingerprints.npz"
# ----------------------------------------------------------------

csv_lock = err_lock = None
def init_worker(lock_csv, lock_err):
    global csv_lock, err_lock
    csv_lock = lock_csv
    err_lock = lock_err

def log_error(path: str, msg: str):
    with err_lock:
        with open("error_log.txt", "a") as ef:
            ef.write(f"{path}\t{msg}\n")

def process_file(path: str):
    """
    Return (path, fingerprint) or None.
    ALSO logs a WARN entry if mpg123 prints 'dequantization failed!'.
    """
    try:
        # capture mpg123 stderr
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            wav, sr = torchaudio.load(path)
        if "dequantization failed" in buf.getvalue():
            log_error(path, "WARN mpg123 dequantization failed (decoded)")

        if wav.shape[0] > 1:
            wav = wav.mean(dim=0, keepdim=True)
        y = wav.squeeze().numpy()

        dur = len(y) / sr
        if dur < MIN_DURATION_SEC:
            log_error(path, f"SKIPPED too short ({dur:.3f}s)")
            return None

        if sr != SAMPLE_RATE:
            y = librosa.resample(y, sr, SAMPLE_RATE); sr = SAMPLE_RATE

        n_fft = N_FFT_DEFAULT if len(y) >= N_FFT_DEFAULT else N_FFT_SMALL
        if len(y) < n_fft:
            y = np.pad(y, (0, n_fft - len(y)))

        mfcc = librosa.feature.mfcc(
            y=y, sr=sr, n_mfcc=N_MFCC,
            n_fft=n_fft, hop_length=HOP_LENGTH)
        fp = mfcc.mean(axis=1).astype(np.float32)
        return path, fp

    except Exception as e:
        log_error(path, f"ERROR {type(e).__name__}: {e}")
        return None

def main():
    mp.set_start_method("forkserver", force=True)  # fast process spawn

    import argparse, pathlib
    pa = argparse.ArgumentParser()
    pa.add_argument("audio_dir")
    pa.add_argument("--workers", type=int, default=os.cpu_count())
    pa.add_argument("--threshold", type=float, default=DIST_THRESHOLD)
    pa.add_argument("--csv", default="duplicates.csv")
    pa.add_argument("--error_log", default="error_log.txt")
    args = pa.parse_args()

    # resume support
    processed = set()
    if os.path.exists(args.csv):
        with open(args.csv) as f:
            for r in csv.reader(f):
                processed.update(r)

    # gather mp3 paths
    targets = [str(p) for p in pathlib.Path(args.audio_dir).rglob("*.mp3")
               if str(p) not in processed]
    if not targets:
        print("Nothing new to process."); return

    open(args.csv, "a").close()
    open(args.error_log, "a").close()

    uniq_feats = np.empty((len(targets), N_MFCC), np.float32)
    uniq_paths = []
    uniq_cnt = dup_cnt = 0

    all_paths = []
    all_feats = []

    lock_csv = Lock(); lock_err = Lock()
    with Pool(args.workers, init_worker, (lock_csv, lock_err)) as pool:
        for res in tqdm(pool.imap_unordered(process_file, targets,
                                            chunksize=CHUNKSIZE),
                        total=len(targets), desc="Processing"):
            if res is None:
                continue
            path, fp = res
            # record fingerprint
            all_paths.append(path)
            all_feats.append(fp)

            if uniq_cnt:
                d2 = np.sum((uniq_feats[:uniq_cnt] - fp) ** 2, 1)
                hit = np.where(d2 < args.threshold ** 2)[0]
                if hit.size:
                    orig = uniq_paths[int(hit[0])]
                    with lock_csv:
                        with open(args.csv, "a", newline="") as cf:
                            csv.writer(cf).writerow([orig, path])
                    dup_cnt += 1
                    continue

            uniq_feats[uniq_cnt] = fp
            uniq_paths.append(path)
            uniq_cnt += 1

    # ---- save fingerprints --------------------------------------
    if not all_feats:
        print("No fingerprints collected! "
              "Check torchaudio backend or MIN_DURATION_SEC.")
        return
    np.savez_compressed(
        FINGERPRINT_FILE,
        paths=np.array(all_paths, dtype=object),
        feats=np.vstack(all_feats)
    )
    # --------------------------------------------------------------

    warn_err_lines = sum(1 for _ in open(args.error_log))
    print("\nSummary")
    print(f"  decoded OK : {len(all_paths)}")
    print(f"  uniques    : {uniq_cnt}")
    print(f"  duplicates : {dup_cnt}")
    print(f"  warnings/errors logged : {warn_err_lines}")
    print(f"\nFingerprints → {FINGERPRINT_FILE}")
    print(f"Duplicates   → {args.csv}")
    print(f"Errors / skips→ {args.error_log}")

if __name__ == "__main__":
    main()
