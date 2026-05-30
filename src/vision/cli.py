"""Vision Router CLI — analyze + serve subcommands."""
import sys
import argparse

from . import analyze_image


def main():
    parser = argparse.ArgumentParser(
        prog="vision",
        description="Vision Router — analyze images via multiple AI providers with auto-fallback"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    ap = sub.add_parser("analyze", help="Analyze an image file")
    ap.add_argument("image", help="Path to image file")
    ap.add_argument("prompt", nargs="?", default="Describe this image in detail",
                    help="Analysis prompt")

    sp = sub.add_parser("serve", help="Start web UI (settings + analyze via browser)")
    sp.add_argument("--port", type=int, default=5050, help="Port (default: 5050)")
    sp.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")

    args = parser.parse_args()

    if args.command == "analyze":
        result = analyze_image(args.image, args.prompt)
        if result["success"]:
            print(f"[provider: {result['provider']}]")
            print()
            print(result["result"])
        else:
            print(f"ERROR: {result['error']}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "serve":
        from .webui import run_server
        run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
