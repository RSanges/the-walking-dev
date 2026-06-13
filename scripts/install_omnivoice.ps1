# Install the GPU TTS stack (PyTorch CUDA + OmniVoice) into the uv venv.
# RTX 2070 Super (Turing, CUDA 7.5) validated. Run once.
#   powershell -ExecutionPolicy Bypass -File scripts\install_omnivoice.ps1

$ErrorActionPreference = "Stop"
Write-Host "1/3 PyTorch CUDA (cu128)..." -ForegroundColor Cyan
uv pip install "torch==2.8.0+cu128" "torchaudio==2.8.0+cu128" `
  --extra-index-url https://download.pytorch.org/whl/cu128

Write-Host "2/3 OmniVoice + soundfile..." -ForegroundColor Cyan
uv pip install omnivoice soundfile numpy

Write-Host "3/3 Verification GPU torch..." -ForegroundColor Cyan
uv run python -c "import torch; print('CUDA dispo:', torch.cuda.is_available(), '|', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no gpu')"

Write-Host "OK. Lance ensuite: uv run python scripts\spike_omnivoice.py" -ForegroundColor Green
