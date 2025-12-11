import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
from matplotlib.lines import Line2D

# Set page config
st.set_page_config(page_title="Chart Generator", layout="wide")

# Title
st.title("Interactive Chart Generator")

# File upload
uploaded_file = st.file_uploader("Upload your Excel or CSV file", type=['xlsx', 'xls', 'csv'])

if uploaded_file is not None:
    # Load the data
    if uploaded_file.name.endswith('.csv'):
        data = pd.read_csv(uploaded_file)
    else:
        data = pd.read_excel(uploaded_file)
    
    # Fixed column names
    date_column = 'Date the participant received the grant'
    value_column = 'Amount received (converted to GBP)'
    
    # Check if required columns exist
    if date_column not in data.columns or value_column not in data.columns:
        st.error(f"File must contain columns: '{date_column}' and '{value_column}'")
        st.stop()
        
    # Ensure date column is datetime for filtering and plotting
    try:
        data[date_column] = pd.to_datetime(data[date_column], errors='coerce')
        # Drop rows where date conversion failed to maintain data integrity
        data.dropna(subset=[date_column], inplace=True) 
    except Exception:
        st.error(f"Could not convert '{date_column}' to datetime format.")
        st.stop()
        
    # Process dates to get min/max year for slider
    min_year = data[date_column].dt.year.min()
    max_year = data[date_column].dt.year.max()
    
    st.success(f"File uploaded successfully! X-axis: '{date_column}', Bar value: '{value_column}'. Shape: {data.shape}")
    st.dataframe(data.head())
    
    # Column selection for category (optional) and Year Range
    st.subheader("Configure Chart Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Category column selection (optional)
        category_columns = ['None'] + data.columns.tolist()
        category_column = st.selectbox("Select Category Column (Bar colors - optional)", category_columns)
        
    with col2:
        # Year Range Selection
        if pd.isna(min_year) or pd.isna(max_year):
             st.warning("No valid dates found for year selection.")
             year_range = (2000, 2024) # Default fallback
        else:
            year_range = st.slider(
                "Select Year Range",
                min_value=int(min_year),
                max_value=int(max_year),
                value=(int(min_year), int(max_year)),
                step=1
            )
            
    # Display options
    st.subheader("Display Options")
    col3, col4 = st.columns(2)
    
    with col3:
        # Re-introducing show_bars for user control
        show_bars = st.checkbox("Show Bars", value=True) 

    with col4:
        show_line = st.checkbox("Show Line (Number of deals)", value=True)
    
    # Function to format currency values
    def format_currency(value):
        if value >= 1e9:
            val = value / 1e9
            if val >= 100:
                return f'£{int(val)}b'
            elif val >= 10:
                formatted = f'£{val:.1f}b'.rstrip('0').rstrip('.')
                return formatted
            else:
                formatted = f'£{val:.2f}b'.rstrip('0').rstrip('.')
                return formatted
        elif value >= 1e6:
            val = value / 1e6
            if val >= 100:
                return f'£{int(val)}m'
            elif val >= 10:
                formatted = f'£{val:.1f}m'
                if formatted.endswith('.0m'):
                    formatted = formatted.replace('.0m', 'm')
                return formatted
            else:
                formatted = f'£{val:.2f}m'
                if formatted.endswith('.0m'):
                    formatted = formatted.replace('.0m', 'm')
                else:
                    formatted = formatted.rstrip('0').rstrip('.')
                return formatted
        elif value >= 1e3:
            val = value / 1e3
            if val >= 100:
                return f'£{int(val)}k'
            elif val >= 10:
                formatted = f'£{val:.1f}k'
                if formatted.endswith('.0k'):
                    formatted = formatted.replace('.0k', 'k')
                return formatted
            else:
                formatted = f'£{val:.2f}k'
                if formatted.endswith('.0k'):
                    formatted = formatted.replace('.0k', 'k')
                else:
                    formatted = formatted.rstrip('0').rstrip('.')
                return formatted
        else:
            return f'£{value:.2f}'

    # Generate chart button
    if st.button("Generate Chart", type="primary"):
        # Filter data based on selected year range
        start_year, end_year = year_range
        chart_data = data[data[date_column].dt.year.between(start_year, end_year, inclusive='bo_]()]()_
