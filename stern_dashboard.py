import os
import re
import pdfplumber
import docx
import pandas as pd
import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import concurrent.futures

#####################################
# Data Extraction Functions         #
#####################################

def extract_text_from_pdf(filepath):
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return text

def extract_text_from_docx(filepath):
    try:
        doc = docx.Document(filepath)
        text = "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        text = ""
    return text

def extract_data_from_report(filepath):
    # Determine AcademicYear and Semester from filename
    basename = os.path.basename(filepath)
    m = re.match(r"(\d{4})_(Fall|Spring)_Report", basename, re.IGNORECASE)
    if m:
        academic_year = m.group(1)
        semester = m.group(2)
    else:
        academic_year = ""
        semester = ""
    # Extract text based on file extension
    if filepath.lower().endswith(".pdf"):
        text = extract_text_from_pdf(filepath)
    elif filepath.lower().endswith((".docx", ".doc")):
        text = extract_text_from_docx(filepath)
    else:
        text = ""
    
    # Use regex patterns to extract key metrics.
    # AUM: Pattern like "with $X million currently under management"
    aum_match = re.search(r"with\s*\$([\d\.]+)\s*million\s+currently\s+under\s+management", text, re.IGNORECASE)
    aum = float(aum_match.group(1)) if aum_match else None

    # 6-month Return: Look for "6[-\s]*month" followed by a percentage
    return6m_match = re.search(r"6[-\s]*month.*?([\-\d\.]+)%", text, re.IGNORECASE)
    return6m = float(return6m_match.group(1)) if return6m_match else None

    # 12-month Return: Look for "12[-\s]*month" followed by a percentage
    return12m_match = re.search(r"12[-\s]*month.*?([\-\d\.]+)%", text, re.IGNORECASE)
    return12m = float(return12m_match.group(1)) if return12m_match else None

    # Dividend: Look for "dividend" and a dollar amount
    dividend_match = re.search(r"dividend.*?\$([\d,\.]+)", text, re.IGNORECASE)
    dividend = float(dividend_match.group(1).replace(",", "")) if dividend_match else None

    # Benchmark Return: Look for "benchmark" followed by a percentage
    benchmark_match = re.search(r"benchmark[^%\n]*?([\-\d\.]+)%", text, re.IGNORECASE)
    benchmark_return = float(benchmark_match.group(1)) if benchmark_match else None

    # Summary: Try to extract text following "Review of Operations" until a marker like "Future" or "Investment"
    summary_match = re.search(r"Review of Operations(.*?)Future", text, re.IGNORECASE|re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else ""
    
    # Future Findings: Look for "Future Findings" text
    future_match = re.search(r"Future Findings(.*?)(Investment Plan|$)", text, re.IGNORECASE|re.DOTALL)
    future_findings = future_match.group(1).strip() if future_match else ""
    
    # Investment Plan: Look for "Investment Plan" text
    plan_match = re.search(r"Investment Plan(.*)", text, re.IGNORECASE|re.DOTALL)
    investment_plan = plan_match.group(1).strip() if plan_match else ""

    return {
        "AcademicYear": academic_year,
        "Semester": semester,
        "Period": f"{academic_year} {semester}",
        "AUM": aum,
        "Return6m": return6m,
        "Return12m": return12m,
        "Dividend": dividend,
        "BenchmarkReturn": benchmark_return,
        "Summary": summary,
        "FutureFindings": future_findings,
        "InvestmentPlan": investment_plan
    }

#####################################
# Process All Reports (Parallel)    #
#####################################

report_folder = "reports"
report_files = [os.path.join(report_folder, f) for f in os.listdir(report_folder)
                if f.lower().endswith((".pdf", ".docx", ".doc"))]

extracted_data = []
with concurrent.futures.ThreadPoolExecutor() as executor:
    futures = {executor.submit(extract_data_from_report, filepath): filepath for filepath in report_files}
    for future in concurrent.futures.as_completed(futures):
        filepath = futures[future]
        try:
            data_dict = future.result()
            extracted_data.append(data_dict)
        except Exception as exc:
            print(f"{filepath} generated an exception: {exc}")

df = pd.DataFrame(extracted_data)
semester_order = {"Spring": 1, "Fall": 2}
df["SemOrder"] = df["Semester"].map(semester_order)
df.sort_values(by=["AcademicYear", "SemOrder"], inplace=True)
df.reset_index(drop=True, inplace=True)

print(df.head())

#####################################
# Build Dashboard with Dash         #
#####################################

fig_aum = px.line(df, x="Period", y="AUM", markers=True,
                  title="Assets Under Management Over Time",
                  labels={"AUM": "AUM (in millions)", "Period": "Academic Period"})

fig_returns = px.line(df, x="Period", y="Return6m", markers=True,
                      title="6-Month Returns Over Time", labels={"Return6m": "6-Month Return (%)"})

# For asset allocation, if allocation fields exist; if not, default values are used.
latest_period = df["Period"].max()
latest_record = df[df["Period"] == latest_period].iloc[0] if not df.empty else {}
alloc_data = {
    "Fund": ["Growth", "Value", "Fixed Income", "ESG"],
    "Allocation": [
        latest_record.get("Allocation_Growth", 0.5),
        latest_record.get("Allocation_Value", 0.3),
        latest_record.get("Allocation_FixedIncome", 0.15),
        latest_record.get("Allocation_ESG", 0.05)
    ]
}
df_alloc = pd.DataFrame(alloc_data)
fig_alloc = px.pie(df_alloc, names="Fund", values="Allocation",
                   title=f"Asset Allocation for {latest_period}")

external_stylesheets = [dbc.themes.FLATLY]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.layout = dbc.Container([
    dbc.NavbarSimple(
        brand="NYU Stern MBA Investment Fund Dashboard",
        brand_href="#",
        color="primary",
        dark=True,
        fluid=True,
    ),
    dcc.Tabs(id="tabs", value="overview", children=[
        dcc.Tab(label="Overview", value="overview"),
        dcc.Tab(label="Comparisons", value="comparisons"),
        dcc.Tab(label="Yearly Summary", value="yearly"),
        dcc.Tab(label="Future & Investment Plan", value="future"),
    ]),
    html.Div(id="tab-content", className="p-4")
], fluid=True)

@app.callback(Output("tab-content", "children"),
              Input("tabs", "value"))
def render_content(tab):
    if tab == "overview":
        return dbc.Container([
            html.H4("Overview: Key Metrics by Academic Period"),
            dash_table.DataTable(
                id="overview-table",
                columns=[{"name": col, "id": col} for col in df.columns if col not in ["Summary", "FutureFindings", "InvestmentPlan", "SemOrder"]],
                data=df.to_dict("records"),
                style_table={'overflowX': 'auto'},
                page_size=10
            )
        ])
    elif tab == "comparisons":
        return dbc.Container([
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("AUM Growth Over Time"),
                    dbc.CardBody(dcc.Graph(figure=fig_aum))
                ]), width=6),
                dbc.Col(dbc.Card([
                    dbc.CardHeader("6-Month Returns Over Time"),
                    dbc.CardBody(dcc.Graph(figure=fig_returns))
                ]), width=6)
            ], className="mb-4"),
            dbc.Row([
                dbc.Col(dbc.Card([
                    dbc.CardHeader("Asset Allocation"),
                    dbc.CardBody(dcc.Graph(figure=fig_alloc))
                ]), width=6)
            ])
        ])
    elif tab == "yearly":
        return dbc.Container([
            html.H4("Yearly Summary & Key Shifts"),
            dbc.Row([
                dbc.Col([
                    html.Label("Select Academic Period:"),
                    dcc.Dropdown(
                        id="period-dropdown",
                        options=[{"label": p, "value": p} for p in sorted(df["Period"].unique())],
                        value=sorted(df["Period"].unique())[-1]
                    )
                ], width=4)
            ], className="mb-4"),
            html.Div(id="yearly-details")
        ])
    elif tab == "future":
        return dbc.Container([
            html.H4("Future Projections & Investment Plan"),
            dbc.Card([
                dbc.CardHeader("Future Findings & Projections"),
                dbc.CardBody(html.Div(id="future-text", children=[
                    html.P("The reports reveal forward-looking insights regarding benchmark adjustments, improvements in attribution analytics, and strategic adaptations to changing market conditions.")
                ]))
            ]),
            dbc.Card([
                dbc.CardHeader("Investment Plan for Future Years"),
                dbc.CardBody(html.Div(id="investment-plan", children=[
                    html.P("Based on historical performance and the strategic initiatives documented, the fund plans to enhance its analytical capabilities, explore new thematic investments (e.g., AI, Energy Transition), and further optimize risk management practices.")
                ]))
            ])
        ])

@app.callback(Output("yearly-details", "children"),
              Input("period-dropdown", "value"))
def update_yearly_summary(selected_period):
    filtered = df[df["Period"] == selected_period]
    if filtered.empty:
        return html.P("No data available for the selected period.")
    record = filtered.iloc[0]
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H5(f"Academic Period: {selected_period}"),
                html.P(f"AUM: ${record['AUM']:.2f} million" if record['AUM'] is not None else "AUM: N/A"),
                html.P(f"6-Month Return: {record['Return6m']}%" if record['Return6m'] is not None else "6-Month Return: N/A"),
                html.P(f"12-Month Return: {record['Return12m']}%" if record['Return12m'] is not None else "12-Month Return: N/A"),
                html.P(f"Dividend Paid: ${record['Dividend']:,}" if record['Dividend'] is not None else "Dividend: N/A"),
                html.P(f"Benchmark Return: {record['BenchmarkReturn']}%" if record['BenchmarkReturn'] is not None else "Benchmark Return: N/A"),
            ], width=6),
            dbc.Col([
                html.H5("Summary & Key Shifts"),
                html.P(record["Summary"] if record["Summary"] else "No summary available."),
            ], width=6)
        ]),
        dbc.Row([
            dbc.Col([
                html.H5("Future Findings & Investment Plan"),
                html.P(record["FutureFindings"] if record["FutureFindings"] else "No future findings provided."),
                html.P(record["InvestmentPlan"] if record["InvestmentPlan"] else "No investment plan provided.")
            ])
        ])
    ])

if __name__ == '__main__':
    app.run(debug=True)
