import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import re
import requests
from io import BytesIO

st.set_page_config(
    page_title="DMI Sprint Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════════
#  DESIGN TOKENS
# ═══════════════════════════════════════════════════════════════════════════════
# Palette
BG          = "#f8fafc"   # page background (slate-50)
CARD        = "#ffffff"
SIDEBAR_BG  = "#1e293b"   # slate-800
TEXT_DARK   = "#0f172a"   # slate-900  — headings, values
TEXT_MID    = "#1e293b"   # slate-800  — body text, labels
TEXT_LIGHT  = "#374151"   # gray-700   — secondary info (still clearly dark)
BORDER      = "#e2e8f0"   # slate-200

BLUE    = "#1d4ed8"   # royal blue  — high contrast on white
GREEN   = "#059669"   # emerald     — vivid, prints well
AMBER   = "#f59e0b"   # bright amber — clearly visible on white
RED     = "#dc2626"   # bold red
PURPLE  = "#6d28d9"   # deep violet — distinct from blue
TEAL    = "#0284c7"   # sky blue

# Categorically distinct, evenly saturated palette for charts
CHART_PALETTE = ["#1d4ed8","#059669","#f59e0b","#dc2626","#6d28d9","#0284c7","#db2777","#0d9488"]

PRIORITY_COLORS = {"P0": "#dc2626", "P1": "#ea580c", "P2": "#ca8a04", "P3": "#1d4ed8"}
STATUS_COLORS   = {"DEV": "#1d4ed8", "UAT": "#6d28d9", "Done": "#059669",
                   "Blocked": "#dc2626", "QA": "#0284c7", "Review": "#6366f1"}

CHART_FONT = dict(family="Inter, Arial, sans-serif", color=TEXT_DARK, size=12)
CHART_BG   = dict(paper_bgcolor=CARD, plot_bgcolor=CARD)
GRID_COLOR = "#f1f5f9"

# ═══════════════════════════════════════════════════════════════════════════════
#  GLOBAL CSS  (screen + print)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<style>
/* ══════════════════════════════════════════════
   LAYOUT — zero wasted space, full width
══════════════════════════════════════════════ */
[data-testid="stAppViewContainer"]  {{ background:{BG}; }}
[data-testid="stMain"]              {{ padding-top:0 !important; max-width:100% !important; width:100% !important; }}
[data-testid="stMainBlockContainer"],
.block-container,
.main .block-container {{
  padding:0 16px 16px !important;
  max-width:100% !important;
  width:100% !important;
}}
[data-testid="stHorizontalBlock"]   {{ gap:10px !important; }}
[data-testid="stVerticalBlock"] > div {{ margin-bottom:0 !important; }}

/* ══════════════════════════════════════════════
   HEADER — hide chrome, keep toggle visible
══════════════════════════════════════════════ */
[data-testid="stHeader"]      {{ background:{BG} !important; border-bottom:none !important; height:36px !important; min-height:36px !important; }}
[data-testid="stToolbar"]     {{ display:none !important; }}
[data-testid="stDecoration"]  {{ display:none !important; }}
[data-testid="stStatusWidget"]{{ display:none !important; }}
[data-testid="stHeader"] button svg {{ fill:{TEXT_DARK} !important; }}

/* ══════════════════════════════════════════════
   SIDEBAR — hidden
══════════════════════════════════════════════ */
[data-testid="stSidebar"] {{ display:none !important; }}
[data-testid="collapsedControl"] {{ display:none !important; }}
/* ── Inline toolbar ── */
.toolbar {{
  display:flex; align-items:center; gap:10px;
  padding:8px 0 6px; margin-bottom:4px;
}}
.toolbar-label {{
  font-size:11px; font-weight:600; color:#64748b;
  text-transform:uppercase; letter-spacing:0.06em; white-space:nowrap;
}}

/* ══════════════════════════════════════════════
   UNIFIED DARK HEADER (sprint info + controls)
══════════════════════════════════════════════ */
div[data-testid="stHorizontalBlock"]:has(.hdr-anchor) {{
  background:linear-gradient(120deg,#0f172a 0%,#1e3a5f 55%,#1e40af 100%);
  border-radius:10px; padding:12px 18px !important;
  margin-bottom:8px !important; align-items:center !important;
  box-shadow:0 2px 8px rgba(15,23,42,0.18);
}}
div[data-testid="stHorizontalBlock"]:has(.hdr-anchor) [data-baseweb="select"] > div {{
  background:rgba(255,255,255,0.08) !important; border-color:rgba(255,255,255,0.18) !important;
  border-radius:7px !important; min-height:36px !important;
}}
div[data-testid="stHorizontalBlock"]:has(.hdr-anchor) [data-baseweb="select"] *,
div[data-testid="stHorizontalBlock"]:has(.hdr-anchor) [data-baseweb="select"] svg {{ color:rgba(255,255,255,0.85) !important; fill:rgba(255,255,255,0.6) !important; }}
div[data-testid="stHorizontalBlock"]:has(.hdr-anchor) [data-baseweb="tag"] {{
  background:rgba(255,255,255,0.15) !important; border-color:rgba(255,255,255,0.2) !important;
}}
div[data-testid="stHorizontalBlock"]:has(.hdr-anchor) [data-baseweb="tag"] span {{ color:white !important; }}
div[data-testid="stHorizontalBlock"]:has(.hdr-anchor) button[kind="secondary"] {{
  background:rgba(255,255,255,0.1) !important; color:white !important;
  border:1px solid rgba(255,255,255,0.25) !important; border-radius:7px !important;
  height:36px !important; font-size:12px !important; font-weight:600 !important;
  padding:0 !important;
}}
div[data-testid="stHorizontalBlock"]:has(.hdr-anchor) button[kind="secondary"]:hover {{
  background:rgba(255,255,255,0.18) !important;
}}
.kpi-inline {{ display:flex; gap:20px; margin-top:8px; flex-wrap:wrap; }}
.kpi-inline-item {{ font-size:10px; color:#94a3b8; text-transform:uppercase; letter-spacing:0.07em; }}
.kpi-inline-item b {{ font-size:16px; font-weight:700; display:block; line-height:1.2; color:#f1f5f9; }}

/* ══════════════════════════════════════════════
   TABS
══════════════════════════════════════════════ */
[data-testid="stTabs"] {{ margin-top:0 !important; }}
[data-testid="stTabs"] [role="tablist"] {{
  border-bottom:1px solid {BORDER}; gap:0; padding:0; background:{CARD};
  border-radius:8px 8px 0 0; padding:0 4px;
  box-shadow:0 1px 3px rgba(15,23,42,0.05);
}}
[data-testid="stTabs"] button[role="tab"] {{
  font-size:12px !important; font-weight:600 !important; color:#64748b !important;
  padding:10px 16px !important; border-radius:0 !important; border:none !important;
  background:transparent !important; border-bottom:2px solid transparent !important;
  margin-bottom:-1px !important;
}}
[data-testid="stTabs"] button[role="tab"]:hover {{ color:{TEXT_DARK} !important; }}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {{
  color:{BLUE} !important; border-bottom:2px solid {BLUE} !important;
}}
[data-testid="stTabs"] [data-testid="stTabPanel"] {{
  background:{CARD}; border:1px solid {BORDER}; border-top:none;
  border-radius:0 0 8px 8px; padding:14px 16px !important;
  box-shadow:0 1px 3px rgba(15,23,42,0.05);
}}

/* ══════════════════════════════════════════════
   METRIC CARDS
══════════════════════════════════════════════ */
[data-testid="stMetric"] {{
  background:{CARD}; border-radius:8px; padding:14px 16px;
  border:1px solid {BORDER}; box-shadow:0 1px 4px rgba(15,23,42,0.06);
  min-height:90px !important; display:flex; flex-direction:column; justify-content:space-between;
}}
[data-testid="stMetricValue"] {{
  font-size:26px !important; font-weight:700 !important; color:{TEXT_DARK} !important;
  line-height:1.15 !important; margin:4px 0 !important;
}}
[data-testid="stMetricLabel"] {{
  font-size:10px !important; color:#64748b !important; font-weight:700 !important;
  text-transform:uppercase; letter-spacing:0.07em; margin-bottom:2px !important;
}}
[data-testid="stMetricDelta"] {{ font-size:11px !important; min-height:18px; }}

/* ══════════════════════════════════════════════
   CARDS & ROWS
══════════════════════════════════════════════ */
.card {{
  background:{CARD}; border-radius:8px; padding:10px 14px;
  border:1px solid {BORDER}; box-shadow:0 1px 4px rgba(15,23,42,0.06);
  margin-bottom:6px;
}}
.row-item {{
  background:{CARD}; border-radius:7px; padding:8px 12px;
  border:1px solid {BORDER}; margin-bottom:6px;
  box-shadow:0 1px 2px rgba(15,23,42,0.04);
}}
.row-item:last-child {{ margin-bottom:0; }}

/* ══════════════════════════════════════════════
   SECTION HEADERS
══════════════════════════════════════════════ */
.section-hdr {{
  border-left:3px solid #bfdbfe; padding:3px 0 3px 10px;
  margin:12px 0 8px; font-size:10px; font-weight:700;
  color:#64748b; text-transform:uppercase; letter-spacing:0.09em;
}}

/* ══════════════════════════════════════════════
   TYPOGRAPHY
══════════════════════════════════════════════ */
.sub {{ font-size:11px; color:#64748b; margin-bottom:6px; line-height:1.4; }}
[data-testid="stMarkdownContainer"] p {{ color:{TEXT_DARK} !important; font-size:13px; }}
[data-testid="stWidgetLabel"] p       {{ color:{TEXT_DARK} !important; }}
[data-testid="stCaptionContainer"] p  {{ color:#64748b !important; font-size:11px !important; }}

/* ══════════════════════════════════════════════
   BADGES
══════════════════════════════════════════════ */
.b-active  {{ background:#dcfce7;color:#166534;border-radius:20px;padding:2px 10px;font-size:11px;font-weight:700 }}
.b-dev     {{ background:#dbeafe;color:#1e40af;border-radius:4px;padding:1px 7px;font-size:11px;font-weight:700 }}
.b-uat     {{ background:#ede9fe;color:#5b21b6;border-radius:4px;padding:1px 7px;font-size:11px;font-weight:700 }}
.b-done    {{ background:#dcfce7;color:#166534;border-radius:4px;padding:1px 7px;font-size:11px;font-weight:700 }}
.b-blocked {{ background:#fee2e2;color:#991b1b;border-radius:4px;padding:1px 7px;font-size:11px;font-weight:700 }}
.b-p0      {{ background:#fee2e2;color:#991b1b;border-radius:4px;padding:1px 6px;font-size:10px;font-weight:800 }}
.b-p1      {{ background:#ffedd5;color:#9a3412;border-radius:4px;padding:1px 6px;font-size:10px;font-weight:800 }}
.b-p2      {{ background:#fef9c3;color:#854d0e;border-radius:4px;padding:1px 6px;font-size:10px;font-weight:800 }}
.b-p3      {{ background:#dbeafe;color:#1e40af;border-radius:4px;padding:1px 6px;font-size:10px;font-weight:800 }}

/* ══════════════════════════════════════════════
   MISC
══════════════════════════════════════════════ */
div[data-testid="stDataFrame"] {{ border-radius:8px; overflow:hidden; border:1px solid {BORDER}; }}

/* ── PRINT / PDF (A4) ──────────────────────── */
@media print {{
  @page {{ size:A4 portrait; margin:12mm 14mm; }}

  /* hide Streamlit chrome */
  [data-testid="stSidebar"],
  [data-testid="stHeader"],
  [data-testid="stToolbar"],
  [data-testid="stAppDeployButton"],
  [data-testid="stMainMenu"],
  [data-testid="stElementToolbar"],
  button, .stButton {{ display:none !important; }}

  /* full-width main content */
  [data-testid="stAppViewContainer"],
  [data-testid="stMain"],
  [data-testid="stMainBlockContainer"] {{
    padding:0 !important; margin:0 !important; width:100% !important;
    background:white !important;
  }}
  [data-testid="stHorizontalBlock"] {{ gap:12px !important; }}

  /* force colours to print */
  * {{ -webkit-print-color-adjust:exact !important; color-adjust:exact !important; }}

  /* page breaks */
  .pb-before {{ page-break-before:always; }}
  .no-break   {{ page-break-inside:avoid; }}

  /* shrink charts for A4 */
  [data-testid="stPlotlyChart"] {{ max-height:240px !important; }}

  .sprint-banner {{ background:#1e293b !important; color:white !important; }}
  .section-hdr, .section-hdr-warn {{ border-color:{BLUE}; }}

  /* metric card borders visible on print */
  [data-testid="stMetric"] {{ border:1px solid #cbd5e1 !important; }}
  .row-item  {{ border:1px solid #cbd5e1 !important; }}
  .card      {{ border:1px solid #cbd5e1 !important; }}
}}
</style>
""", unsafe_allow_html=True)

# ── Inject JS to force the sidebar toggle button to always be visible ──────────
import streamlit.components.v1 as _comp
_comp.html("""
<script>
function fixSidebarToggle() {
    const doc = window.parent.document;
    // collapsed toggle (sidebar is closed)
    const collapsed = doc.querySelector('[data-testid="collapsedControl"]');
    if (collapsed) {
        collapsed.style.cssText = [
            'background:#1e293b',
            'border-radius:0 6px 6px 0',
            'padding:10px 6px',
            'display:flex',
            'align-items:center',
            'cursor:pointer',
            'position:fixed',
            'top:50%',
            'left:0',
            'z-index:99999',
            'box-shadow:2px 0 8px rgba(0,0,0,0.3)'
        ].join(';');
        collapsed.querySelectorAll('svg,path').forEach(function(el){
            el.style.fill='white'; el.style.stroke='white';
        });
    }
}
fixSidebarToggle();
setInterval(fixSidebarToggle, 400);
</script>
""", height=0)


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════════════════════
def badge(text: str) -> str:
    cls = {"DEV":"b-dev","UAT":"b-uat","Done":"b-done","Blocked":"b-blocked",
           "P0":"b-p0","P1":"b-p1","P2":"b-p2","P3":"b-p3"}.get(text,"b-dev")
    return f'<span class="{cls}">{text}</span>'


def remarks_color(remark: str):
    """Returns (text_color, bg_color) — both are high-contrast for readability."""
    r = remark.lower()
    if any(w in r for w in ["completed","done","delivered","closed"]):
        return "#065f46", "#a7f3d0"   # dark green text, vivid green bg
    if any(w in r for w in ["on track","testing","progress","review","uat"]):
        return "#78350f", "#fde68a"   # dark brown text, vivid yellow bg
    if any(w in r for w in ["delay","blocked","risk","issue","hold","stuck"]):
        return "#7f1d1d", "#fecaca"   # dark red text, vivid red bg
    return "#1e293b", "#e2e8f0"       # dark text, light slate bg


def pbar(pct: float, color: str, height: int = 8) -> str:
    """Progress bar — always a min 4px wide so empty bars stay visible."""
    fill = max(min(pct, 100), 0)
    min_w = "4px" if fill == 0 else f"{fill:.0f}%"
    return (f'<div style="background:#e2e8f0;border-radius:4px;height:{height}px;margin-top:7px">'
            f'<div style="background:{color};border-radius:4px;height:{height}px;'
            f'width:{min_w};min-width:4px"></div></div>')


def pbar_color(pct: float) -> str:
    """Pick a vivid bar colour based on completion percentage."""
    if pct >= 80: return "#059669"   # emerald
    if pct >= 40: return "#f59e0b"   # bright amber
    return "#dc2626"                  # red


def fetch_gsheet(url: str):
    """Download a publicly-shared Google Sheet as xlsx bytes. Returns bytes or None."""
    match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', url)
    if not match:
        return None, "Could not find a Sheet ID in that URL."
    sheet_id = match.group(1)
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    try:
        r = requests.get(export_url, timeout=15)
        if r.status_code == 200:
            return r.content, None
        return None, f"Google returned status {r.status_code}. Make sure the sheet is shared as **Anyone with link → Viewer**."
    except Exception as e:
        return None, str(e)


def load_data(file) -> pd.DataFrame:
    if isinstance(file, (bytes, bytearray)):
        file = BytesIO(file)
    df = pd.read_excel(file, engine="openpyxl")
    df = df.dropna(axis=1, how="all")
    df.columns = df.columns.str.strip()
    for col in ["Percentage Complete","Total Estimated Hours",
                "Estimated Effort this sprint","Actual Effort"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if {"Estimated Effort this sprint","Actual Effort"} <= set(df.columns):
        df["Remaining effort"] = (
            df["Estimated Effort this sprint"] - df["Actual Effort"]
        ).clip(lower=0)
    for col in ["Blocker","Starred","Status","Priority","Team","Resource",
                "Remarks","Summary","Jira ID","From","Sprint"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
    return df


# ── Chart factories ────────────────────────────────────────────────────────────
def _base_layout(title="", height=210, **kw):
    base = dict(
        title={"text": title,
               "font": {"size": 12, "color": TEXT_DARK, "family": "Inter, Arial"},
               "x": 0.02, "pad": {"t": 2}},
        height=height,
        margin=dict(l=6, r=6, t=36, b=8),
        **CHART_BG,
        font=CHART_FONT,
    )
    base.update(kw)   # kw wins — callers can override margin etc.
    return base




def gauge_chart(value: float) -> go.Figure:
    color = GREEN if value >= 75 else AMBER if value >= 40 else RED
    # Track: light band behind the bar
    steps = [
        {"range": [0,   40],  "color": "#fee2e2"},   # red zone
        {"range": [40,  75],  "color": "#fef3c7"},   # amber zone
        {"range": [75, 100],  "color": "#d1fae5"},   # green zone
    ]
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        number={"suffix": "%", "font": {"size": 34, "color": TEXT_DARK, "family": "Inter"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#94a3b8",
                     "nticks": 6, "tickfont": {"size": 10, "color": TEXT_DARK}},
            "bar":   {"color": color, "thickness": 0.38},
            "bgcolor": CARD, "borderwidth": 0,
            "steps": steps,
            "threshold": {"line": {"color": color, "width": 4},
                          "thickness": 0.9, "value": value},
        },
    ))
    fig.update_layout(height=170, margin=dict(l=16, r=16, t=24, b=4),
                      paper_bgcolor=CARD, font=CHART_FONT)
    return fig


def donut_chart(labels, values, title, colors=None) -> go.Figure:
    colors = colors or [STATUS_COLORS.get(l, TEXT_LIGHT) for l in labels]
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.58,
        marker=dict(colors=colors, line=dict(color=CARD, width=2)),
        textinfo="percent", textfont={"size": 11, "color": TEXT_DARK},
        insidetextorientation="horizontal",
        hovertemplate="<b>%{label}</b><br>%{value} tasks (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        **_base_layout(title, 200, margin=dict(l=6, r=6, t=36, b=28)),
        legend=dict(
            orientation="h", x=0.5, y=-0.08, xanchor="center",
            font={"size": 11, "color": TEXT_MID}, bgcolor="rgba(0,0,0,0)",
            itemwidth=40,
        ),
        showlegend=True,
    )
    return fig


def grouped_bar(df_grp, x, ys, title, colors) -> go.Figure:
    fig = go.Figure()
    for y, color in zip(ys, colors):
        fig.add_trace(go.Bar(
            name=y, x=df_grp[x], y=df_grp[y],
            marker_color=color,
            text=df_grp[y].round(0).astype(int),
            textposition="outside",
            textfont={"size": 11, "color": TEXT_DARK},
        ))
    fig.update_layout(
        **_base_layout(title, 210),
        barmode="group",
        xaxis={"gridcolor": GRID_COLOR, "title": "",
               "tickfont": {"size": 12, "color": GREEN, "family": "Inter, Arial"}},
        yaxis={"gridcolor": GRID_COLOR, "title": {"text": "Hours", "font": {"size": 11}},
               "tickfont": {"size": 11, "color": TEXT_MID}},
        legend=dict(orientation="h", y=1.12, font={"size": 11, "color": TEXT_MID},
                    bgcolor="rgba(0,0,0,0)"),
        bargap=0.25, bargroupgap=0.06,
    )
    return fig


def team_bar(teams, values) -> go.Figure:
    colors = ["#059669" if v >= 80 else "#1d4ed8" if v >= 50 else "#f59e0b" for v in values]
    fig = go.Figure(go.Bar(
        x=teams, y=values, marker_color=colors,
        text=[f"{v:.0f}%" for v in values],
        textposition="outside", textfont={"size": 11, "color": TEXT_DARK},
        marker_line=dict(color=CARD, width=1),
    ))
    fig.update_layout(
        **_base_layout("Completion % by Team", 190),
        yaxis={"range": [0, 120], "gridcolor": GRID_COLOR, "title": "",
               "tickfont": {"size": 11, "color": TEXT_MID}},
        xaxis={"title": "",
               "tickfont": {"size": 12, "color": GREEN, "family": "Inter, Arial"}},
        bargap=0.4,
    )
    return fig


def variance_chart(df: pd.DataFrame) -> go.Figure:
    tmp = df.copy()
    tmp["var"] = (
        (tmp["Actual Effort"] - tmp["Estimated Effort this sprint"])
        / tmp["Estimated Effort this sprint"].replace(0, 1) * 100
    ).round(1)
    tmp = tmp.sort_values("var")
    label = tmp["Jira ID"] + "   " + tmp["Resource"]

    def _bar_color(v):
        if v > 10:   return "#dc2626"   # over budget — red
        if v < -10:  return "#059669"   # under budget — green
        return       "#374151"          # on-estimate (±10%) — dark gray

    # Give 0-variance bars a minimum visible width so they render
    plot_vals = [v if abs(v) > 3 else (4 if v >= 0 else -4) for v in tmp["var"]]
    bar_labels = [f"{v:+.0f}%  ✓ On estimate" if abs(v) <= 10
                  else f"{v:+.0f}%" for v in tmp["var"]]

    colors = [_bar_color(v) for v in tmp["var"]]

    fig = go.Figure(go.Bar(
        x=plot_vals, y=label,
        orientation="h",
        marker=dict(color=colors, line=dict(color=CARD, width=1)),
        text=bar_labels,
        textposition="outside",
        textfont={"size": 11, "color": TEXT_DARK},
    ))
    fig.add_vline(x=0, line_width=2, line_dash="dash", line_color=TEXT_MID)
    # Force x-axis to always show a readable range
    max_abs = max(abs(v) for v in tmp["var"]) if len(tmp) else 20
    x_range = max(max_abs * 1.5, 20)
    fig.update_layout(
        **_base_layout(
            "1 · Effort Variance  "
            "<span style='color:#059669'>■ Green = under budget</span>  "
            "<span style='color:#dc2626'>■ Red = over budget</span>  "
            "<span style='color:#374151'>■ Grey = on estimate</span>",
            max(260, len(tmp) * 56 + 80)),
        xaxis={"gridcolor": GRID_COLOR, "title": "Variance %",
               "zeroline": False, "range": [-x_range, x_range],
               "tickfont": {"size": 11, "color": TEXT_MID}},
        yaxis={"gridcolor": "rgba(0,0,0,0)",
               "tickfont": {"size": 12, "color": GREEN, "family": "Inter, Arial"}},
    )
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
#  LANDING PAGE  (no sidebar required — uploader is front and centre)
# ═══════════════════════════════════════════════════════════════════════════════
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None


if st.session_state.uploaded_file is None:
    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:linear-gradient(120deg,#0f172a 0%,#1e3a5f 55%,#1e40af 100%);
                border-radius:14px;padding:40px 48px 36px;margin-bottom:20px">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:24px">
        <div>
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
            <div style="font-size:11px;font-weight:700;color:#60a5fa;letter-spacing:0.12em;text-transform:uppercase">Sprint Intelligence</div>
            <div style="width:1px;height:12px;background:rgba(255,255,255,0.2)"></div>
            <div style="font-size:11px;color:#64748b;letter-spacing:0.04em">Powered by <span style="color:#94a3b8;font-weight:700">Zorvix</span></div>
          </div>
          <div style="font-size:32px;font-weight:800;color:#f8fafc;line-height:1.15;margin-bottom:10px">
            DMI Sprint Dashboard
          </div>
          <div style="font-size:15px;color:#94a3b8;max-width:480px;line-height:1.6">
            Turn your MSME Tracker Excel into a live sprint intelligence dashboard —
            effort variance, on-time risk, team load, and management insights in seconds.
          </div>
        </div>
        <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
          <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);
                      border-radius:10px;padding:14px 20px;text-align:center;min-width:80px">
            <div style="font-size:24px;font-weight:800;color:#4ade80">4</div>
            <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em">Views</div>
          </div>
          <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);
                      border-radius:10px;padding:14px 20px;text-align:center;min-width:80px">
            <div style="font-size:24px;font-weight:800;color:#60a5fa">7+</div>
            <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em">Insights</div>
          </div>
          <div style="background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.12);
                      border-radius:10px;padding:14px 20px;text-align:center;min-width:80px">
            <div style="font-size:24px;font-weight:800;color:#f59e0b">PDF</div>
            <div style="font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:0.08em">Export</div>
          </div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Feature cards ─────────────────────────────────────────────────────────
    fc1, fc2, fc3, fc4 = st.columns(4)
    features = [
        ("📊", "Overview", BLUE,
         ["Sprint progress gauge", "Status & priority donuts", "Blocker highlights", "Team completion bars"]),
        ("📋", "Tasks", "#6d28d9",
         ["Full sortable task table", "On-time risk scoring", "Blocked / tight / on-track labels", "Days to release tracking"]),
        ("👥", "Team", "#059669",
         ["Effort vs actual bars", "Workload utilisation %", "Resource overload alerts", "Sprint capacity view"]),
        ("📈", "Insights", "#dc2626",
         ["Effort variance per task", "Category breakdown donut", "Critical vs standard analysis", "Remarks health heatmap"]),
    ]
    for col, (icon, title, color, bullets) in zip([fc1, fc2, fc3, fc4], features):
        with col:
            st.markdown(f"""
            <div style="background:{CARD};border:1px solid {BORDER};border-radius:10px;
                        padding:18px 16px;height:100%;border-top:3px solid {color}">
              <div style="font-size:24px;margin-bottom:8px">{icon}</div>
              <div style="font-size:14px;font-weight:700;color:{TEXT_DARK};margin-bottom:10px">{title}</div>
              {''.join(f'<div style="display:flex;align-items:flex-start;gap:6px;margin-bottom:5px"><span style="color:{color};font-size:12px;margin-top:1px">✓</span><span style="font-size:12px;color:#475569">{b}</span></div>' for b in bullets)}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # ── Two-option data source panel ──────────────────────────────────────────
    col_up, col_div, col_gs = st.columns([1, 0.04, 1])

    with col_up:
        st.markdown(f"""
        <div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;
                    padding:24px 24px 16px;height:100%">
          <div style="font-size:20px;margin-bottom:6px">📂</div>
          <div style="font-size:14px;font-weight:700;color:{TEXT_DARK};margin-bottom:4px">Upload Excel File</div>
          <div style="font-size:12px;color:#64748b;margin-bottom:14px">Accepts .xlsx or .xls · Max 200 MB</div>
        </div>
        """, unsafe_allow_html=True)
        landing_file = st.file_uploader(
            "Choose file", type=["xlsx","xls"], label_visibility="collapsed"
        )
        if landing_file is not None:
            st.session_state.uploaded_file = landing_file
            st.rerun()

    with col_div:
        st.markdown(f"""
        <div style="display:flex;flex-direction:column;align-items:center;
                    justify-content:center;height:180px;gap:6px">
          <div style="flex:1;width:1px;background:{BORDER}"></div>
          <div style="font-size:11px;font-weight:600;color:#94a3b8;padding:4px 0">OR</div>
          <div style="flex:1;width:1px;background:{BORDER}"></div>
        </div>
        """, unsafe_allow_html=True)

    with col_gs:
        st.markdown(f"""
        <div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;
                    padding:24px 24px 16px;height:100%">
          <div style="font-size:20px;margin-bottom:6px">🔗</div>
          <div style="font-size:14px;font-weight:700;color:{TEXT_DARK};margin-bottom:4px">Connect Google Sheet</div>
          <div style="font-size:12px;color:#64748b;margin-bottom:14px">Share sheet as <b>Anyone with link → Viewer</b> first</div>
        </div>
        """, unsafe_allow_html=True)
        gs_url = st.text_input(
            "Google Sheets URL", placeholder="https://docs.google.com/spreadsheets/d/...",
            label_visibility="collapsed"
        )
        if st.button("Connect Sheet", use_container_width=True, type="primary"):
            if gs_url.strip():
                with st.spinner("Fetching sheet…"):
                    data, err = fetch_gsheet(gs_url.strip())
                if err:
                    st.error(err)
                else:
                    st.session_state.uploaded_file = data
                    st.rerun()
            else:
                st.warning("Please paste a Google Sheets URL first.")

    st.markdown(f"""
    <div style="text-align:center;padding:24px 0 8px">
      <span style="font-size:12px;color:#94a3b8">Powered by </span>
      <span style="font-size:13px;font-weight:700;color:{BLUE};letter-spacing:0.02em">Zorvix</span>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📋  Expected Excel columns"):
        st.dataframe(pd.DataFrame({
            "Column":      ["Sprint","Team","Jira ID","Priority","Status",
                            "Percentage Complete","Resource","Estimated Effort this sprint",
                            "Actual Effort","Blocker","Starred","From","Remarks",
                            "Start date","Release Date"],
            "Description": ["Sprint name + date range","Team code (SF, FE, Secured, DSA…)",
                            "Ticket ID","P0/P1/P2/P3","DEV / UAT / Done / Blocked",
                            "0–100","Assignee name","Hours planned for sprint",
                            "Hours logged","Yes / No","Yes / No  (leadership items)",
                            "Category (Credit, PMO, Ops…)","Free-text health notes",
                            "Task start date","Target release date"],
        }), use_container_width=True, hide_index=True)
    st.stop()

uploaded = st.session_state.uploaded_file


# ═══════════════════════════════════════════════════════════════════════════════
#  LOAD DATA + UNIFIED DARK HEADER (filter controls + sprint info in one row)
# ═══════════════════════════════════════════════════════════════════════════════
df_all   = load_data(uploaded)
sprints  = [s for s in df_all["Sprint"].dropna().unique() if s]
teams_all = sorted(df_all["Team"].unique().tolist())
today    = pd.Timestamp.now().normalize()

import streamlit.components.v1 as _components

# Create the unified header row — 5 columns
col_info, col_sprint, col_teams, col_browse, col_print = st.columns([2.6, 1.1, 2.2, 0.7, 0.65])

# ── Fill filter controls first (needed before data filtering) ──
with col_sprint:
    sel_sprint = st.selectbox("Sprint", ["All"] + sprints, label_visibility="collapsed")
with col_teams:
    sel_teams = st.multiselect("Teams", teams_all, default=teams_all,
                               placeholder="All teams", label_visibility="collapsed")
with col_browse:
    if st.button("⌂  Home", use_container_width=True):
        st.session_state.uploaded_file = None
        st.rerun()
with col_print:
    _components.html(
        '''<button onclick="window.parent.print()" style="
            width:100%;background:rgba(255,255,255,0.12);color:white;
            border:1px solid rgba(255,255,255,0.25);border-radius:7px;
            padding:0 12px;height:36px;font-size:12px;font-weight:600;
            cursor:pointer;font-family:Inter,sans-serif;white-space:nowrap">
          🖨 Print</button>''',
        height=38,
    )

# ── Filter & KPIs ──
df = df_all.copy()
if sel_sprint != "All":
    df = df[df["Sprint"] == sel_sprint]
if sel_teams:
    df = df[df["Team"].isin(sel_teams)]
if df.empty:
    st.warning("No data for current filters.")
    st.stop()

avg_pct      = df["Percentage Complete"].mean()
blocked_n    = (df["Blocker"].str.lower() == "yes").sum()
total_actual = df["Actual Effort"].sum()
total_est    = df["Estimated Effort this sprint"].sum()
remaining    = max(total_est - total_actual, 0)
total_tasks  = len(df)
done_n       = (df["Status"].str.lower() == "done").sum()

sprint_label = sel_sprint if sel_sprint != "All" else (sprints[0] if sprints else "Sprint")
s_start = df["Start date"].min()   if "Start date"   in df.columns else None
s_end   = df["Release Date"].max() if "Release Date" in df.columns else None
date_str = ""
try:
    if pd.notna(s_start) and pd.notna(s_end):
        date_str = (f"{pd.to_datetime(s_start).strftime('%d %b')} – "
                    f"{pd.to_datetime(s_end).strftime('%d %b, %Y')}")
except Exception:
    pass

days_left_banner = 0
try:
    sp_end_dt = pd.to_datetime(df["Release Date"].max(), errors="coerce") if "Release Date" in df.columns else None
    if sp_end_dt and pd.notna(sp_end_dt):
        days_left_banner = max(int((sp_end_dt - today).days), 0)
except Exception:
    pass

# ── Fill sprint info column LAST (uses computed KPIs) ──
with col_info:
    days_badge = f"<span style='background:rgba(245,158,11,0.2);color:#fbbf24;border-radius:4px;padding:1px 8px;font-size:10px;font-weight:700'>{days_left_banner}d left</span>" if days_left_banner else ""
    st.markdown(f"""
    <span class="hdr-anchor"></span>
    <div style="padding:2px 0">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:3px">
        <span style="font-size:17px;font-weight:700;color:#f1f5f9;letter-spacing:-0.01em">{sprint_label}</span>
        <span style="background:#dcfce7;color:#166534;border-radius:20px;padding:1px 8px;font-size:10px;font-weight:700">Active</span>
        {days_badge}
      </div>
      <div style="font-size:11px;color:#64748b;margin-bottom:8px">{date_str}</div>
      <div class="kpi-inline">
        <div class="kpi-inline-item">Tasks<b>{total_tasks}</b></div>
        <div class="kpi-inline-item">Complete<b>{avg_pct:.0f}%</b></div>
        <div class="kpi-inline-item">Done<b style="color:#4ade80">{done_n}</b></div>
        <div class="kpi-inline-item">Blocked<b style="color:{'#f87171' if blocked_n else '#f1f5f9'}">{blocked_n}</b></div>
        <div class="kpi-inline-item">Effort<b>{total_actual:.0f}h</b></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(["📊  Overview", "📋  Tasks", "👥  Team", "📈  Insights"])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
with tab1:

    c1, c2, c3 = st.columns(3)
    with c1:
        sc = df["Status"].value_counts()
        st.plotly_chart(
            donut_chart(sc.index.tolist(), sc.values.tolist(), "Tasks by Status",
                        [STATUS_COLORS.get(s, TEXT_LIGHT) for s in sc.index]),
            use_container_width=True, config={"displayModeBar": False})

    with c2:
        pc = df["Priority"].replace("","—").value_counts().sort_index()
        st.plotly_chart(
            donut_chart(pc.index.tolist(), pc.values.tolist(), "Tasks by Priority",
                        [PRIORITY_COLORS.get(p, TEXT_LIGHT) for p in pc.index]),
            use_container_width=True, config={"displayModeBar": False})

    with c3:
        st.markdown(f'<p style="font-size:13px;font-weight:700;color:{TEXT_DARK};margin-bottom:8px">🚧 Top Blockers</p>',
                    unsafe_allow_html=True)
        blk = df[df["Blocker"].str.lower() == "yes"]
        if blk.empty:
            st.success("No blockers!")
        else:
            for _, r in blk.iterrows():
                fc = PRIORITY_COLORS.get(r["Priority"], TEXT_LIGHT)
                st.markdown(f"""
                <div class="row-item" style="border-left:4px solid {fc}">
                  <div style="display:flex;align-items:center;gap:6px;margin-bottom:3px">
                    <b style="color:{TEXT_DARK};font-size:13px">{r['Jira ID']}</b>
                    {badge(r['Priority'])} {badge(r['Status'])}
                  </div>
                  <div style="font-size:12px;color:{TEXT_MID}">{str(r.get('Summary',''))[:55] or '—'}</div>
                  <div style="font-size:11px;color:{TEXT_LIGHT};margin-top:3px">👤 {r['Resource']}</div>
                </div>""", unsafe_allow_html=True)

    tc = df.groupby("Team")["Percentage Complete"].mean().reset_index()
    st.plotly_chart(team_bar(tc["Team"].tolist(), tc["Percentage Complete"].tolist()),
                    use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — TASKS
# ─────────────────────────────────────────────────────────────────────────────
with tab2:
    show_cols = [c for c in [
        "Jira ID","Team","Priority","From","Summary","Status",
        "Percentage Complete","Resource","Actual Effort",
        "Remaining effort","Start date","Release Date","Remarks",
    ] if c in df.columns]

    def _cs(val):
        return {"DEV":"background-color:#dbeafe;color:#1e40af",
                "UAT":"background-color:#ede9fe;color:#5b21b6",
                "Done":"background-color:#dcfce7;color:#166534",
                "Blocked":"background-color:#fee2e2;color:#991b1b"}.get(val,"")

    def _cp(val):
        return {"P0":"background-color:#fee2e2;color:#991b1b",
                "P1":"background-color:#ffedd5;color:#9a3412",
                "P2":"background-color:#fef9c3;color:#854d0e",
                "P3":"background-color:#dbeafe;color:#1e40af"}.get(val,"")

    styled = (
        df[show_cols].style
        .map(_cs, subset=["Status"]   if "Status"   in show_cols else [])
        .map(_cp, subset=["Priority"] if "Priority" in show_cols else [])
        .format({"Percentage Complete":"{:.0f}%",
                 "Actual Effort":"{:.0f}h",
                 "Remaining effort":"{:.0f}h"}, na_rep="—")
    )
    st.dataframe(styled, use_container_width=True, height=420, hide_index=True)

    st.markdown(f'<div class="section-hdr" style="margin-top:16px">On-Time Risk</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub">Remaining effort vs days to release — signals potential misses</p>', unsafe_allow_html=True)

    rdf = df.copy()
    if "Release Date" in rdf.columns:
        rdf["rel_dt"]    = pd.to_datetime(rdf["Release Date"], errors="coerce")
        rdf["days_left"] = (rdf["rel_dt"] - today).dt.days.fillna(99).astype(int)
    else:
        rdf["days_left"] = 99

    def _risk(row):
        if row["Percentage Complete"] >= 100:       return "Done",    "#059669", "#a7f3d0"
        if row["Blocker"].lower() == "yes":          return "Blocked", "#dc2626", "#fecaca"
        if row["days_left"] <= 1 and row["Remaining effort"] > 0:
                                                     return "At Risk", "#dc2626", "#fecaca"
        if row["days_left"] <= 3 and row["Remaining effort"] > row["days_left"] * 6:
                                                     return "At Risk", "#dc2626", "#fecaca"
        if row["days_left"] <= 3:                    return "Tight",   "#d97706", "#fde68a"
        return "On Track", "#059669", "#a7f3d0"

    rdf[["rl","rfc","rbc"]] = rdf.apply(lambda r: pd.Series(_risk(r)), axis=1)
    risk_cols = st.columns(2)
    for i, (_, r) in enumerate(rdf.sort_values("days_left").iterrows()):
        with risk_cols[i % 2]:
            st.markdown(f"""
            <div class="row-item" style="border-left:4px solid {r['rfc']}">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div style="display:flex;align-items:center;gap:6px">
                  <b style="color:{TEXT_DARK};font-size:13px">{r['Jira ID']}</b>
                  {badge(r['Priority'])} {badge(r['Status'])}
                </div>
                <span style="background:{r['rbc']};color:{r['rfc']};
                             border-radius:5px;padding:2px 9px;font-size:11px;font-weight:700">
                  {r['rl']}
                </span>
              </div>
              <div style="font-size:12px;color:{TEXT_MID};margin:3px 0">
                {str(r.get('Summary',''))[:60] or '—'}
              </div>
              <div style="font-size:11px;color:{TEXT_LIGHT}">
                👤 {r['Resource']} &nbsp;·&nbsp;
                🕐 {r['Remaining effort']:.0f}h left &nbsp;·&nbsp;
                📅 {r['days_left']}d to release
              </div>
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — TEAM
# ─────────────────────────────────────────────────────────────────────────────
with tab3:
    eff = (df.groupby("Resource")[["Estimated Effort this sprint","Actual Effort"]]
             .sum().reset_index())
    st.plotly_chart(
        grouped_bar(eff, "Resource",
                    ["Estimated Effort this sprint","Actual Effort"],
                    "Effort — Estimated vs Actual (Hours)",
                    [BLUE, GREEN]),
        use_container_width=True, config={"displayModeBar": False})

    w_col, o_col = st.columns([1, 1])

    with w_col:
        st.markdown(f'<div class="section-hdr">Workload Utilisation</div>', unsafe_allow_html=True)
        wdf = (df.groupby("Resource")
                 .agg(Act=("Actual Effort","sum"), Est=("Estimated Effort this sprint","sum"))
                 .reset_index())
        wdf["util"] = ((wdf["Act"] / wdf["Est"].replace(0,1)) * 100).clip(upper=100).round(0)
        for _, r in wdf.iterrows():
            u = int(r["util"])
            bc = "#059669" if u <= 70 else "#f59e0b" if u <= 90 else "#dc2626"
            st.markdown(f"""
            <div class="row-item">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <b style="color:{TEXT_DARK};font-size:13px">{r['Resource']}</b>
                <span style="font-size:12px;color:{TEXT_MID}">
                  {r['Act']:.0f}h / {r['Est']:.0f}h &nbsp;
                  <b style="color:{bc}">{u}%</b>
                </span>
              </div>
              {pbar(u, bc)}
            </div>""", unsafe_allow_html=True)

    with o_col:
        st.markdown(f'<div class="section-hdr">Resource Overload Alert</div>', unsafe_allow_html=True)

        if "Release Date" in df.columns:
            sp_end    = pd.to_datetime(df["Release Date"].max(), errors="coerce")
            days_left = max(int((sp_end - today).days), 1) if pd.notna(sp_end) else 3
        else:
            days_left = 3
        capacity = days_left * 8

        odf = (df.groupby("Resource")
                 .agg(rem=("Remaining effort","sum"), est=("Estimated Effort this sprint","sum"))
                 .reset_index())

        st.markdown(f"""
        <div style="background:#f8fafc;border:1px solid {BORDER};border-radius:8px;
                    padding:8px 12px;margin-bottom:10px;font-size:12px;color:{TEXT_MID}">
          Sprint ends in <b style="color:{TEXT_DARK}">{days_left} day{'s' if days_left!=1 else ''}</b>
          &nbsp;·&nbsp; Capacity: <b style="color:{TEXT_DARK}">{capacity}h / person</b>
        </div>""", unsafe_allow_html=True)

        for _, r in odf.iterrows():
            rem  = r["rem"]
            fill = min((rem / capacity) * 100, 100) if capacity > 0 else 100
            if rem > capacity:
                lbl, bc, bgc = f"⚠ Overloaded +{rem-capacity:.0f}h", "#dc2626", "#fecaca"
            elif rem > capacity * 0.8:
                lbl, bc, bgc = "Near capacity",                        "#d97706", "#fde68a"
            elif rem == 0:
                lbl, bc, bgc = "✓ Complete",                           "#059669", "#a7f3d0"
            else:
                lbl, bc, bgc = "✓ On track",                           "#059669", "#a7f3d0"
            st.markdown(f"""
            <div class="row-item" style="border-left:4px solid {bc}">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <b style="color:{TEXT_DARK};font-size:13px">{r['Resource']}</b>
                <span style="background:{bgc};color:{bc};border-radius:5px;
                             padding:2px 8px;font-size:11px;font-weight:700">{lbl}</span>
              </div>
              <div style="font-size:12px;color:{TEXT_MID};margin:4px 0">
                {rem:.0f}h remaining &nbsp;/&nbsp; {capacity}h available
              </div>
              {pbar(fill, bc)}
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4 — INSIGHTS
# ─────────────────────────────────────────────────────────────────────────────
with tab4:
    st.markdown(f'<div class="section-hdr">Effort Variance per Task</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub">Red = over budget · Green = under budget · Zero line = on estimate</p>', unsafe_allow_html=True)
    st.plotly_chart(variance_chart(df), use_container_width=True,
                    config={"displayModeBar": False})

    ca, cb, cc = st.columns(3)

    with ca:
        from_eff = df.groupby("From")["Actual Effort"].sum().reset_index()
        from_eff = from_eff[from_eff["From"] != ""]
        st.plotly_chart(
            donut_chart(from_eff["From"].tolist(), from_eff["Actual Effort"].tolist(),
                        "Effort by Category",
                        CHART_PALETTE[:len(from_eff)]),
            use_container_width=True, config={"displayModeBar": False})

    with cb:
        st.markdown(f'<div class="section-hdr">Critical vs Non-Critical</div>', unsafe_allow_html=True)
        st.markdown(f'<p class="sub">Are P0/P1 completing faster than P2/P3?</p>', unsafe_allow_html=True)

        high_df  = df[df["Priority"].isin(["P0","P1"])]["Percentage Complete"]
        low_df   = df[df["Priority"].isin(["P2","P3"])]["Percentage Complete"]
        high_avg = high_df.mean() if len(high_df) else 0
        low_avg  = low_df.mean()  if len(low_df)  else 0

        for lbl, avg, color, cnt in [
            ("P0 + P1  — Critical", high_avg, RED,  len(high_df)),
            ("P2 + P3  — Standard", low_avg,  BLUE, len(low_df)),
        ]:
            st.markdown(f"""
            <div class="row-item" style="margin-bottom:12px">
              <div style="display:flex;justify-content:space-between;margin-bottom:6px">
                <span style="font-size:13px;font-weight:600;color:{TEXT_DARK}">{lbl}</span>
                <span style="font-size:14px;font-weight:700;color:{color}">{avg:.0f}%</span>
              </div>
              {pbar(avg, color, 10)}
              <div style="font-size:11px;color:{TEXT_LIGHT};margin-top:5px">
                {cnt} task{'s' if cnt!=1 else ''}
              </div>
            </div>""", unsafe_allow_html=True)

        if high_avg < low_avg - 10:
            st.warning("⚠️ Standard tasks are ahead of critical — review priorities.")
        elif high_avg >= low_avg:
            st.success("✅ Critical tasks are on track.")

    with cc:
        st.markdown(f'<div class="section-hdr">⭐ Starred / Leadership Items</div>', unsafe_allow_html=True)
        st.markdown(f'<p class="sub">Items leadership is watching (Starred = Yes)</p>', unsafe_allow_html=True)
        starred = df[df["Starred"].str.lower() == "yes"]
        if starred.empty:
            st.info("No starred items.")
        else:
            for _, r in starred.iterrows():
                pct = int(r["Percentage Complete"])
                fc  = PRIORITY_COLORS.get(r["Priority"], TEXT_LIGHT)
                bc  = pbar_color(pct)
                st.markdown(f"""
                <div class="row-item" style="border-left:4px solid {fc}">
                  <div style="display:flex;align-items:center;gap:5px;margin-bottom:3px">
                    <b style="color:{TEXT_DARK};font-size:13px">{r['Jira ID']}</b>
                    {badge(r['Priority'])} {badge(r['Status'])}
                  </div>
                  <div style="font-size:12px;color:{TEXT_MID};margin:3px 0">
                    {str(r.get('Summary',''))[:50] or '—'}
                  </div>
                  {pbar(pct, bc, 6)}
                  <div style="font-size:11px;color:{TEXT_LIGHT};margin-top:4px">
                    {pct}% · 👤 {r['Resource']}
                  </div>
                </div>""", unsafe_allow_html=True)

    st.markdown(f'<div class="section-hdr" style="margin-top:16px">Remarks Health Heatmap</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="sub">Green = done/on-track · Amber = in progress · Red = issue/delay</p>', unsafe_allow_html=True)

    if "Remarks" in df.columns:
        hm_cols = st.columns(min(len(df), 4))
        for i, (_, r) in enumerate(df.iterrows()):
            remark = str(r.get("Remarks","")) or "—"
            fg, bg = remarks_color(remark)
            pct    = int(r.get("Percentage Complete", 0))
            with hm_cols[i % len(hm_cols)]:
                st.markdown(f"""
                <div style="background:{bg};border:1.5px solid {fg};border-radius:10px;
                            padding:14px 16px;margin-bottom:10px;text-align:center">
                  <div style="font-size:13px;font-weight:700;color:{fg}">
                    {r.get('Jira ID',f'Task {i+1}')}
                  </div>
                  <div style="font-size:11px;color:{TEXT_MID};margin:3px 0">
                    {r.get('Team','')} · {pct}%
                  </div>
                  <div style="font-size:12px;color:{fg};font-weight:600;margin-top:4px">
                    {remark}
                  </div>
                </div>""", unsafe_allow_html=True)
    else:
        st.info("Add a 'Remarks' column to your Excel to see this heatmap.")
