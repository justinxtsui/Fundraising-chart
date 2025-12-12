import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from matplotlib.lines import Line2D
from matplotlib.colors import to_rgb
from streamlit_sortables import sort_items

# --- CONFIGURATION ---
# Define required column names
DATE_COLUMN = 'Deal date' 
VALUE_COLUMN = 'Amount raised (converted to GBP)' 
# Alternative Column Names (Original Names for Backwards Compatibility)
ALT_DATE_COLUMN = 'Date the participant received the grant'
ALT_VALUE_COLUMN = 'Amount received (converted to GBP)'

# Refined color palette - sophisticated purples with better contrast
CATEGORY_COLORS = ['#4A3F8F', '#C8C3E0']  # Deep purple and soft lavender
PREDEFINED_COLORS = {
    'Deep Purple': '#4A3F8F',
    'Royal Purple': '#6B5FA0',
    'Soft Lavender': '#C8C3E0'
}
SINGLE_BAR_COLOR = '#9B94C7'
LINE_COLOR = '#1A1A1A'
TITLE_COLOR = '#1A1A1A'
APP_TITLE_COLOR = '#1A1A1A'
DEFAULT_TITLE = 'Grant Funding and Deal Count Over Time'

# Set page config and general styles
st.set_page_config(
    page_title="Time Series Chart Generator", 
    layout="wide", 
    initial_sidebar_state="expanded"
)
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Helvetica Neue', 'Arial', 'Public Sans', 'DejaVu Sans']

# Elegant, refined CSS with sophisticated aesthetics
st.markdown("""
    <style>
    /* Import beautiful fonts */
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700&family=Inter:wght@300;400;500;600&display=swap');
    
    /* Global typography and foundation */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, system-ui, sans-serif;
        font-weight: 400;
        letter-spacing: -0.01em;
    }
    
    /* Refined color palette */
    :root {
        --primary: #4A3F8F;
        --primary-light: #6B5FA0;
        --background: #FAFAFA;
        --surface: #FFFFFF;
        --text: #1A1A1A;
        --text-secondary: #666666;
        --border: #E8E8E8;
        --border-hover: #D0D0D0;
        --accent: #9B94C7;
    }
    
    /* Main content - elevated background */
    .main {
        background: linear-gradient(135deg, #FAFAFA 0%, #F5F5F5 100%);
        padding: 0;
    }
    
    /* Sidebar - clean and refined */
    [data-testid="stSidebar"] {
        background: var(--surface);
        border-right: 1px solid var(--border);
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.02);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        padding: 2rem 1.5rem;
    }
    
    /* Typography hierarchy */
    h1 {
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        letter-spacing: -0.03em !important;
        color: var(--text) !important;
        margin: 0 0 0.5rem 0 !important;
        line-height: 1.2 !important;
    }
    
    h2 {
        font-family: 'Syne', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.125rem !important;
        letter-spacing: -0.015em !important;
        color: var(--text) !important;
        margin: 2rem 0 1rem 0 !important;
        text-transform: uppercase;
        font-size: 0.75rem !important;
        letter-spacing: 0.08em !important;
        font-weight: 600 !important;
        opacity: 0.7;
    }
    
    h3 {
        font-family: 'Syne', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.25rem !important;
        letter-spacing: -0.02em !important;
        color: var(--text) !important;
        margin: 0 0 0.75rem 0 !important;
    }
    
    /* Refined paragraphs */
    p {
        color: var(--text-secondary);
        font-size: 0.9375rem;
        line-height: 1.6;
        margin: 0 0 1rem 0;
    }
    
    /* Elegant links */
    a {
        color: var(--primary) !important;
        text-decoration: none !important;
        font-weight: 500 !important;
        transition: all 0.2s ease;
        border-bottom: 1px solid transparent;
    }
    
    a:hover {
        color: var(--primary-light) !important;
        border-bottom-color: var(--primary-light);
    }
    
    /* Clean container spacing */
    .block-container {
        padding: 3rem 4rem !important;
        max-width: 1400px !important;
    }
    
    /* Refined form inputs */
    .stTextInput input, .stSelectbox select, .stMultiSelect {
        border: 1.5px solid var(--border) !important;
        border-radius: 8px !important;
        padding: 0.625rem 0.875rem !important;
        font-size: 0.9375rem !important;
        transition: all 0.2s ease !important;
        background: var(--surface) !important;
    }
    
    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(74, 63, 143, 0.08) !important;
        outline: none !important;
    }
    
    /* Elegant buttons */
    .stButton button {
        background: var(--primary) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 500 !important;
        font-size: 0.9375rem !important;
        letter-spacing: -0.01em !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 2px 8px rgba(74, 63, 143, 0.15) !important;
    }
    
    .stButton button:hover {
        background: var(--primary-light) !important;
        box-shadow: 0 4px 12px rgba(74, 63, 143, 0.25) !important;
        transform: translateY(-1px);
    }
    
    .stDownloadButton button {
        background: white !important;
        color: var(--primary) !important;
        border: 1.5px solid var(--border) !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06) !important;
    }
    
    .stDownloadButton button:hover {
        background: var(--background) !important;
        border-color: var(--primary) !important;
        color: var(--primary-light) !important;
    }
    
    /* Refined checkboxes */
    .stCheckbox {
        padding: 0.5rem 0;
    }
    
    .stCheckbox label {
        font-size: 0.9375rem !important;
        color: var(--text) !important;
        font-weight: 400 !important;
    }
    
    /* Beautiful dividers */
    hr {
        border: none !important;
        height: 1px !important;
        background: linear-gradient(90deg, transparent, var(--border), transparent) !important;
        margin: 2rem 0 !important;
        opacity: 0.6;
    }
    
    /* Refined expander */
    .streamlit-expanderHeader {
        background: var(--surface) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        padding: 0.875rem 1rem !important;
        transition: all 0.2s ease !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: var(--background) !important;
        border-color: var(--border-hover) !important;
    }
    
    /* Elegant code blocks */
    code {
        background: linear-gradient(135deg, #F8F8F8 0%, #F3F3F3 100%) !important;
        padding: 0.25rem 0.5rem !important;
        border-radius: 4px !important;
        font-size: 0.875rem !important;
        color: var(--primary) !important;
        border: 1px solid var(--border) !important;
        font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace !important;
    }
    
    /* Sortable items - modern drag interface */
    .sortable-item {
        background: var(--surface) !important;
        border: 2px dashed var(--border) !important;
        border-radius: 10px !important;
        padding: 1rem 1.25rem !important;
        margin: 0.75rem 0 !important;
        cursor: grab !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    }
    
    .sortable-item:hover {
        background: var(--background) !important;
        border: 2px solid var(--primary) !important;
        box-shadow: 0 4px 12px rgba(74, 63, 143, 0.12) !important;
        transform: translateY(-2px) !important;
    }
    
    .sortable-item:active {
        cursor: grabbing !important;
        transform: scale(0.98) !important;
    }
    
    .sortable-ghost {
        opacity: 0.3 !important;
        background: var(--background) !important;
    }
    
    /* Caption styling */
    .caption, [data-testid="stCaption"] {
        color: var(--text-secondary) !important;
        font-size: 0.8125rem !important;
        line-height: 1.5 !important;
        opacity: 0.8;
    }
    
    /* Error/Warning/Info boxes - refined */
    .stAlert {
        border-radius: 10px !important;
        border: none !important;
        padding: 1rem 1.25rem !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06) !important;
    }
    
    /* Radio buttons */
    .stRadio label {
        font-size: 0.9375rem !important;
        color: var(--text) !important;
    }
    
    /* Multi-select styling */
    .stMultiSelect [data-baseweb="tag"] {
        background: var(--primary) !important;
        color: white !important;
        border-radius: 6px !important;
        font-size: 0.875rem !important;
    }
    
    /* File uploader */
    [data-testid="stFileUploader"] {
        border: 2px dashed var(--border) !important;
        border-radius: 12px !important;
        padding: 2rem !important;
        background: var(--surface) !important;
        transition: all 0.2s ease !important;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: var(--primary) !important;
        background: var(--background) !important;
    }
    
    /* Smooth animations */
    * {
        transition: background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---

def format_currency(value):
    """
    Format a numeric value as money with £ and units (k, m, b),
    to 3 significant figures.
    """
    value = float(value)
    if value == 0:
        return "£0"
    neg = value < 0
    x_abs = abs(value)
    
    if x_abs >= 1e9:
        unit = "b"
        divisor = 1e9
    elif x_abs >= 1e6:
        unit = "m"
        divisor = 1e6
    elif x_abs >= 1e3:
        unit = "k"
        divisor = 1e3
    else:
        unit = ""
        divisor = 1.0

    scaled = x_abs / divisor
    s = f"{scaled:.3g}"
    
    try:
        if float(s).is_integer():
            s = str(int(float(s)))
    except:
        pass 

    sign = "-" if neg else ""
    return f"{sign}£{s}{unit}"

def is_dark_color(hex_color):
    """Check if a hex color is dark. Returns True if dark, False if light."""
    try:
        r, g, b = to_rgb(hex_color)
        luminance = (0.2126 * r + 0.7152 * g + 0.0722 * b)
        return luminance < 0.5
    except ValueError:
        return False

@st.cache_data
def load_data(uploaded_file):
    """Loads and preprocesses the uploaded file, handling dual column names."""
    if uploaded_file.name.endswith('.csv'):
        data = pd.read_csv(uploaded_file)
    else:
        data = pd.read_excel(uploaded_file, sheet_name=0)
        
    data.columns = data.columns.str.strip()
    original_value_column = None
    
    if DATE_COLUMN not in data.columns:
        if ALT_DATE_COLUMN in data.columns:
            data.rename(columns={ALT_DATE_COLUMN: DATE_COLUMN}, inplace=True)
        else:
            return None, f"File must contain a date column named **`{DATE_COLUMN}`** or **`{ALT_DATE_COLUMN}`**.", None

    if VALUE_COLUMN not in data.columns:
        if ALT_VALUE_COLUMN in data.columns:
            original_value_column = 'received'
            data.rename(columns={ALT_VALUE_COLUMN: VALUE_COLUMN}, inplace=True)
        else:
            return None, f"File must contain a value column named **`{VALUE_COLUMN}`** or **`{ALT_VALUE_COLUMN}`**.", None
    else:
        original_value_column = 'raised'

    try:
        data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN], errors='coerce')
        data.dropna(subset=[DATE_COLUMN], inplace=True)
    except Exception:
        return None, f"Could not convert **`{DATE_COLUMN}`** to datetime format.", None

    return data, None, original_value_column

@st.cache_data
def apply_filter(df, filter_config):
    """Applies dynamic filters to the DataFrame."""
    if not filter_config['enabled'] or filter_config['column'] == 'None':
        return df

    col = filter_config['column']
    values = filter_config['values']
    is_include = filter_config['include']

    if values:
        if is_include:
            return df[df[col].isin(values)]
        else:
            return df[~df[col].isin(values)]
    return df

@st.cache_data
def process_data(df, year_range, category_column):
    """Filters and aggregates the data for charting."""
    df = df.copy()
    start_year, end_year = year_range
    
    chart_data = df[df[DATE_COLUMN].dt.year.between(start_year, end_year, inclusive='both')].copy()
    
    if chart_data.empty:
        return None, "No data available for the selected year range."
    
    chart_data['time_period'] = chart_data[DATE_COLUMN].dt.year
    
    if category_column != 'None':
        grouped = chart_data.groupby(['time_period', category_column]).agg({
            VALUE_COLUMN: 'sum'
        }).reset_index()
        row_counts = chart_data.groupby('time_period').size().reset_index(name='row_count')
        pivot_data = grouped.pivot(index='time_period', columns=category_column, values=VALUE_COLUMN).fillna(0)
        final_data = pivot_data.reset_index().merge(row_counts, on='time_period')
    else:
        grouped = chart_data.groupby('time_period').agg({
            VALUE_COLUMN: 'sum'
        }).reset_index()
        row_counts = chart_data.groupby('time_period').size().reset_index(name='row_count')
        final_data = grouped.merge(row_counts, on='time_period')
    
    return final_data, None


def generate_chart(final_data, category_column, show_bars, show_line, chart_title, original_value_column='raised', category_colors=None, category_order=None):
    """Generates the dual-axis Matplotlib chart."""
    chart_fig, chart_ax1 = plt.subplots(figsize=(20, 10)) 
    
    bar_width = 0.8
    x_pos = np.arange(len(final_data))
    
    num_bars = len(final_data)
    min_size = 8
    max_size = 22
    
    if num_bars > 0:
        scale_factor = 150 / num_bars 
        DYNAMIC_FONT_SIZE = int(max(min_size, min(max_size, scale_factor)))
    else:
        DYNAMIC_FONT_SIZE = 12
    
    category_cols = []
    if category_column != 'None':
        category_cols = [col for col in final_data.columns if col not in ['time_period', 'row_count']]
        
        if category_order:
            category_order_list = [(cat, category_order.get(cat, 999)) for cat in category_cols]
            category_order_list.sort(key=lambda x: x[1])
            category_cols = [cat for cat, _ in category_order_list]

    if category_column == 'None':
        y_max = final_data[VALUE_COLUMN].max()
    else:
        y_max = final_data[category_cols].sum(axis=1).max()

    vertical_offset = y_max * 0.01 
    
    if category_column != 'None':
        bottom = np.zeros(len(final_data))
        for idx, cat in enumerate(category_cols):
            if category_colors and cat in category_colors:
                color = category_colors[cat]
            else:
                color = CATEGORY_COLORS[idx % len(CATEGORY_COLORS)]
            
            if show_bars:
                chart_ax1.bar(x_pos, final_data[cat], bar_width, bottom=bottom, 
                              label=cat, color=color, alpha=1.0)
            
            for i, x in enumerate(x_pos):
                val = final_data[cat].iloc[i]
                if val > 0 and show_bars:
                    label_text = format_currency(val)
                    current_color = color
                    text_color = '#FFFFFF' if is_dark_color(current_color) else '#000000'
                    
                    if idx == 0:
                        y_pos = vertical_offset
                        va = 'bottom'
                    else:
                        y_pos = bottom[i] + val / 2
                        va = 'center'
                        
                    chart_ax1.text(x, y_pos, label_text, ha='center', va=va,
                                     fontsize=DYNAMIC_FONT_SIZE, fontweight='bold', color=text_color)
            bottom += final_data[cat].values
    else:
        if show_bars:
            chart_ax1.bar(x_pos, final_data[VALUE_COLUMN], bar_width, 
                          label='Total amount received', color=SINGLE_BAR_COLOR, alpha=1.0) 
        
            for i, x in enumerate(x_pos):
                val = final_data[VALUE_COLUMN].iloc[i]
                if val > 0:
                    label_text = format_currency(val)
                    text_color = '#FFFFFF' if is_dark_color(SINGLE_BAR_COLOR) else '#000000'
                    y_pos = vertical_offset
                    va = 'bottom'
                        
                    chart_ax1.text(x, y_pos, label_text, ha='center', va=va,
                                     fontsize=DYNAMIC_FONT_SIZE, fontweight='bold', color=text_color)
    
    chart_ax1.set_xticks(x_pos)
    plt.setp(chart_ax1.get_xticklabels(), fontsize=DYNAMIC_FONT_SIZE, fontweight='normal')
    chart_ax1.set_xticklabels(final_data['time_period'])
    
    chart_ax1.set_ylim(0, y_max * 1.1)
    chart_ax1.tick_params(axis='y', left=False, labelleft=False, right=False, labelright=False, length=0)
    chart_ax1.tick_params(axis='x', bottom=False, length=0, pad=6)
    for spine in chart_ax1.spines.values():
        spine.set_visible(False)
    chart_ax1.grid(False)

    if show_line:
        chart_ax2 = chart_ax1.twinx()
        line_data = final_data['row_count'].values
        
        chart_ax2.plot(x_pos, line_data, color=LINE_COLOR, marker='o', linewidth=1.5, markersize=6, label='Number of deals') 
        
        max_count = line_data.max()
        chart_ax2.set_ylim(0, max_count * 1.5)
        
        chart_ax2.tick_params(axis='y', right=False, labelright=False, left=False, labelleft=False, length=0)
        for spine in chart_ax2.spines.values():
            spine.set_visible(False)
            
        y_range = chart_ax2.get_ylim()[1] - chart_ax2.get_ylim()[0]
        base_offset = y_range * 0.025 
        
        num_points = len(line_data)
        
        for i, y in enumerate(line_data):
            x = x_pos[i]
            place_above = True
            
            if num_points == 1:
                place_above = True
            elif i == 0:
                if line_data[i+1] > y:
                    place_above = True
                elif line_data[i+1] < y:
                    place_above = False
            elif i == num_points - 1:
                if line_data[i-1] < y:
                    place_above = True
                elif line_data[i-1] > y:
                    place_above = False
            else:
                y_prev = line_data[i-1]
                y_next = line_data[i+1]
                
                is_peak = (y > y_prev) and (y > y_next)
                is_valley = (y < y_prev) and (y < y_next)

                if is_peak:
                    place_above = True 
                elif is_valley:
                    place_above = False
                elif y > y_prev and y < y_next:
                    place_above = True
                elif y < y_prev and y > y_next:
                    place_above = False
                elif y_prev == y and y_next > y:
                    place_above = True
                elif y_prev == y and y_next < y:
                    place_above = False
                elif y_prev < y and y_next == y:
                    place_above = True
                elif y_prev > y and y_next == y:
                    place_above = False
                else:
                    place_above = True
                        
            if place_above:
                va = 'bottom'
                y_pos = y + base_offset
            else:
                va = 'top' 
                y_pos = y - base_offset
            
            chart_ax2.text(x, y_pos, str(int(y)), ha='center', va=va, 
                            fontsize=DYNAMIC_FONT_SIZE,
                            color=LINE_COLOR, fontweight='bold')
    
    legend_elements = []
    LEGEND_FONT_SIZE = 18
    LEGEND_MARKER_SIZE = 16
    
    if original_value_column == 'received':
        bar_legend_label = 'Total amount received'
    else:
        bar_legend_label = 'Amount raised'
    
    if show_bars:
        if category_column != 'None':
            for idx, cat in enumerate(category_cols):
                if category_colors and cat in category_colors:
                    color = category_colors[cat]
                else:
                    color = CATEGORY_COLORS[idx % len(CATEGORY_COLORS)]
                legend_elements.append(Line2D([0], [0], marker='o', color='w', 
                                              markerfacecolor=color, markersize=LEGEND_MARKER_SIZE, label=cat)) 
        else:
            legend_elements.append(Line2D([0], [0], marker='o', color='w', 
                                          markerfacecolor=SINGLE_BAR_COLOR, markersize=LEGEND_MARKER_SIZE, label=bar_legend_label)) 
            
    if show_line:
        legend_elements.append(Line2D([0], [0], marker='o', color='w', 
                                      markerfacecolor=LINE_COLOR, markersize=LEGEND_MARKER_SIZE, label='Number of deals')) 
        
    chart_ax1.legend(handles=legend_elements, loc='upper left', 
                     prop={'size': LEGEND_FONT_SIZE, 'weight': 'normal'}, 
                     frameon=False, labelspacing=1.0)
    
    plt.title(chart_title, fontsize=18, fontweight='bold', pad=20, color=TITLE_COLOR)
    plt.tight_layout()
    
    return chart_fig

# --- STREAMLIT APP LAYOUT ---

# 1. REFINED HEADER
st.markdown("""
    <div style="background: white; 
                padding: 2.5rem 0; 
                border-bottom: 2px solid #F0F0F0;
                margin-bottom: 2rem;
                background: linear-gradient(135deg, #FFFFFF 0%, #FAFAFA 100%);">
        <h1 style="margin: 0 0 0.75rem 0; background: linear-gradient(135deg, #4A3F8F 0%, #6B5FA0 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
                   background-clip: text;">
            Time Series Chart Generator
        </h1>
        <p style="color: #666; margin: 0 0 1.25rem 0; font-size: 1rem; line-height: 1.5; max-width: 600px;">
            Transform your fundraising or grant data into elegant, publication-ready time series visualizations.
        </p>
        <div style="display: inline-flex; align-items: center; gap: 0.5rem; 
                    background: linear-gradient(135deg, #F8F7FC 0%, #F3F2F8 100%); 
                    padding: 0.625rem 1rem; border-radius: 8px; border: 1px solid #E8E3F5;">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" style="opacity: 0.7;">
                <path d="M8 2L2 6L8 10L14 6L8 2Z" stroke="#4A3F8F" stroke-width="1.5" stroke-linejoin="round"/>
                <path d="M2 10L8 14L14 10" stroke="#4A3F8F" stroke-width="1.5" stroke-linejoin="round"/>
            </svg>
            <a href="https://platform.beauhurst.com/search/advancedsearch/?avs_json=eyJiYXNlIjoiY29tcGFueSIsImNvbWJpbmUiOiJhbmQiLCJjaGlsZHJlbiI6W119" 
               target="_blank" 
               style="font-size: 0.875rem; font-weight: 500; color: #4A3F8F;">
               Export from Beauhurst →
            </a>
        </div>
    </div>
""", unsafe_allow_html=True)

# Initialize session state
if 'year_range' not in st.session_state:
    st.session_state['year_range'] = (1900, 2100)
    st.session_state['category_column'] = 'None'
    st.session_state['show_bars'] = True
    st.session_state['show_line'] = True
    st.session_state['chart_title'] = DEFAULT_TITLE
    st.session_state['buf_png'] = BytesIO()
    st.session_state['buf_svg'] = BytesIO()
    st.session_state['filter_enabled'] = False
    st.session_state['filter_column'] = 'None'
    st.session_state['filter_include'] = True
    st.session_state['filter_values'] = []
    st.session_state['original_value_column'] = 'raised'
    st.session_state['stacked_enabled'] = False
    st.session_state['category_colors'] = {}
    st.session_state['category_order'] = {}

# --- ELEGANT SIDEBAR ---
with st.sidebar:
    st.markdown("## Data Source")
    uploaded_file = st.file_uploader(
        "Upload your data file", 
        type=['xlsx', 'xls', 'csv'],
        help="Excel or CSV file containing date and value columns"
    )
    st.markdown("---")

    df_base = None 
    
    if uploaded_file:
        df_base, error_msg, original_value_column = load_data(uploaded_file)
        if df_base is None:
            st.error(error_msg)
            st.stop()
        
        st.caption(f"✓ Loaded {df_base.shape[0]:,} records")
        st.session_state['original_value_column'] = original_value_column
        
    if df_base is not None:
        
        # --- CHART TITLE ---
        st.markdown("---")
        st.markdown("## Chart Title")
        
        custom_title = st.text_input(
            "Title", 
            value=st.session_state.get('chart_title', DEFAULT_TITLE),
            key='chart_title_input',
            label_visibility="collapsed",
            placeholder="Enter chart title..."
        )
        st.session_state['chart_title'] = custom_title
        
        # --- TIME RANGE ---
        st.markdown("---")
        st.markdown("## Time Range")
        
        min_year = int(df_base[DATE_COLUMN].dt.year.min())
        max_year = int(df_base[DATE_COLUMN].dt.year.max())
        all_years = list(range(min_year, max_year + 1))
        
        default_start = min_year
        default_end = max_year
        
        current_start, current_end = st.session_state.get('year_range', (default_start, default_end))
        
        col_start, col_end = st.columns(2)
        
        with col_start:
            start_year = st.selectbox(
                "From",
                options=all_years,
                index=all_years.index(current_start) if current_start in all_years else 0,
                key='start_year_selector'
            )
            
        with col_end:
            end_year = st.selectbox(
                "To",
                options=all_years,
                index=all_years.index(current_end) if current_end in all_years else len(all_years) - 1,
                key='end_year_selector'
            )
            
        if start_year > end_year:
            st.error("Start year must be before or equal to end year")
            st.stop()
            
        year_range = (start_year, end_year)
        
        # --- VISUAL ELEMENTS ---
        st.markdown("---")
        st.markdown("## Visual Elements")
        
        col_elem_1, col_elem_2 = st.columns(2)
        
        with col_elem_1:
            show_bars = st.checkbox(
                "Value bars", 
                value=st.session_state.get('show_bars', True), 
                key='show_bars_selector'
            )
        with col_elem_2:
            show_line = st.checkbox(
                "Count line", 
                value=st.session_state.get('show_line', True), 
                key='show_line_selector'
            )
        
        if not show_bars and not show_line:
            st.warning("Please select at least one element")
            st.stop()
        
        st.session_state['year_range'] = year_range
        st.session_state['show_bars'] = show_bars
        st.session_state['show_line'] = show_line
        
        # --- STACKED BARS ---
        st.markdown("---")
        st.markdown("## Stacked Bars")

        stacked_enabled = st.checkbox('Enable stacking', value=st.session_state.get('stacked_enabled', False))
        st.session_state['stacked_enabled'] = stacked_enabled

        if stacked_enabled:
            config_columns = [col for col in df_base.columns if col not in [DATE_COLUMN, VALUE_COLUMN]]
            category_columns = ['None'] + sorted(config_columns)
            
            category_column = st.selectbox(
                "Stack by", 
                category_columns,
                index=category_columns.index(st.session_state.get('category_column', 'None')),
                key='category_col_selector'
            )
            st.session_state['category_column'] = category_column
            
            if category_column != 'None':
                st.markdown("### Order & Colors")
                
                unique_categories = sorted(df_base[category_column].dropna().unique())
                
                if 'category_colors' not in st.session_state:
                    st.session_state['category_colors'] = {}
                if 'category_order' not in st.session_state:
                    st.session_state['category_order'] = {}
                
                if 'sorted_categories' not in st.session_state or set(st.session_state.get('sorted_categories', [])) != set(unique_categories):
                    st.session_state['sorted_categories'] = list(reversed(unique_categories))
                
                for idx, category in enumerate(st.session_state['sorted_categories']):
                    if category not in st.session_state['category_colors']:
                        default_color = CATEGORY_COLORS[idx % len(CATEGORY_COLORS)]
                        st.session_state['category_colors'][category] = default_color
                
                sorted_categories = sort_items(
                    st.session_state['sorted_categories'],
                    direction='vertical',
                    key='category_sorter'
                )
                
                st.session_state['sorted_categories'] = sorted_categories
                
                num_categories = len(sorted_categories)
                for idx, category in enumerate(sorted_categories):
                    st.session_state['category_order'][category] = num_categories - idx
                
                st.markdown("---")
                
                for idx, category in enumerate(sorted_categories):
                    current_color = st.session_state['category_colors'].get(category, CATEGORY_COLORS[idx % len(CATEGORY_COLORS)])
                    
                    col1, col2, col3 = st.columns([1, 1.5, 0.5])
                    
                    with col1:
                        st.markdown(f"<div style='padding-top: 8px; font-size: 0.9375rem; font-weight: 500;'>{category}</div>", unsafe_allow_html=True)
                    
                    with col2:
                        color_options = list(PREDEFINED_COLORS.values())
                        
                        selected_hex = st.selectbox(
                            f"Color for {category}",
                            options=color_options,
                            index=color_options.index(current_color) if current_color in color_options else 0,
                            key=f'color_select_{category}',
                            label_visibility='collapsed'
                        )
                        
                        st.session_state['category_colors'][category] = selected_hex
                    
                    with col3:
                        st.markdown(
                            f'<div style="background-color: {selected_hex}; height: 40px; width: 100%; '
                            f'border-radius: 6px; border: 1.5px solid #E8E8E8; box-shadow: 0 2px 4px rgba(0,0,0,0.04);"></div>',
                            unsafe_allow_html=True
                        )
        else:
            st.session_state['category_column'] = 'None'
            st.session_state['category_colors'] = {}
            st.session_state['category_order'] = {}
            if 'sorted_categories' in st.session_state:
                del st.session_state['sorted_categories']

        # --- DATA FILTER ---
        st.markdown("---")
        st.markdown("## Data Filter")

        filter_enabled = st.checkbox('Enable filtering', value=st.session_state['filter_enabled'])
        st.session_state['filter_enabled'] = filter_enabled

        if filter_enabled:
            
            filter_columns = [c for c in df_base.columns if df_base[c].dtype in ['object', 'category'] and c not in [DATE_COLUMN]]
            filter_columns = ['None'] + sorted(filter_columns)
            
            filter_column = st.selectbox(
                "Filter column",
                filter_columns,
                index=filter_columns.index(st.session_state['filter_column']) if st.session_state['filter_column'] in filter_columns else 0,
                key='filter_col_selector'
            )
            st.session_state['filter_column'] = filter_column

            if filter_column != 'None':
                
                unique_values = df_base[filter_column].astype(str).unique().tolist()
                
                filter_mode = st.radio(
                    "Mode",
                    options=["Include", "Exclude"],
                    index=0 if st.session_state['filter_include'] else 1,
                    key='filter_mode_radio',
                    horizontal=True
                )
                
                st.session_state['filter_include'] = (filter_mode == "Include")
                
                default_selection = st.session_state['filter_values'] if st.session_state['filter_values'] else unique_values
                
                selected_values = st.multiselect(
                    f"Values",
                    options=unique_values,
                    default=[v for v in default_selection if v in unique_values],
                    key='filter_values_selector'
                )
                st.session_state['filter_values'] = selected_values
            else:
                 st.session_state['filter_values'] = []

        # --- DOWNLOAD ---
        st.markdown("---")
        st.markdown("## Export")
        
        with st.expander("📥 Download Files", expanded=False):
            st.download_button(
                label="PNG (High Resolution)",
                data=st.session_state.get('buf_png', BytesIO()),
                file_name=f"{custom_title.replace(' ', '_').lower()}_chart.png",
                mime="image/png",
                key="download_png",
                use_container_width=True
            )
            st.download_button(
                label="SVG (Vector)",
                data=st.session_state.get('buf_svg', BytesIO()),
                file_name=f"{custom_title.replace(' ', '_').lower()}_chart.svg",
                mime="image/svg+xml",
                key="download_svg",
                use_container_width=True
            )

# --- MAIN AREA ---

if 'df_base' in locals() and df_base is not None:
    
    filter_config = {
        'enabled': st.session_state['filter_enabled'],
        'column': st.session_state['filter_column'],
        'include': st.session_state['filter_include'],
        'values': st.session_state['filter_values']
    }
    
    df_filtered = apply_filter(df_base, filter_config)
    
    if df_filtered.empty:
        st.error("No data matches your filter criteria. Please adjust your settings.")
        st.stop()
        
    final_data, process_error = process_data(df_filtered, st.session_state['year_range'], st.session_state['category_column'])
    
    if final_data is None:
        st.error(process_error)
        st.stop()
    
    chart_fig = generate_chart(final_data, st.session_state['category_column'], 
                               st.session_state['show_bars'], st.session_state['show_line'], 
                               st.session_state['chart_title'], 
                               st.session_state.get('original_value_column', 'raised'),
                               st.session_state.get('category_colors', {}),
                               st.session_state.get('category_order', {}))

    col_left, col_chart, col_right = st.columns([0.05, 7, 0.05])
    
    with col_chart:
        st.pyplot(chart_fig, use_container_width=True) 
    
    buf_png = BytesIO()
    chart_fig.savefig(buf_png, format='png', dpi=300, bbox_inches='tight')
    buf_png.seek(0)
    st.session_state['buf_png'] = buf_png

    buf_svg = BytesIO()
    chart_fig.savefig(buf_svg, format='svg', bbox_inches='tight')
    buf_svg.seek(0)
    st.session_state['buf_svg'] = buf_svg

else:
    # Elegant empty state
    st.markdown("""
        <div style="max-width: 720px; margin: 3rem auto; text-align: center;">
            <div style="background: linear-gradient(135deg, #FFFFFF 0%, #FAFAFA 100%); 
                        padding: 3rem; 
                        border-radius: 16px;
                        border: 2px solid #F0F0F0;
                        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);">
                <div style="width: 80px; height: 80px; margin: 0 auto 1.5rem; 
                            background: linear-gradient(135deg, #F8F7FC 0%, #F3F2F8 100%); 
                            border-radius: 50%; display: flex; align-items: center; justify-content: center;
                            border: 2px solid #E8E3F5;">
                    <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
                        <path d="M8 32L8 20M16 32V12M24 32V16M32 32V8" 
                              stroke="#4A3F8F" stroke-width="3" stroke-linecap="round"/>
                        <circle cx="8" cy="20" r="3" fill="#6B5FA0"/>
                        <circle cx="16" cy="12" r="3" fill="#6B5FA0"/>
                        <circle cx="24" cy="16" r="3" fill="#6B5FA0"/>
                        <circle cx="32" cy="8" r="3" fill="#6B5FA0"/>
                    </svg>
                </div>
                <h3 style="color: #1A1A1A; margin: 0 0 0.75rem 0; font-size: 1.5rem; font-weight: 600;">
                    Ready to Create Your Chart
                </h3>
                <p style="color: #666; margin: 0 0 2rem 0; font-size: 1rem; line-height: 1.6;">
                    Upload your data file in the sidebar to begin. Your chart will appear here instantly.
                </p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Instructions card
    st.markdown("""
        <div style="max-width: 720px; margin: 2rem auto;">
            <div style="background: white; 
                        padding: 2rem; 
                        border-radius: 12px;
                        border: 1.5px solid #E8E8E8;
                        box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);">
                <h3 style="color: #1A1A1A; margin: 0 0 1rem 0; font-size: 1.125rem; font-weight: 600;">
                    Data Requirements
                </h3>
                <p style="color: #666; font-size: 0.9375rem; line-height: 1.6; margin: 0 0 1rem 0;">
                    Your file must contain a date column and a value column with one of these names:
                </p>
                <div style="background: linear-gradient(135deg, #F8F8F8 0%, #F5F5F5 100%); 
                            padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; 
                            border: 1px solid #E8E8E8;">
                    <div style="margin-bottom: 0.75rem;">
                        <strong style="color: #4A3F8F; font-size: 0.875rem;">Date Column:</strong><br>
                        <code style="margin-top: 0.25rem; display: inline-block;">Deal date</code> or 
                        <code>Date the participant received the grant</code>
                    </div>
                    <div>
                        <strong style="color: #4A3F8F; font-size: 0.875rem;">Value Column:</strong><br>
                        <code style="margin-top: 0.25rem; display: inline-block;">Amount raised (converted to GBP)</code> or 
                        <code>Amount received (converted to GBP)</code>
                    </div>
                </div>
                
                <h3 style="color: #1A1A1A; margin: 0 0 1rem 0; font-size: 1.125rem; font-weight: 600;">
                    Quick Start Guide
                </h3>
                <div style="color: #666; font-size: 0.9375rem; line-height: 1.7;">
                    <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                        <div style="color: #4A3F8F; font-weight: 600; min-width: 24px;">1.</div>
                        <div><strong>Upload</strong> your Excel or CSV file using the sidebar</div>
                    </div>
                    <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                        <div style="color: #4A3F8F; font-weight: 600; min-width: 24px;">2.</div>
                        <div><strong>Configure</strong> your chart using the sidebar controls</div>
                    </div>
                    <div style="display: flex; gap: 1rem;">
                        <div style="color: #4A3F8F; font-weight: 600; min-width: 24px;">3.</div>
                        <div><strong>Export</strong> as high-resolution PNG or vector SVG</div>
                    </div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
