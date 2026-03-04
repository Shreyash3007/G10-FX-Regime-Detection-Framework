# reports package — all report generators for the fx_regime pipeline.
#
# Structure (current state → target state):
#   text.py        ← generate_text_brief()  [wired from morning_brief.py]
#   html.py        ← generate_html_brief()  [wired from create_html_brief.py]
#   template.py    ← HTML_TEMPLATE string   [eliminates circular self-reading]
#
# Migration plan:
#   1. text.py wraps morning_brief.generate_brief()  — no logic duplication
#   2. html.py wraps create_html_brief.generate_html_brief() — same
#   3. Once template.py is written, html.py builds page from scratch
#      (no reading of previous brief as template)
#
# For now, call morning_brief and create_html_brief directly via run.py.
