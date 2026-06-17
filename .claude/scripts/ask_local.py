"""Send a prompt to a local Ollama model and print the response."""
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

DEFAULT_MODEL = "qwen2.5-coder:7b"
OLLAMA_URL = "http://localhost:11434/api/chat"
TIMEOUT = 300


def ask(prompt, model=DEFAULT_MODEL):
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
    }).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())["message"]["content"]
    except TimeoutError:
        print(f"ERROR: Model took longer than {TIMEOUT}s. Try a smaller model.", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError:
        print("ERROR: Ollama is not running. Start it with: ollama serve", file=sys.stderr)
        sys.exit(1)
    except KeyError:
        print("ERROR: Unexpected response from Ollama.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    args = sys.argv[1:]
    model = DEFAULT_MODEL
    file_paths = []

    if "--model" in args:
        i = args.index("--model")
        model = args[i + 1]
        args = args[:i] + args[i + 2:]

    # --file path.txt injects file contents into the prompt
    while "--file" in args:
        i = args.index("--file")
        file_paths.append(args[i + 1])
        args = args[:i] + args[i + 2:]

    prompt = " ".join(args) if args else sys.stdin.read().strip()

    for fp in file_paths:
        content = Path(fp).read_text(encoding="utf-8")
        prompt += f"\n\n--- {fp} ---\n{content}"

    if not prompt:
        print("Usage: python ask_local.py [--model NAME] [--file PATH] <prompt>", file=sys.stderr)
        sys.exit(1)

    print(ask(prompt, model))
