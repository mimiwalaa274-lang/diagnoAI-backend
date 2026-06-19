from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def normalize_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


RANGE_ALIASES = {
    "fasting_glucose": "blood_glucose",
    "glucose": "blood_glucose",
    "t3_ng_dl": "t3",
    "t4_ug_dl": "t4",
}


class FindingDetector:
    def __init__(self, ranges_path: Path):
        self.ranges_path = ranges_path
        self.ranges = json.loads(ranges_path.read_text(encoding="utf-8"))
        self._panel_lookup = {normalize_key(panel): panel for panel in self.ranges}

    def panels(self) -> list[str]:
        return list(self.ranges.keys())

    def panel_ranges(self, panel: str) -> dict[str, Any]:
        canonical = self._panel_lookup.get(normalize_key(panel))
        if not canonical:
            return {}
        return self.ranges[canonical]

    def detect(self, panel: str, values: dict[str, Any]) -> list[str]:
        panel_ranges = self.panel_ranges(panel)
        if not panel_ranges:
            return []

        test_lookup = {normalize_key(test): config for test, config in panel_ranges.items()}
        findings: list[str] = []
        for raw_name, raw_value in values.items():
            key = normalize_key(raw_name)
            config = test_lookup.get(key) or test_lookup.get(RANGE_ALIASES.get(key, ""))
            if not config:
                continue
            try:
                value = float(raw_value)   
            except (TypeError, ValueError):
                continue

            if normalize_key(panel) == "cbc":
                  if key in ["wbc", "platelets"] and value < 1000:
                    value = value * 1000
            low = config.get("low")
            high = config.get("high")
            if low is not None and value < float(low):
                findings.append(config["finding_low"])
            elif high is not None and value > float(high):
                findings.append(config["finding_high"])
        return findings
