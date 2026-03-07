# AfriLearn — System Architecture

## End-to-End Data Flow

```
[AfriLearn PWA — browser / Android home screen]
         |
         | POST http://localhost:8000/generate
         | { country, subject, grade, term, week, difficulty, student_context }
         v
[FastAPI local server — api/main.py — port 8000]
         |
         |-- Retrieves top-3 curriculum chunks from ChromaDB (RAG)
         |   [ChromaDB vector store — afrilearn_knowledge_base/]
         |   [Embedded with all-MiniLM-L6-v2 — 80MB, runs on CPU]
         |
         |-- Builds full Alpaca-format prompt with RAG context prepended
         |
         | POST http://localhost:11434/api/generate
         v
[Ollama local server — port 11434]
         |
         | Loads: afrilearn-tutor (Gemma 12B Q4_K_M GGUF)
         | Runs entirely on device CPU/GPU
         v
[Generated response]
         |
         |-- Format validated (format_validator.py)
         |-- curriculum_ref extracted
         v
[JSON response returned to PWA]
         |
         v
[PWA renders question card / tutor chat bubble]
[Answer stored in IndexedDB — no server write]
```

---

## Training Pipeline

```
[Nigeria NERDC PDF]  [Ghana NaCCA PDFs]
         |                   |
         v                   v
[dataset/build_dataset.py]  (generate 64K examples)
         |
         v
[dataset/validate_dataset.py]  (schema + curriculum ref + forbidden content)
         |
         v
[dataset/deduplicate.py]  (MinHash, threshold=0.85)
         |
         v
[data/processed/afrilearn_train.jsonl]  (90%)
[data/processed/afrilearn_eval.jsonl]   (10%)
         |
         v
[training/train.py]
  Unsloth FastLanguageModel
  Gemma 12B base (4-bit QLoRA)
  LoRA rank=16, 3 epochs, A100
         |
         v
[outputs/afrilearn-gemma-12b-qlora/final_adapters/]
         |
         v
[evaluation/evaluate.py]
  Accuracy by subject
  Consistency (5 runs)
  Format compliance
  Human educator review
         |
         v
[quantization/merge_and_export.py]  → merged fp16 model
         |
         v
[quantization/quantize.sh]  → Q4_K_M GGUF (~7GB)
         |
         v
[ollama create afrilearn-tutor -f modelfile/Modelfile]
         |
         v
[rag/build_knowledge_base.py]  → ChromaDB from curriculum PDFs
         |
         v
[uvicorn api.main:app --port 8000]
         |
         v
[AfriLearn PWA calls /generate or /tutor]
```

---

## Component Responsibilities

| Component | File | Responsibility |
|-----------|------|----------------|
| Dataset validator | `dataset/validate_dataset.py` | Enforces schema, curriculum ref, forbidden content rules |
| Deduplicator | `dataset/deduplicate.py` | MinHash near-duplicate removal |
| Prompt formatter | `training/alpaca_prompt.py` | Converts rows to training text + inference prompts |
| Trainer | `training/train.py` | QLoRA fine-tuning via Unsloth + SFTTrainer |
| Evaluator | `evaluation/evaluate.py` | Accuracy + consistency + format checks |
| Format validator | `evaluation/format_validator.py` | Regex checks on required output tags |
| Merger | `quantization/merge_and_export.py` | Merges LoRA adapters into base weights |
| Quantizer | `quantization/quantize.sh` | llama.cpp GGUF conversion |
| KB builder | `rag/build_knowledge_base.py` | ChromaDB index from curriculum PDFs |
| API server | `api/main.py` | FastAPI endpoints — RAG retrieval + Ollama call |
| Pydantic models | `api/models.py` | Request/response validation with subject allowlists |
| Modelfile | `modelfile/Modelfile` | Ollama system prompt + generation parameters |

---

## Storage — Where Data Lives

| Data | Location | Persists? |
|------|----------|-----------|
| Student profiles + progress | IndexedDB in PWA browser | Yes — survives app restart |
| Quiz session results | IndexedDB | Yes |
| Curriculum knowledge base | `afrilearn_knowledge_base/` (ChromaDB) | Yes — local file |
| GGUF model weights | `outputs/*.gguf` | Yes — local file, never cloud |
| Training dataset | `data/processed/*.jsonl` | gitignored — large files |
| Training checkpoints | `outputs/` | gitignored — use DVC or HF Hub |

**Zero data transmitted to any external server during normal operation.**
