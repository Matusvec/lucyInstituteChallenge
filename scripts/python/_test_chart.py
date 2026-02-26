"""
Save prescriptionsVsOverdose chart as PNG.

Run from project root: python scripts/python/_test_chart.py
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

# Project root is parent of scripts/
_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(_script_dir))
import sys
sys.path.insert(0, project_root)
viz_path = os.path.join(project_root, "visualizations", "prescriptionsVsOverdose.py")

code = open(viz_path, encoding="utf-8").read()
code = code.replace("plt.show()", "plt.savefig(os.path.join(BASE, 'output', 'cdc', 'rx_vs_overdose_by_type.png'), dpi=150, bbox_inches='tight'); print('Chart saved!')")

exec(compile(code, viz_path, "exec"), {"__file__": viz_path, "__name__": "__main__"})
