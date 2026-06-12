CHART_COLORS = [
    '#111111',
    '#444444',
    '#777777',
    '#999999',
    '#bbbbbb',
]


def apply_enterprise_chart_style(fig):
    fig.update_layout(
        template='plotly_white',
        paper_bgcolor='white',
        plot_bgcolor='white',
        font={
            'family': 'Inter, Segoe UI, sans-serif',
            'color': '#111111',
            'size': 13,
        },
        title={
            'font': {'color': '#111111', 'size': 18},
            'x': 0.01,
        },
        colorway=CHART_COLORS,
        legend={
            'font': {'color': '#111111'},
            'bgcolor': 'rgba(0,0,0,0)',
        },
    )

    fig.update_xaxes(
        gridcolor='#eeeeee',
        linecolor='#dddddd',
        tickfont={'color': '#111111'},
        title_font={'color': '#111111'},
    )

    fig.update_yaxes(
        gridcolor='#eeeeee',
        linecolor='#dddddd',
        tickfont={'color': '#111111'},
        title_font={'color': '#111111'},
    )

    return fig


def setup_global_chart_theme():
    import plotly.io as pio
    import plotly.graph_objects as go
    
    enterprise_template = go.layout.Template()
    enterprise_template.layout = go.Layout(
        paper_bgcolor='white',
        plot_bgcolor='white',
        font={
            'family': 'Inter, Segoe UI, sans-serif',
            'color': '#111111',
            'size': 13,
        },
        title={
            'font': {'color': '#111111', 'size': 18},
            'x': 0.01,
        },
        colorway=CHART_COLORS,
        legend={
            'font': {'color': '#111111'},
            'bgcolor': 'rgba(0,0,0,0)',
        },
        xaxis={
            'gridcolor': '#eeeeee',
            'linecolor': '#dddddd',
            'tickfont': {'color': '#111111'},
            'title': {'font': {'color': '#111111'}},
        },
        yaxis={
            'gridcolor': '#eeeeee',
            'linecolor': '#dddddd',
            'tickfont': {'color': '#111111'},
            'title': {'font': {'color': '#111111'}},
        }
    )
    
    pio.templates["enterprise"] = enterprise_template
    pio.templates.default = "plotly_white+enterprise"
