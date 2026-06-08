# Python conversion of Zorotaro Outreach

Quick start

1. Create a virtualenv and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate   # on Windows: .venv\Scripts\Activate.ps1
pip install -r python_outreach/requirements.txt
```

2. Ensure required environment variables are set (see `config.py`).

3. Run the pipeline:

```bash
python -m python_outreach.pipeline --help
python -m python_outreach.pipeline example.com --max-companies 5
```
