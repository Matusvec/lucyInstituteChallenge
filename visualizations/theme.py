"""
Shared color theme for Lucy Institute visualizations.

DARK_BLUE  = "#0C2340"   # Dark Blue
MID_BLUE   = "#3B5E8C"   # Midpoint between dark blue and light
GOLD_BROWN = "#BFA15D"   # Golden Brown
TEAL       = "#4EAE81"   # Teal
DARK_TEAL  = "#1B3B2C"   # Dark Teal
"""

# Hex (for matplotlib)
DARK_BLUE = "#0C2340"
MID_BLUE = "#3B5E8C"
GOLD_BROWN = "#BFA15D"
TEAL = "#4EAE81"
DARK_TEAL = "#1B3B2C"

# RGB strings (for Plotly)
DARK_BLUE_RGB = "rgb(12, 35, 64)"
MID_BLUE_RGB = "rgb(59, 94, 140)"
GOLD_BROWN_RGB = "rgb(191, 161, 93)"
TEAL_RGB = "rgb(78, 174, 129)"
DARK_TEAL_RGB = "rgb(27, 59, 44)"

# Light variants for high-end of scales
LIGHT_TEAL = "rgb(140, 220, 180)"
LIGHT_GOLD = "rgb(230, 210, 150)"

# Background (dark blue)
BG_COLOR = DARK_BLUE_RGB

# Plotly colorscales (low→high): Dark blue background → lighter → brighter red
# Blends into background at low end; gets redder and brighter toward high end
SCALE_BLUE_TO_RED = [
    [0.00, DARK_BLUE_RGB],           # 0: matches background
    [0.08, "rgb(25, 55, 95)"],       # slightly lighter blue
    [0.18, "rgb(50, 90, 140)"],      # mid blue
    [0.32, "rgb(90, 130, 180)"],     # light blue
    [0.48, "rgb(160, 140, 180)"],    # pale blue-purple
    [0.60, "rgb(220, 120, 80)"],     # orange
    [0.75, "rgb(255, 80, 50)"],      # red-orange
    [0.88, "rgb(255, 45, 35)"],      # bright red
    [1.00, "rgb(255, 20, 20)"],      # pure bright red (max)
]

# All map metrics use the same blue→red scale
SCALE_OVERDOSE = SCALE_BLUE_TO_RED
SCALE_RX = SCALE_BLUE_TO_RED
SCALE_MME = SCALE_BLUE_TO_RED
SCALE_MEDICAID = SCALE_BLUE_TO_RED
SCALE_FENTANYL = SCALE_BLUE_TO_RED
