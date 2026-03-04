import os
import glob
import pandas as pd
import numpy as np
import sys
from core.utils import ordinal, embed_image, fmt_pct, color_class
from config import TODAY, TODAY_FMT, DATE_SLUG


# ============================================================================
# STEP 3B — Import and call chart functions
# ============================================================================

from charts.registry import CHART_REGISTRY
import plotly.io as pio

plotly_config = dict(scrollZoom=True, displayModeBar=False)

def fig_to_div(fig, height=480):
    if fig is None:
        return '<div style="color:#555;padding:20px;font-size:11px;">Chart unavailable</div>'
    div = pio.to_html(
        fig,
        full_html=False,
        config=plotly_config,
        include_plotlyjs=False,
        div_id=None,
        default_width='100%',
        default_height=f'{height}px'
    )
    return f'<div style="width:100%;height:{height}px;overflow:hidden;">{div}</div>'

# Build all chart divs from the registry — adding a new pair only requires
# updating charts/registry.py; no changes needed here.
CHART_DIVS = {
    (pair, pane): fig_to_div(builder(pair), height)
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
    """Generate complete HTML brief with Plotly charts and tabs."""
    brief_file = load_latest_brief_data()
    if not brief_file:
        print("No previous brief found. Create a text brief first with morning_brief.py")
        return
    
    # Read the previous brief as template
    with open(brief_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # INJECT fresh chart divs from registry — loops over ALL registered pairs/panes
    import re
    chart_map = {
        (pair, str(pane)): div
        for (pair, pane), div in CHART_DIVS.items()
    }
    for (pair, pane), new_div in chart_map.items():
        if new_div is None:
            continue
        # Chart content is always a single long line after the opening tag.
        # Match opening tag + the one content line; leave the closing </div> untouched.
        pattern = (
            rf'(<div class="chart-pane"[^>]*data-pair="{pair}"[^>]*'
            rf'data-pane="{pane}"[^>]*>)'
            rf'(\n[^\n]*)'   # one content line (may be empty on first run)
        )
        html_content = re.sub(
            pattern,
            lambda m, d=new_div: m.group(1) + '\n' + d,
            html_content
        )
    
    # FIX: card-body 380px clips charts (tallest is 480px). Bump to min-height.
    html_content = html_content.replace(
        '.card-body {\n    height: 380px;\n',
        '.card-body {\n    min-height: 520px;\n'
    )

    # FIX: chart-display-area needs an explicit min-height so flex-grow works
    html_content = html_content.replace(
        '.chart-display-area {\n    flex-grow: 1;\n    position: relative;\n    overflow: hidden;\n}',
        '.chart-display-area {\n    flex-grow: 1;\n    min-height: 420px;\n    position: relative;\n    overflow: hidden;\n}'
    )

    # DIAGNOSTIC 2 FIX: Change CSS from display:none to visibility:hidden (keeps element in layout)
    html_content = html_content.replace(
        '.chart-pane {\n    display: none;\n    width: 100%;\n    overflow: visible;\n}',
        '.chart-pane {\n    width: 100%;\n    overflow: visible;\n}'
    )
    
    # DIAGNOSTIC 2 FIX: Convert inline styles from display:block/none to visibility:visible/hidden
    # First pane (initially visible)
    html_content = html_content.replace(
        'style="display:block; width:100%;"',
        'style="visibility:visible; position:relative; pointer-events:auto; width:100%;"'
    )
    # Hidden panes
    html_content = html_content.replace(
        'style="display:none; width:100%;"',
        'style="visibility:hidden; position:absolute; pointer-events:none; width:100%;"'
    )
    
    # ====================================================================
    # REPLACE the entire last <script> block with definitive tab handler
    # ====================================================================
    # Instead of trying to match specific old handler text (which varies
    # depending on which version is in the archive), find the last <script>
    # block and replace its content entirely.
    # ====================================================================
    import re as _re
    
    definitive_handler = r'''
document.querySelectorAll('.chart-tab').forEach(function(tab) {
  tab.addEventListener('click', function() {
    var pair   = this.dataset.pair;
    var tabIdx = this.dataset.tab;

    document.querySelectorAll('.chart-tab[data-pair="' + pair + '"]')
      .forEach(function(t) { t.classList.remove('active'); });

    document.querySelectorAll('.chart-pane[data-pair="' + pair + '"]')
      .forEach(function(p) {
        p.style.visibility   = 'hidden';
        p.style.position     = 'absolute';
        p.style.pointerEvents = 'none';
      });

    this.classList.add('active');

    var pane = document.querySelector(
      '.chart-pane[data-pair="' + pair + '"][data-pane="' + tabIdx + '"]'
    );
    pane.style.visibility   = 'visible';
    pane.style.position     = 'relative';
    pane.style.pointerEvents = 'auto';

    // resize the chart that just became visible
    setTimeout(function() {
      pane.querySelectorAll('.plotly-graph-div').forEach(function(el) {
        Plotly.Plots.resize(el);
      });
    }, 50);
  });
});

// On full page load flex layout is computed — resize every chart once.
window.addEventListener('load', function() {
  document.querySelectorAll('.plotly-graph-div').forEach(function(el) {
    Plotly.Plots.resize(el);
  });
});
'''

    # ====================================================================
    # Remove any old deferred-init scripts (idempotency from previous runs)
    # ====================================================================
    html_content = _re.sub(
        r'\n?<script>\s*\(function\(\)\{\s*var _orig = Plotly\.newPlot.*?\}\)\(\);\s*</script>\n?',
        '',
        html_content,
        flags=_re.DOTALL
    )

    # ====================================================================
    # Replace the last plain <script> block with the definitive handler
    # ====================================================================
    all_scripts = list(_re.finditer(r'(<script>)(.*?)(</script>)', html_content, _re.DOTALL))
    if all_scripts:
        m = all_scripts[-1]
        html_content = (html_content[:m.start(2)] + definitive_handler +
                        html_content[m.end(2):])
    
    # Save the modified brief
    os.makedirs('briefs', exist_ok=True)
    output_file = f'briefs/brief_{DATE_SLUG}.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated: {output_file}")

if __name__ == '__main__':
    generate_html_brief()