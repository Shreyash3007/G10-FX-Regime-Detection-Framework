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
    """Load data from latest generated brief file."""
    # Find latest brief file
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
document.querySelectorAll('.chart-tab').forEach(tab => {
  tab.addEventListener('click', function() {
    const pair = this.dataset.pair;
    const tabIdx = this.dataset.tab;

    document.querySelectorAll(
      `.chart-tab[data-pair="${pair}"]`
    ).forEach(t => t.classList.remove('active'));

    document.querySelectorAll(
      `.chart-pane[data-pair="${pair}"]`
    ).forEach(p => {
      p.style.visibility = 'hidden';
      p.style.position = 'absolute';
      p.style.pointerEvents = 'none';
    });

    this.classList.add('active');

    const pane = document.querySelector(
      `.chart-pane[data-pair="${pair}"][data-pane="${tabIdx}"]`
    );
    pane.style.visibility = 'visible';
    pane.style.position = 'relative';
    pane.style.pointerEvents = 'auto';

    setTimeout(function() {
      pane.querySelectorAll('.plotly-graph-div').forEach(function(plot) {
        Plotly.Plots.resize(plot);
      });
    }, 60);
  });
});

window.addEventListener('load', function() {
  document.querySelectorAll('.plotly-graph-div').forEach(function(plot) {
    if (plot.data) Plotly.Plots.resize(plot);
  });
});
'''
    
    # Find the last <script>...</script> block and replace its body
    last_script = list(_re.finditer(r'(<script>)(.*?)(</script>)', html_content, _re.DOTALL))
    if last_script:
        m = last_script[-1]
        html_content = (html_content[:m.start(2)] + definitive_handler +
                        html_content[m.end(2):])
    
    # ====================================================================
    # CRITICAL FIX: Defer all Plotly.newPlot calls until window.load
    # ====================================================================
    # Plotly's inline <script> tags call Plotly.newPlot() during HTML parsing,
    # before the browser computes flex layout.  At that moment the container
    # has width=0 so every chart collapses to a single vertical line.
    #
    # Strategy: inject a script RIGHT AFTER the Plotly CDN <script> that
    # monkey-patches Plotly.newPlot to queue calls; then on window.load
    # it replays them (container now has its real pixel width) and
    # restores the original function.
    # ====================================================================
    
    deferred_script = '''<script>
(function(){
  var _orig = Plotly.newPlot.bind(Plotly);
  var _q = [];
  Plotly.newPlot = function(){_q.push(Array.prototype.slice.call(arguments)); return Promise.resolve();};
  window.addEventListener("load", function(){
    Plotly.newPlot = _orig;
    _q.forEach(function(a){_orig.apply(Plotly, a);});
  });
})();
</script>'''
    
    # Insert right after the Plotly CDN script tag
    html_content = html_content.replace(
        '</script>\n<style>',
        '</script>\n' + deferred_script + '\n<style>',
        1  # only the first occurrence (CDN script is first)
    )
    
    # Save the modified brief
    os.makedirs('briefs', exist_ok=True)
    output_file = f'briefs/brief_{DATE_SLUG}.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Generated: {output_file}")

if __name__ == '__main__':
    generate_html_brief()