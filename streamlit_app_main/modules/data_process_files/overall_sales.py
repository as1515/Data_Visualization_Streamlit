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
        "Total Sales": filtered_data['totalsales'].sum().round(2),
        "Total Returns": filtered_data_r['treturnamt'].sum().round(2),
        "Net Sales": filtered_data['totalsales'].sum() - filtered_data_r['treturnamt'].sum().round(2),
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
    
    # Create a grid-like layout with three columns
    col1, col2, col3 = st.columns(3)
    
    # Split stats into three parts
    stats_items = list(stats.items())
    first_third = stats_items[:len(stats_items)//3]
    second_third = stats_items[len(stats_items)//3:2*len(stats_items)//3]
    third_third = stats_items[2*len(stats_items)//3:]
    
    # Display first third of stats in first column
    with col1:
        for stat_name, value in first_third:
            st.markdown(f"**{stat_name}:** {value:,.2f}")
    
    # Display second third of stats in second column
    with col2:
        for stat_name, value in second_third:
            st.markdown(f"**{stat_name}:** {value:,.2f}")
    
    # Display third third of stats in third column
    with col3:
        for stat_name, value in third_third:
            st.markdown(f"**{stat_name}:** {value:,.2f}")


def display_pivot_tables(filtered_data, filtered_data_r, current_page):
    """
    Display pivoted tables for various categories in the Streamlit app using a dropdown selection.
    
    Parameters:
    - filtered_data: Filtered sales DataFrame
    - filtered_data_r: Filtered returns DataFrame
    - current_page: Current page context
    """
    pivot_args_list = [
        {'title': 'Net Sales by Salesman', 'args': {'valuesales': 'totalsales', 'valuereturn': 'treturnamt', 'index': ['spid', 'spname'], 'column': ['year', 'month']}},
        {'title': 'Net Sales by Area', 'args': {'valuesales': 'totalsales', 'valuereturn': 'treturnamt', 'index': 'area', 'column': ['year', 'month']}},
        {'title': 'Net Sales by Customer', 'args': {'valuesales': 'totalsales', 'valuereturn': 'treturnamt', 'index': ['cusid', 'cusname'], 'column': ['year', 'month']}},
        {'title': 'Net Sales by Product', 'args': {'valuesales': 'totalsales', 'valuereturn': 'treturnamt', 'index': ['itemcode', 'itemname'], 'column': ['year', 'month']}},
        {'title': 'Quantity Sold per Product', 'args': {'valuesales': 'quantity', 'valuereturn': 'returnqty', 'index': ['itemcode', 'itemname'], 'column': ['year', 'month']}},
        {'title': 'Net Sales by Product Group', 'args': {'valuesales': 'totalsales', 'valuereturn': 'treturnamt', 'index': 'itemgroup', 'column': ['year', 'month']}}
    ]
    
    # Create a dropdown to select pivot table
    selected_pivot = st.selectbox(
        "Select a Pivot Table to Display", 
        [pivot['title'] for pivot in pivot_args_list],
        key="pivot_table_selector"
    )
    
    # Find the selected pivot configuration
    selected_pivot_config = next(
        pivot for pivot in pivot_args_list 
        if pivot['title'] == selected_pivot
    )
    
    # Generate and display the selected pivot table
    try:
        pivot_table = common.net_pivot(
            filtered_data, 
            filtered_data_r, 
            selected_pivot_config['args'], 
            current_page
        )
        
        st.markdown(f"**{selected_pivot}**")
        st.write(pivot_table)
        st.markdown(common.create_download_link(pivot_table), unsafe_allow_html=True)
    
    except ValueError as e:
        st.error(f"Error generating pivot table: {e}")
        st.warning("This might be due to insufficient or incompatible data for the selected filter.")
        
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        st.warning("Please try a different filter or contact support if the issue persists.")

    # New section for column list selection
    st.subheader("Cross Relation Analysis")
    
    # Define options with their corresponding column lists
    column_options = {
        'Salesman': ['spid', 'spname'],
        'Customer': ['cusid', 'cusname'],
        'Product': ['itemcode', 'itemname'],
        'Product Group': ['itemgroup'],
        'Area': ['area']
    }
    
    # Create columns for side-by-side selectboxes
    col1, col2 = st.columns(2)
    
    with col1:
        first_selection = st.selectbox(
            "Select First Column List", 
            list(column_options.keys()), 
            index=0,
            key='first_column_list'
        )
    
    with col2:
        second_selection = st.selectbox(
            "Select Second Column List", 
            list(column_options.keys()), 
            index=1,
            key='second_column_list'
        )
    
    # Generate the column lists based on selections
    first_column_list = column_options[first_selection]
    second_column_list = column_options[second_selection]

    try: 
        pivot_args = {
            'title': f"{first_selection} vs {second_selection}",
            'valuesales': 'totalsales',
            'valuereturn': 'treturnamt',
            'index': first_column_list,
            'column': second_column_list
        }
        
        pivot_table_2 = common.net_pivot(
            filtered_data, 
            filtered_data_r, 
            pivot_args, 
            current_page
        )

        st.markdown(f"**{pivot_args['title']}**")
        # Display the styled table
        st.write(pivot_table_2)
        # Provide download link for original data
        st.markdown(common.create_download_link(pivot_table_2), unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"Error generating column lists: {e}")
        # Uncomment for detailed debugging
        # st.error(f"Traceback: {traceback.format_exc()}")
    
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        st.warning("Please try a different filter or contact support if the issue persists.")


def prepare_number_of_orders(filtered_data):
    """
    Prepare data for plotting the number of orders.
    
    Parameters:
    - filtered_data: Filtered sales DataFrame
    
    Returns:
    - DataFrame with the number of orders
    """
    # Calculate number of orders
    orders_data = filtered_data.groupby(['year', 'month']).size().reset_index(name='number_of_orders')
    return orders_data


def prepare_number_of_returns(filtered_data_r):
    """
    Prepare data for plotting the number of returns.
    
    Parameters:
    - filtered_data_r: Filtered returns DataFrame
    
    Returns:
    - DataFrame with the number of returns
    """
    # Calculate number of returns
    returns_data = filtered_data_r.groupby(['year', 'month']).size().reset_index(name='number_of_returns')
    return returns_data


def prepare_number_of_customers(filtered_data):
    """
    Prepare data for plotting the number of customers.
    
    Parameters:
    - filtered_data: Filtered sales DataFrame
    
    Returns:
    - DataFrame with the number of customers
    """
    # Calculate number of unique customers
    customers_data = filtered_data.groupby(['year', 'month'])['cusid'].nunique().reset_index(name='number_of_customers')
    return customers_data


def prepare_number_of_customer_returns(filtered_data_r):
    """
    Prepare data for plotting the number of customer returns.
    
    Parameters:
    - filtered_data_r: Filtered returns DataFrame
    
    Returns:
    - DataFrame with the number of customer returns
    """
    # Calculate number of unique customer returns
    customer_returns_data = filtered_data_r.groupby(['year', 'month'])['cusid'].nunique().reset_index(name='number_of_customer_returns')
    return customer_returns_data


def prepare_number_of_products(filtered_data):
    """
    Prepare data for plotting the number of products.
    
    Parameters:
    - filtered_data: Filtered sales DataFrame
    
    Returns:
    - DataFrame with the number of products
    """
    # Calculate number of unique products
    products_data = filtered_data.groupby(['year', 'month'])['itemcode'].nunique().reset_index(name='number_of_products')
    return products_data


def prepare_number_of_product_returns(filtered_data_r):
    """
    Prepare data for plotting the number of product returns.
    
    Parameters:
    - filtered_data_r: Filtered returns DataFrame
    
    Returns:
    - DataFrame with the number of product returns
    """
    # Calculate number of unique product returns
    product_returns_data = filtered_data_r.groupby(['year', 'month'])['itemcode'].nunique().reset_index(name='number_of_product_returns')
    return product_returns_data


def prepare_net_sales(filtered_data, filtered_data_r):
    """
    Prepare data for plotting the net sales, adjusted for returns.
    
    Parameters:
    - filtered_data: Sales DataFrame
    - filtered_data_r: Returns DataFrame
    
    Returns:
    - DataFrame with the net sales
    """
    # Calculate total sales per month
    sales_data = filtered_data.groupby(['year', 'month'])['totalsales'].sum().reset_index(name='total_sales')
    
    # Calculate total returns per month
    returns_data = filtered_data_r.groupby(['year', 'month'])['treturnamt'].sum().reset_index(name='total_returns')
    
    # Merge sales and returns data
    net_sales_data = sales_data.merge(returns_data, on=['year', 'month'], how='left')
    
    # Fill NaN returns with 0 and calculate net sales
    net_sales_data['total_returns'] = net_sales_data['total_returns'].fillna(0)
    net_sales_data['net_sales'] = net_sales_data['total_sales'] - net_sales_data['total_returns']
    
    # Select and rename columns
    net_sales_data = net_sales_data[['year', 'month', 'net_sales']]
    
    return net_sales_data


def prepare_sales_performance_ratios(filtered_data, filtered_data_r):
    """
    Calculate various sales performance ratios over time.
    
    Parameters:
    - filtered_data: Sales DataFrame
    - filtered_data_r: Returns DataFrame
    
    Returns:
    - DataFrame with performance ratios pivoted
    """
    # Prepare data for different metrics
    orders_data = prepare_number_of_orders(filtered_data)
    returns_data = prepare_number_of_returns(filtered_data_r)
    customers_data = prepare_number_of_customers(filtered_data)
    customer_returns_data = prepare_number_of_customer_returns(filtered_data_r)
    net_sales_data = prepare_net_sales(filtered_data, filtered_data_r)
    
    # Merge all dataframes on year and month
    merged_data = orders_data.merge(
        returns_data[['year', 'month', 'number_of_returns']], 
        on=['year', 'month'], 
        how='outer'
    ).merge(
        customers_data[['year', 'month', 'number_of_customers']], 
        on=['year', 'month'], 
        how='outer'
    ).merge(
        customer_returns_data[['year', 'month', 'number_of_customer_returns']], 
        on=['year', 'month'], 
        how='outer'
    ).merge(
        net_sales_data[['year', 'month', 'net_sales']], 
        on=['year', 'month'], 
        how='outer'
    )
    
    # Fill NaN values with 0 to prevent division errors
    merged_data = merged_data.fillna(0)
    
    # Calculate ratios
    merged_data['net_sales_per_order'] = merged_data['net_sales'] / merged_data['number_of_orders'].replace(0, 1)
    merged_data['net_sales_per_customer'] = merged_data['net_sales'] / merged_data['number_of_customers'].replace(0, 1)
    merged_data['orders_per_customer'] = merged_data['number_of_orders'] / merged_data['number_of_customers'].replace(0, 1)
    merged_data['returns_per_customer_return'] = merged_data['number_of_customer_returns'] / merged_data['number_of_returns'].replace(0, 1)
    merged_data['orders_to_returns_ratio'] = merged_data['number_of_returns']/merged_data['number_of_orders'].replace(0, 1)
    merged_data['customers_to_customer_returns_ratio'] = merged_data['number_of_customer_returns'] / merged_data['number_of_customers'].replace(0, 1)
    
    # Sort by year and month
    merged_data['month_numeric'] = merged_data['month'].apply(convert_month_to_number)
    merged_data['sort_key'] = merged_data.apply(lambda row: (int(row['year']), row['month_numeric']), axis=1)
    merged_data = merged_data.sort_values('sort_key')
    
    # Format month for display
    merged_data['month_formatted'] = merged_data['month_numeric'].astype(str).str.zfill(2)
    merged_data['period'] = merged_data.apply(lambda row: f"{row['year']}-{row['month_formatted']}", axis=1)
    
    # Select ratio columns for melting
    ratio_columns = [
        'net_sales_per_order', 
        'net_sales_per_customer', 
        'orders_per_customer', 
        'returns_per_customer_return', 
        'orders_to_returns_ratio', 
        'customers_to_customer_returns_ratio'
    ]
    
    # Rename columns for better readability
    ratio_names = {
        'net_sales_per_order': 'Net Sales per Order', 
        'net_sales_per_customer': 'Net Sales per Customer', 
        'orders_per_customer': 'Orders per Customer', 
        'returns_per_customer_return': 'Returns per Customer Return', 
        'orders_to_returns_ratio': 'Orders to Returns Ratio', 
        'customers_to_customer_returns_ratio': 'Customers to Customer Returns Ratio'
    }
    
    # Melt the data to create a long-format DataFrame
    melted_data = merged_data.melt(
        id_vars=['period'], 
        value_vars=ratio_columns, 
        var_name='Ratio', 
        value_name='Value'
    )
    
    # Replace ratio column names with readable names
    melted_data['Ratio'] = melted_data['Ratio'].map(ratio_names)
    
    # Pivot the melted data
    pivoted_data = melted_data.pivot_table(
        index='Ratio', 
        columns='period', 
        values='Value', 
        aggfunc='first'
    )
    
    # Round values
    pivoted_data = pivoted_data.round(2)
    
    return pivoted_data


def convert_month_to_number(month):
    """
    Convert month name or string to its numeric representation.
    
    Parameters:
    - month: Month name or string representation
    
    Returns:
    - Numeric month (1-12)
    """
    month_mapping = {
        'January': 1, 'Jan': 1,
        'February': 2, 'Feb': 2,
        'March': 3, 'Mar': 3,
        'April': 4, 'Apr': 4,
        'May': 5,
        'June': 6, 'Jun': 6,
        'July': 7, 'Jul': 7,
        'August': 8, 'Aug': 8,
        'September': 9, 'Sep': 9,
        'October': 10, 'Oct': 10,
        'November': 11, 'Nov': 11,
        'December': 12, 'Dec': 12
    }
    
    # If it's already a number, convert to int
    if isinstance(month, (int, float)):
        return int(month)
    
    # If it's a string, look up in mapping
    if isinstance(month, str):
        # Try exact match first
        if month in month_mapping:
            return month_mapping[month]
        
        # Try case-insensitive match
        month_lower = month.lower()
        for key, value in month_mapping.items():
            if key.lower() == month_lower:
                return value
    
    # If no match found, raise an error
    raise ValueError(f"Could not convert month: {month}")