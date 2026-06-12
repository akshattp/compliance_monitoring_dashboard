import plotly.express as px
from .theme import apply_enterprise_chart_style


def plot_branch_comparison(df, branch_column, value_column, title):

    summary = (
        df.groupby(branch_column)
        .agg(Total_Amount=(value_column, 'sum'))
        .reset_index()
        .sort_values('Total_Amount', ascending=False)
    )

    fig = px.bar(
        summary.head(25),
        x='Total_Amount',
        y=branch_column,
        orientation='h',
        title=title,
        text='Total_Amount'
    )

    # Enterprise styling
    fig.update_traces(
        marker=dict(
            color='black',
            line=dict(color='rgba(120,120,120,0.4)', width=1)
        ),
        textposition='outside',
        hovertemplate=
        '<b>%{y}</b><br>' +
        'Amount: %{x}<extra></extra>'
    )

    fig.update_layout(
        margin={'l': 90, 'r': 15, 't': 45, 'b': 45},
        yaxis={
            'categoryorder': 'total ascending',
            'showgrid': False
        },
        xaxis={
            'showgrid': True,
            'gridcolor': 'rgba(200,200,200,0.25)'
        },
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='y unified'
    )

    return apply_enterprise_chart_style(fig)