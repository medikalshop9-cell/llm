#!/usr/bin/env bash
# AfriLearn AI — one-command environment setup
set -e

echo "Setting up AfriLearn AI environment..."

# 1. Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Upgrade pip
pip install --upgrade pip

# 3. Install base requirements
pip install -r requirements.txt

# 4. Unsloth — must be installed separately (version-sensitive)
# Detect CUDA version and install appropriate build
CUDA_VERSION=$(python -c "import torch; print(torch.version.cuda)" 2>/dev/null || echo "none")

if [ "$CUDA_VERSION" != "none" ]; then
  echo "CUDA $CUDA_VERSION detected — installing Unsloth with CUDA support..."
  pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
else
  echo "No CUDA detected — installing CPU Unsloth (training will be slow, use GPU for actual training runs)..."
  pip install "unsloth @ git+https://github.com/unslothai/unsloth.git"
fi

# 5. Create required directories that are gitignored
mkdir -p data/raw data/processed data/curriculum/nigeria data/curriculum/ghana outputs checkpoints

# 6. Check Ollama is installed
if ! command -v ollama &> /dev/null; then
  echo ""
  echo "Ollama is not installed. Install it from: https://ollama.com/download"
  echo "Required to run inference locally after quantization."
else
  echo "Ollama found: $(ollama --version)"
fi

echo ""
echo "Setup complete. Activate your environment with:"
echo "  source .venv/bin/activate"
echo ""
echo "Next step: Drop your Nigeria NERDC PDF into data/curriculum/nigeria/"
echo "           Download Ghana NaCCA PDFs from https://nacca.gov.gh and drop into data/curriculum/ghana/"
