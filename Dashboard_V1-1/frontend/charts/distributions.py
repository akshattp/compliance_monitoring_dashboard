import plotly.express as px
from .theme import apply_enterprise_chart_style


def plot_donut(df, names, values, title):
    fig = px.pie(df, names=names, values=values, hole=0.55, title=title)
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(margin={'l': 15, 'r': 15, 't': 45, 'b': 15}, legend={'orientation': 'h', 'y': -0.1})
    return apply_enterprise_chart_style(fig)


def plot_bar(df, x, y, title, color=None, orientation='v', text_auto=True):

    fig = px.bar(
        df,
        x=x,
        y=y,
        color=color,
        title=title,
        orientation=orientation,
        text_auto=text_auto
    )

    # Enterprise Black Theme Styling
    fig.update_traces(
        marker=dict(
            color='black',
            line=dict(
                color='rgba(140,140,140,0.35)',
                width=1
            )
        ),
        textposition='outside',
        hovertemplate=
        '<b>%{x}</b><br>' +
        'Value: %{y}<extra></extra>'
        if orientation == 'v'
        else
        '<b>%{y}</b><br>' +
        'Value: %{x}<extra></extra>'
    )

    fig.update_layout(
        margin={'l': 15, 'r': 15, 't': 45, 'b': 15},

        plot_bgcolor='white',
        paper_bgcolor='white',

        hovermode='closest',

        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(210,210,210,0.25)',
            zeroline=False
        ),

        yaxis=dict(
            showgrid=True,
            gridcolor='rgba(210,210,210,0.25)',
            zeroline=False
        )
    )

    if orientation == 'h':
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'}
        )

    return apply_enterprise_chart_style(fig)