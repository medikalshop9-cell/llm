#!/usr/bin/env bash
# quantization/quantize.sh
# AfriLearn — GGUF quantization via llama.cpp
#
# Usage:
#   bash quantization/quantize.sh <merged_model_dir> <output_gguf_path> [quantization_type]
#
# Arguments:
#   merged_model_dir   Path to merged fp16 HuggingFace model (output of merge_and_export.py)
#   output_gguf_path   Desired path for final .gguf file
#   quantization_type  Optional. Default: Q4_K_M
#                      Options: Q8_0 | Q5_K_M | Q4_K_M | Q3_K_M | Q2_K
#
# Quantization guide:
#   Q8_0   ~13GB RAM  — School lab PCs, minimal quality loss
#   Q5_K_M  ~9GB RAM  — Mid-range Android devices
#   Q4_K_M  ~7GB RAM  — PRIMARY TARGET: best quality/size tradeoff
#   Q3_K_M  ~5.5GB    — Fallback for <6GB RAM Android
#   Q2_K    ~3.5GB    — Last resort only, noticeable quality loss
#
# Example:
#   bash quantization/quantize.sh \
#     outputs/afrilearn-gemma-12b-merged \
#     outputs/afrilearn-gemma-12b-Q4_K_M.gguf \
#     Q4_K_M

set -e

MERGED_DIR="${1:-outputs/afrilearn-gemma-12b-merged}"
OUTPUT_GGUF="${2:-outputs/afrilearn-gemma-12b-Q4_K_M.gguf}"
QUANT_TYPE="${3:-Q4_K_M}"
LLAMACPP_DIR="./llama.cpp"
INTERMEDIATE_F16="${MERGED_DIR}/afrilearn-f16.gguf"

echo "AfriLearn GGUF Quantization"
echo "==========================="
echo "  Source:       $MERGED_DIR"
echo "  Output:       $OUTPUT_GGUF"
echo "  Quant type:   $QUANT_TYPE"
echo ""

# Step 1: Clone and build llama.cpp if not present
if [ ! -d "$LLAMACPP_DIR" ]; then
  echo "Cloning llama.cpp..."
  git clone https://github.com/ggerganov/llama.cpp "$LLAMACPP_DIR"
fi

echo "Building llama.cpp..."
cd "$LLAMACPP_DIR"
make -j$(nproc) 2>/dev/null || make
cd ..

# Step 2: Convert merged HF model to f16 GGUF
echo ""
echo "Step 1/2: Converting HuggingFace model to f16 GGUF..."
python "$LLAMACPP_DIR/convert_hf_to_gguf.py" \
  "$MERGED_DIR" \
  --outfile "$INTERMEDIATE_F16" \
  --outtype f16

echo "f16 GGUF created: $INTERMEDIATE_F16"

# Step 3: Quantize
echo ""
echo "Step 2/2: Quantizing to $QUANT_TYPE..."
mkdir -p "$(dirname "$OUTPUT_GGUF")"
"$LLAMACPP_DIR/llama-quantize" \
  "$INTERMEDIATE_F16" \
  "$OUTPUT_GGUF" \
  "$QUANT_TYPE"

echo ""
echo "Quantization complete."
echo "  Output: $OUTPUT_GGUF"
echo "  Size:   $(du -sh "$OUTPUT_GGUF" | cut -f1)"
echo ""
echo "Next step — register with Ollama:"
echo "  ollama create afrilearn-tutor -f modelfile/Modelfile"
echo ""
echo "Then test:"
echo "  ollama run afrilearn-tutor 'Generate a Grade 3 Mathematics question about multiplication. Difficulty: medium. Country: Nigeria.'"
