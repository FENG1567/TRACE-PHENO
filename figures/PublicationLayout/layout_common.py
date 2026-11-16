"""Shared typography, panel headers and exports for the publication figures."""
from pathlib import Path
import os
from matplotlib import font_manager
import json
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.text import Text
from matplotlib.patches import FancyBboxPatch
from data_and_prior_layout import P, STATUS, CAPABILITY, REVISION, DATA, OLD_SOURCE, read_csv

OUT = Path(__file__).resolve().parent
FONT_FAMILY = os.environ.get("TRACE_PHENO_FONT_FAMILY", "")
if not FONT_FAMILY:
    for candidate in ("Arial", "Liberation Sans", "DejaVu Sans"):
        try:
            font_manager.findfont(candidate, fallback_to_default=False)
            FONT_FAMILY = candidate
            break
        except ValueError:
            continue
if not FONT_FAMILY:
    raise RuntimeError("No supported sans-serif font is installed")
mpl.rcParams.update({
    'font.family': FONT_FAMILY, 'font.sans-serif': [FONT_FAMILY],
    'font.size': 10, 'font.weight': 'bold',
    'axes.labelsize': 10, 'axes.labelweight': 'bold',
    'axes.titlesize': 11, 'axes.titleweight': 'bold',
    'xtick.labelsize': 9, 'ytick.labelsize': 9,
    'legend.fontsize': 9.2, 'legend.frameon': False,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.linewidth': 1, 'xtick.major.size': 3, 'ytick.major.size': 3,
    'xtick.major.pad': 3, 'ytick.major.pad': 3,
    'pdf.fonttype': 42, 'ps.fonttype': 42, 'svg.fonttype': 'none',
    'savefig.facecolor': 'white',
})


def canvas(height, width=7.6):
    fig = plt.figure(figsize=(width, height), facecolor='white')
    fig._box_texts = []
    fig._panel_labels = []
    return fig


def panel(fig, rect, letter, title, *, margins=(40, 31, 8, 30), title_size=11):
    """Reserve a physical header strip above each independently laid-out panel."""
    x, y, width, height = rect
    fw, fh = fig.get_size_inches() * 72
    fig.text(x, y + height - 1 / fh, letter, fontsize=18, va='top', ha='left')
    fig._panel_labels.append(letter)
    fig.text(x + 24 / fw, y + height - 5 / fh, title,
             fontsize=title_size, va='top', ha='left', linespacing=1.1)
    left, bottom, right, top = margins
    ax = fig.add_axes([x + left / fw, y + bottom / fh,
                       width - (left + right) / fw, height - (bottom + top) / fh])
    return ax


def diagram(fig, rect, letter, title, *, title_size=11):
    ax = panel(fig, rect, letter, title, margins=(4, 3, 4, 29), title_size=title_size)
    ax.set(xlim=(0, 1), ylim=(0, 1))
    ax.axis('off')
    return ax


def box(ax, x, y, width, height, text, *, fc='#F5F8FA', ec='#718096',
        fs=10, color='#18212B'):
    patch = FancyBboxPatch((x, y), width, height,
                           boxstyle='round,pad=0,rounding_size=0.008',
                           facecolor=fc, edgecolor=ec, linewidth=1.1)
    ax.add_patch(patch)
    label = ax.text(x + width / 2, y + height / 2, text, ha='center', va='center',
                    fontsize=fs, color=color, linespacing=1.18)
    ax.figure._box_texts.append((patch, label))
    return patch


def arrow(ax, start, end, color='#65727E'):
    ax.annotate('', xy=end, xytext=start,
                arrowprops={'arrowstyle': '-|>', 'lw': 1.3, 'color': color,
                            'shrinkA': 1, 'shrinkB': 1})


def grid(ax, axis='x'):
    ax.set_axisbelow(True)
    ax.grid(axis=axis, color='#D5DCE1', linewidth=.65, alpha=.7)


def export(fig, stem):
    for text in fig.findobj(match=Text):
        text.set_fontfamily(FONT_FAMILY)
        text.set_fontweight('bold')
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    outside, box_issues = [], []
    for text in fig.findobj(match=Text):
        if not text.get_visible() or not text.get_text().strip():
            continue
        bounds = text.get_window_extent(renderer)
        if bounds.x0 < -1 or bounds.y0 < -1 or bounds.x1 > fig.bbox.width + 1 or bounds.y1 > fig.bbox.height + 1:
            outside.append(text.get_text())
    for patch, text in fig._box_texts:
        area = patch.get_window_extent(renderer)
        content = text.get_window_extent(renderer)
        if content.x0 < area.x0 + 2 or content.x1 > area.x1 - 2 or content.y0 < area.y0 + 2 or content.y1 > area.y1 - 2:
            box_issues.append(text.get_text())
    if outside or box_issues:
        print('figure layout issue', stem, outside, box_issues, flush=True)
    fig.savefig(OUT / (stem + '.svg'), facecolor='white')
    fig.savefig(OUT / (stem + '.pdf'), facecolor='white')
    fig.savefig(OUT / (stem + '_preview.png'), dpi=300, facecolor='white')
    fig.savefig(OUT / (stem + '.tif'), dpi=600, facecolor='white', pil_kwargs={'compression': 'tiff_lzw'})
    plt.close(fig)
    print('EXPORTED', stem, flush=True)
