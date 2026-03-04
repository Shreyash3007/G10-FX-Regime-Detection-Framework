# FX Regime Detection Framework — Project Structure

## Clean Directory Layout

```
fx_regime/
├── Core Pipeline (Executable)
│   ├── run_all.py              # Master orchestrator - runs entire pipeline
│   ├── pipeline.py             # FX market data ETL & regime indicators
│   ├── cot_pipeline.py         # CFTC COT positioning data pipeline
│   ├── inr_pipeline.py         # INR-specific data pipeline
│   ├── morning_brief.py        # Text brief generation
│   ├── create_html_brief.py    # HTML brief with interactive charts
│   └── deploy.py               # Deploy to GitHub Pages
│
├── Supporting Modules
│   ├── config.py               # Configuration & constants
│   ├── create_charts_plotly.py # Plotly chart builders
│   └── check_latest.py         # Data freshness checks
│
├── Data Directories (Generated, excluded from git)
│   ├── data/                   # Latest market data & processed files
│   ├── briefs/                 # Generated text + HTML briefs  
│   ├── charts/                 # Generated chart images
│   └── runs/                   # Daily run archives with outputs
│
├── Configuration Files
│   ├── requirements.txt        # Python dependencies
│   ├── README.md               # Project documentation
│   ├── .gitignore              # Git exclusion rules
│   └── .env                    # Secrets (excluded from git)
│
├── Production Output
│   └── index.html              # Deployed brief (GitHub Pages)
│
├── Version Control
│   └── .git/                   # Git history
│
└── Virtual Environment
    └── .venv/                  # Python virtualenv (excluded from git)
```

## Pipeline Flow

1. **run_all.py** → orchestrates complete workflow
2. **pipeline.py** → fetches market data, calculates regime indicators
3. **cot_pipeline.py** → loads CFTC positioning data
4. **inr_pipeline.py** → loads INR-specific metrics
5. **morning_brief.py** → generates text brief from combined data
6. **create_html_brief.py** → generates interactive HTML with charts
7. **deploy.py** → pushes to GitHub for Pages deployment

## Key Principles

- ✅ **Single Responsibility** — Each script has one clear purpose
- ✅ **Clean Data Flow** — Data passes through pipeline incrementally
- ✅ **Output Versioning** — Daily archives in `runs/` directory
- ✅ **No Test Files** — Test/debug files deleted (use proper test suite if needed)
- ✅ **Git Hygiene** — `.gitignore` excludes all generated & temporary files

## How to Run

```bash
# Initial setup
python -m venv .venv
source .venv/Scripts/Activate.ps1  # or bash equivalent
pip install -r requirements.txt

# Execute full pipeline (daily)
python run_all.py

# Or run individual components
python pipeline.py
python morning_brief.py
python create_html_brief.py
python deploy.py
```

## Output Locations

- **Latest brief (text)**: `briefs/brief_YYYYMMDD.txt`
- **Latest brief (HTML)**: `briefs/brief_YYYYMMDD.html`
- **Daily archive**: `runs/YYYY-MM-DD/` (contains brief + data CSVs)
- **Live deployment**: GitHub Pages (pushes to `index.html`)
