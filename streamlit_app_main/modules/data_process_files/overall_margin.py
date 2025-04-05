import streamlit as st
import pandas as pd
from modules.data_process_files import common
pd.set_option('display.float_format', '{:.2f}'.format)


### for display overall analysis

def calculate_summary_statistics(filtered_data, filtered_data_r):
    """
    Calculate summary of sales data for the filtered data.

    Args:
    - filtered_data: Filtered sales data.
    - filtered_data_r: Filtered returns data.

    Returns:
    - Dictionary containing the summary statistics.
    """
    return {
        "Total Sales": filtered_data['totalsales'].sum(),
        "Total Returns": filtered_data_r['treturnamt'].sum(),
        "Total Return cost":filtered_data_r['returncost'].sum(),
        "Net Sales": filtered_data['totalsales'].sum() - filtered_data_r['treturnamt'].sum(),
        "Total Gross Margin": filtered_data['gross_margin'].sum() + filtered_data_r['returncost'].sum() - filtered_data_r['treturnamt'].sum()
    }


def display_summary_statistics(stats):
    """
    Display summary statistics in the Streamlit app.

    Args:
    - stats: Dictionary containing the summary statistics.
    """
    st.sidebar.title("Overall Margin Analysis")
    cols = st.columns(len(stats))
    
    for i, (stat_name, value) in enumerate(stats.items()):
        with cols[i]:
            st.markdown(f"**{stat_name}**")
            st.write(value)


def display_pivot_tables(filtered_data, filtered_data_r, current_page):
    """
    Display pivoted tables for various categories in the Streamlit app.

    Args:
    - filtered_data: Filtered sales data.
    - filtered_data_r: Filtered returns data.
    - current_page: Currently selected page or filter in the Streamlit app.
    - we are also creating a column which is the difference between the return amount and the return cost. And then adjusting, the return value. 
    """

    filtered_data_r['amt_cost_diff'] = filtered_data_r['returncost'] - filtered_data_r['treturnamt']
    
    pivot_args_list = [
    {'title': 'Gross Margin by Salesman', 'args': {'valuesales': 'gross_margin', 'valuereturn': 'amt_cost_diff', 'index': ['spid', 'spname'], 'column': ['year', 'month']}},
    {'title': 'Gross Margin by Area', 'args': {'valuesales': 'gross_margin', 'valuereturn': 'amt_cost_diff', 'index': 'area', 'column': ['year', 'month']}},
    {'title': 'Gross Margin by Customer', 'args': {'valuesales': 'gross_margin', 'valuereturn': 'amt_cost_diff', 'index': ['cusid', 'cusname'], 'column': ['year', 'month']}},
    {'title': 'Gross Margin by Product', 'args': {'valuesales': 'gross_margin', 'valuereturn': 'amt_cost_diff', 'index': ['itemcode', 'itemname'], 'column': ['year', 'month']}},
    {'title': 'Gross Margin by Product Group', 'args': {'valuesales': 'gross_margin', 'valuereturn': 'amt_cost_diff', 'index': 'itemgroup', 'column': ['year', 'month']}}
    ]

    for pivot in pivot_args_list:
        pivot_table = common.net_pivot(filtered_data, filtered_data_r, pivot['args'], current_page)
        st.markdown(pivot['title'])
        st.write(pivot_table)
        st.markdown(common.create_download_link(pivot_table), unsafe_allow_html=True)
        

##### finish overall analysis here