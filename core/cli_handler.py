import argparse
import config

class CliHandler:
    def __init__(self):
        # The description appears at the top of the help menu
        self.parser = argparse.ArgumentParser(
            description="PlayTimeTracker - A game time tracking utility for KDE Wayland 6.",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        self._setup_args()

    def _setup_args(self):
        self.parser.add_argument(
            "target", 
            nargs="?", 
            metavar="target",
            help="The .exe or process name to track automatically (Requires more testing still). If omitted, the GUI launches normally."
        )
        
        # Version flag
        self.parser.add_argument(
            "-v", "--version", 
            action="version", 
            version=f"PlayTimeTracker {config.VERSION}",
            help="Show the application version and exit."
        )

    def parse(self):
        return self.parser.parse_args()