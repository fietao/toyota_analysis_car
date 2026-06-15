"""
Reads Excel files and sends a structured summary to a local Ollama model for analysis.
Usage: python analyze_excel.py <file_path> [--model qwen3:8b] [--sheet all]
"""

import argparse
import json
import sys
import requests
import pandas as pd
from pathlib import Path


def summarize_excel(file_path: str, sheet_name=None) -> str:
    path = Path(file_path)
    if not path.exists():
        return f"ERROR: File not found: {file_path}"

    xl = pd.ExcelFile(file_path)
    sheet_names = xl.sheet_names

    sections = [f"File: {path.name}", f"Sheets: {sheet_names}", ""]

    target_sheets = sheet_names if sheet_name == "all" or sheet_name is None else [sheet_name]

    for sheet in target_sheets:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet, nrows=1000)
            sections.append(f"=== Sheet: {sheet} ===")
            sections.append(f"Rows (first 1000 sampled): {len(df)}")
            sections.append(f"Columns ({len(df.columns)}): {list(df.columns)}")
            sections.append(f"Dtypes:\n{df.dtypes.to_string()}")
            sections.append(f"Sample (first 5 rows):\n{df.head(5).to_string()}")

            # Unique values for object columns (brand-like columns)
            for col in df.select_dtypes(include="object").columns:
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) <= 100:
                    sections.append(f"Unique values in '{col}': {list(unique_vals)}")
                else:
                    sections.append(f"Unique values in '{col}': {len(unique_vals)} unique values (too many to list)")
            sections.append("")
        except Exception as e:
            sections.append(f"ERROR reading sheet '{sheet}': {e}\n")

    return "\n".join(sections)


def ask_ollama(prompt: str, model: str) -> str:
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=300,
        )
        resp.raise_for_status()
        return resp.json().get("response", "No response from model")
    except Exception as e:
        return f"ERROR calling Ollama: {e}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Path to Excel file")
    parser.add_argument("--model", default="qwen3:8b", help="Ollama model to use")
    parser.add_argument("--sheet", default="all", help="Sheet name or 'all'")
    parser.add_argument("--question", default=None, help="Custom question to ask about the data")
    args = parser.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    print(f"Reading {args.file}...", flush=True)
    summary = summarize_excel(args.file, args.sheet)

    default_question = (
        "You are a data analyst. Analyze this Excel file structure and tell me:\n"
        "1. What is the data about?\n"
        "2. What are the key columns and their meaning?\n"
        "3. What are all unique brand names (brand column) ?\n"
        "4. What data quality issues do you notice?\n"
        "5. What columns could be used to group or filter the data?\n"
        "Answer in English, be concise."
    )

    question = args.question if args.question else default_question
    prompt = f"{question}\n\n--- DATA SUMMARY ---\n{summary}"

    print(f"\nSending to Ollama ({args.model})...\n", flush=True)
    answer = ask_ollama(prompt, args.model)
    print("=== ANALYSIS ===")
    print(answer)


if __name__ == "__main__":
    main()
