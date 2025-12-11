def generate_chart(final_data, category_column, show_bars, show_line, chart_title):
    """Generates the dual-axis Matplotlib chart."""
    chart_fig, chart_ax1 = plt.subplots(figsize=(12, 6))
    
    bar_width = 0.8
    x_pos = np.arange(len(final_data))
    dynamic_font_size = max(8, min(14, int(50 / len(final_data)) * 3))
    
    category_cols = []
    if category_column != 'None':
        category_cols = [col for col in final_data.columns if col not in ['time_period', 'row_count']]

    if category_column == 'None':
        y_max = final_data[VALUE_COLUMN].max()
    else:
        y_max = final_data[category_cols].sum(axis=1).max()

    vertical_offset = y_max * 0.01 
    
    # --- AXIS 1 (Bar Chart - Value) ---
    if category_column != 'None':
        bottom = np.zeros(len(final_data))
        for idx, cat in enumerate(category_cols):
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
                                   fontsize=dynamic_font_size, fontweight='bold', color=text_color)
            bottom += final_data[cat].values
    else:
        if show_bars:
            chart_ax1.bar(x_pos, final_data[VALUE_COLUMN], bar_width, 
                          label='Total Amount', color=SINGLE_BAR_COLOR, alpha=1.0)
        
            for i, x in enumerate(x_pos):
                val = final_data[VALUE_COLUMN].iloc[i]
                if val > 0:
                    label_text = format_currency(val)
                    text_color = '#FFFFFF' if is_dark_color(SINGLE_BAR_COLOR) else '#000000'
                    chart_ax1.text(x, vertical_offset, label_text, ha='center', va='bottom',
                                   fontsize=dynamic_font_size, fontweight='bold', color=text_color)
    
    chart_ax1.set_xticks(x_pos)
    chart_ax1.set_xticklabels(final_data['time_period'])
    
    plt.setp(chart_ax1.get_xticklabels(), fontsize=dynamic_font_size + 1, fontweight='normal')
    
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
        
        chart_ax2.plot(x_pos, line_data, color=LINE_COLOR, marker='o', linewidth=1.5, markersize=6, label='Number of Deals')
        
        # Calculate max_count after plotting to get accurate current limits
        max_count = line_data.max()
        chart_ax2.set_ylim(0, max_count * 1.5)
        
        chart_ax2.tick_params(axis='y', right=False, labelright=False, left=False, labelleft=False, length=0)
        for spine in chart_ax2.spines.values():
            spine.set_visible(False)
            
        y_range = chart_ax2.get_ylim()[1] - chart_ax2.get_ylim()[0]
        base_offset = y_range * 0.025 
        
        # --- NEW PEAK/VALLEY/SLOPE PLACEMENT LOGIC ---
        num_points = len(line_data)
        
        for i, y in enumerate(line_data):
            x = x_pos[i]
            
            # Default placement is ABOVE (va='bottom')
            place_above = True
            
            if num_points == 1:
                place_above = True # Only one point, always place above
            elif i == 0:
                # First point: Check slope to the next point
                if line_data[i+1] > y:
                    place_above = True # Rising slope: Place label ABOVE
                elif line_data[i+1] < y:
                    place_above = False # Falling slope: Place label BELOW
                # If flat, default to True
            elif i == num_points - 1:
                # Last point: Check slope from the previous point
                if line_data[i-1] < y:
                    place_above = True # Rising slope came in: Place label ABOVE
                elif line_data[i-1] > y:
                    place_above = False # Falling slope came in: Place label BELOW
                # If flat, default to True
            else:
                # Middle points: Check incoming and outgoing slopes
                y_prev = line_data[i-1]
                y_next = line_data[i+1]
                
                # Check Local Peak: higher than both neighbors
                is_peak = (y > y_prev) and (y > y_next)
                # Check Local Valley: lower than both neighbors
                is_valley = (y < y_prev) and (y < y_next)

                if is_peak:
                    # Peak: Rising slope in, falling slope out. Default to ABOVE.
                    place_above = True 
                elif is_valley:
                    # Valley: Falling slope in, rising slope out. Default to BELOW.
                    place_above = False
                elif y > y_prev and y < y_next:
                    # Continuously Rising segment (e.g., 100 -> 150 -> 200)
                    place_above = True # Place ABOVE
                elif y < y_prev and y > y_next:
                    # Continuously Falling segment (e.g., 200 -> 150 -> 100)
                    place_above = False # Place BELOW
                elif y_prev == y and y_next > y:
                    # Flat then Rising: Treat as rising, place ABOVE
                    place_above = True
                elif y_prev == y and y_next < y:
                    # Flat then Falling: Treat as falling, place BELOW
                    place_above = False
                elif y_prev < y and y_next == y:
                    # Rising then Flat: Treat as rising, place ABOVE
                    place_above = True
                elif y_prev > y and y_next == y:
                    # Falling then Flat: Treat as falling, place BELOW
                    place_above = False
                else:
                    # Completely flat segment (y_prev == y == y_next) or edge case: Default to ABOVE
                    place_above = True
                        

            # Determine final vertical alignment and position
            if place_above:
                # Place ABOVE the dot (va='bottom', text sits on top of y_pos)
                va = 'bottom'
                y_pos = y + base_offset
            else:
                # Place BELOW the dot (va='top', text hangs below y_pos)
                va = 'top' 
                y_pos = y - base_offset
            
            chart_ax2.text(x, y_pos, str(int(y)), ha='center', va=va, fontsize=dynamic_font_size, 
                           color=LINE_COLOR, fontweight='bold')
    
    # --- LEGEND & TITLE ---
    legend_elements = []
    
    if show_bars:
        if category_column != 'None':
            for idx, cat in enumerate(category_cols):
                color = CATEGORY_COLORS[idx % len(CATEGORY_COLORS)]
                legend_elements.append(Line2D([0], [0], marker='o', color='w', 
                                              markerfacecolor=color, markersize=10, label=cat))
        else:
            legend_elements.append(Line2D([0], [0], marker='o', color='w', 
                                          markerfacecolor=SINGLE_BAR_COLOR, markersize=10, label='Total Amount'))
            
    if show_line:
        legend_elements.append(Line2D([0], [0], marker='o', color='w', 
                                      markerfacecolor=LINE_COLOR, markersize=10, label='Number of Deals'))
        
    chart_ax1.legend(handles=legend_elements, loc='upper left', fontsize=12, frameon=False, 
                     prop={'weight': 'normal'}, labelspacing=1.0)
    
    # Use the custom title here
    plt.title(chart_title, fontsize=18, fontweight='bold', pad=20)
    plt.tight_layout()
    
    return chart_fig
