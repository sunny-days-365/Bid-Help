# Green Japan Auto Job Finder

Automatically searches [Green Japan](https://www.green-japan.com/) for jobs matching your resume, situation, and career hopes — then returns ranked job URLs.

## Features

- 📄 **Resume parsing** — supports `.docx` and `.txt`
- 🤖 **AI keyword extraction** — uses GPT-4o to extract smart search keywords (falls back to pattern matching if no API key)
- 🌐 **Green Japan scraping** — uses Playwright (headless Chromium) to scrape JavaScript-rendered job listings
- 🏆 **AI-powered ranking** — ranks results by relevance to your profile
- 💾 **Saves results** — outputs `.txt` and `.json` files

## Setup

```powershell
python -m pip install requests beautifulsoup4 python-docx openai playwright
python -m playwright install chromium
```

## Usage

### GUI mode (recommended)
```powershell
python ui.py
```

### CLI interactive mode
```powershell
python main.py
```

### Command-line mode
```powershell
python main.py --resume "my_resume.docx" --situation "5 years Python backend engineer" --hope "remote job, 700万円+, startup"
```

### With manual keywords (no AI needed)
```powershell
python main.py --resume "my_resume.docx" --situation "..." --hope "..." --keywords "Python,バックエンド,リモート"
```

### All options
| Flag | Default | Description |
|------|---------|-------------|
| `--resume` | (prompted) | Path to `.docx` or `.txt` resume |
| `--situation` | (prompted) | Your current situation |
| `--hope` | (prompted) | Your ideal job |
| `--pages` | `3` | Pages to scrape per keyword |
| `--top` | `20` | Number of top results |
| `--output` | `results.txt` | Output file |
| `--keywords` | (AI generated) | Comma-separated manual keywords |

## AI (Optional)

Set your OpenAI API key for smarter keyword extraction and ranking:
```powershell
$env:OPENAI_API_KEY = "sk-..."
python main.py --resume resume.docx --situation "..." --hope "..."
```

Without the key, the tool uses pattern-matching (still works well for common job types).

## Output

- `results.txt` — Human-readable ranked job list with URLs
- `results.json` — Raw JSON with all job data

## File Structure

```
Bid-help/
├── main.py              # Entry point
├── resume_parser.py     # Resume reading (.docx / .txt)
├── keyword_extractor.py # AI or pattern-based keyword extraction
├── green_scraper.py     # Playwright scraper for Green Japan
├── job_ranker.py        # AI or keyword-based job ranking
└── README.md
```
