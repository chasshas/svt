#!/usr/bin/env python3
"""SVT Terminal - Main entry point.

Usage:
    python -m svt                  # Start interactive REPL
    python -m svt <script.svt>     # Execute a script file
    python -m svt -e "command"     # Execute a single command
"""

import sys
import os

# Ensure the parent directory of svt package is in sys.path
pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from svt.core.engine import SVTEngine


def main():
    engine = SVTEngine()
    engine.init()

    if len(sys.argv) > 1:
        if sys.argv[1] == '-e' and len(sys.argv) > 2:
            # Execute inline command
            code = ' '.join(sys.argv[2:])
            result = engine.execute_line(code)
            engine.shutdown()
            sys.exit(0)
        elif sys.argv[1] == '-f' or sys.argv[1].endswith('.svt'):
            # Execute script file
            filepath = sys.argv[2] if sys.argv[1] == '-f' else sys.argv[1]
            # Pass remaining args as script arguments
            if len(sys.argv) > 2 and sys.argv[1].endswith('.svt'):
                engine.variables.set("ARGV", sys.argv[2:])
            elif len(sys.argv) > 3 and sys.argv[1] == '-f':
                engine.variables.set("ARGV", sys.argv[3:])
            result = engine.run_script(filepath)
            engine.shutdown()
            if result and result.status.value == "exit":
                sys.exit(result.value if isinstance(result.value, int) else 0)
            sys.exit(0)
        elif sys.argv[1] in ('-h', '--help'):
            print(__doc__)
            sys.exit(0)

    # Interactive REPL
    try:
        engine.repl()
    except Exception as e:
        print(f"\n[SVT Fatal Error] {e}")
    finally:
        engine.shutdown()


if __name__ == "__main__":
    main()
