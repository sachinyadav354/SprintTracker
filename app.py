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
/* Ensure column groups don't bleed into next row */
[data-testid="stHorizontalBlock"] {{ margin-bottom:4px !important; }}

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


def severity_badge(priority: str) -> str:
    """High / Medium / Low severity label derived from task priority."""
    mapping = {"P0": ("#991b1b","#fee2e2","High"),
               "P1": ("#92400e","#fef3c7","Medium"),
               "P2": ("#1e40af","#dbeafe","Low"),
               "P3": ("#374151","#f1f5f9","Low")}
    tc, bg, lbl = mapping.get(priority, ("#374151","#f1f5f9","Low"))
    return (f'<span style="background:{bg};color:{tc};border-radius:4px;'
            f'padding:1px 7px;font-size:10px;font-weight:700">{lbl}</span>')


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
    if pct >= 80: return "#059669"
    if pct >= 40: return "#f59e0b"
    return "#dc2626"


_AVATAR_COLORS = ["#1d4ed8","#059669","#7c3aed","#dc2626","#0284c7",
                  "#db2777","#d97706","#0d9488"]

def avatar(name: str, size: int = 28) -> str:
    initials = "".join(p[0].upper() for p in name.strip().split()[:2]) or "?"
    color = _AVATAR_COLORS[hash(name) % len(_AVATAR_COLORS)]
    return (f'<div style="width:{size}px;height:{size}px;border-radius:50%;'
            f'background:{color};color:white;font-size:{size//2-1}px;'
            f'font-weight:700;display:inline-flex;align-items:center;'
            f'justify-content:center;flex-shrink:0">{initials}</div>')


def time_ago(dt) -> str:
    if pd.isna(dt):
        return "—"
    diff = pd.Timestamp.now() - pd.Timestamp(dt)
    mins = int(diff.total_seconds() / 60)
    if mins < 1:   return "just now"
    if mins < 60:  return f"{mins}m ago"
    if mins < 1440: return f"{mins//60}h ago"
    return f"{mins//1440}d ago"


def status_badge_ref(status: str) -> str:
    """Colored badge matching reference-style status labels."""
    s = status.lower()
    if s in ("done","completed"):
        return f'<span style="background:#dcfce7;color:#166534;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:700">Completed</span>'
    if s in ("dev","in progress","uat"):
        return f'<span style="background:#dbeafe;color:#1e40af;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:700">In Progress</span>'
    if s == "blocked":
        return f'<span style="background:#fee2e2;color:#991b1b;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:700">Blocked</span>'
    return f'<span style="background:#f1f5f9;color:#475569;border-radius:4px;padding:2px 8px;font-size:11px;font-weight:700">To Do</span>'


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


def load_data(file) -> tuple:
    """Returns (sprint_df, daily_df). daily_df is None if sheet not present."""
    if isinstance(file, (bytes, bytearray)):
        file = BytesIO(file)
    xls = pd.ExcelFile(file, engine="openpyxl")
    df = xls.parse("Sprint Data") if "Sprint Data" in xls.sheet_names else xls.parse(0)
    df = df.dropna(axis=1, how="all")
    df.columns = df.columns.str.strip()
    for col in ["Percentage Complete","Total Estimated Hours",
                "Estimated Effort this sprint","Actual Effort","Story Points"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    if {"Estimated Effort this sprint","Actual Effort"} <= set(df.columns):
        df["Remaining effort"] = (
            df["Estimated Effort this sprint"] - df["Actual Effort"]
        ).clip(lower=0)
    for col in ["Blocker","Starred","Status","Priority","Team","Resource",
                "Remarks","Summary","Jira ID","From","Sprint","Sprint Goal",
                "Last Updated By"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str).str.strip()
    if "Last Updated" in df.columns:
        df["Last Updated"] = pd.to_datetime(df["Last Updated"], errors="coerce")
    if "Story Points" not in df.columns:
        df["Story Points"] = 0
    daily_df = None
    if "Daily Log" in xls.sheet_names:
        daily_df = xls.parse("Daily Log")
        daily_df.columns = daily_df.columns.str.strip()
        daily_df["Date"] = pd.to_datetime(daily_df["Date"], errors="coerce")
        for c in ["Ideal SP Remaining","Actual SP Remaining",
                  "Planned Effort (h)","Actual Effort Logged (h)"]:
            if c in daily_df.columns:
                daily_df[c] = pd.to_numeric(daily_df[c], errors="coerce").fillna(0)
    return df, daily_df


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


def donut_chart(labels, values, title, colors=None, center_text=None) -> go.Figure:
    colors = colors or [STATUS_COLORS.get(l, TEXT_LIGHT) for l in labels]
    total  = sum(values)
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.60,
        marker=dict(colors=colors, line=dict(color=CARD, width=2)),
        textinfo="percent", textfont={"size": 11, "color": TEXT_DARK},
        insidetextorientation="horizontal",
        hovertemplate="<b>%{label}</b><br>%{value} (%{percent})<extra></extra>",
    ))
    center = center_text or f"<b>{total}</b>"
    fig.add_annotation(
        text=center, x=0.5, y=0.5, showarrow=False,
        font=dict(size=15, color=TEXT_DARK, family="Inter, Arial"),
        xanchor="center", yanchor="middle",
    )
    fig.update_layout(
        **_base_layout(title, 210, margin=dict(l=6, r=6, t=36, b=28)),
        legend=dict(
            orientation="h", x=0.5, y=-0.06, xanchor="center",
            font={"size": 11, "color": TEXT_MID}, bgcolor="rgba(0,0,0,0)",
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


def burndown_chart(daily_df: pd.DataFrame, sprint: str) -> go.Figure:
    d = daily_df[daily_df["Sprint"] == sprint].sort_values("Day")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d["Day"], y=d["Ideal SP Remaining"], name="Ideal",
        line=dict(color="#94a3b8", width=2, dash="dash"),
        hovertemplate="Day %{x} — Ideal: %{y} SP<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=d["Day"], y=d["Actual SP Remaining"], name="Actual",
        line=dict(color=BLUE, width=2.5),
        fill="tozeroy", fillcolor="rgba(29,78,216,0.06)",
        hovertemplate="Day %{x} — Actual: %{y} SP<extra></extra>"))
    fig.update_layout(
        **_base_layout("Burndown Chart", 220),
        xaxis={"title": "Sprint Day", "gridcolor": GRID_COLOR,
               "tickfont": {"size": 11, "color": TEXT_MID}},
        yaxis={"title": "SP Remaining", "gridcolor": GRID_COLOR,
               "tickfont": {"size": 11, "color": TEXT_MID}},
        legend=dict(orientation="h", y=1.12, font={"size": 11}, bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def effort_trend_chart(daily_df: pd.DataFrame, sprint: str) -> go.Figure:
    d = daily_df[daily_df["Sprint"] == sprint].sort_values("Day")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=d["Day"], y=d["Planned Effort (h)"], name="Planned",
        line=dict(color="#94a3b8", width=2, dash="dot"),
        hovertemplate="Day %{x} — Planned: %{y}h<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=d["Day"], y=d["Actual Effort Logged (h)"], name="Actual Logged",
        line=dict(color=GREEN, width=2.5),
        fill="tozeroy", fillcolor="rgba(5,150,105,0.07)",
        hovertemplate="Day %{x} — Actual: %{y}h<extra></extra>"))
    fig.update_layout(
        **_base_layout("Effort Trend (Cumulative)", 220),
        xaxis={"title": "Sprint Day", "gridcolor": GRID_COLOR,
               "tickfont": {"size": 11, "color": TEXT_MID}},
        yaxis={"title": "Hours", "gridcolor": GRID_COLOR,
               "tickfont": {"size": 11, "color": TEXT_MID}},
        legend=dict(orientation="h", y=1.12, font={"size": 11}, bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def velocity_chart(df_all: pd.DataFrame) -> go.Figure:
    vel = (df_all.groupby("Sprint")
           .agg(SP_Done=("Story Points", lambda x:
               x[df_all.loc[x.index,"Status"].str.lower()=="done"].sum()),
                SP_Total=("Story Points","sum"))
           .reset_index())
    vel["Sprint_Short"] = vel["Sprint"].str.extract(r'(Sprint \d+)')
    avg = vel["SP_Done"].mean()

    # Delta vs previous sprint
    delta_text = ""
    if len(vel) >= 2:
        curr = vel["SP_Done"].iloc[-1]
        prev = vel["SP_Done"].iloc[-2]
        if prev > 0:
            delta_pct = (curr - prev) / prev * 100
            arrow = "▲" if delta_pct >= 0 else "▼"
            delta_color = GREEN if delta_pct >= 0 else RED
            delta_text = f"  <span style='color:{delta_color}'>{arrow} {abs(delta_pct):.0f}% vs last sprint</span>"

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=vel["Sprint_Short"], y=vel["SP_Total"], name="Committed",
        marker_color="#e0e7ff", text=vel["SP_Total"],
        textposition="outside", textfont={"size": 11, "color": TEXT_MID}))
    fig.add_trace(go.Bar(
        x=vel["Sprint_Short"], y=vel["SP_Done"], name="Delivered",
        marker_color=BLUE, text=vel["SP_Done"],
        textposition="inside", textfont={"size": 11, "color": "white"}))
    fig.add_hline(y=avg, line_dash="dash", line_color=AMBER, line_width=1.5,
                  annotation_text=f"Avg {avg:.0f} SP", annotation_font_color=AMBER)
    fig.update_layout(
        **_base_layout(f"Team Velocity{delta_text}", 220),
        barmode="overlay",
        xaxis={"gridcolor": GRID_COLOR, "tickfont": {"size": 12, "color": GREEN}},
        yaxis={"gridcolor": GRID_COLOR, "title": "Story Points",
               "tickfont": {"size": 11, "color": TEXT_MID}},
        legend=dict(orientation="h", y=1.12, font={"size": 11}, bgcolor="rgba(0,0,0,0)"),
        bargap=0.35,
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
df_all, daily_df = load_data(uploaded)
sprints  = [s for s in df_all["Sprint"].dropna().unique() if s]
teams_all = sorted(df_all["Team"].unique().tolist())
today    = pd.Timestamp.now().normalize()

import streamlit.components.v1 as _components

# Create the unified header row — 5 columns
col_info, col_sprint, col_teams, col_browse, col_print, col_user = st.columns([2.4, 1.1, 2.0, 0.7, 0.65, 0.9])

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

# Feature 10 — User Profile widget in header
with col_user:
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:8px">
      <div style="width:32px;height:32px;border-radius:8px;background:{BLUE};
                  color:white;font-size:11px;font-weight:800;display:flex;
                  align-items:center;justify-content:center;flex-shrink:0;
                  letter-spacing:-0.02em">ZX</div>
      <div style="min-width:0">
        <div style="font-size:12px;font-weight:700;color:#f1f5f9;white-space:nowrap">Zorvix</div>
        <div style="font-size:10px;color:#64748b;white-space:nowrap">Sprint Intelligence</div>
      </div>
    </div>""", unsafe_allow_html=True)

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
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊  Overview", "📋  Tasks", "👥  Team", "📈  Insights",
    "🔍  Reports", "📅  Capacity", "🗓  Timeline", "📥  Backlog"
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — OVERVIEW
# ─────────────────────────────────────────────────────────────────────────────
with tab1:
    # ── Row 1: SP progress + Sprint Goal + Blockers ───────────────────────────
    sp_total     = int(df["Story Points"].sum()) if "Story Points" in df.columns else 0
    sp_done      = int(df.loc[df["Status"].str.lower()=="done","Story Points"].sum()) if sp_total else 0
    sp_remaining = sp_total - sp_done
    sp_pct       = int(sp_done/sp_total*100) if sp_total else 0
    sprint_goal  = df["Sprint Goal"].iloc[0] if "Sprint Goal" in df.columns and df["Sprint Goal"].iloc[0] else ""

    # ── Feature 5: Sprint Health Score ───────────────────────────────────────
    # Weighted score: completion rate (40%) + no blockers (25%) + P0/P1 progress (25%) + effort (10%)
    blocker_score  = max(0, 100 - blocked_n * 20)
    p0p1 = df[df["Priority"].isin(["P0","P1"])]["Percentage Complete"]
    p0p1_score     = float(p0p1.mean()) if len(p0p1) else 100
    effort_score   = min(100, (total_actual / max(total_est,1)) * 100)
    health_score   = int(avg_pct * 0.40 + blocker_score * 0.25 + p0p1_score * 0.25 + effort_score * 0.10)
    if health_score >= 75:   health_label, health_color, health_bg = "Healthy",  "#059669", "#dcfce7"
    elif health_score >= 50: health_label, health_color, health_bg = "At Risk",  "#d97706", "#fef3c7"
    else:                    health_label, health_color, health_bg = "Critical", "#dc2626", "#fee2e2"

    # ── Row 1: 3 equal cards — SP / Health / Goal (fixed height, no overflow) ──
    CARD_H = "140px"
    sg1, sg2, sg3 = st.columns(3)

    with sg1:
        st.markdown(f"""
        <div class="card" style="border-top:3px solid {BLUE};min-height:{CARD_H}">
          <div style="font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;
                      letter-spacing:0.08em;margin-bottom:10px">Story Points</div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:4px;text-align:center">
            <div style="background:#f8fafc;border-radius:8px;padding:8px 4px">
              <div style="font-size:22px;font-weight:800;color:{TEXT_DARK}">{sp_total}</div>
              <div style="font-size:10px;color:#94a3b8;text-transform:uppercase">Committed</div>
            </div>
            <div style="background:#f0fdf4;border-radius:8px;padding:8px 4px">
              <div style="font-size:22px;font-weight:800;color:{GREEN}">{sp_done}</div>
              <div style="font-size:10px;color:#94a3b8;text-transform:uppercase">Done</div>
            </div>
            <div style="background:#fffbeb;border-radius:8px;padding:8px 4px">
              <div style="font-size:22px;font-weight:800;color:{AMBER}">{sp_remaining}</div>
              <div style="font-size:10px;color:#94a3b8;text-transform:uppercase">Remaining</div>
            </div>
          </div>
          {pbar(sp_pct, BLUE, 6)}
          <div style="font-size:10px;color:#64748b;margin-top:5px;text-align:right">{sp_pct}% complete</div>
        </div>""", unsafe_allow_html=True)

    with sg2:
        st.markdown(f"""
        <div class="card" style="border-top:3px solid {health_color};min-height:{CARD_H};text-align:center">
          <div style="font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;
                      letter-spacing:0.08em;margin-bottom:8px">Sprint Health</div>
          <div style="font-size:40px;font-weight:800;color:{health_color};line-height:1">{health_score}</div>
          <div style="font-size:10px;color:#94a3b8;margin-bottom:8px">out of 100</div>
          <div style="background:{health_bg};color:{health_color};border-radius:20px;
                      padding:3px 12px;font-size:11px;font-weight:700;display:inline-block">
            {health_label}
          </div>
          {pbar(health_score, health_color, 6)}
        </div>""", unsafe_allow_html=True)

    with sg3:
        goal_html = (sprint_goal if sprint_goal
                     else "<span style='color:#94a3b8;font-size:12px'>Add a <b>Sprint Goal</b> column to your Excel.</span>")
        prog_html = (pbar(avg_pct, GREEN, 6) +
                     f'<div style="font-size:11px;color:#64748b;margin-top:6px">{avg_pct:.0f}% complete</div>'
                     if sprint_goal else "")
        st.markdown(f"""
        <div class="card" style="border-top:3px solid {GREEN};min-height:{CARD_H}">
          <div style="font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;
                      letter-spacing:0.08em;margin-bottom:8px">&#127919; Sprint Goal</div>
          <div style="font-size:13px;color:{TEXT_DARK};line-height:1.6">{goal_html}</div>
          {prog_html}
        </div>""", unsafe_allow_html=True)

    # ── Row 2: Top Blockers (2 per row, compact) ──────────────────────────────
    blk = df[df["Blocker"].str.lower() == "yes"]
    if not blk.empty:
        st.markdown(f'<div class="section-hdr">&#x1F6A7; Top Blockers</div>', unsafe_allow_html=True)
        blk_top = blk.head(4)
        blk_cols = st.columns(2)
        for i, (_, r) in enumerate(blk_top.iterrows()):
            fc = PRIORITY_COLORS.get(r["Priority"], TEXT_LIGHT)
            try:
                days_blocked = max(int((today - pd.to_datetime(r.get("Start date", today))).days), 0)
                since_html = (f'<span style="background:#fee2e2;color:#991b1b;border-radius:4px;'
                              f'padding:1px 6px;font-size:10px;font-weight:700">since {days_blocked}d</span>')
            except Exception:
                since_html = ""
            with blk_cols[i % 2]:
                st.markdown(
                    f'<div class="row-item" style="border-left:4px solid {fc}">'
                    f'<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:2px">'
                    f'<div style="display:flex;align-items:center;gap:5px">'
                    f'<b style="color:{TEXT_DARK};font-size:12px">{r["Jira ID"]}</b>'
                    f'{badge(r["Priority"])}</div>'
                    f'<div style="display:flex;align-items:center;gap:4px">'
                    f'{severity_badge(r["Priority"])} {since_html}</div></div>'
                    f'<div style="font-size:11px;color:{TEXT_MID};margin:2px 0">'
                    f'{str(r.get("Summary",""))[:55] or "—"}</div>'
                    f'<div style="font-size:10px;color:#64748b">&#128100; {r["Resource"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True)
        st.markdown('<div style="margin-bottom:8px"></div>', unsafe_allow_html=True)

    # ── Row 3: Burndown + Effort Trend (if Daily Log exists) ──────────────────
    if daily_df is not None and sprint_label in daily_df["Sprint"].values:
        bd_col, et_col = st.columns(2)
        with bd_col:
            st.plotly_chart(burndown_chart(daily_df, sprint_label),
                            use_container_width=True, config={"displayModeBar": False})
        with et_col:
            st.plotly_chart(effort_trend_chart(daily_df, sprint_label),
                            use_container_width=True, config={"displayModeBar": False})

    # ── Row 3: Status donut | Priority donut | Velocity ───────────────────────
    c1, c2, c3 = st.columns(3)
    with c1:
        sc = df["Status"].value_counts()
        st.plotly_chart(
            donut_chart(sc.index.tolist(), sc.values.tolist(), "Tasks by Status",
                        [STATUS_COLORS.get(s, TEXT_LIGHT) for s in sc.index],
                        center_text=f"<b>{sc.sum()}</b><br><span style='font-size:10px'>Tasks</span>"),
            use_container_width=True, config={"displayModeBar": False})
    with c2:
        pc = df["Priority"].replace("","—").value_counts().sort_index()
        st.plotly_chart(
            donut_chart(pc.index.tolist(), pc.values.tolist(), "Tasks by Priority",
                        [PRIORITY_COLORS.get(p, TEXT_LIGHT) for p in pc.index],
                        center_text=f"<b>{pc.sum()}</b><br><span style='font-size:10px'>Tasks</span>"),
            use_container_width=True, config={"displayModeBar": False})
    with c3:
        if "Story Points" in df_all.columns and df_all["Sprint"].nunique() >= 1:
            st.plotly_chart(velocity_chart(df_all),
                            use_container_width=True, config={"displayModeBar": False})
        else:
            tc = df.groupby("Team")["Percentage Complete"].mean().reset_index()
            st.plotly_chart(team_bar(tc["Team"].tolist(), tc["Percentage Complete"].tolist()),
                            use_container_width=True, config={"displayModeBar": False})

    # ── Row 4: Team completion bar ────────────────────────────────────────────
    tc = df.groupby("Team")["Percentage Complete"].mean().reset_index()
    st.plotly_chart(team_bar(tc["Team"].tolist(), tc["Percentage Complete"].tolist()),
                    use_container_width=True, config={"displayModeBar": False})

    # ── Row 5: Top Stories | Tracker Update ──────────────────────────────────
    ts_col, tu_col = st.columns([3, 2])

    with ts_col:
        st.markdown(f'<div class="section-hdr">Top Stories</div>', unsafe_allow_html=True)
        top = (df[df["Priority"].isin(["P0","P1"])]
               .sort_values(["Priority","Percentage Complete"], ascending=[True,False])
               .head(6))
        # Header
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:80px 1fr 110px 60px 32px;
                    gap:8px;padding:4px 12px;font-size:10px;font-weight:700;
                    color:#94a3b8;text-transform:uppercase;letter-spacing:0.07em;
                    border-bottom:1px solid {BORDER};margin-bottom:4px">
          <div>ID</div><div>Title</div><div>Status</div>
          <div style="text-align:center">SP</div><div></div>
        </div>""", unsafe_allow_html=True)
        for _, r in top.iterrows():
            sp = int(r.get("Story Points", 0))
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:80px 1fr 110px 60px 32px;
                        gap:8px;align-items:center;padding:7px 12px;
                        border-bottom:1px solid {BORDER}">
              <div style="font-size:12px;font-weight:600;color:{BLUE}">{r['Jira ID']}</div>
              <div style="font-size:12px;color:{TEXT_DARK};white-space:nowrap;
                          overflow:hidden;text-overflow:ellipsis" title="{r.get('Summary','')}">
                {str(r.get('Summary',''))[:38] or r['Jira ID']}
              </div>
              <div>{status_badge_ref(r['Status'])}</div>
              <div style="text-align:center;font-size:12px;font-weight:700;
                          color:{TEXT_DARK}">{sp} <span style="font-size:10px;
                          color:#94a3b8">SP</span></div>
              <div style="display:flex;justify-content:center">
                {avatar(r['Resource'], 26)}
              </div>
            </div>""", unsafe_allow_html=True)
        st.markdown(f'<div style="padding:8px 12px"><a style="font-size:12px;color:{BLUE};text-decoration:none;font-weight:600">View all stories →</a></div>', unsafe_allow_html=True)

    with tu_col:
        st.markdown(f'<div class="section-hdr">Tracker Update</div>', unsafe_allow_html=True)
        if "Last Updated By" in df.columns and "Last Updated" in df.columns:
            recent = (df[df["Last Updated"].notna()]
                      .sort_values("Last Updated", ascending=False)
                      .drop_duplicates("Last Updated By")
                      .head(6))
            for _, r in recent.iterrows():
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;
                            padding:8px 4px;border-bottom:1px solid {BORDER}">
                  {avatar(r['Last Updated By'], 32)}
                  <div style="flex:1;min-width:0">
                    <div style="font-size:12px;font-weight:600;color:{TEXT_DARK}">
                      {r['Last Updated By']}
                    </div>
                    <div style="font-size:11px;color:#64748b">
                      updated tracker · {r['Jira ID']}
                    </div>
                  </div>
                  <div style="font-size:11px;color:#94a3b8;white-space:nowrap">
                    {time_ago(r['Last Updated'])}
                  </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Add **Last Updated By** and **Last Updated** columns to your Excel to see activity here.")


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
        st.markdown(f'<div class="section-hdr">Team Workload</div>', unsafe_allow_html=True)
        wdf = (df.groupby("Resource")
                 .agg(Act=("Actual Effort","sum"), Est=("Estimated Effort this sprint","sum"))
                 .reset_index())
        wdf["util"] = ((wdf["Act"] / wdf["Est"].replace(0,1)) * 100).clip(upper=100).round(0)
        # Header row
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:36px 1fr 110px 52px;
                    gap:8px;padding:4px 8px;font-size:10px;font-weight:700;
                    color:#94a3b8;text-transform:uppercase;letter-spacing:0.07em;
                    border-bottom:1px solid {BORDER};margin-bottom:4px">
          <div></div><div>Member</div>
          <div>Logged / Cap</div><div style="text-align:right">Util</div>
        </div>""", unsafe_allow_html=True)
        for _, r in wdf.iterrows():
            u  = int(r["util"])
            bc = "#059669" if u <= 70 else "#f59e0b" if u <= 90 else "#dc2626"
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:36px 1fr 110px 52px;
                        gap:8px;align-items:center;padding:6px 8px;
                        border-bottom:1px solid {BORDER}">
              {avatar(r['Resource'], 30)}
              <div style="font-size:13px;font-weight:600;color:{TEXT_DARK}">{r['Resource']}</div>
              <div>
                <div style="font-size:11px;color:#64748b;margin-bottom:3px">
                  {r['Act']:.0f}h / {r['Est']:.0f}h
                </div>
                {pbar(u, bc, 6)}
              </div>
              <div style="text-align:right;font-size:13px;font-weight:700;color:{bc}">{u}%</div>
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


# ─────────────────────────────────────────────────────────────────────────────
# TAB 5 — REPORTS (new data-driven insights)
# ─────────────────────────────────────────────────────────────────────────────
with tab5:

    # ── 1. Priority Inversion Alert ───────────────────────────────────────────
    st.markdown('<div class="section-hdr">Priority Completion Health</div>', unsafe_allow_html=True)
    st.markdown('<p class="sub">Are high-priority tasks completing faster than low-priority? Inversion = red flag.</p>', unsafe_allow_html=True)

    pri_health = (df.groupby("Priority")
                  .agg(Avg_Pct=("Percentage Complete","mean"),
                       SP=("Story Points","sum"),
                       Tasks=("Jira ID","count"),
                       Blockers=("Blocker", lambda x: (x=="Yes").sum()))
                  .reset_index()
                  .sort_values("Priority"))

    p_cols = st.columns(len(pri_health))
    for col, (_, r) in zip(p_cols, pri_health.iterrows()):
        pct       = int(r["Avg_Pct"])
        bc        = pbar_color(pct)
        warn      = " &#x1F6A8;" if r["Priority"] in ("P0","P1") and pct < 60 else ""
        blk_count = int(r["Blockers"])
        blk_html  = (f'<div style="font-size:10px;color:#dc2626;margin-top:4px;font-weight:600">'
                     f'&#9888; {blk_count} blocker(s)</div>') if blk_count > 0 else ""
        bar_html  = pbar(pct, bc, 6)
        border_c  = PRIORITY_COLORS.get(r["Priority"], BLUE)
        html = (f'<div class="card" style="border-top:3px solid {border_c};text-align:center">'
                f'<div style="font-size:11px;font-weight:700;color:#64748b;margin-bottom:4px">'
                f'{r["Priority"]}{warn}</div>'
                f'<div style="font-size:28px;font-weight:800;color:{bc}">{pct}%</div>'
                f'<div style="font-size:10px;color:#94a3b8;margin:4px 0">'
                f'{int(r["Tasks"])} tasks &middot; {int(r["SP"])} SP</div>'
                f'{bar_html}{blk_html}</div>')
        with col:
            st.markdown(html, unsafe_allow_html=True)

    p0_avg = float(pri_health.loc[pri_health["Priority"]=="P0","Avg_Pct"].values[0]) if "P0" in pri_health["Priority"].values else 100
    p3_avg = float(pri_health.loc[pri_health["Priority"]=="P3","Avg_Pct"].values[0]) if "P3" in pri_health["Priority"].values else 0
    if p0_avg < p3_avg - 20:
        st.error(f"🚨 **Priority Inversion detected** — P0 tasks at {p0_avg:.0f}% while P3 tasks at {p3_avg:.0f}%. Critical items are being left behind.")

    # ── 2. SP Delivery by Team + Resource Efficiency ──────────────────────────
    r1, r2 = st.columns(2)

    with r1:
        st.markdown('<div class="section-hdr">Story Points Delivery by Team</div>', unsafe_allow_html=True)
        team_sp = df.groupby("Team").agg(
            Committed=("Story Points","sum"),
            Delivered=("Story Points", lambda x: x[df.loc[x.index,"Status"]=="Done"].sum())
        ).reset_index()
        fig_sp = go.Figure()
        fig_sp.add_trace(go.Bar(x=team_sp["Team"], y=team_sp["Committed"], name="Committed",
                                marker_color="#e0e7ff", text=team_sp["Committed"],
                                textposition="outside", textfont={"size":11,"color":TEXT_MID}))
        fig_sp.add_trace(go.Bar(x=team_sp["Team"], y=team_sp["Delivered"], name="Delivered",
                                marker_color=BLUE, text=team_sp["Delivered"],
                                textposition="inside", textfont={"size":11,"color":"white"}))
        fig_sp.update_layout(**_base_layout("SP Committed vs Delivered", 220),
                             barmode="overlay", bargap=0.35,
                             xaxis={"tickfont":{"size":12,"color":GREEN}},
                             yaxis={"gridcolor":GRID_COLOR,"tickfont":{"size":11,"color":TEXT_MID}},
                             legend=dict(orientation="h",y=1.12,font={"size":11},bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_sp, use_container_width=True, config={"displayModeBar":False})

    with r2:
        st.markdown('<div class="section-hdr">Resource Efficiency Score</div>', unsafe_allow_html=True)
        st.markdown('<p class="sub">Actual hours logged vs estimated — over 100% = over budget</p>', unsafe_allow_html=True)
        eff_df = df.groupby("Resource").agg(
            Est=("Estimated Effort this sprint","sum"),
            Act=("Actual Effort","sum"),
            Done=("Status", lambda x: (x=="Done").sum()),
            SP=("Story Points", lambda x: x[df.loc[x.index,"Status"]=="Done"].sum())
        ).reset_index()
        eff_df["Eff"] = (eff_df["Act"] / eff_df["Est"].replace(0,1) * 100).round(0).astype(int)
        # Header
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:36px 1fr 80px 60px 50px;
                    gap:8px;padding:4px 8px;font-size:10px;font-weight:700;color:#94a3b8;
                    text-transform:uppercase;letter-spacing:0.07em;border-bottom:1px solid {BORDER};margin-bottom:4px">
          <div></div><div>Member</div><div>Act/Est</div><div>SP Done</div><div style="text-align:right">Eff%</div>
        </div>""", unsafe_allow_html=True)
        for _, r in eff_df.sort_values("Eff").iterrows():
            bc = "#059669" if r["Eff"] <= 80 else "#f59e0b" if r["Eff"] <= 100 else "#dc2626"
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:36px 1fr 80px 60px 50px;
                        gap:8px;align-items:center;padding:7px 8px;border-bottom:1px solid {BORDER}">
              {avatar(r['Resource'], 28)}
              <div style="font-size:12px;font-weight:600;color:{TEXT_DARK}">{r['Resource']}</div>
              <div style="font-size:11px;color:#64748b">{r['Act']:.0f}h / {r['Est']:.0f}h</div>
              <div style="font-size:12px;font-weight:700;color:{BLUE};text-align:center">{int(r['SP'])} SP</div>
              <div style="text-align:right;font-size:13px;font-weight:700;color:{bc}">{r['Eff']}%</div>
            </div>""", unsafe_allow_html=True)

    # ── 3. Category Health + Sprint Comparison ────────────────────────────────
    r3, r4 = st.columns(2)

    with r3:
        st.markdown('<div class="section-hdr">Category Health Scorecard</div>', unsafe_allow_html=True)
        cat = df.groupby("From").agg(
            Tasks=("Jira ID","count"),
            SP=("Story Points","sum"),
            Avg_Pct=("Percentage Complete","mean"),
            Blockers=("Blocker", lambda x: (x=="Yes").sum()),
            Act=("Actual Effort","sum")
        ).reset_index().sort_values("Avg_Pct", ascending=False)
        for _, r in cat.iterrows():
            pct        = int(r["Avg_Pct"])
            bc         = pbar_color(pct)
            blk_count  = int(r["Blockers"])
            blk_html   = (f'<span style="font-size:10px;color:#dc2626;font-weight:700">'
                          f'&#9888; {blk_count} blocked</span>') if blk_count > 0 else ""
            bar_html   = pbar(pct, bc, 7)
            html = (f'<div class="row-item">'
                    f'<div style="display:flex;justify-content:space-between;'
                    f'align-items:center;margin-bottom:5px">'
                    f'<div><span style="font-size:13px;font-weight:700;color:{TEXT_DARK}">'
                    f'{r["From"]}</span>'
                    f'<span style="font-size:11px;color:#94a3b8;margin-left:8px">'
                    f'{int(r["Tasks"])} tasks &middot; {int(r["SP"])} SP &middot; {r["Act"]:.0f}h'
                    f'</span></div>'
                    f'<div style="display:flex;align-items:center;gap:8px">'
                    f'{blk_html}'
                    f'<span style="font-size:14px;font-weight:800;color:{bc}">{pct}%</span>'
                    f'</div></div>'
                    f'{bar_html}</div>')
            st.markdown(html, unsafe_allow_html=True)

    with r4:
        st.markdown('<div class="section-hdr">Sprint Comparison</div>', unsafe_allow_html=True)
        scomp = df_all.groupby("Sprint").agg(
            Tasks=("Jira ID","count"),
            SP=("Story Points","sum"),
            Done=("Status", lambda x: (x=="Done").sum()),
            Blocked=("Blocker", lambda x: (x=="Yes").sum()),
            Avg_Pct=("Percentage Complete","mean"),
            Est=("Estimated Effort this sprint","sum"),
            Act=("Actual Effort","sum")
        ).reset_index()
        # Header
        st.markdown(f"""
        <div style="display:grid;grid-template-columns:1fr 40px 40px 40px 50px 50px;
                    gap:6px;padding:5px 10px;font-size:10px;font-weight:700;color:#94a3b8;
                    text-transform:uppercase;border-bottom:1px solid {BORDER};margin-bottom:4px">
          <div>Sprint</div><div>Tasks</div><div>SP</div>
          <div>Done</div><div>Velocity</div><div>Progress</div>
        </div>""", unsafe_allow_html=True)
        for i, (_, r) in enumerate(scomp.iterrows()):
            pct = int(r["Avg_Pct"])
            bc  = pbar_color(pct)
            sp_name = str(r["Sprint"])[:14] + "…" if len(str(r["Sprint"])) > 14 else str(r["Sprint"])
            bg = "#f8fafc" if i % 2 == 0 else CARD
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:1fr 40px 40px 40px 50px 50px;
                        gap:6px;align-items:center;padding:8px 10px;background:{bg};
                        border-bottom:1px solid {BORDER}">
              <div style="font-size:11px;font-weight:600;color:{TEXT_DARK}">{sp_name}</div>
              <div style="font-size:12px;color:#64748b;text-align:center">{int(r['Tasks'])}</div>
              <div style="font-size:12px;color:#64748b;text-align:center">{int(r['SP'])}</div>
              <div style="font-size:12px;font-weight:700;color:{GREEN};text-align:center">{int(r['Done'])}</div>
              <div style="font-size:12px;font-weight:700;color:{BLUE};text-align:center">{r['Act']:.0f}h</div>
              <div style="font-size:13px;font-weight:700;color:{bc};text-align:right">{pct}%</div>
            </div>""", unsafe_allow_html=True)

    # ── 4. Daily Risk Radar ───────────────────────────────────────────────────
    st.markdown('<div class="section-hdr" style="margin-top:16px">Daily Risk Radar — Hours/Day Needed to Finish</div>', unsafe_allow_html=True)
    st.markdown('<p class="sub">Tasks requiring the most hours per remaining day to hit release date on time</p>', unsafe_allow_html=True)

    risk = df[df["Percentage Complete"] < 100].copy()
    risk["days_left"] = (pd.to_datetime(risk["Release Date"]) - today).dt.days.clip(lower=1)
    risk["h_per_day"] = (risk["Remaining effort"] / risk["days_left"]).round(1)
    risk = risk[risk["Remaining effort"] > 0].sort_values("h_per_day", ascending=False).head(8)

    r_c1, r_c2 = st.columns(2)
    for i, (_, r) in enumerate(risk.iterrows()):
        col = r_c1 if i % 2 == 0 else r_c2
        fc  = PRIORITY_COLORS.get(r["Priority"], TEXT_LIGHT)
        danger = r["h_per_day"] >= 4
        with col:
            st.markdown(f"""
            <div class="row-item" style="border-left:4px solid {'#dc2626' if danger else '#f59e0b'}">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <div style="display:flex;align-items:center;gap:6px">
                  <b style="color:{TEXT_DARK};font-size:13px">{r['Jira ID']}</b>
                  {badge(r['Priority'])} {badge(r['Status'])}
                </div>
                <span style="font-size:14px;font-weight:800;color:{'#dc2626' if danger else '#f59e0b'}">
                  {r['h_per_day']}h/day
                </span>
              </div>
              <div style="font-size:11px;color:#64748b;margin:3px 0">
                {str(r.get('Summary',''))[:55] or '—'}
              </div>
              <div style="font-size:11px;color:#94a3b8">
                👤 {r['Resource']} &nbsp;·&nbsp; 🕐 {r['Remaining effort']:.0f}h left &nbsp;·&nbsp; 📅 {int(r['days_left'])}d to release
              </div>
            </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 6 — CAPACITY PLAN
# ─────────────────────────────────────────────────────────────────────────────
with tab6:
    SPRINT_CAPACITY_H = 40  # hours per person per sprint

    cap_df = df.groupby("Resource").agg(
        Allocated=("Estimated Effort this sprint", "sum"),
        Actual=("Actual Effort", "sum"),
        Tasks=("Jira ID", "count"),
        Done=("Status", lambda x: (x == "Done").sum()),
    ).reset_index()
    cap_df["Capacity"]  = SPRINT_CAPACITY_H
    cap_df["Available"] = (cap_df["Capacity"] - cap_df["Allocated"]).clip(lower=0)
    cap_df["Util_pct"]  = (cap_df["Allocated"] / cap_df["Capacity"] * 100).clip(upper=120).round(0).astype(int)

    # Summary row
    total_cap   = len(cap_df) * SPRINT_CAPACITY_H
    total_alloc = int(cap_df["Allocated"].sum())
    total_avail = max(total_cap - total_alloc, 0)
    alloc_pct   = int(total_alloc / total_cap * 100)

    s1, s2, s3, s4 = st.columns(4)
    for col, lbl, val, color in [
        (s1, "Team Capacity",  f"{total_cap}h",   BLUE),
        (s2, "Allocated",      f"{total_alloc}h",  AMBER),
        (s3, "Available",      f"{total_avail}h",  GREEN),
        (s4, "Utilisation",    f"{alloc_pct}%",    RED if alloc_pct > 90 else GREEN),
    ]:
        with col:
            st.markdown(f"""
            <div class="card" style="text-align:center;border-top:3px solid {color}">
              <div style="font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;
                          letter-spacing:0.07em;margin-bottom:6px">{lbl}</div>
              <div style="font-size:28px;font-weight:800;color:{color}">{val}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown('<div class="section-hdr" style="margin-top:14px">Per-Person Capacity</div>', unsafe_allow_html=True)
    # Table header
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:44px 1fr 80px 80px 80px 80px 100px 60px;
                gap:8px;padding:5px 10px;font-size:10px;font-weight:700;color:#94a3b8;
                text-transform:uppercase;letter-spacing:0.07em;border-bottom:1px solid #e2e8f0">
      <div></div><div>Member</div><div>Capacity</div><div>Allocated</div>
      <div>Actual</div><div>Available</div><div>Utilisation</div><div>Tasks</div>
    </div>""", unsafe_allow_html=True)

    for _, r in cap_df.sort_values("Util_pct", ascending=False).iterrows():
        bc = "#059669" if r["Util_pct"] <= 80 else "#f59e0b" if r["Util_pct"] <= 100 else "#dc2626"
        over = " &#9888;" if r["Util_pct"] > 100 else ""
        st.markdown(
            f'<div style="display:grid;grid-template-columns:44px 1fr 80px 80px 80px 80px 100px 60px;'
            f'gap:8px;align-items:center;padding:8px 10px;border-bottom:1px solid #e2e8f0">'
            f'{avatar(r["Resource"], 32)}'
            f'<div style="font-size:13px;font-weight:600;color:#0f172a">{r["Resource"]}</div>'
            f'<div style="font-size:12px;color:#64748b">{int(r["Capacity"])}h</div>'
            f'<div style="font-size:12px;color:#64748b">{int(r["Allocated"])}h</div>'
            f'<div style="font-size:12px;color:#64748b">{int(r["Actual"])}h</div>'
            f'<div style="font-size:12px;font-weight:600;color:{GREEN}">{int(r["Available"])}h</div>'
            f'<div>{pbar(min(r["Util_pct"],100), bc, 8)}'
            f'<div style="font-size:10px;color:{bc};margin-top:2px">{r["Util_pct"]}%{over}</div></div>'
            f'<div style="font-size:12px;color:#64748b;text-align:center">'
            f'{int(r["Done"])}/{int(r["Tasks"])}</div>'
            f'</div>',
            unsafe_allow_html=True)

    # Allocation chart
    st.markdown('<div class="section-hdr" style="margin-top:14px">Capacity Allocation Chart</div>', unsafe_allow_html=True)
    fig_cap = go.Figure()
    fig_cap.add_trace(go.Bar(x=cap_df["Resource"], y=cap_df["Capacity"],
                             name="Capacity", marker_color="#e0e7ff",
                             text=cap_df["Capacity"], textposition="outside",
                             textfont={"size": 11, "color": TEXT_MID}))
    fig_cap.add_trace(go.Bar(x=cap_df["Resource"], y=cap_df["Allocated"],
                             name="Allocated", marker_color=BLUE,
                             text=cap_df["Allocated"], textposition="inside",
                             textfont={"size": 11, "color": "white"}))
    fig_cap.add_trace(go.Bar(x=cap_df["Resource"], y=cap_df["Actual"],
                             name="Actual", marker_color=GREEN,
                             text=cap_df["Actual"], textposition="inside",
                             textfont={"size": 11, "color": "white"}))
    fig_cap.update_layout(**_base_layout("Hours: Capacity vs Allocated vs Actual", 240),
                          barmode="group", bargap=0.25, bargroupgap=0.06,
                          xaxis={"tickfont": {"size": 12, "color": GREEN}},
                          yaxis={"gridcolor": GRID_COLOR, "tickfont": {"size": 11, "color": TEXT_MID}},
                          legend=dict(orientation="h", y=1.12, font={"size": 11}, bgcolor="rgba(0,0,0,0)"))
    st.plotly_chart(fig_cap, use_container_width=True, config={"displayModeBar": False})


# ─────────────────────────────────────────────────────────────────────────────
# TAB 7 — TIMELINE (Gantt)
# ─────────────────────────────────────────────────────────────────────────────
with tab7:
    st.markdown('<div class="section-hdr">Sprint Timeline</div>', unsafe_allow_html=True)
    st.markdown('<p class="sub">Each bar shows a task from Start date to Release date, coloured by status</p>', unsafe_allow_html=True)

    tdf = df.copy()
    tdf["Start date"]   = pd.to_datetime(tdf["Start date"],   errors="coerce")
    tdf["Release Date"] = pd.to_datetime(tdf["Release Date"], errors="coerce")
    tdf = tdf.dropna(subset=["Start date", "Release Date"])
    tdf = tdf.sort_values(["Start date","Priority"])
    tdf["Label"] = tdf["Jira ID"] + " · " + tdf["Summary"].str[:28]
    tdf["Detail"] = (tdf["Resource"] + " · " + tdf["Status"] +
                     " · " + tdf["Percentage Complete"].astype(int).astype(str) + "%")

    # Use px.timeline — designed specifically for Gantt charts
    fig_gantt = px.timeline(
        tdf,
        x_start="Start date",
        x_end="Release Date",
        y="Label",
        color="Status",
        color_discrete_map=STATUS_COLORS,
        hover_name="Jira ID",
        hover_data={"Label": False, "Start date": True, "Release Date": True,
                    "Resource": True, "Percentage Complete": True,
                    "Priority": True, "Status": True},
        text="Detail",
    )

    fig_gantt.update_traces(
        textposition="inside",
        textfont=dict(size=10, color="white"),
        marker_line=dict(color=CARD, width=1),
        insidetextanchor="middle",
    )

    # Today line — use add_shape (add_vline breaks with px.timeline date axis)
    today_str = str(today.date())
    fig_gantt.add_shape(
        type="line",
        x0=today_str, x1=today_str, y0=0, y1=1, yref="paper",
        line=dict(color=RED, width=2, dash="dash"),
    )
    fig_gantt.add_annotation(
        x=today_str, y=1.03, yref="paper",
        text="<b>Today</b>", showarrow=False,
        font=dict(color=RED, size=11, family="Inter, Arial"),
        xanchor="left",
    )

    fig_gantt.update_layout(
        height=max(320, len(tdf) * 30 + 80),
        margin=dict(l=6, r=16, t=40, b=8),
        paper_bgcolor=CARD, plot_bgcolor=CARD,
        font=CHART_FONT,
        xaxis=dict(
            title="", gridcolor=GRID_COLOR,
            tickfont={"size": 11, "color": TEXT_MID},
            tickformat="%d %b",
        ),
        yaxis=dict(
            gridcolor="rgba(0,0,0,0)",
            tickfont={"size": 11, "color": TEXT_DARK},
            autorange="reversed",
        ),
        legend=dict(
            orientation="h", y=1.06, x=0,
            font={"size": 11, "color": TEXT_MID},
            bgcolor="rgba(0,0,0,0)",
            title_text="",
        ),
        showlegend=True,
    )
    st.plotly_chart(fig_gantt, use_container_width=True, config={"displayModeBar": False})

    # Summary row below chart
    col_s = st.columns(len(STATUS_COLORS))
    for col, (status, color) in zip(col_s, STATUS_COLORS.items()):
        count = (tdf["Status"] == status).sum()
        with col:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:6px;padding:4px 8px;'
                f'background:#f8fafc;border-radius:6px;border:1px solid {BORDER}">'
                f'<div style="width:10px;height:10px;border-radius:3px;background:{color};flex-shrink:0"></div>'
                f'<span style="font-size:11px;font-weight:600;color:{TEXT_DARK}">{status}</span>'
                f'<span style="font-size:11px;color:#94a3b8;margin-left:auto">{count}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────────────────────────────────
# TAB 8 — BACKLOG
# ─────────────────────────────────────────────────────────────────────────────
with tab8:
    # Backlog = incomplete tasks from previous sprints (not current sprint)
    backlog = df_all[
        (df_all["Sprint"] != sprint_label) &
        (df_all["Percentage Complete"].astype(float) < 100) &
        (df_all["Status"].str.lower() != "done")
    ].copy()

    st.markdown(f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
      <div>
        <div style="font-size:16px;font-weight:700;color:{TEXT_DARK}">Backlog</div>
        <div style="font-size:12px;color:#64748b">Incomplete tasks from previous sprints</div>
      </div>
      <div style="background:#fee2e2;color:#991b1b;border-radius:20px;
                  padding:4px 14px;font-size:13px;font-weight:700">{len(backlog)} items</div>
    </div>""", unsafe_allow_html=True)

    if backlog.empty:
        st.success("No backlog items — all previous sprint tasks are completed!")
    else:
        # Group by sprint
        for sprint_name, grp in backlog.groupby("Sprint"):
            sp_label_short = sprint_name[:30] + "…" if len(sprint_name) > 30 else sprint_name
            st.markdown(f'<div class="section-hdr">{sp_label_short} — {len(grp)} items</div>',
                        unsafe_allow_html=True)
            for _, r in grp.sort_values("Priority").iterrows():
                pct = int(r["Percentage Complete"])
                fc  = PRIORITY_COLORS.get(r["Priority"], TEXT_LIGHT)
                bc  = pbar_color(pct)
                sp  = int(r.get("Story Points", 0))
                st.markdown(
                    f'<div class="row-item" style="border-left:4px solid {fc}">'
                    f'<div style="display:flex;align-items:center;justify-content:space-between">'
                    f'<div style="display:flex;align-items:center;gap:6px">'
                    f'<b style="color:{TEXT_DARK};font-size:13px">{r["Jira ID"]}</b>'
                    f'{badge(r["Priority"])} {badge(r["Status"])}'
                    f'</div>'
                    f'<div style="display:flex;align-items:center;gap:8px">'
                    f'{severity_badge(r["Priority"])}'
                    f'<span style="font-size:12px;font-weight:700;color:#94a3b8">{sp} SP</span>'
                    f'<span style="font-size:13px;font-weight:700;color:{bc}">{pct}%</span>'
                    f'</div></div>'
                    f'<div style="font-size:12px;color:{TEXT_MID};margin:3px 0">'
                    f'{str(r.get("Summary",""))[:65] or "—"}</div>'
                    f'<div style="display:flex;align-items:center;justify-content:space-between;margin-top:2px">'
                    f'<div style="font-size:10px;color:#64748b">&#128100; {r["Resource"]} &nbsp;&#128197; {r.get("Release Date","")}</div>'
                    f'{pbar(pct, bc, 4)}</div>'
                    f'</div>',
                    unsafe_allow_html=True)
