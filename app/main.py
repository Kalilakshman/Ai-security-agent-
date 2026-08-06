"""
Main executable entry point for AI Security Orchestrator CLI.

Provides signal handling (SIGINT/SIGTERM) and top-level exception handling.
"""

import sys
import signal
from app.cli import app
from core.logger import get_logger, get_console

logger = get_logger("main")
console = get_console()


def signal_handler(sig, frame):
    """Handle graceful shutdown on interrupt signals."""
    console.print("\n[bold yellow]⚠️ Interrupted by user. Shutting down gracefully...[/bold yellow]")
    sys.exit(130)


def main():
    """Bootstraps application and invokes Typer CLI."""
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal_handler)

    try:
        app()
    except Exception as e:
        logger.critical(f"Unhandled fatal exception: {str(e)}", exc_info=True)
        console.print(f"[bold red]FATAL ERROR:[/bold red] {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
