# Skill: analyze-excel

Analyze an Excel file using a local Ollama LLM to understand its structure without consuming Claude's context window.

## When to use
- Before reading any Excel file directly into Claude context
- When you need to understand column names, data types, unique values, and data quality
- When the file is large (>1MB) and reading it directly would waste tokens

## How to run

Use the system Python (not the venv one), with UTF-8 encoding:

```powershell
$env:PYTHONUTF8=1; C:\Users\georg\AppData\Local\Programs\Python\Python312\python.exe .claude/scripts/analyze_excel.py "<file_path>" --model llama3:latest
```

### Options
- `--model` — Ollama model to use (default: `qwen3:8b`, also good: `devstral:latest` for code-heavy analysis)
- `--sheet` — specific sheet name or `all` (default: `all`)
- `--question` — custom question to ask about the data

## Example usage

Analyze raw data file:
```bash
python .claude/scripts/analyze_excel.py "รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564 - พฤษภาคม 2569 (raw data).xlsx" --model qwen3:8b
```

Analyze with a specific question:
```bash
python .claude/scripts/analyze_excel.py "file.xlsx" --question "List all unique brand names in the brand column"
```

## What the output tells you
1. Sheet names and row counts
2. All column names and data types
3. Unique values for text columns (brand names, fuel types, etc.)
4. Data quality issues spotted by the LLM
5. Suggested grouping/filtering columns

## After running
Report the key findings back to the user in a short summary:
- Column names in the brand column (ยี่ห้อรถ)
- Any obvious data quality issues
- Sheet structure
