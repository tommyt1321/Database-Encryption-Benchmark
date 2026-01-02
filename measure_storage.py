import sqlite3
import os
import pandas as pd
import matplotlib.pyplot as plt

# --- CONFIGURATION ---
SOURCE_DB = "hospital.db"
SOURCE_TABLE = "Encryption_Results"  # The table created by your Performance Test

DB_NAMES = {
    "Plain": "storage_control.db",
    "AES": "storage_aes.db",
    "RSA": "storage_rsa.db"
}

print(f"STARTING FINAL STORAGE ANALYSIS (Detailed Breakdown)...")
print(f"SOURCE: {SOURCE_DB} -> Table: {SOURCE_TABLE}")
print("=" * 80)

# --- CLEANUP (Delete old files) ---
for name in DB_NAMES.values():
    if os.path.exists(name):
        os.remove(name)

# --- 1. FETCH THE PRE-GENERATED DATA ---
try:
    conn = sqlite3.connect(SOURCE_DB)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (SOURCE_TABLE,))
    if not cursor.fetchone():
        print(f"ERROR: Table '{SOURCE_TABLE}' not found in {SOURCE_DB}!")
        print("   Run your Performance Test script first to generate this table.")
        exit()

    print("Fetching existing encrypted records...")
    cursor.execute(f"SELECT Original_SSN, AES_Encrypted_Hex, RSA_Encrypted_Hex FROM {SOURCE_TABLE}")
    rows = cursor.fetchall()
    conn.close()
    
    row_count = len(rows)
    print(f" Loaded {row_count} records.")
    
    if row_count == 0:
        print(" ERROR: The table is empty.")
        exit()

except Exception as e:
    print(f" Database Error: {e}")
    exit()

# --- 2. BUILD THE STORAGE TEST FILES ---
print("\nWriting to clean database files and calculating payload size...")

# Initialize counters for Raw Text Size (The "Water")
total_text_bytes = {"Plain": 0, "AES": 0, "RSA": 0}

# Setup connections
conns = {k: sqlite3.connect(v) for k, v in DB_NAMES.items()}
cursors = {k: c.cursor() for k, c in conns.items()}

# Create Tables
for c in cursors.values():
    c.execute("CREATE TABLE Patients (ID INTEGER PRIMARY KEY, SSN TEXT)")

# Insert Data & Count Bytes Loop
for i, (original, aes_hex, rsa_hex) in enumerate(rows):
    # A. Plaintext
    cursors["Plain"].execute("INSERT INTO Patients (SSN) VALUES (?)", (original,))
    total_text_bytes["Plain"] += len(original) # Measure raw string length

    # B. AES
    cursors["AES"].execute("INSERT INTO Patients (SSN) VALUES (?)", (aes_hex,))
    total_text_bytes["AES"] += len(aes_hex)

    # C. RSA
    cursors["RSA"].execute("INSERT INTO Patients (SSN) VALUES (?)", (rsa_hex,))
    total_text_bytes["RSA"] += len(rsa_hex)

# Commit & Close
for conn in conns.values():
    conn.commit()
    conn.close()

print("Storage Files Created Successfully.")

# --- 3. MEASURE & ANALYZE (With Expansion Ratio) ---
print("\nFINAL DISK FOOTPRINT ANALYSIS:")
print("-" * 100)
print(f"{'Type':<10} | {'Sum of TEXT Only':<18} | {'Real DB FILE Size':<18} | {'Database Overhead':<18} | {'Expansion Ratio':<15}")

stats = {"Type": [], "Size_KB": []}
base_file_kb = os.path.getsize(DB_NAMES["Plain"]) / 1024  # Baseline for Ratio

for name, filename in DB_NAMES.items():
    # 1. Calculate Raw Text Size in KB
    text_kb = total_text_bytes[name] / 1024
    
    # 2. Calculate Actual File Size in KB
    file_kb = os.path.getsize(filename) / 1024
    
    # 3. Calculate Overhead (File - Text)
    overhead_kb = file_kb - text_kb
    
    # 4. Calculate Expansion Ratio (Current File / Plaintext File)
    if base_file_kb > 0:
        ratio = file_kb / base_file_kb
    else:
        ratio = 0
    
    stats["Type"].append(name)
    stats["Size_KB"].append(file_kb)
    print(f"{name:<10} | {text_kb:.2f} KB           | {file_kb:.2f} KB           | {overhead_kb:.2f} KB           | {ratio:.2f}x")

# --- 4. GENERATE GRAPH ---
df = pd.DataFrame(stats)
plt.figure(figsize=(9, 6))

# Simple Bar Chart showing Total File Size
bars = plt.bar(df["Type"], df["Size_KB"], color=['green', 'blue', 'red'], edgecolor='black', alpha=0.8)

# Add labels
for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 50, f'{yval:.0f} KB', ha='center', va='bottom', fontweight='bold')

plt.title(f"Total Disk Usage Comparison ({row_count} Records)")
plt.ylabel("Disk Usage (KB)")
plt.grid(axis='y', linestyle='--', alpha=0.5)

plt.savefig("Graph3_Final_Storage.png")
print("\nDONE! Saved 'Graph3_Final_Storage.png'")