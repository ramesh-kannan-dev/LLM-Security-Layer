import os
import torch
from transformers import BertTokenizer, BertForSequenceClassification, Trainer, TrainingArguments
from datasets import load_dataset, concatenate_datasets

# 1. SETUP: Check for GPU or CPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"🚀 Training on: {device}")

# --- 2. PREPARE DATASETS (The Professional Way) ---

# A. Load "Bad" Data (Real Prompt Injections)
print("⬇️ Downloading Attack Dataset (deepset/prompt-injections)...")
attack_dataset = load_dataset("deepset/prompt-injections", split="train")

# Select 500 random attacks
attack_subset = attack_dataset.shuffle(seed=42).select(range(500))

# Format it: We only need the 'text' column, and we set label=1 (Malicious)
def format_attack(example):
    return {"text": example["text"], "label": 1}

attack_ready = attack_subset.map(format_attack, remove_columns=attack_subset.column_names)


# B. Load "Good" Data (Databricks Dolly 15k)
print("⬇️ Downloading Safe Dataset (databricks/databricks-dolly-15k)...")
safe_dataset = load_dataset("databricks/databricks-dolly-15k", split="train")

# Select 500 random safe instructions
safe_subset = safe_dataset.shuffle(seed=42).select(range(500))

# Format it: Use 'instruction' as text, set label=0 (Safe)
def format_safe(example):
    return {"text": example["instruction"], "label": 0}

safe_ready = safe_subset.map(format_safe, remove_columns=safe_subset.column_names)


# C. Combine Them
print("⚖️ Balancing the Dataset (50% Safe, 50% Attack)...")
combined_dataset = concatenate_datasets([attack_ready, safe_ready])
final_dataset = combined_dataset.shuffle(seed=42)

# Split into Train (80%) and Test (20%)
data_split = final_dataset.train_test_split(test_size=0.2)

print(f"✅ Data Ready! Training on {len(data_split['train'])} examples.")
print(f"   - Source 1: Deepset Prompt Injections (Attacks)")
print(f"   - Source 2: Databricks Dolly 15k (Safe)")

# --- 3. LOAD THE BRAIN ---
model_name = "bert-base-uncased"
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertForSequenceClassification.from_pretrained(model_name, num_labels=2)
model.to(device)

def tokenize_function(examples):
    return tokenizer(examples["text"], padding="max_length", truncation=True, max_length=128)

print("⚙️ Tokenizing data...")
tokenized_datasets = data_split.map(tokenize_function, batched=True)

# --- 4. TRAIN ---
training_args = TrainingArguments(
    output_dir="./archias_results_v3",
    num_train_epochs=3,              # 3 Rounds
    per_device_train_batch_size=4,   # Safe for Laptop CPU
    logging_steps=10,
    save_strategy="no",
    use_cpu=True if device.type == 'cpu' else False
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["test"],
)

print("🔥 STARTING TRAINING... (This is the Real Deal!)")
trainer.train()

# --- 5. SAVE ---
print("💾 Saving the Professional Model...")
model.save_pretrained("./archias_model")
tokenizer.save_pretrained("./archias_model")

print("✅ DONE! You now have a Research-Grade Security Model.")