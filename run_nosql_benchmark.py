import time
import pandas as pd
import matplotlib.pyplot as plt
from pymongo import MongoClient
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes

# --- CONFIGURATION ---
DB_NAME = "Hospital_IoT_DB"
COLLECTION_NAME = "patient_logs"
MONGO_URI = "mongodb://localhost:27017/"

# --- SETUP MONGODB ---
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# --- CRYPTO SETUP ---
aes_key = get_random_bytes(32) # 256-bit key
rsa_key = RSA.generate(2048)
public_key = rsa_key.publickey()
cipher_rsa_encrypt = PKCS1_OAEP.new(public_key)
cipher_rsa_decrypt = PKCS1_OAEP.new(rsa_key)

# --- HELPER FUNCTIONS ---
def generate_iot_data(num_records):
    data = []
    for i in range(num_records):
        record = {
            "device_id": f"DEV-{i}",
            "timestamp": time.time(),
            "vitals": {"bpm": 70 + (i % 30), "temp": 36.5},
            "patient_ssn": f"999-00-{1000+i}"
        }
        data.append(record)
    return data

def get_logical_size():
    # Force MongoDB to update stats
    db.command("collStats", COLLECTION_NAME)
    stats = db.command("collstats", COLLECTION_NAME)
    # Use 'size' (Logical Data Size) instead of 'storageSize' (Disk Allocation)
    return stats['size'] / 1024  # Return in KB

def run_benchmark():
    batch_sizes = [1000, 3000, 5000, 7000, 10000]
    results = []
    final_storage = {}

    print("--- Starting NoSQL (MongoDB) Benchmark ---")

    # 1. CAPTURE "BEFORE" DATA
    print("\n--- GENERATING RAW DATA SAMPLE ---")
    raw_sample = generate_iot_data(1)
    print("Raw JSON Document (Before Encryption):")
    print(raw_sample[0])
    print("--------------------------------------------\n")

    # 2. BASELINE (PLAIN TEXT) - 10k Records
    print("Measuring Baseline Storage (10,000 records)...")
    raw_data = generate_iot_data(10000)
    collection.drop()
    collection.insert_many(raw_data)
    final_storage["Plain JSON"] = get_logical_size()
    print(f"Plain Storage: {final_storage['Plain JSON']:.2f} KB")

    # 3. PERFORMANCE LOOP
    for n in batch_sizes:
        print(f"Processing Batch: {n} records... (Encrypting)")
        raw_data = generate_iot_data(n)
        
        # --- AES BENCHMARK ---
        start = time.perf_counter()
        aes_docs = []
        for doc in raw_data:
            cipher_aes = AES.new(aes_key, AES.MODE_EAX)
            ciphertext, tag = cipher_aes.encrypt_and_digest(doc["patient_ssn"].encode('utf-8'))
            new_doc = doc.copy()
            new_doc["patient_ssn"] = ciphertext.hex()
            new_doc["nonce"] = cipher_aes.nonce.hex()
            aes_docs.append(new_doc)
        
        collection.drop()
        collection.insert_many(aes_docs)
        aes_enc_time = time.perf_counter() - start

        # Capture AES Storage only at max load (10k)
        if n == 10000:
            final_storage["AES-256"] = get_logical_size()

        # Decrypt AES
        start = time.perf_counter()
        docs = list(collection.find())
        for doc in docs:
            nonce = bytes.fromhex(doc["nonce"])
            ciphertext = bytes.fromhex(doc["patient_ssn"])
            cipher = AES.new(aes_key, AES.MODE_EAX, nonce=nonce)
            plaintext = cipher.decrypt(ciphertext)
        aes_dec_time = time.perf_counter() - start

        # --- RSA BENCHMARK ---
        start = time.perf_counter()
        rsa_docs = []
        for doc in raw_data:
            ciphertext = cipher_rsa_encrypt.encrypt(doc["patient_ssn"].encode('utf-8'))
            new_doc = doc.copy()
            new_doc["patient_ssn"] = ciphertext.hex()
            rsa_docs.append(new_doc)
        
        collection.drop()
        collection.insert_many(rsa_docs)
        rsa_enc_time = time.perf_counter() - start

        # Capture RSA Storage only at max load (10k)
        if n == 10000:
            final_storage["RSA-2048"] = get_logical_size()

        # Decrypt RSA
        start = time.perf_counter()
        docs = list(collection.find())
        for doc in docs:
            ciphertext = bytes.fromhex(doc["patient_ssn"])
            plaintext = cipher_rsa_decrypt.decrypt(ciphertext)
        rsa_dec_time = time.perf_counter() - start

        results.append({
            "Records": n,
            "AES_Enc": aes_enc_time, "AES_Dec": aes_dec_time,
            "RSA_Enc": rsa_enc_time, "RSA_Dec": rsa_dec_time
        })

    # --- SAVE GRAPHS ---
    df = pd.DataFrame(results)
    
    # 1. Encryption Graph
    plt.figure(figsize=(10, 6))
    plt.plot(df["Records"], df["AES_Enc"], marker='o', label='AES (NoSQL)', color='blue')
    plt.plot(df["Records"], df["RSA_Enc"], marker='x', linestyle='--', label='RSA (NoSQL)', color='red')
    plt.title("Encryption Speed (Latency): AES vs RSA")
    plt.xlabel("Number of Documents")
    plt.ylabel("Time (Seconds)")
    plt.legend()
    plt.grid()
    plt.savefig("NoSQL_Graph1_Encryption.png")

    # 2. Decryption Graph
    plt.figure(figsize=(10, 6))
    plt.plot(df["Records"], df["AES_Dec"], marker='o', label='AES (NoSQL)', color='blue')
    plt.plot(df["Records"], df["RSA_Dec"], marker='x', linestyle='--', label='RSA (NoSQL)', color='red')
    plt.title("Decryption Speed (Latency): AES vs RSA")
    plt.xlabel("Number of Documents")
    plt.ylabel("Time (Seconds)")
    plt.legend()
    plt.grid()
    plt.savefig("NoSQL_Graph2_Decryption.png")
    
    # 3. Storage Graph (Bar Chart)
    plt.figure(figsize=(8, 6))
    plt.bar(final_storage.keys(), final_storage.values(), color=['green', 'blue', 'red'])
    plt.title("Data Storage Consumption (10,000 Records)")
    plt.ylabel("Size in Kilobytes (KB)")
    plt.grid(axis='y')
    for i, v in enumerate(final_storage.values()):
        plt.text(i, v + 50, f"{v:.1f} KB", ha='center', fontweight='bold')
    plt.savefig("NoSQL_Graph3_Storage.png")

    # Print Results
    print("\n--- TIMING RESULTS ---")
    print(df)
    print("\n--- STORAGE RESULTS (Logical Data Size) ---")
    print(final_storage)
    print("\nDone! 3 Graphs saved.")

if __name__ == "__main__":
    run_benchmark()