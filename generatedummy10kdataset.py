import random

# --- CONFIGURATION ---
OUTPUT_FILE = "populate_data.sql"
NUM_RECORDS = 10000 

print(f"Generating {NUM_RECORDS} SQL commands with RANDOM notes...")

with open(OUTPUT_FILE, "w") as f:
    # 1. Setup Table
    f.write("DROP TABLE IF EXISTS Patients;\n")
    f.write("CREATE TABLE Patients (id INTEGER PRIMARY KEY, name TEXT, diagnosis TEXT, ssn TEXT, notes TEXT);\n")
    f.write("BEGIN TRANSACTION;\n") 

    # 2. Lists for Random Selection
    diagnoses = ["Hypertension", "Diabetes", "Covid-19", "Flu", "Fracture"]
    
    # NEW: Different notes for variety
    note_templates = [
        "Patient reported mild symptoms during intake.",
        "CRITICAL: Immediate surgery required.",
        "Follow-up appointment scheduled for next week.",
        "Prescription refill approved by Dr. Smith.",
        "Patient discharged. Vitals stable."
    ]
    
    for i in range(NUM_RECORDS):
        p_name = f"Patient_{i}"
        p_diag = random.choice(diagnoses)
        p_ssn = f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}"
        
        # Randomly pick one note
        p_note = random.choice(note_templates)
        
        sql = f"INSERT INTO Patients VALUES ({i}, '{p_name}', '{p_diag}', '{p_ssn}', '{p_note}');\n"
        f.write(sql)

    f.write("COMMIT;\n")

print(f"Created {NUM_RECORDS} records with random notes.")