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
        "Net Sales": filtered_data['totalsales'].sum() - filtered_data_r['treturnamt'].sum(),
        "Number of Orders": filtered_data['voucher'].nunique(),
        "Number of Returns": filtered_data_r['revoucher'].nunique(),
        "Number of Customers": filtered_data['cusid'].nunique(),
        "Number of Customer Returned": filtered_data_r['cusid'].nunique(),
        "Number of Products": filtered_data['itemcode'].nunique(),
        "Number of Products Returned": filtered_data_r['itemcode'].nunique()
    }


def display_summary_statistics(stats):
    """
    Display summary statistics in the Streamlit app.

    Args:
    - stats: Dictionary containing the summary statistics.
    """
    st.sidebar.title("Overall Sales Analysis")
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
    """
    pivot_args_list = [
            {'title': 'Net Sales by Salesman', 'args': {'valuesales': 'totalsales', 'valuereturn': 'treturnamt', 'index': ['spid', 'spname'], 'column': ['year', 'month']}},
            {'title': 'Net Sales by Area', 'args': {'valuesales': 'totalsales', 'valuereturn': 'treturnamt', 'index': 'area', 'column': ['year', 'month']}},
            {'title': 'Net Sales by Customer', 'args': {'valuesales': 'totalsales', 'valuereturn': 'treturnamt', 'index': ['cusid', 'cusname'], 'column': ['year', 'month']}},
            {'title': 'Net Sales by Product', 'args': {'valuesales': 'totalsales', 'valuereturn': 'treturnamt', 'index': ['itemcode', 'itemname'], 'column': ['year', 'month']}},
            {'title': 'Quantity Sold per Product', 'args': {'valuesales': 'quantity', 'valuereturn': 'returnqty', 'index': ['itemcode', 'itemname'], 'column': ['year', 'month']}},
            {'title': 'Net Sales by Product Group', 'args': {'valuesales': 'totalsales', 'valuereturn': 'treturnamt', 'index': 'itemgroup', 'column': ['year', 'month']}}
        ]
    
    st.markdown(filtered_data['cost'].isna().sum())
    st.markdown(filtered_data_r['returncost'].isna().sum())

    for pivot in pivot_args_list:
        pivot_table = common.net_pivot(filtered_data, filtered_data_r, pivot['args'], current_page)
        st.markdown(pivot['title'])
        st.write(pivot_table)
        st.markdown(common.create_download_link(pivot_table), unsafe_allow_html=True)
        
##### finish overall analysis here