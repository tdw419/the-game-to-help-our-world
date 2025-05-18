# black-vault/backup_benchmark.py

import os
import time
from encoder import encode_file_to_image


def benchmark_file(file_path, output_image_path):
    print(f"Benchmarking: {file_path}")
    original_size = os.path.getsize(file_path)
    print(f"Original Size: {original_size / (1024 * 1024):.2f} MB")

    start_time = time.time()
    encode_file_to_image(file_path, output_image_path, compress=True)
    end_time = time.time()

    backup_size = os.path.getsize(output_image_path)
    print(f"Backup Image Size: {backup_size / (1024 * 1024):.2f} MB")
    print(f"Time Taken: {end_time - start_time:.2f} seconds")

    compression_ratio = backup_size / original_size
    print(f"Compression Ratio: {compression_ratio:.2f}")
    print("-" * 40)


if __name__ == "__main__":
    # Example usage
    test_files = [
        "sample_music.mp3",
        # Add more test files here
    ]

    for file in test_files:
        if os.path.exists(file):
            output_file = file + ".png"
            benchmark_file(file, output_file)
        else:
            print(f"File not found: {file}")
