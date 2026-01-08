# Performance Analysis of NoSQL Ingestion Latency for Secure Medical IoT Streams

## Project Overview
This research project investigates the computational overhead of end-to-end encryption on high-velocity NoSQL database ingestion.

In modern healthcare IoT environments, the migration from SQL to NoSQL (MongoDB) is driven by the need for high write throughput and schema flexibility. However, regulatory standards (HIPAA/GDPR) mandate strict encryption, which often acts as a bottleneck.

This repository contains the benchmarking suite used to quantify the specific trade-offs between Symmetric (AES-256) and Asymmetric (RSA-2048) encryption when applied to unstructured JSON payloads before ingestion into a MongoDB document store.

## Key Features & NoSQL Utilization
* **Schema-Agnostic Storage:** Utilizes MongoDB's BSON document structure to store nested IoT sensor data ("vitals" object) without rigid schema constraints.
* **High-Velocity Simulation:** Implements a Python-based client emulator that generates and ingests synthetic patient records in bulk batches (up to 10,000 records) to test write latency.
* **Cryptographic Compliance:** Strict implementation of AES-256 (EAX Mode) and RSA-2048 (PKCS#1 OAEP) using the PyCryptodome library.

## Technology Stack
* **Language:** Python 3.10+
* **Database:** MongoDB Community Server (v8.0+)
* **Libraries:** * pymongo (Database Driver)
    * pycryptodome (Security Standards)
    * pandas & matplotlib (Data Visualization)

## Installation & Setup

### 1. Prerequisites
Ensure you have MongoDB Community Server installed and running locally on the default port 27017.

### 2. Clone Repository
git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
cd YOUR_REPO_NAME

### 3. Install Dependencies
pip install pymongo pycryptodome pandas matplotlib
