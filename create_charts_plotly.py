import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import datetime, timedelta


def build_eurusd_fundamentals_prototype():
    df = pd.read_csv('data/latest_with_cot.csv', index_col=0, parse_dates=True)

    cutoff = df.index.max() - timedelta(days=365)
    df = df[df.index >= cutoff]
    df = df[df['EURUSD'].notna()]

    # The correlation column in the CSV is EURUSD_spread_corr_60d
    corr_col = 'EURUSD_spread_corr_60d'

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.45, 0.35, 0.20],
        vertical_spacing=0.06,
    )

    # --- Subplot 1: EUR/USD price ---
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['EURUSD'],
            mode='lines',
            line=dict(color='#4da6ff', width=1.5),
            name='EUR/USD',
            hovertemplate='%{x|%d %b %Y}<br>%{y:.4f}<extra></extra>',
        ),
        row=1, col=1,
    )

    # --- Subplot 2: Dual spreads ---
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['US_DE_10Y_spread'],
            mode='lines',
            line=dict(color='#2980b9'),
            name='US 2Y - DE 10Y',
            hovertemplate='%{x|%d %b %Y}<br>%{y:.2f}%<extra></extra>',
        ),
        row=2, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['US_DE_2Y_spread'],
            mode='lines',
            line=dict(color='#e67e22'),
            name='US 2Y - DE 2Y',
            hovertemplate='%{x|%d %b %Y}<br>%{y:.2f}%<extra></extra>',
        ),
        row=2, col=1,
    )
    fig.add_hline(y=0, line_dash='dash', line_color='#444444', line_width=1, row=2, col=1)

    # --- Subplot 3: Regime correlation ---
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df[corr_col],
            mode='lines',
            line=dict(color='#cccccc', width=1),
            name='60D Corr',
            hovertemplate='%{x|%d %b %Y}<br>%{y:.2f}<extra></extra>',
        ),
        row=3, col=1,
    )
    # INTACT threshold
    fig.add_hline(y=0.6, line_color='#00d4aa', line_dash='dash', line_width=1, row=3, col=1)
    # BROKEN threshold
    fig.add_hline(y=0.3, line_color='#ff4444', line_dash='dash', line_width=1, row=3, col=1)
    # Broken zone (below 0.3)
    fig.add_hrect(y0=-1, y1=0.3, fillcolor='rgba(255,68,68,0.05)', line_width=0, row=3, col=1)
    # Intact zone (above 0.6)
    fig.add_hrect(y0=0.6, y1=1, fillcolor='rgba(0,212,170,0.05)', line_width=0, row=3, col=1)

    # --- Theme ---
    fig.update_layout(
        template='plotly_dark',
        paper_bgcolor='#0d0d0d',
        plot_bgcolor='#141414',
        font=dict(family='Inter, system-ui, sans-serif', color='#cccccc', size=11),
        height=520,
        margin=dict(l=50, r=30, t=30, b=30),
        legend=dict(bgcolor='rgba(0,0,0,0)', borderwidth=0,
                    font=dict(size=10, color='#888888')),
        hovermode='x unified',
        hoverlabel=dict(bgcolor='#1a1a1a', bordercolor='#333333',
                        font=dict(color='#cccccc', size=11)),
        xaxis_showgrid=True, xaxis_gridcolor='#1e1e1e', xaxis_gridwidth=1,
        yaxis_showgrid=True, yaxis_gridcolor='#1e1e1e', yaxis_gridwidth=1,
        dragmode='pan',
    )

    fig.update_xaxes(
        showgrid=True, gridcolor='#1e1e1e', gridwidth=1,
        showline=False, zeroline=False,
        tickfont=dict(size=10, color='#666666'),
    )
    fig.update_yaxes(
        showgrid=True, gridcolor='#1e1e1e', gridwidth=1,
        showline=False, zeroline=False,
        tickfont=dict(size=10, color='#666666'),
    )

    # --- Subplot title annotations ---
    # y positions are derived from row_heights=[0.45, 0.35, 0.20] and spacing=0.06
    # Row domains (bottom to top): row3=[0,0.20], row2=[0.26,0.61], row1=[0.67,1.0]
    subplot_titles = [
        dict(
            text='EUR/USD PRICE',
            x=0.01, y=1.0,
            xref='paper', yref='paper',
            xanchor='left', yanchor='top',
            font=dict(size=9, color='#555555'),
            showarrow=False,
        ),
        dict(
            text='RATE DIFFERENTIALS (pp) \u2014 narrowing = EUR/USD should rise',
            x=0.01, y=0.61,
            xref='paper', yref='paper',
            xanchor='left', yanchor='top',
            font=dict(size=9, color='#555555'),
            showarrow=False,
        ),
        dict(
            text='REGIME CORRELATION (60D)',
            x=0.01, y=0.20,
            xref='paper', yref='paper',
            xanchor='left', yanchor='top',
            font=dict(size=9, color='#555555'),
            showarrow=False,
        ),
    ]
    fig.update_layout(annotations=fig.layout.annotations + tuple(subplot_titles))

    return fig


if __name__ == '__main__':
    import plotly.io as pio
    fig = build_eurusd_fundamentals_prototype()
    pio.write_html(fig, 'prototype_test.html',
                   config=dict(scrollZoom=True, displayModeBar=False))
    print('saved: prototype_test.html')
