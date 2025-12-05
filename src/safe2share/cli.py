# CLI entrypoint
import argparse
import json
from .service import Safe2ShareService
from .logconfig import logger


def main():

    available_modes = list(Safe2ShareService.ANALYZER_REGISTRY_CLASSES.keys()) + ["auto"]
    
    parser = argparse.ArgumentParser(prog="safe2share")
    parser.add_argument("text", help="Text to analyze")
    parser.add_argument(
        "--mode", 
        choices=available_modes,
        default=None, 
        help=f"Analysis mode. Available: {', '.join(available_modes)}."
    )
    args = parser.parse_args()

    # Instantiate the service
    svc = Safe2ShareService(mode=args.mode)
    
    # Get the result and the analyzer name used
    res, analyzer_name = svc.analyze_with_info(args.text) 
    
    # --- Report Fallback ---
    requested_mode = args.mode or svc.mode

    RULE_MODES = ('local', 'rule')
    # Determine the analyzer name if the request was for a rule mode
    fallback_model = requested_mode if requested_mode in RULE_MODES else analyzer_name
    
    if requested_mode != fallback_model:
        # Check if the requested mode was a specific analyzer that had to fall back
        if requested_mode in Safe2ShareService.ANALYZER_REGISTRY_CLASSES and analyzer_name == 'rulebased':
             print(f"Warning: Requested mode '{requested_mode}' unavailable (missing credentials/host). Used **{analyzer_name.upper()}** fallback.")
        
        # Note: 'auto' is an orchestrator, so report if its component failed
        elif requested_mode == 'auto' and analyzer_name == 'rulebased':
             print(f"Warning: AUTO mode failed to initialize AI component. Used **{analyzer_name.upper()}** only.")

    print(json.dumps(res.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
