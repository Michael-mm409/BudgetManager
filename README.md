# Budget Manager

A lightweight desktop budgeting application built with Python and PyQt6. It lets you record expenses and income, compare actuals vs planned amounts per category, and view monthly summaries. Descriptions support multi‑line bullet lists for clearer breakdowns.

## Features
- Track expenses and income with date, amount, category, multi‑line description
- Auto bullet formatting helper ("Bullets" button) for descriptions
- Planned vs Actual monthly summary for both expenses and income
- Automatic difference (+/−) calculation with currency formatting
- Categories and planned amounts driven by a CSV file (easy to edit)
- SQLite database stored locally inside the package data folder
- Robust date normalization (accepts dd-mm-YYYY and common ISO format on load)

## Tech Stack
- Python 3.11+ (recommended)
- PyQt6 for the GUI
- pandas for data loading & aggregation
- SQLite (standard library `sqlite3`)

## Repository Structure
```
budget/
  application/          # Application services (data loading, normalization)
  infrastructure/
    db/                 # DB connection + CRUD helpers
    config_loader/      # Category + planned amount loader from CSV
  presentation/
    qt/                 # PyQt UI (main window, table model)
  data/                 # Runtime data files (budget.db, categories.csv)
main.py / ui.py         # (legacy / entry helpers if present)
README.md
```

## Categories Configuration
Categories + planned amounts live in: `budget/data/categories.csv`.

CSV expected headers:
```
type,category,planned
```
Rows example:
```
expense,Rent,1500
expense,Groceries,600
expense,Utilities,300
income,Salary,4000
income,Other,200
```
Notes:
- `type` must be `expense` or `income` (case-insensitive)
- `planned` is a number (float allowed)
- A synthetic `Totals` row is added automatically; do not include it in the CSV
- Categories named `Totals` are reserved and skipped if present

If the CSV is missing, default categories `Totals` and `Other` (planned 0) are created in-memory.

## Database
- Created automatically at: `budget/data/budget.db`
- Tables: `expenses` and `income`
- Date stored as `dd-mm-YYYY` strings (normalized on insert)

Schema (simplified):
```
CREATE TABLE expenses (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  amount REAL NOT NULL,
  description TEXT,
  category TEXT
);
CREATE TABLE income (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  date TEXT NOT NULL,
  amount REAL NOT NULL,
  description TEXT,
  category TEXT
);
```

## Running the App
### 1. Create & activate a virtual environment (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install dependencies
Create `requirements.txt` (example):
```
PyQt6
pandas
```
Install:
```powershell
pip install -r requirements.txt
```

### 3. Initialize DB (first run only)
```powershell
python -c "from budget.infrastructure.db.connection import init_db; init_db(); print('DB ready')"
```

### 4. Run UI
If `main.py` calls `run_app()` you can:
```powershell
python -m budget.presentation.qt.main_window
```
(or run your launcher script if different.)

## Using Bullet Descriptions
1. Type multiple lines in the description box.
2. Click the "Bullets" button – each non-empty line gets a leading • (idempotent; existing •, -, * prefixes are preserved).

## Planned vs Actual Summary
- Select month at top of Summary tab.
- Planned: pulled from the CSV per category.
- Actual: sum of amounts for that month/category.
- Diff: `Planned - Actual` (positive means under budget for expenses / shortfall for income).

## Common Tasks
| Task | Action |
|------|--------|
| Add new category | Edit `budget/data/categories.csv`, restart app |
| Reset DB | Delete `budget/data/budget.db`, re-run init_db |
| Change planned amount | Edit CSV value & restart |
| Backup data | Copy the `budget/data` folder |

## Development Tips
- Keep UI logic in `presentation/qt/` and business/data logic elsewhere.
- Prefer adding tests (if you introduce them later) around DataService & formatting.
- Avoid committing `budget/data/budget.db`.

## Troubleshooting
| Issue | Cause | Fix |
|-------|-------|-----|
| Categories not updating | CSV edited while app open | Restart app |
| No categories except Totals/Other | Missing CSV file | Add CSV then restart |
| Dates show as NaT in summary | Unparseable date format in DB | Ensure inserts go through provided helpers |
| GUI not launching | Missing PyQt6 | `pip install PyQt6` |

## License
Add a license (e.g. MIT) here.

## Roadmap (Ideas)
- Export to CSV
- Simple charts (spending over time)
- Per-category running monthly averages
- Validation feedback styling improvements

---
Feel free to modify or trim sections based on your distribution needs.
