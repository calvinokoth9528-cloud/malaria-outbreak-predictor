"""
LinkedIn Banner Image Generator — Calvin Omondi Okoth
1584 x 396 pixels (LinkedIn recommended size)
"""
import sys, os, io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

# Output
out = os.path.join('docs', 'images', 'linkedin_banner.png')
os.makedirs(os.path.dirname(out), exist_ok=True)

# LinkedIn banner: 1584 x 396
fig, ax = plt.subplots(1, 1, figsize=(15.84, 3.96), dpi=150)
ax.set_xlim(0, 100)
ax.set_ylim(0, 25)
ax.set_aspect('equal')
ax.axis('off')

# --- Background gradient ---
gradient = np.linspace(0, 1, 256).reshape(1, -1)
gradient = np.vstack([gradient] * 256)
ax.imshow(gradient, aspect='auto', cmap=plt.cm.RdYlBu_r,
          extent=[0, 100, 0, 25], alpha=0.35, zorder=0)

# Dark overlay
overlay = plt.Rectangle((0, 0), 100, 25, fc='#1a1a2e', alpha=0.82, zorder=1)
ax.add_patch(overlay)

# --- Decorative data viz elements (background) ---
np.random.seed(42)

# Scatter points (like a data cloud)
x_scatter = np.random.uniform(60, 95, 120)
y_scatter = np.random.uniform(3, 22, 120)
colors_scatter = plt.cm.plasma(np.linspace(0.2, 0.9, 120))
sizes_scatter = np.random.uniform(8, 60, 120)
ax.scatter(x_scatter, y_scatter, c=colors_scatter, s=sizes_scatter, alpha=0.15, zorder=2)

# Fake trend line (malaria decline)
x_trend = np.linspace(62, 95, 50)
y_trend = 20 - (x_trend - 62) * 0.35 + np.sin(x_trend * 0.5) * 0.5
ax.plot(x_trend, y_trend, color='#e94560', linewidth=2.5, alpha=0.5, zorder=2)
ax.fill_between(x_trend, y_trend - 1.5, y_trend, alpha=0.08, color='#e94560', zorder=2)

# Grid lines (subtle)
for y in [5, 10, 15, 20]:
    ax.axhline(y=y, color='white', linewidth=0.3, alpha=0.1, zorder=2)
for x in [65, 70, 75, 80, 85, 90]:
    ax.axvline(x=x, color='white', linewidth=0.3, alpha=0.1, zorder=2)

# --- Accent bar (left side) ---
accent = FancyBboxPatch((0, 0), 0.8, 25, boxstyle="square,pad=0",
                         fc='#e94560', ec='none', zorder=3)
ax.add_patch(accent)

# --- Text content ---
# Name
ax.text(4, 17.5, 'CALVIN OMONDI OKOTH', fontsize=18, fontweight='bold',
        color='white', fontfamily='sans-serif', zorder=5, va='center')

# Headline line 1
ax.text(4, 13.5, 'Data Scientist & ML Engineer', fontsize=12,
        color='#e94560', fontweight='bold', fontfamily='sans-serif', zorder=5)

# Headline line 2
ax.text(4, 11, 'Building Open-Source Public Health AI', fontsize=10,
        color='#cccccc', fontfamily='sans-serif', zorder=5)

# Divider line
ax.plot([4, 45], [9.2, 9.2], color='#e94560', linewidth=1.5, alpha=0.6, zorder=5)

# Tech stack pills
pill_y = 7
pill_labels = ['R', 'Python', 'scikit-learn', 'FastAPI', 'Docker', 'Shiny']
pill_x = 4
for i, label in enumerate(pill_labels):
    w = len(label) * 0.65 + 2
    pill = FancyBboxPatch((pill_x, pill_y - 1), w, 2.2,
                          boxstyle="round,pad=0.2",
                          fc='#e94560' if i < 2 else '#16213e',
                          ec='#e94560', linewidth=0.8, alpha=0.9, zorder=5)
    ax.add_patch(pill)
    ax.text(pill_x + w/2, pill_y + 0.1, label, fontsize=6.5,
            color='white', fontweight='bold', ha='center', va='center',
            fontfamily='sans-serif', zorder=6)
    pill_x += w + 1

# Bottom tagline
ax.text(4, 3, 'KEMRI-Inspired Malaria Prediction  |  44K+ Data Points  |  WHO + World Bank + NASA',
        fontsize=7, color='#888888', fontfamily='sans-serif', zorder=5)

# --- Right side: KEMRI badge ---
badge = plt.Circle((88, 12.5), 5.5, fc='#16213e', ec='#e94560',
                    linewidth=2, alpha=0.9, zorder=5)
ax.add_patch(badge)
ax.text(88, 14, 'ML', fontsize=16, fontweight='bold', color='#e94560',
        ha='center', va='center', fontfamily='sans-serif', zorder=6)
ax.text(88, 11.5, 'PREDICT', fontsize=7, color='white',
        ha='center', va='center', fontfamily='sans-serif', zorder=6, fontweight='bold')

plt.tight_layout(pad=0)
plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#1a1a2e', pad_inches=0)
plt.close()
print(f"Saved: {out}")
