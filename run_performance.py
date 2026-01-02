import sqlite3
import time
import pandas as pd
import matplotlib.pyplot as plt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes

# --- CONFIGURATION ---
DB_FILE = "hospital.db"
BATCH_SIZES = [1000, 3000, 5000, 7000, 10000]

# --- SETUP ENCRYPTION KEYS ---
print("Setting up Encryption Keys...")
# 1. AES Key (Symmetric)
aes_key = Fernet.generate_key()
aes_cipher = Fernet(aes_key)

# 2. RSA Keys (Asymmetric)
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

def run_aes_test(data):
    # --- AES ENCRYPTION ---
    encrypted_data = []
    start = time.perf_counter() 
    for text in data:
        encrypted_data.append(aes_cipher.encrypt(text.encode()))
    end = time.perf_counter()
    enc_time = end - start

    # --- AES DECRYPTION ---
    start = time.perf_counter()
    for enc_text in encrypted_data:
        aes_cipher.decrypt(enc_text)
    end = time.perf_counter()
    dec_time = end - start

    return enc_time, dec_time, encrypted_data

def run_rsa_test(data):
    # --- RSA ENCRYPTION ---
    encrypted_data = []
    start = time.perf_counter()
    for text in data:
        encrypted_data.append(public_key.encrypt(
            text.encode(),
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        ))
    end = time.perf_counter()
    enc_time = end - start

    # --- RSA DECRYPTION ---
    start = time.perf_counter()
    for enc_text in encrypted_data:
        private_key.decrypt(
            enc_text,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
    end = time.perf_counter()
    dec_time = end - start
    
    return enc_time, dec_time, encrypted_data

# --- MAIN EXECUTION ---
try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    results = {
        "Batch Size": [], 
        "AES Enc (s)": [], "AES Dec (s)": [],
        "RSA Enc (s)": [], "RSA Dec (s)": []
    }
    
    # Variables to hold the final batch data for the database
    final_original_data = []
    final_aes_blobs = []
    final_rsa_blobs = []

    print(f"\n{'Batch':<8} | {'AES Enc':<10} | {'AES Dec':<10} | {'RSA Enc':<10} | {'RSA Dec':<10}")
    print("-" * 65)

    for size in BATCH_SIZES:
        # Fetch Data
        cursor.execute(f"SELECT ssn FROM Patients LIMIT {size}")
        rows = cursor.fetchall()
        
        if not rows:
            print(f"Error: No data found for size {size}")
            continue
            
        data = [str(r[0]) for r in rows]

        # Run Tests
        aes_enc, aes_dec, aes_blobs = run_aes_test(data)
        rsa_enc, rsa_dec, rsa_blobs = run_rsa_test(data)

        # Save Results for Graph
        results["Batch Size"].append(size)
        results["AES Enc (s)"].append(aes_enc)
        results["AES Dec (s)"].append(aes_dec)
        results["RSA Enc (s)"].append(rsa_enc)
        results["RSA Dec (s)"].append(rsa_dec)

        # Print to Console
        print(f"{size:<8} | {aes_enc:.4f}s    | {aes_dec:.4f}s    | {rsa_enc:.4f}s    | {rsa_dec:.4f}s")

        # If this is the 10,000 batch, save the data for the Database Table
        if size == 10000:
            final_original_data = data
            final_aes_blobs = aes_blobs
            final_rsa_blobs = rsa_blobs

    # --- SAVE ENCRYPTION RESULTS TO DATABASE ---
    print("\nSaving 10,000 Encrypted Records to table 'Encryption_Results'...")
    cursor.execute("DROP TABLE IF EXISTS Encryption_Results")
    cursor.execute("""
        CREATE TABLE Encryption_Results (
            Original_SSN TEXT, 
            AES_Encrypted_Hex TEXT, 
            RSA_Encrypted_Hex TEXT
        )
    """)
    
    # Convert binary blobs to Hex strings for readable storage
    evidence_data = []
    for i in range(len(final_original_data)):
        evidence_data.append((
            final_original_data[i],
            final_aes_blobs[i].hex(),  # Convert AES bytes to Hex
            final_rsa_blobs[i].hex()   # Convert RSA bytes to Hex
        ))

    cursor.executemany("INSERT INTO Encryption_Results VALUES (?, ?, ?)", evidence_data)
    conn.commit()
    conn.close()
    print("Database Updated! Check table 'Encryption_Results'.")

    # --- DRAW GRAPHS ---
    if results["Batch Size"]:
        df = pd.DataFrame(results)

        # Graph 1: Encryption
        plt.figure(figsize=(10, 6))
        plt.plot(df["Batch Size"], df["AES Enc (s)"], marker='o', label='AES Encrypt', color='blue')
        plt.plot(df["Batch Size"], df["RSA Enc (s)"], marker='x', label='RSA Encrypt', color='red', linestyle='--')
        plt.title("Encryption Speed: AES vs RSA")
        plt.xlabel("Records")
        plt.ylabel("Time (Seconds)")
        plt.legend()
        plt.grid(True)
        plt.savefig("Graph1_Encryption.png")
        print("Saved Graph1_Encryption.png")

        # Graph 2: Decryption
        plt.figure(figsize=(10, 6))
        plt.plot(df["Batch Size"], df["AES Dec (s)"], marker='o', label='AES Decrypt', color='blue')
        plt.plot(df["Batch Size"], df["RSA Dec (s)"], marker='x', label='RSA Decrypt', color='red', linestyle='--')
        plt.title("Decryption Speed: AES vs RSA")
        plt.xlabel("Records")
        plt.ylabel("Time (Seconds)")
        plt.legend()
        plt.grid(True)
        plt.savefig("Graph2_Decryption.png")
        print("Saved Graph2_Decryption.png")

except Exception as e:
    print(f"\nAn error occurred: {e}")