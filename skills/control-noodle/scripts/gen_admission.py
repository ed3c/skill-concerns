#!/usr/bin/env python3
"""Stamp this Skill's admission receipt through the shared refusing surface."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))
from admission_stamp import stamp  # noqa: E402

raise SystemExit(stamp("control-noodle"))
