# Comparative Analysis of Database Encryption: AES vs. RSA

## Project Overview
This project evaluates the performance trade-offs between **Symmetric (AES-256)** and **Asymmetric (RSA-2048)** encryption algorithms for securing sensitive patient data (SSNs) in a SQLite database. 

It measures three key metrics:
1. **Execution Latency:** CPU time for encryption/decryption.
2. **Storage Overhead:** Expansion of database file size.
3. **Scalability:** Performance impact on batches from 1,000 to 10,000 records.

## Tech Stack
- **Language:** Python 3.10
- **Database:** SQLite3
- **Cryptography:** PyCryptodome (AES-EAX, RSA-OAEP)
- **Analysis:** Pandas, Matplotlib

## Project Structure
- `src/generatedummy10kdataset.py`: Generates synthetic patient records.
- `src/run_performance.py`: Executes the encryption benchmark and logs latency.
- `src/measure_storage.py`: Calculates file size overhead and expansion ratios.

## Key Findings
- **AES-256** is significantly faster and more storage-efficient, making it ideal for bulk data encryption.
- **RSA-2048** incurred massive storage overhead (approx. 40x expansion) and high CPU latency, confirming it is unsuitable for bulk database encryption but useful for key exchange.

## How to Run
1. Install dependencies:
   ```bash
   pip install pandas matplotlib pycryptodome
