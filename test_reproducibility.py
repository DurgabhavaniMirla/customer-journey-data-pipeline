import os
import hashlib
import subprocess

def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

print("=" * 60)
print(" REPRODUCIBILITY AUDIT ")
print("=" * 60)

target_file = "journey_event.csv"

# 1. Get initial hash
if not os.path.exists(target_file):
    print(f"[Error] {target_file} not found. Run generate_journey_data.py first.")
    exit(1)
    
hash_run_1 = get_file_hash(target_file)
print(f"[Run 1] {target_file} MD5 Checksum: {hash_run_1}")

# 2. Trigger second run
print("[Info] Triggering second generation run. Please wait (~60 seconds)...")
subprocess.run(["python", "generate_journey_data.py"], check=True)

# 3. Get new hash
hash_run_2 = get_file_hash(target_file)
print(f"[Run 2] {target_file} MD5 Checksum: {hash_run_2}")

# 4. Compare
if hash_run_1 == hash_run_2:
    print("[SUCCESS] Files match exactly. Pipeline is 100% deterministic and reproducible.")
else:
    print("[FAIL] Checksums differ. Pipeline is not strictly deterministic.")