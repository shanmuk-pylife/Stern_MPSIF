import json
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output
import plotly.graph_objects as go

# Load JSON data from an external file with UTF-8 encoding
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Extract available years (assumed to be strings)
available_years = sorted(list(data.keys()))

# External stylesheets: Bootstrap theme and animate.css for animations
external_stylesheets = [
    dbc.themes.FLATLY,
    "https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"
]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "MPSIF Fund Dashboard"

# -------------------------
# Define layouts for each tab
# -------------------------

# Overview tab: Choose year and semester and display detailed report
overview_layout = dbc.Container([
    dbc.Row(
        dbc.Col(
            html.H2("Overview", className="text-center text-primary animate__animated animate__fadeInDown"),
            width=12
        ), className="mb-4"
    ),
    dbc.Row([
        dbc.Col([
            dbc.Label("Select Year:", className="font-weight-bold"),
            dcc.Dropdown(
                id='overview-year-dropdown',
                options=[{'label': year, 'value': year} for year in available_years],
                value=available_years[0],
                clearable=False
            )
        ], width=4),
        dbc.Col([
            dbc.Label("Select Semester:", className="font-weight-bold"),
            dcc.Dropdown(
                id='overview-semester-dropdown',
                options=[],  # Will update via callback
                clearable=False
            )
        ], width=4)
    ], className="mb-4"),
    html.Div(id='overview-report-content', className="animate__animated animate__fadeInUp")
], fluid=True)

# Comparisons tab: Multiple years comparison graph using 6-month returns
comparisons_layout = dbc.Container([
    dbc.Row(
        dbc.Col(
            html.H2("Comparisons", className="text-center text-primary animate__animated animate__fadeInDown"),
            width=12
        ), className="mb-4"
    ),
    dbc.Row([
        dbc.Col([
            dbc.Label("Select Years to Compare:", className="font-weight-bold"),
            dcc.Dropdown(
                id='compare-years-dropdown',
                options=[{'label': year, 'value': year} for year in available_years],
                value=[available_years[0]],
                multi=True
            )
        ], width=12, className="mb-4")
    ]),
    dbc.Row(
        dbc.Col(
            dcc.Graph(id='year-comparison-graph', className="animate__animated animate__fadeInUp"),
            width=12
        )
    )
], fluid=True)

# Key Findings & Future Projections tab: Display key findings from the selected year and some static projection text
findings_future_layout = dbc.Container([
    dbc.Row(
        dbc.Col(
            html.H2("Key Findings & Future Projections", className="text-center text-primary animate__animated animate__fadeInDown"),
            width=12
        ), className="mb-4"
    ),
    dbc.Row([
        dbc.Col([
            dbc.Label("Select Year:", className="font-weight-bold"),
            dcc.Dropdown(
                id='findings-year-dropdown',
                options=[{'label': year, 'value': year} for year in available_years],
                value=available_years[0],
                clearable=False
            )
        ], width=4)
    ], className="mb-4"),
    dbc.Row(
        dbc.Col(
            html.Div(id='findings-content', className="animate__animated animate__fadeInUp")
        )
    )
], fluid=True)

# Investment Plan tab: Static content outlining the plan for 2025-2026
investment_plan_layout = dbc.Container([
    dbc.Row(
        dbc.Col(
            html.H2("Investment Plan for 2025-2026", className="text-center text-primary animate__animated animate__fadeInDown"),
            width=12
        ), className="mb-4"
    ),
    dbc.Row(
        dbc.Col(
            dbc.Card([
                dbc.CardBody([
                    html.P("Our investment plan for 2025-2026 focuses on diversification, sustainable growth, and strategic rebalancing. Key elements include:",
                           className="lead"),
                    html.Ul([
                        html.Li("Increased allocation to ESG-compliant sectors based on global trends."),
                        html.Li("Expansion into emerging markets with strong growth potential."),
                        html.Li("Enhanced risk management strategies to safeguard against volatility."),
                        html.Li("Optimization of asset allocation to maximize dividend yield and total return.")
                    ], className="lead"),
                    html.P("We are also investing in innovative portfolio management tools and advanced analytics to ensure that MPSIF remains a leader among student-managed funds.",
                           className="lead")
                ])
            ], className="shadow animate__animated animate__fadeInUp")
        )
    )
], fluid=True)

# Main layout: Tabs container holding all four tabs
app.layout = dbc.Container([
    dcc.Tabs(id='tabs-layout', value='overview', children=[
        dcc.Tab(label="Overview", value="overview", children=overview_layout),
        dcc.Tab(label="Comparisons", value="comparisons", children=comparisons_layout),
        dcc.Tab(label="Key Findings & Future Projections", value="findings_future", children=findings_future_layout),
        dcc.Tab(label="Investment Plan 2025-2026", value="investment_plan", children=investment_plan_layout)
    ])
], fluid=True, style={"backgroundColor": "#f8f9fa", "padding": "20px"})

# --------------------------------------
# Callbacks for each tab
# --------------------------------------

# Callback for updating the semester dropdown in the Overview tab
@app.callback(
    [Output('overview-semester-dropdown', 'options'),
     Output('overview-semester-dropdown', 'value')],
    [Input('overview-year-dropdown', 'value')]
)
def update_overview_semester(selected_year):
    semesters = list(data[selected_year].keys())
    options = [{'label': sem, 'value': sem} for sem in semesters]
    value = options[0]['value'] if options else None
    return options, value

# Callback for updating the Overview report content (similar to your previous code)
@app.callback(
    Output('overview-report-content', 'children'),
    [Input('overview-year-dropdown', 'value'),
     Input('overview-semester-dropdown', 'value')]
)
def update_overview_report(selected_year, selected_semester):
    if not selected_year or not selected_semester:
        return dbc.Alert("No data available.", color="warning")
    
    report = data.get(selected_year, {}).get(selected_semester, {})
    performance = report.get("performance_metrics", {})
    six_month = performance.get("6_month_return", "N/A")
    one_year = performance.get("1_year_return", "N/A")
    AUM = performance.get("AUM", "N/A")
    dividend = performance.get("dividend", "N/A")
    
    summary = report.get("summary", "Summary not available.")
    key_findings = report.get("key_findings", [])
    strategic_decisions = report.get("strategic_decisions", [])
    comparisons = report.get("comparisons", "Not available")
    
    graphs_data = report.get("graphs_data", {})
    performance_graph_data = graphs_data.get("performance", {})
    graph_figure = None
    if performance_graph_data:
        metrics = performance_graph_data.get("metrics", [])
        values = performance_graph_data.get("values", [])
        if metrics and values:
            graph_figure = go.Figure(data=go.Bar(x=metrics, y=values, marker_color='indigo'))
            graph_figure.update_layout(title="Performance Metrics", template="plotly_white")
    
    sector_data = graphs_data.get("sector_allocation", {})
    sector_figure = None
    if sector_data:
        labels = sector_data.get("labels", [])
        values = sector_data.get("values", [])
        if labels and values:
            sector_figure = go.Figure(data=[go.Pie(labels=labels, values=values, hole=0.4)])
            sector_figure.update_layout(title="Sector Allocation", template="plotly_white")
    
    heatmap_data = graphs_data.get("heatmap", {})
    heatmap_figure = None
    if heatmap_data:
        hm_metrics = heatmap_data.get("metrics", [])
        spring_vals = heatmap_data.get("Spring", [])
        fall_vals = heatmap_data.get("Fall", [])
        z = []
        y = []
        if spring_vals:
            z.append(spring_vals)
            y.append("Spring")
        if fall_vals:
            z.append(fall_vals)
            y.append("Fall")
        if z and hm_metrics:
            heatmap_figure = go.Figure(data=go.Heatmap(z=z, x=hm_metrics, y=y, colorscale='Viridis'))
            heatmap_figure.update_layout(title="Heatmap", template="plotly_white")
    
    kpi_cards = dbc.Row([
        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.H5("6-Month Return", className="card-title"),
                html.H3(f"{six_month}", className="card-text")
            ]), color="light", outline=True, className="shadow animate__animated animate__fadeIn"
        ), width=3),
        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.H5("1-Year Return", className="card-title"),
                html.H3(f"{one_year}", className="card-text")
            ]), color="light", outline=True, className="shadow animate__animated animate__fadeIn"
        ), width=3),
        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.H5("AUM", className="card-title"),
                html.H3(f"{AUM}", className="card-text")
            ]), color="light", outline=True, className="shadow animate__animated animate__fadeIn"
        ), width=3),
        dbc.Col(dbc.Card(
            dbc.CardBody([
                html.H5("Dividend", className="card-title"),
                html.H3(f"{dividend}", className="card-text")
            ]), color="light", outline=True, className="shadow animate__animated animate__fadeIn"
        ), width=3)
    ], className="mb-4")
    
    content = dbc.Container([
        dbc.Row(
            dbc.Col(html.H3(f"Report: {selected_year} - {selected_semester}", className="text-center text-secondary animate__animated animate__fadeInDown"))
        ),
        kpi_cards,
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Summary", style={"backgroundColor": "#6c757d", "color": "white"}),
                    dbc.CardBody(html.P(summary, className="lead"))
                ], className="mb-3 shadow animate__animated animate__fadeInUp")
            )
        ]),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Comparisons", style={"backgroundColor": "#6c757d", "color": "white"}),
                    dbc.CardBody(html.P(comparisons, className="lead"))
                ], className="mb-3 shadow animate__animated animate__fadeInUp")
            , md=6),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Key Findings", style={"backgroundColor": "#6c757d", "color": "white"}),
                    dbc.CardBody(html.Ul([html.Li(item) for item in key_findings], className="lead"))
                ], className="mb-3 shadow animate__animated animate__fadeInUp")
            , md=6)
        ]),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Strategic Decisions", style={"backgroundColor": "#6c757d", "color": "white"}),
                    dbc.CardBody(html.Ul([html.Li(item) for item in strategic_decisions], className="lead"))
                ], className="mb-3 shadow animate__animated animate__fadeInUp")
            )
        ]),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Performance Graph", style={"backgroundColor": "#6c757d", "color": "white"}),
                    dbc.CardBody(dcc.Graph(figure=graph_figure)) if graph_figure else html.Div("No graph data available.")
                ], className="mb-3 shadow animate__animated animate__fadeInUp"),
                md=6
            ),
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Sector Allocation", style={"backgroundColor": "#6c757d", "color": "white"}),
                    dbc.CardBody(dcc.Graph(figure=sector_figure)) if sector_figure else html.Div("No sector allocation data.")
                ], className="mb-3 shadow animate__animated animate__fadeInUp"),
                md=6
            )
        ]),
        dbc.Row([
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Heatmap", style={"backgroundColor": "#6c757d", "color": "white"}),
                    dbc.CardBody(dcc.Graph(figure=heatmap_figure)) if heatmap_figure else html.Div("No heatmap data available.")
                ], className="mb-3 shadow animate__animated animate__fadeInUp")
            )
        ])
    ], fluid=True)
    
    return content

# Callback for updating the year comparison graph in the Comparisons tab
@app.callback(
    Output('year-comparison-graph', 'figure'),
    [Input('compare-years-dropdown', 'value')]
)
def update_comparison_graph(selected_years):
    if not selected_years:
        return go.Figure()
    
    labels = []
    values = []
    for year in selected_years:
        for sem in data[year]:
            perf = data[year][sem].get("performance_metrics", {})
            ret = perf.get("6_month_return", None)
            if ret is not None:
                labels.append(f"{year} - {sem}")
                values.append(ret)
    fig = go.Figure(data=go.Bar(x=labels, y=values, marker_color='teal'))
    fig.update_layout(
        title="6-Month Return Comparison Across Selected Years",
        xaxis_title="Year - Semester",
        yaxis_title="6-Month Return (%)",
        template="plotly_white"
    )
    return fig

# Callback for updating key findings and future projections in the Findings & Future Projections tab
@app.callback(
    Output('findings-content', 'children'),
    [Input('findings-year-dropdown', 'value')]
)
def update_findings(selected_year):
    if not selected_year or selected_year not in data:
        return dbc.Alert("No data available for key findings.", color="warning")
    
    findings_list = []
    # Aggregate key findings from all semesters for the selected year
    for sem in data[selected_year]:
        sem_findings = data[selected_year][sem].get("key_findings", [])
        if sem_findings:
            findings_list.append(html.H5(f"{selected_year} - {sem}", className="text-primary"))
            findings_list.extend([html.Li(item) for item in sem_findings])
    
    if not findings_list:
        findings_list = [html.P("No key findings available for the selected year.", className="lead")]
    
    future_projection_text = (
        "Future projections: Based on historical performance and current market conditions, "
        "we anticipate a continuing emphasis on advanced analytics, increased ESG integration, "
        "and strategic rebalancing to optimize returns while minimizing risk."
    )
    
    content = dbc.Container([
        dbc.Row(
            dbc.Col(html.H4("Key Findings", className="text-center text-secondary animate__animated animate__fadeInDown"))
        ),
        dbc.Row(
            dbc.Col(html.Ul(findings_list, className="lead"))
        ),
        dbc.Row(
            dbc.Col(
                dbc.Card([
                    dbc.CardHeader("Future Projections", style={"backgroundColor": "#6c757d", "color": "white"}),
                    dbc.CardBody(html.P(future_projection_text, className="lead"))
                ], className="shadow animate__animated animate__fadeInUp")
            )
        )
    ], fluid=True)
    
    return content

if __name__ == '__main__':
    app.run(debug=True)
