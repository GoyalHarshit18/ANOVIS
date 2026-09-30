import os
import time
import joblib
import psutil
from pathlib import Path

if __name__ == "__main__":
    process = psutil.Process(os.getpid())
    model_dir = Path("models")

    models = {}

    print("=" * 60)
    print("MODEL MEMORY TEST")
    print("=" * 60)

    before = process.memory_info().rss / 1024 / 1024
    print(f"Initial RAM: {before:.1f} MB")

    files = sorted(model_dir.glob("*.pkl"))

    print(f"Found {len(files)} model files")

    for i, file in enumerate(files, 1):
        print("\n" + "-" * 60)
        print(f"[{i}/{len(files)}] Loading: {file.name}")

        start = time.time()

        try:
            models[file.name] = joblib.load(file)

            ram = process.memory_info().rss / 1024 / 1024
            disk = file.stat().st_size / 1024 / 1024

            print(f"Disk size : {disk:.1f} MB")
            print(f"RAM now   : {ram:.1f} MB")
            print(f"Load time : {time.time() - start:.2f}s")

        except Exception as e:
            print(f"FAILED: {e}")

    final_ram = process.memory_info().rss / 1024 / 1024

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print(f"Models loaded : {len(models)}/{len(files)}")
    print(f"Final RAM     : {final_ram:.1f} MB")
    print("=" * 60)