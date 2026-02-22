# CLI entrypoint


import argparse
import json
import sys
from pathlib import Path

from .providers import Provider

# from .logconfig import logger
from .service import Safe2ShareService


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="safe2share",
        description="Preflight confidentiality scanner for prompts and text.",
    )
    p.add_argument(
        "text",
        nargs="?",
        help="Text to analyze. If omitted, reads from stdin (or --file).",
    )
    p.add_argument("--file", "-f", help="Path to a text file to analyze (utf-8).")
    p.add_argument(
        "--max-chars",
        type=int,
        default=200_000,
        help="Max characters to analyze (default: 200000).",
    )
    p.add_argument(
        "--provider", choices=[e.value for e in Provider], default=Provider.LOCAL.value
    )
    p.add_argument("--json", action="store_true", help="Output JSON")
    return p


def main() -> int:
    args = build_parser().parse_args()

    # Determine input source priority:
    # 1) --file
    # 2) positional text
    # 3) stdin
    text: str | None = None

    if args.file:
        path = Path(args.file)
        if not path.exists() or not path.is_file():
            print(f"File not found: {path}", file=sys.stderr)
            return 2
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(
                "File must be UTF-8 encoded text for MVP. Convert the file and retry.",
                file=sys.stderr,
            )
            return 2
    elif args.text:
        text = args.text
    else:
        text = sys.stdin.read()

    text = (text or "").strip()
    if not text:
        print("No input text provided.", file=sys.stderr)
        return 2

    if len(text) > args.max_chars:
        print(
            f"Input too large ({len(text)} chars). Limit is {args.max_chars}. "
            "Tip: increase --max-chars, split the file, or use provider local for huge text.",
            file=sys.stderr,
        )
        return 2

    provider = Provider(args.provider)

    try:
        service = Safe2ShareService(provider=provider)
        result = service.analyze(text)
    except RuntimeError as e:
        # Clean, user-facing error (e.g., LLM not configured / not reachable)
        print(str(e), file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                result.model_dump() if hasattr(result, "model_dump") else result,
                indent=2,
            )
        )
    else:
        # Minimal, readable output for MVP (we'll improve formatting later)
        if hasattr(result, "risk") and hasattr(result, "score"):
            print(f"Risk: {result.risk} | Score: {result.score}")
            if getattr(result, "reasons", None):
                print("Reasons:")
                for r in result.reasons:
                    print(f" - {r}")
            if getattr(result, "detections", None):
                print("Detections:")
                for d in result.detections:
                    print(f" - {d.label}: {d.span} ({d.score})")
        else:
            print(result)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
