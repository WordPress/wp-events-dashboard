import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "build_dashboard.py").read_text(encoding="utf-8")
DATA = json.loads((ROOT / "dashboard_data.json").read_text(encoding="utf-8"))


class MeetupMapZoomTest(unittest.TestCase):
    def test_main_meetup_zoom_floor_allows_dense_area_inspection(self):
        block = SOURCE.split("/* Interactive map: wheel/button zoom", 1)[1].split("/* Interactive \"met this month\" map", 1)[0]
        minimum = float(re.search(r"MINW=(\d+(?:\.\d+)?)", block).group(1))
        width = DATA["meetups"]["map"]["w"]
        requested_width = width
        for _ in range(12):
            requested_width = max(minimum, requested_width * 0.7)
        self.assertLessEqual(requested_width, 27.5, "main Meetup map should zoom to the selected dense-area detail width")

    def test_map_pan_clamp_and_sibling_map_limits_remain(self):
        self.assertRegex(SOURCE, r"const clamp=\(\)=>\{vb\.w=Math\.min\(W,vb\.w\);vb\.h=vb\.w\*ASPECT;vb\.x=Math\.max\(0,Math\.min\(W-vb\.w,vb\.x\)\);vb\.y=Math\.max\(0,Math\.min\(H-vb\.h,vb\.y\)\);\};")
        monthly = SOURCE.split("/* Interactive \"met this month\" map", 1)[1].split("/*", 1)[0]
        events = SOURCE.split("/* Interactive events map", 1)[1].split("/*", 1)[0]
        self.assertRegex(monthly, r"MINW=110")
        self.assertRegex(events, r"MINW=110")


if __name__ == "__main__":
    unittest.main()
