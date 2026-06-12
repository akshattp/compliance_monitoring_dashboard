import plotly.graph_objects as go
from .theme import apply_enterprise_chart_style


def plot_heatmap(df, x, y, z, title):
    pivot = df.pivot_table(index=y, columns=x, values=z, aggfunc='sum', fill_value=0)
    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns.astype(str),
        y=pivot.index.astype(str),
        colorscale=[
            [0, '#111827'],
            [0.35, '#1f2937'],
            [0.7, '#64748b'],
            [1, '#d1d5db'],
        ],
        colorbar={'tickfont': {'color': '#9ca3af'}},
    ))
    fig.update_layout(title=title, xaxis_title=str(x), yaxis_title=str(y), margin={'l': 80, 'r': 15, 't': 45, 'b': 45})
    return apply_enterprise_chart_style(fig)
