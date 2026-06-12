import plotly.express as px
from .theme import apply_enterprise_chart_style


def plot_trend(df, date_column, value_column, title, mode='lines+markers'):
    fig = px.line(
        df,
        x=date_column,
        y=value_column,
        title=title,
        markers=True
    )

    # Black line + light grey filled area
    fig.update_traces(
        mode=mode,
        line=dict(color='black', width=3),
        marker=dict(color='black', size=6),
        fill='tozeroy',
        fillcolor='rgba(180,180,180,0.25)'
    )

    fig.update_layout(
        margin={'l': 15, 'r': 15, 't': 45, 'b': 15},
        xaxis_title=date_column,
        yaxis_title=value_column,
        hovermode='x unified'
    )

    return apply_enterprise_chart_style(fig)


def plot_weekly_trend(df, week_column, value_column, title):
    fig = px.line(
        df,
        x=week_column,
        y=value_column,
        title=title,
        markers=True
    )

    # Black line + light grey filled area
    fig.update_traces(
        line=dict(color='black', width=3),
        marker=dict(color='black', size=6),
        fill='tozeroy',
        fillcolor='rgba(180,180,180,0.25)'
    )

    fig.update_layout(
        margin={'l': 15, 'r': 15, 't': 45, 'b': 15},
        xaxis_title='Week',
        yaxis_title=value_column,
        hovermode='x unified'
    )

    return apply_enterprise_chart_style(fig)
