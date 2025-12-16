import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from matplotlib.lines import Line2D
from matplotlib.colors import to_rgb
from matplotlib.patches import Patch
from streamlit_sortables import sort_items

# --- CONFIGURATION ---
# Define required column names
DATE_COLUMN = 'Deal date'
VALUE_COLUMN = 'Amount raised (converted to GBP)'
# Alternative Column Names (Original Names for Backwards Compatibility)
ALT_DATE_COLUMN = 'Date the participant received the grant'
ALT_VALUE_COLUMN = 'Amount received (converted to GBP)'
# Define the color palette for categories
# FIX: The non-printable character (U+00A0) has been replaced with a standard space.
CATEGORY_COLORS = ['#302A7E', '#D0CCE5'] # Dark Purple and Light Lavender only

# Predefined color palette for user selection (3 purple/lavender shades)
PREDEFINED_COLORS = {
    'Dark Purple': '#302A7E',
    'Medium Purple': '#8884B3',
    'Light Lavender': '#D0CCE5'
}
# Define the default single bar color (third color in the palette for a lighter tone)
SINGLE_BAR_COLOR = '#BBBAF6'
# Define the line chart color
LINE_COLOR = '#000000' # Black for high contrast
# Define the chart title color
TITLE_COLOR = '#000000' # Matplotlib Chart Title Color is Black
# Define the Application Title Color (Black)
APP_TITLE_COLOR = '#000000'
# Default Title
DEFAULT_TITLE = 'Grant Funding and Deal Count Over Time'

# Set page config and general styles
st.set_page_config(page_title="Time Series Chart Generator", layout="wide", initial_sidebar_state="expanded")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'Public Sans', 'DejaVu Sans']

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
        # Calculate luminance
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
        # Load the first sheet
        data = pd.read_excel(uploaded_file, sheet_name=0)
        
    # 1. Clean column names by stripping whitespace
    data.columns = data.columns.str.strip()
    
    # Track original value column name for legend
    original_value_column = None
    
    # 2. Check and rename date column
    if DATE_COLUMN not in data.columns:
        if ALT_DATE_COLUMN in data.columns:
            data.rename(columns={ALT_DATE_COLUMN: DATE_COLUMN}, inplace=True)
        else:
            return None, f"File must contain a date column named **`{DATE_COLUMN}`** or **`{ALT_DATE_COLUMN}`**.", None

    # 3. Check and rename value column
    if VALUE_COLUMN not in data.columns:
        if ALT_VALUE_COLUMN in data.columns:
            original_value_column = 'received'  # Track that it was "received"
            data.rename(columns={ALT_VALUE_COLUMN: VALUE_COLUMN}, inplace=True)
        else:
            return None, f"File must contain a value column named **`{VALUE_COLUMN}`** or **`{ALT_VALUE_COLUMN}`**.", None
    else:
        original_value_column = 'raised'  # Track that it was "raised"

    try:
        data[DATE_COLUMN] = pd.to_datetime(data[DATE_COLUMN], format='%d/%m/%Y', errors='coerce')
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


def generate_chart(final_data, category_column, show_bars, show_line, chart_title, original_value_column='raised', category_colors=None, category_order=None, prediction_start_year=None):
    """Generates the dual-axis Matplotlib chart with prediction styling."""
    # Matplotlib Figure Size (Increased for resolution)
    chart_fig, chart_ax1 = plt.subplots(figsize=(20, 10)) 
    
    bar_width = 0.8
    x_pos = np.arange(len(final_data))
    years = final_data['time_period'].values
    
    # Determine which bars/points are for predicted data
    is_predicted = (years >= prediction_start_year) if prediction_start_year is not None else np.full(len(years), False)
    
    # --- DYNAMIC FONT SIZE CALCULATION ---
    
    num_bars = len(final_data)
    min_size = 8    # Minimum acceptable font size
    max_size = 22   # Maximum acceptable font size
    
    if num_bars > 0:
        # Scaling numerator INCREASED to 150 for greater sensitivity.
        scale_factor = 150 / num_bars 
        
        # Apply both minimum and maximum caps
        DYNAMIC_FONT_SIZE = int(max(min_size, min(max_size, scale_factor)))
    else:
        DYNAMIC_FONT_SIZE = 12
    # -------------------------------------------------------------
    
    category_cols = []
    if category_column != 'None':
        category_cols = [col for col in final_data.columns if col not in ['time_period', 'row_count']]
        
        # Sort categories by user-defined order if provided
        if category_order:
            category_order_list = [(cat, category_order.get(cat, 999)) for cat in category_cols]
            category_order_list.sort(key=lambda x: x[1])
            category_cols = [cat for cat, _ in category_order_list]

    if category_column == 'None':
        y_max = final_data[VALUE_COLUMN].max()
    else:
        y_max = final_data[category_cols].sum(axis=1).max()

    # Use vertical_offset for placement near the base of the bar
    vertical_offset = y_max * 0.01 
    
    # --- AXIS 1 (Bar Chart - Value) ---
    if category_column != 'None':
        bottom = np.zeros(len(final_data))
        for idx, cat in enumerate(category_cols):
            # Use custom color if available, otherwise use default palette
            if category_colors and cat in category_colors:
                color = category_colors[cat]
            else:
                color = CATEGORY_COLORS[idx % len(CATEGORY_COLORS)]
            
            for i in range(len(final_data)):
                x = x_pos[i]
                val = final_data[cat].iloc[i]
                
                if show_bars and val > 0:
                    # Bar shading logic: Use solid color for non-predicted, shaded for predicted
                    bar_color = color
                    hatch_style = '///' if is_predicted[i] else None # Hatching for prediction
                    alpha_val = 0.5 if is_predicted[i] else 1.0    # Optional: Reduce opacity
                    
                    # Plot the bar
                    # Only use label in legend for the first category instance (i==0)
                    chart_ax1.bar(x, val, bar_width, bottom=bottom[i], 
                                  label=cat if i == 0 else None, color=bar_color, alpha=alpha_val, hatch=hatch_style)
                    
                    # Data label logic
                    label_text = format_currency(val)
                    text_color = '#FFFFFF' if is_dark_color(bar_color) else '#000000'
                    # Vertical positioning logic (near the base / center):
                    if idx == 0:
                        y_pos = bottom[i] + vertical_offset
                        va = 'bottom'
                    else:
                        y_pos = bottom[i] + val / 2
                        va = 'center'
                        
                    chart_ax1.text(x, y_pos, label_text, ha='center', va=va,
                                     fontsize=DYNAMIC_FONT_SIZE, fontweight='bold', color=text_color)

                # Update bottom for stacking
                bottom[i] += final_data[cat].iloc[i]

    else:
        # Non-stacked bar chart
        if show_bars:
            for i in range(len(final_data)):
                x = x_pos[i]
                val = final_data[VALUE_COLUMN].iloc[i]
                bar_color = SINGLE_BAR_COLOR
                hatch_style = '///' if is_predicted[i] else None
                alpha_val = 1.0 # Keep alpha 1.0 for non-stacked bars (hatch visibility is better)
                
                # Only use label in legend for the first category instance (i==0)
                chart_ax1.bar(x, val, bar_width, 
                              label='Total amount received' if i == 0 else None,
                              color=bar_color, alpha=alpha_val, hatch=hatch_style) 
        
                if val > 0:
                    label_text = format_currency(val)
                    text_color = '#FFFFFF' if is_dark_color(SINGLE_BAR_COLOR) else '#000000'

                    # Vertical positioning logic (near the base):
                    y_pos = vertical_offset
                    va = 'bottom'
                        
                    chart_ax1.text(x, y_pos, label_text, ha='center', va=va,
                                     fontsize=DYNAMIC_FONT_SIZE, fontweight='bold', color=text_color)
    
    chart_ax1.set_xticks(x_pos)
    plt.setp(chart_ax1.get_xticklabels(), fontsize=DYNAMIC_FONT_SIZE, fontweight='normal') # Use DYNAMIC_FONT_SIZE for x-ticks
    chart_ax1.set_xticklabels(final_data['time_period'])
    
    chart_ax1.set_ylim(0, y_max * 1.1)
    chart_ax1.tick_params(axis='y', left=False, labelleft=False, right=False, labelright=False, length=0)
    chart_ax1.tick_params(axis='x', bottom=False, length=0, pad=6)
    for spine in chart_ax1.spines.values():
        spine.set_visible(False)
    chart_ax1.grid(False)

    # --- AXIS 2 (Line Chart - Count) ---
    if show_line:
        chart_ax2 = chart_ax1.twinx()
        line_data = final_data['row_count'].values
        
        # Split data into actual and predicted sections for separate plotting styles
        actual_x = x_pos[~is_predicted]
        actual_y = line_data[~is_predicted]
        predicted_x = x_pos[is_predicted]
        predicted_y = line_data[is_predicted]
        
        # 1. Plot Actual (Solid Line)
        if len(actual_x) > 0:
            # Draw solid line between actual points
            chart_ax2.plot(actual_x, actual_y, color=LINE_COLOR, marker='o', linestyle='-', linewidth=1.5, markersize=6, label='Number of deals (Actual)')

        # 2. Plot Predicted (Dotted Line)
        if len(predicted_x) > 0:
            # Find the connection point (last actual data point)
            if len(actual_x) > 0 and predicted_x[0] == actual_x[-1] + 1:
                # Include the last actual point to ensure connection
                connection_x = np.concatenate(([actual_x[-1]], predicted_x))
                connection_y = np.concatenate(([actual_y[-1]], predicted_y))
            else:
                connection_x = predicted_x
                connection_y = predicted_y

            chart_ax2.plot(connection_x, connection_y, color=LINE_COLOR, marker='o', linestyle='--', linewidth=1.5, markersize=6, label='Number of deals (Predicted)')
        
        # Fallback for non-predicted line if prediction mode is off
        if prediction_start_year is None and len(final_data) > 0:
            chart_ax2.plot(x_pos, line_data, color=LINE_COLOR, marker='o', linestyle='-', linewidth=1.5, markersize=6, label='Number of deals')
        
        # Calculate max_count after plotting to get accurate current limits
        max_count = line_data.max()
        chart_ax2.set_ylim(0, max_count * 1.5)
        
        chart_ax2.tick_params(axis='y', right=False, labelright=False, left=False, labelleft=False, length=0)
        for spine in chart_ax2.spines.values():
            spine.set_visible(False)
            
        y_range = chart_ax2.get_ylim()[1] - chart_ax2.get_ylim()[0]
        base_offset = y_range * 0.025 
        
        # --- LINE DATA LABEL PLACEMENT LOGIC ---
        num_points = len(line_data)
        
        for i, y in enumerate(line_data):
            x = x_pos[i]
            # Placement logic remains the same (checking peaks/valleys)
            place_above = True
            if num_points > 1:
                if i == 0:
                    place_above = line_data[i+1] >= y
                elif i == num_points - 1:
                    place_above = line_data[i-1] <= y
                else:
                    is_peak = (y >= line_data[i-1]) and (y >= line_data[i+1])
                    is_valley = (y < line_data[i-1]) and (y < line_data[i+1])
                    place_above = is_peak or (y > line_data[i-1] and y < line_data[i+1])
                    if is_valley:
                        place_above = False

            # Determine final vertical alignment and position
            va = 'bottom' if place_above else 'top'
            y_pos = y + base_offset if place_above else y - base_offset
            
            chart_ax2.text(x, y_pos, str(int(y)), ha='center', va=va, 
                            fontsize=DYNAMIC_FONT_SIZE, # <-- APPLY DYNAMIC FONT SIZE
                            color=LINE_COLOR, fontweight='bold')
    
    # --- LEGEND & TITLE ---
    legend_elements = []
    
    # Define large font size for legend
    LEGEND_FONT_SIZE = 18  # Legend font size
    # Keep marker size fixed at 16 points
    LEGEND_MARKER_SIZE = 16
    
    # Set legend label based on original column type
    if original_value_column == 'received':
        bar_legend_label = 'Total amount received'
    else:  # 'raised'
        bar_legend_label = 'Amount raised'
    
    if show_bars:
        if category_column != 'None':
            for idx, cat in enumerate(category_cols):
                if category_colors and cat in category_colors:
                    color = category_colors[cat]
                else:
                    color = CATEGORY_COLORS[idx % len(CATEGORY_COLORS)]
                # Use square marker for bar categories
                legend_elements.append(Line2D([0], [0], marker='s', linestyle='', 
                                              markerfacecolor=color, markersize=LEGEND_MARKER_SIZE * 0.7, label=cat))
        else:
            # Single bar category
            legend_elements.append(Line2D([0], [0], marker='s', linestyle='', 
                                          markerfacecolor=SINGLE_BAR_COLOR, markersize=LEGEND_MARKER_SIZE * 0.7, label=bar_legend_label)) 
            
    # Add a special entry for predicted bars if applicable
    if show_bars and prediction_start_year is not None and prediction_start_year <= years.max():
        # Create a proxy element for the hatched bar using the first category color or single bar color
        default_color = CATEGORY_COLORS[0] if category_column != 'None' else SINGLE_BAR_COLOR
        proxy = Patch(facecolor=default_color, edgecolor='k', hatch='///', alpha=0.5, label=f'{bar_legend_label} (Predicted)')
        legend_elements.append(proxy)
    
    if show_line:
        # Add two entries for the line to show solid/dotted distinction
        legend_elements.append(Line2D([0], [0], color=LINE_COLOR, marker='o', linestyle='-', linewidth=1.5, markersize=6, label='Number of deals (Actual)'))
        if prediction_start_year is not None and prediction_start_year <= years.max():
            legend_elements.append(Line2D([0], [0], color=LINE_COLOR, marker='o', linestyle='--', linewidth=1.5, markersize=6, label='Number of deals (Predicted)'))

    # Remove duplicates in the legend (e.g. if default line and actual line are the same)
    final_legend_elements = []
    seen_labels = set()
    for element in legend_elements:
        label = element.get_label()
        if label not in seen_labels and label != '_nolegend_':
            final_legend_elements.append(element)
            seen_labels.add(label)

    # Legend with increased font size and proportional markers
    chart_ax1.legend(handles=final_legend_elements, loc='upper left', 
                     prop={'size': LEGEND_FONT_SIZE, 'weight': 'normal'}, 
                     frameon=False, labelspacing=1.0, ncol=2)
    
    # Matplotlib Chart Title: Color is TITLE_COLOR (Black)
    plt.title(chart_title, fontsize=18, fontweight='bold', pad=20, color=TITLE_COLOR)
    plt.tight_layout()
    
    return chart_fig

# --- STREAMLIT APP LAYOUT ---

# 1. MAIN APPLICATION TITLE
st.markdown(f'<h1 style="color:{APP_TITLE_COLOR};">Time Series Chart Generator</h1>', unsafe_allow_html=True)

# Styled description box
st.markdown("""
    <div style="background: #f5f7fa; 
                padding: 20px; 
                border-radius: 10px; 
                border-left: 5px solid #302A7E; 
                margin: 15px 0;">
        <p style="margin: 0 0 10px 0; font-size: 16px; color: #333;">
            <strong>Turn any fundraising or grant export into a time series chart – JT</strong>
        </p>
        <a href="https://platform.beauhurst.com/search/advancedsearch/?avs_json=eyJiYXNlIjoiY29tcGFueSIsImNvbWJpbmUiOiJhbmQiLCJjaGlsZHJlbiI6W119" 
           target="_blank" 
           style="display: inline-block; background: #fff; padding: 10px 16px; border-radius: 6px; 
                  border: 1px solid #ddd; color: #302A7E; font-weight: 600; text-decoration: none; 
                  font-size: 14px; transition: all 0.2s ease;">
           🔗 Beauhurst Advanced Search
        </a>
    </div>
""", unsafe_allow_html=True)

st.markdown("---")

# Initialize buffers and session state
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
    st.session_state['original_value_column'] = 'raised'  # Default
    st.session_state['stacked_enabled'] = False  # Default
    st.session_state['category_colors'] = {}  # Default
    st.session_state['category_order'] = {}  # Default
    st.session_state['prediction_start_year'] = None # New default

# --- SIDEBAR (All Controls) ---
with st.sidebar:
    st.header("1. Data Source")
    uploaded_file = st.file_uploader("Upload your Excel or CSV file", type=['xlsx', 'xls', 'csv'], 
                                     help="The file must contain a date column and a value column.")

    # Initialize df_base to None
    df_base = None 
    
    if uploaded_file:
        df_base, error_msg, original_value_column = load_data(uploaded_file)
        if df_base is None:
            st.error(error_msg)
            st.stop()
        
        st.caption(f"Loaded **{df_base.shape[0]}** rows for processing.")
        # Store original_value_column in session state
        st.session_state['original_value_column'] = original_value_column
        
    if df_base is not None:
        
        # --- 2. CHART TITLE ---
        st.markdown("---")
        st.header("2. Chart Title")
        
        custom_title = st.text_input(
            "Chart Title", 
            value=st.session_state.get('chart_title', DEFAULT_TITLE),
            key='chart_title_input',
            help="Customize the title shown above the chart."
        )
        st.session_state['chart_title'] = custom_title
        
        # --- 3. TIME FILTERS ---
        st.markdown("---")
        st.header("3. Time Filters")
        
        # FIX: Using df_base inside the conditional block
        min_year = int(df_base[DATE_COLUMN].dt.year.min())
        max_year = int(df_base[DATE_COLUMN].dt.year.max())
        all_years = list(range(min_year, max_year + 1))
        
        default_start = min_year
        default_end = max_year
        
        current_start, current_end = st.session_state.get('year_range', (default_start, default_end))
        
        col_start, col_end = st.columns(2)
        
        with col_start:
            start_year = st.selectbox(
                "Start Year",
                options=all_years,
                index=all_years.index(current_start) if current_start in all_years else 0,
                key='start_year_selector',
                help="First year of data to include."
            )
            
        with col_end:
            end_year = st.selectbox(
                "End Year",
                options=all_years,
                index=all_years.index(current_end) if current_end in all_years else len(all_years) - 1,
                key='end_year_selector',
                help="Last year of data to include."
            )
            
        if start_year > end_year:
            st.error("Start Year must be <= End Year.")
            st.stop()
            
        year_range = (start_year, end_year)
        
        # --- 4. VISUAL ELEMENTS ---
        st.markdown("---")
        st.header("4. Visual Elements")
        
        col_elem_1, col_elem_2 = st.columns(2)
        
        with col_elem_1:
            show_bars = st.checkbox(
                "Show bar for deal value", 
                value=st.session_state.get('show_bars', True), 
                key='show_bars_selector'
            )
        with col_elem_2:
            show_line = st.checkbox(
                "Show line for number of deals", 
                value=st.session_state.get('show_line', True), 
                key='show_line_selector'
            )
        
        if not show_bars and not show_line:
            st.warning("Select at least one element.")
            st.stop()
        
        # Update session state
        st.session_state['year_range'] = year_range
        st.session_state['show_bars'] = show_bars
        st.session_state['show_line'] = show_line
        
        # --- PREDICTION TOGGLE AND YEAR SELECT ---
        st.subheader("Prediction Visuals (Dotted Line / Hatched Bar)")
        enable_prediction = st.checkbox("Enable prediction mode", key='enable_prediction_checkbox')
        
        prediction_start_year = None
        
        # Check if the currently filtered time range has any years
        filtered_years = list(range(start_year, end_year + 1))
        
        if enable_prediction and filtered_years:
            # Only allow selection of years that are visible in the chart
            prediction_options = ['None'] + filtered_years
            
            # Find the index of the current or last year
            default_year_to_select = st.session_state['prediction_start_year']
            if default_year_to_select not in prediction_options:
                # If the previous selection is outside the new range, default to the last year of the range
                default_year_to_select = filtered_years[-1] if filtered_years else 'None'
            
            default_index = prediction_options.index(default_year_to_select) if default_year_to_select != 'None' else 0
            
            selected_prediction_year = st.selectbox(
                "Start Year for Prediction/Shading",
                options=prediction_options,
                index=default_index,
                key='prediction_year_selector',
                help="Data from this year (inclusive) will be rendered as predicted (dotted line/hatched bars)."
            )
            
            if selected_prediction_year != 'None':
                prediction_start_year = int(selected_prediction_year)
                # Ensure the prediction year is within the selected filter range
                if prediction_start_year < start_year or prediction_start_year > end_year:
                    st.warning(f"Prediction start year {prediction_start_year} is outside the time filter range ({start_year}-{end_year}). Prediction styling will not be shown.")
                    prediction_start_year = None
            
        st.session_state['prediction_start_year'] = prediction_start_year
        
        # --- 5. STACKED BAR (OPTIONAL) ---
        st.markdown("---")
        st.header("5. Stacked bar? (Optional)")

        stacked_enabled = st.checkbox('Enable Stacked Bar', value=st.session_state.get('stacked_enabled', False))
        st.session_state['stacked_enabled'] = stacked_enabled

        if stacked_enabled:
            config_columns = [col for col in df_base.columns if col not in [DATE_COLUMN, VALUE_COLUMN]]
            category_columns = ['None'] + sorted(config_columns)
            
            category_column = st.selectbox(
                "Select Column for Stacking", 
                category_columns,
                index=category_columns.index(st.session_state.get('category
