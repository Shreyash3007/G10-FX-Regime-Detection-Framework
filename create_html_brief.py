import os
import glob
import pandas as pd
import numpy as np
import sys
from core.utils import ordinal, embed_image, fmt_pct, color_class
from config import TODAY, TODAY_FMT, DATE_SLUG


# ============================================================================
# STEP 3B — Build charts as standalone HTML files and embed via <iframe>
#
# Why iframes? pio.to_html() embeds inline <script> tags that run before the
# browser flex layout is computed → container width=0 → broken charts.
# Each iframe gets its own full document layout so Plotly always renders at
# the correct container size, with no script timing issues.
# ============================================================================

from charts.registry import CHART_REGISTRY
import plotly.io as pio

plotly_config = dict(scrollZoom=True, displayModeBar=False)

CHARTS_DIR = 'charts'
os.makedirs(CHARTS_DIR, exist_ok=True)

def fig_to_iframe(fig, pair, pane, height=480):
    """Save figure as a standalone HTML file and return an <iframe> tag."""
    if fig is None:
        return (
            f'<div style="color:#555;padding:20px;font-size:11px;'
            f'height:{height}px;">Chart unavailable</div>'
        )
    chart_file = f'{CHARTS_DIR}/{pair}_{pane}.html'
    pio.write_html(
        fig,
        file=chart_file,
        config=plotly_config,
        full_html=True,
        include_plotlyjs='cdn',
        auto_open=False,
    )
    # brief lives in briefs/ so path to charts/ is ../charts/
    return (
        f'<iframe src="../{chart_file}" '
        f'style="width:100%;height:{height}px;border:none;display:block;" '
        f'loading="eager" scrolling="no"></iframe>'
    )

# Build all chart iframes from the registry at import time.
CHART_DIVS = {
    (pair, pane): fig_to_iframe(builder(pair), pair, pane, height)
    for (pair, pane), (builder, pair, height) in CHART_REGISTRY.items()
}

# ============================================================================
# Load brief data from existing generated brief
# ============================================================================
import shutil

def load_latest_brief_data():
    """Load the most recent HTML brief as the base template."""
    brief_files = sorted(glob.glob('briefs/brief_*.html'))
    if not brief_files:
        return None
    return brief_files[-1]

def generate_html_brief():
    """Generate complete HTML brief with charts embedded as iframes."""
    brief_file = load_latest_brief_data()
    if not brief_file:
        print("No previous brief found. Run morning_brief.py first.")
        return

    with open(brief_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    import re as _re

    # ------------------------------------------------------------------
    # 1. Inject chart iframes into chart-pane divs
    # ------------------------------------------------------------------
    chart_map = {
        (pair, str(pane)): iframe
        for (pair, pane), iframe in CHART_DIVS.items()
    }
    for (pair, pane_str), new_content in chart_map.items():
        pattern = (
            rf'(<div class="chart-pane"[^>]*data-pair="{pair}"[^>]*'
            rf'data-pane="{pane_str}"[^>]*>)'
            rf'(\n[^\n]*)'
        )
        html_content = _re.sub(
            pattern,
            lambda m, c=new_content: m.group(1) + '\n' + c,
            html_content,
        )

    # ------------------------------------------------------------------
    # 2. CSS patches (idempotent — cascade through version history)
    # ------------------------------------------------------------------
    # card-body: 380px → 520px (old) → 560px (current)
    html_content = html_content.replace(
        '.card-body {\n    height: 380px;\n',
        '.card-body {\n    min-height: 560px;\n    height: auto;\n',
    )
    html_content = html_content.replace(
        '.card-body {\n    min-height: 380px;\n',
        '.card-body {\n    min-height: 560px;\n    height: auto;\n',
    )
    html_content = html_content.replace(
        '.card-body {\n    min-height: 520px;\n',
        '.card-body {\n    min-height: 560px;\n    height: auto;\n',
    )
    # also handle briefs that already have height: auto line
    html_content = html_content.replace(
        '.card-body {\n    min-height: 520px;\n    height: auto;\n',
        '.card-body {\n    min-height: 560px;\n    height: auto;\n',
    )
    # chart-display-area: 420px → 480px
    html_content = html_content.replace(
        '.chart-display-area {\n    flex-grow: 1;\n    position: relative;\n    overflow: hidden;\n}',
        '.chart-display-area {\n    flex-grow: 1;\n    min-height: 480px;\n    position: relative;\n    overflow: hidden;\n}',
    )
    html_content = html_content.replace(
        '.chart-display-area {\n    flex-grow: 1;\n    min-height: 420px;\n    position: relative;\n    overflow: hidden;\n}',
        '.chart-display-area {\n    flex-grow: 1;\n    min-height: 480px;\n    position: relative;\n    overflow: hidden;\n}',
    )

    # ------------------------------------------------------------------
    # 3. Pane visibility (display → visibility so hidden panes keep size)
    # ------------------------------------------------------------------
    html_content = html_content.replace(
        'style="display:block; width:100%;"',
        'style="visibility:visible; position:relative; pointer-events:auto; width:100%;"',
    )
    html_content = html_content.replace(
        'style="display:none; width:100%;"',
        'style="visibility:hidden; position:absolute; pointer-events:none; width:100%;"',
    )

    # ------------------------------------------------------------------
    # 4. Remove stale deferred-init scripts from previous runs
    # ------------------------------------------------------------------
    html_content = _re.sub(
        r'\n?<script>\s*\(function\(\)\{\s*var _orig = Plotly\.newPlot.*?\}\)\(\);\s*</script>\n?',
        '',
        html_content,
        flags=_re.DOTALL,
    )

    # ------------------------------------------------------------------
    # 5. Replace last plain <script> block with clean tab handler
    #    (iframes are self-contained; no Plotly.Plots.resize needed)
    # ------------------------------------------------------------------
    tab_handler = '''
document.querySelectorAll('.chart-tab').forEach(function(tab) {
  tab.addEventListener('click', function() {
    var pair   = this.dataset.pair;
    var tabIdx = this.dataset.tab;

    document.querySelectorAll('.chart-tab[data-pair="' + pair + '"]')
      .forEach(function(t) { t.classList.remove('active'); });

    document.querySelectorAll('.chart-pane[data-pair="' + pair + '"]')
      .forEach(function(p) {
        p.style.visibility    = 'hidden';
        p.style.position      = 'absolute';
        p.style.pointerEvents = 'none';
      });

    this.classList.add('active');

    var pane = document.querySelector(
      '.chart-pane[data-pair="' + pair + '"][data-pane="' + tabIdx + '"]'
    );
    pane.style.visibility    = 'visible';
    pane.style.position      = 'relative';
    pane.style.pointerEvents = 'auto';
  });
});
'''

    all_scripts = list(_re.finditer(r'(<script>)(.*?)(</script>)', html_content, _re.DOTALL))
    if all_scripts:
        m = all_scripts[-1]
        html_content = html_content[:m.start(2)] + tab_handler + html_content[m.end(2):]

    # ------------------------------------------------------------------
    # 6. Write output
    # ------------------------------------------------------------------
    os.makedirs('briefs', exist_ok=True)
    output_file = f'briefs/brief_{DATE_SLUG}.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Generated: {output_file}")

if __name__ == '__main__':
    generate_html_brief()
