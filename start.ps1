$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

if (-not (Test-Path ".\\node_modules")) {
  npm install
}

if (-not (Test-Path ".\\backend\\.venv\\Scripts\\python.exe")) {
  python -m venv ".\\backend\\.venv"
  .\\backend\\.venv\\Scripts\\python.exe -m pip install -r ".\\backend\\requirements.txt"
}

npm run dev
