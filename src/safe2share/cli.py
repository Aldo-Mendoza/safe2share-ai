# CLI entrypoint



from .providers import Provider
import sys
from .logconfig import logger
from .service import Safe2ShareService
import json
import argparse


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="safe2share", description="Preflight confidentiality scanner for prompts and text.")
    p.add_argument("text", nargs="?",
                   help="Text to analyze. If omitted, reads from stdin.")
    p.add_argument(
        "--provider", choices=[e.value for e in Provider], default=Provider.LOCAL.value)
    p.add_argument("--json", action="store_true", help="Output JSON")
    return p


def main() -> int:
    args = build_parser().parse_args()

    text = args.text
    if not text:
        text = sys.stdin.read().strip()

    if not text:
        print("No input text provided.", file=sys.stderr)
        return 2

    provider = Provider(args.provider)
    service = Safe2ShareService(provider=provider)

    result = service.analyze(text)

    if args.json:
        print(json.dumps(result.model_dump() if hasattr(
            result, "model_dump") else result, indent=2))
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
