"""Command-line demo:  python -m veritas.cli "some text to fact-check"

Reads text from the argument, a file (--file), or stdin.
"""

from __future__ import annotations

import argparse
import sys

from .pipeline import analyze
from .schemas import Verdict

_COLORS = {
    Verdict.SUPPORTED: "\033[92m",   # green
    Verdict.DISPUTED: "\033[91m",    # red
    Verdict.MISLEADING: "\033[93m",  # yellow
    Verdict.UNSUPPORTED: "\033[90m", # grey
    Verdict.OPINION: "\033[94m",     # blue
}
_RESET = "\033[0m"


def _read_input(args: argparse.Namespace) -> str:
    if args.file:
        with open(args.file, "r", encoding="utf-8") as fh:
            return fh.read()
    if args.text:
        return " ".join(args.text)
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise SystemExit("Provide text as an argument, --file PATH, or via stdin.")


def main() -> None:
    # Windows terminals default to cp1252, which can't print emoji/arrows.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    parser = argparse.ArgumentParser(description="Veritas — grounded claim checker.")
    parser.add_argument("text", nargs="*", help="Text to fact-check.")
    parser.add_argument("--file", help="Read text from a file instead.")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors.")
    args = parser.parse_args()

    report = analyze(_read_input(args))

    print("\n" + "=" * 60)
    print(f"  VERITAS REPORT   credibility: {report.credibility_score}/100")
    print("=" * 60)
    print(report.summary + "\n")

    for i, r in enumerate(report.results, 1):
        color = "" if args.no_color else _COLORS.get(r.verdict, "")
        reset = "" if args.no_color else _RESET
        print(f"{i}. {color}[{r.verdict.value}]{reset} ({r.confidence:.0%}) {r.claim}")
        print(f"   → {r.explanation}")
        for c in r.citations[:3]:
            label = c.title or c.uri
            print(f"     • {label}")
        print()


if __name__ == "__main__":
    main()
