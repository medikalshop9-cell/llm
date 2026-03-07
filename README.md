# AfriLearn AI — Gemma 12B Fine-Tuning Pipeline

**Offline AI tutor for primary school children in Ghana (NaCCA) and Nigeria (NERDC)**
**Stack: Gemma 12B + QLoRA + Unsloth + RAG + Ollama GGUF**

> This repository contains the full ML pipeline to produce `afrilearn-tutor` — a fine-tuned,
> quantized, RAG-augmented Gemma 12B model that runs entirely on-device with no internet required.

---

## Repository Structure

```
afrilearn-ai/
├── data/
│   ├── curriculum/nigeria/        # Drop NERDC PDF(s) here
│   ├── curriculum/ghana/          # Drop NaCCA PDF(s) here
│   ├── samples/                   # Seed examples (human-validated)
│   ├── raw/                       # Synthetic output before QA
│   └── processed/                 # Clean, deduplicated .jsonl ready for training
├── dataset/
│   ├── schemas/                   # JSON schemas for Nigeria + Ghana row formats
│   ├── build_dataset.py           # Generates dataset rows from curriculum PDFs
│   ├── validate_dataset.py        # Schema + curriculum ref + quality checks
│   └── deduplicate.py             # MinHash deduplication
├── training/
│   ├── train.py                   # QLoRA fine-tuning via Unsloth
│   ├── config.yaml                # All hyperparameters in one place
│   └── alpaca_prompt.py           # Prompt formatter
├── evaluation/
│   ├── evaluate.py                # Automated accuracy + consistency + format checks
│   ├── format_validator.py        # Regex-based output format compliance
│   └── human_eval_template.csv    # Template for educator review sessions
├── quantization/
│   ├── merge_and_export.py        # Merges LoRA adapters into base model
│   └── quantize.sh                # llama.cpp GGUF quantization script
├── rag/
│   ├── build_knowledge_base.py    # Indexes curriculum PDFs into ChromaDB
│   └── query_rag.py               # Test RAG retrieval before connecting to API
├── api/
│   ├── main.py                    # FastAPI local server (RAG + Ollama)
│   └── models.py                  # Pydantic request/response models
├── modelfile/
│   └── Modelfile                  # Ollama model definition
├── scripts/
│   └── setup.sh                   # One-command environment setup
├── docs/
│   ├── ROADMAP.md                 # Full phase-by-phase technical roadmap
│   ├── CURRICULUM_SOURCES.md      # All curriculum sources with URLs
│   └── ARCHITECTURE.md            # System architecture diagrams (text)
├── requirements.txt
└── .gitignore
```

---

## Quickstart

### 1. Clone and set up environment

```bash
git clone https://github.com/YOUR_USERNAME/afrilearn-ai.git
cd afrilearn-ai
bash scripts/setup.sh
```

### 2. Add curriculum documents

```bash
# Drop your Nigeria NERDC PDF into:
data/curriculum/nigeria/

# Download Ghana NaCCA PDFs from https://nacca.gov.gh and drop into:
data/curriculum/ghana/
```

### 3. Build dataset

```bash
python dataset/build_dataset.py --country nigeria --output data/raw/nigeria_raw.jsonl
python dataset/validate_dataset.py --input data/raw/nigeria_raw.jsonl --output data/processed/nigeria_clean.jsonl
python dataset/deduplicate.py --input data/processed/nigeria_clean.jsonl --output data/processed/nigeria_final.jsonl
```

### 4. Train

```bash
python training/train.py --config training/config.yaml
```

### 5. Evaluate

```bash
python evaluation/evaluate.py --model ./outputs/afrilearn-gemma-12b-lora-adapters --eval-set data/processed/eval_set.jsonl
```

### 6. Quantize

```bash
python quantization/merge_and_export.py
bash quantization/quantize.sh
```

### 7. Build RAG knowledge base

```bash
python rag/build_knowledge_base.py --curriculum-dir data/curriculum/
```

### 8. Run local API

```bash
ollama create afrilearn-tutor -f modelfile/Modelfile
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## Target Curriculum Coverage

| Country | Authority | Grades | Subjects |
|---------|-----------|--------|----------|
| Nigeria | NERDC | Primary 1-6 | English, Mathematics, Basic Science & Tech, Social Studies, Religious Studies (CRS/IRS), Computer Studies, PHE |
| Ghana | NaCCA 2019 | Basic 1-6 | English, Mathematics, Science, OWOP, RME, Computing (B4-B6), PE |

**Dataset target:** 64,000 examples across both curricula.

---

## Hardware Requirements

| Phase | Minimum | Recommended |
|-------|---------|-------------|
| Dataset build | Any CPU | Any CPU |
| Training | RTX 4090 (24GB VRAM) | A100 40GB (RunPod ~$35 total) |
| Quantization | 16GB RAM CPU | Same |
| Inference (device) | 6GB RAM Android | 8GB RAM Android |

---

## Team

| Name | Role |
|------|------|
| Hinneh Yaw Acheampong | Founder & CEO |
| Amuzie Grace | TBD |
| Jeffrey Kwame Andoh | TBD |

---

## License

Proprietary — AfriLearn. All rights reserved.
Base model: Gemma 12B (Google, Apache 2.0 — https://ai.google.dev/gemma/terms)
