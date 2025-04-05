import plotly.graph_objects as go
import streamlit as st
import plotly.express as px
from modules.data_process_files import common

def plot_histogram(data_dict, y_axis_title):
    x = list(data_dict.keys())
    y = [val[0] for val in data_dict.values()]

    fig = go.Figure(data=[go.Bar(x=x, y=y)])

    fig.update_layout(title_text='Histogram of Values Over Time',
                      xaxis_title='Timeline',
                      yaxis_title=y_axis_title)

    st.plotly_chart(fig, use_container_width=True)

def plot_bar_chart(data, x_axis, y_axis, color=None, title=""):
    """
    Create an interactive bar chart using plotly.graph_objects.

    Parameters:
    - data: DataFrame containing the data to be plotted.
    - x_axis: The column in the dataframe to be used for the x-axis.
    - y_axis: The column in the dataframe to be used for the y-axis.
    - color: The column in the dataframe to be used for bar colors (for grouped bars).
    - title: The title of the chart.
    """

    if color:
        unique_colors = data[color].unique()
        traces = []

        for col in unique_colors:
            subset = data[data[color] == col]
            traces.append(go.Bar(x=subset[x_axis], y=subset[y_axis], name=str(col)))

        layout = go.Layout(title=title, barmode='group')
        fig = go.Figure(data=traces, layout=layout)

    else:
        fig = go.Figure(data=[go.Bar(x=data[x_axis], y=data[y_axis])])
        fig.update_layout(title_text=title)

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)

def plot_net_sales(data1,data2,xaxis,yaxis1,yaxis2,bartitle,current_page):

    grouped_data,yaxis = common.net_sales_vertical(data1,data2,xaxis,yaxis1,yaxis2,current_page)

    # Create the bar plot using Plotly
    fig = px.bar(grouped_data, x='xaxis', y=yaxis, title=bartitle)

    # Display the plot in Streamlit
    st.plotly_chart(fig,use_container_width=True)


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


def plot_number_of_orders(filtered_data, current_page):
    """
    Plot the number of orders over time as a bar graph.
    
    Parameters:
    - filtered_data: Filtered sales DataFrame
    - current_page: Current page context
    """
    from modules.data_process_files import overall_sales
    
    # Prepare data
    orders_data = overall_sales.prepare_number_of_orders(filtered_data)
    
    # Create a custom sorting key with robust month conversion
    orders_data['month_numeric'] = orders_data['month'].apply(convert_month_to_number)
    orders_data['sort_key'] = orders_data.apply(lambda row: (int(row['year']), row['month_numeric']), axis=1)
    orders_data = orders_data.sort_values('sort_key')
    
    # Ensure month is a string and padded
    orders_data['month_formatted'] = orders_data['month_numeric'].astype(str).str.zfill(2)
    orders_data['x_label'] = orders_data.apply(lambda row: f"{row['year']}-{row['month_formatted']}", axis=1)
    
    # Create Plotly bar graph
    fig = px.bar(
        orders_data, 
        x='x_label', 
        y='number_of_orders',
        title='Number of Orders Over Time',
        labels={'x_label': 'Year-Month', 'number_of_orders': 'Number of Orders'}
    )
    
    # Customize layout
    fig.update_layout(
        xaxis_title='Year-Month',
        yaxis_title='Number of Orders',
        template='plotly_white',
        xaxis_tickangle=-45
    )
    
    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True)


def plot_number_of_returns(filtered_data_r, current_page):
    """
    Plot the number of returns over time as a bar graph.
    
    Parameters:
    - filtered_data_r: Filtered returns DataFrame
    - current_page: Current page context
    """
    from modules.data_process_files import overall_sales
    
    # Prepare data
    returns_data = overall_sales.prepare_number_of_returns(filtered_data_r)
    
    # Create a custom sorting key with robust month conversion
    returns_data['month_numeric'] = returns_data['month'].apply(convert_month_to_number)
    returns_data['sort_key'] = returns_data.apply(lambda row: (int(row['year']), row['month_numeric']), axis=1)
    returns_data = returns_data.sort_values('sort_key')
    
    # Ensure month is a string and padded
    returns_data['month_formatted'] = returns_data['month_numeric'].astype(str).str.zfill(2)
    returns_data['x_label'] = returns_data.apply(lambda row: f"{row['year']}-{row['month_formatted']}", axis=1)
    
    # Create Plotly bar graph
    fig = px.bar(
        returns_data, 
        x='x_label', 
        y='number_of_returns',
        title='Number of Returns Over Time',
        labels={'x_label': 'Year-Month', 'number_of_returns': 'Number of Returns'}
    )
    
    # Customize layout
    fig.update_layout(
        xaxis_title='Year-Month',
        yaxis_title='Number of Returns',
        template='plotly_white',
        xaxis_tickangle=-45
    )
    
    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True)


def plot_number_of_customers(filtered_data, current_page):
    """
    Plot the number of unique customers over time as a bar graph.
    
    Parameters:
    - filtered_data: Filtered sales DataFrame
    - current_page: Current page context
    """
    from modules.data_process_files import overall_sales
    
    # Prepare data
    customers_data = overall_sales.prepare_number_of_customers(filtered_data)
    
    # Create a custom sorting key with robust month conversion
    customers_data['month_numeric'] = customers_data['month'].apply(convert_month_to_number)
    customers_data['sort_key'] = customers_data.apply(lambda row: (int(row['year']), row['month_numeric']), axis=1)
    customers_data = customers_data.sort_values('sort_key')
    
    # Ensure month is a string and padded
    customers_data['month_formatted'] = customers_data['month_numeric'].astype(str).str.zfill(2)
    customers_data['x_label'] = customers_data.apply(lambda row: f"{row['year']}-{row['month_formatted']}", axis=1)
    
    # Create Plotly bar graph
    fig = px.bar(
        customers_data, 
        x='x_label', 
        y='number_of_customers',
        title='Number of Unique Customers Over Time',
        labels={'x_label': 'Year-Month', 'number_of_customers': 'Number of Customers'}
    )
    
    # Customize layout
    fig.update_layout(
        xaxis_title='Year-Month',
        yaxis_title='Number of Customers',
        template='plotly_white',
        xaxis_tickangle=-45
    )
    
    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True)


def plot_number_of_customer_returns(filtered_data_r, current_page):
    """
    Plot the number of unique customer returns over time as a bar graph.
    
    Parameters:
    - filtered_data_r: Filtered returns DataFrame
    - current_page: Current page context
    """
    from modules.data_process_files import overall_sales
    
    # Prepare data
    customer_returns_data = overall_sales.prepare_number_of_customer_returns(filtered_data_r)
    
    # Create a custom sorting key with robust month conversion
    customer_returns_data['month_numeric'] = customer_returns_data['month'].apply(convert_month_to_number)
    customer_returns_data['sort_key'] = customer_returns_data.apply(lambda row: (int(row['year']), row['month_numeric']), axis=1)
    customer_returns_data = customer_returns_data.sort_values('sort_key')
    
    # Ensure month is a string and padded
    customer_returns_data['month_formatted'] = customer_returns_data['month_numeric'].astype(str).str.zfill(2)
    customer_returns_data['x_label'] = customer_returns_data.apply(lambda row: f"{row['year']}-{row['month_formatted']}", axis=1)
    
    # Create Plotly bar graph
    fig = px.bar(
        customer_returns_data, 
        x='x_label', 
        y='number_of_customer_returns',
        title='Number of Unique Customer Returns Over Time',
        labels={'x_label': 'Year-Month', 'number_of_customer_returns': 'Number of Customer Returns'}
    )
    
    # Customize layout
    fig.update_layout(
        xaxis_title='Year-Month',
        yaxis_title='Number of Customer Returns',
        template='plotly_white',
        xaxis_tickangle=-45
    )
    
    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True)


def plot_number_of_products(filtered_data, current_page):
    """
    Plot the number of unique products over time as a bar graph.
    
    Parameters:
    - filtered_data: Filtered sales DataFrame
    - current_page: Current page context
    """
    from modules.data_process_files import overall_sales
    
    # Prepare data
    products_data = overall_sales.prepare_number_of_products(filtered_data)
    
    # Create a custom sorting key with robust month conversion
    products_data['month_numeric'] = products_data['month'].apply(convert_month_to_number)
    products_data['sort_key'] = products_data.apply(lambda row: (int(row['year']), row['month_numeric']), axis=1)
    products_data = products_data.sort_values('sort_key')
    
    # Ensure month is a string and padded
    products_data['month_formatted'] = products_data['month_numeric'].astype(str).str.zfill(2)
    products_data['x_label'] = products_data.apply(lambda row: f"{row['year']}-{row['month_formatted']}", axis=1)
    
    # Create Plotly bar graph
    fig = px.bar(
        products_data, 
        x='x_label', 
        y='number_of_products',
        title='Number of Unique Products Over Time',
        labels={'x_label': 'Year-Month', 'number_of_products': 'Number of Products'}
    )
    
    # Customize layout
    fig.update_layout(
        xaxis_title='Year-Month',
        yaxis_title='Number of Products',
        template='plotly_white',
        xaxis_tickangle=-45
    )
    
    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True)


def plot_number_of_product_returns(filtered_data_r, current_page):
    """
    Plot the number of unique product returns over time as a bar graph.
    
    Parameters:
    - filtered_data_r: Filtered returns DataFrame
    - current_page: Current page context
    """
    from modules.data_process_files import overall_sales
    
    # Prepare data
    product_returns_data = overall_sales.prepare_number_of_product_returns(filtered_data_r)
    
    # Create a custom sorting key with robust month conversion
    product_returns_data['month_numeric'] = product_returns_data['month'].apply(convert_month_to_number)
    product_returns_data['sort_key'] = product_returns_data.apply(lambda row: (int(row['year']), row['month_numeric']), axis=1)
    product_returns_data = product_returns_data.sort_values('sort_key')
    
    # Ensure month is a string and padded
    product_returns_data['month_formatted'] = product_returns_data['month_numeric'].astype(str).str.zfill(2)
    product_returns_data['x_label'] = product_returns_data.apply(lambda row: f"{row['year']}-{row['month_formatted']}", axis=1)
    
    # Create Plotly bar graph
    fig = px.bar(
        product_returns_data, 
        x='x_label', 
        y='number_of_product_returns',
        title='Number of Unique Product Returns Over Time',
        labels={'x_label': 'Year-Month', 'number_of_product_returns': 'Number of Product Returns'}
    )
    
    # Customize layout
    fig.update_layout(
        xaxis_title='Year-Month',
        yaxis_title='Number of Product Returns',
        template='plotly_white',
        xaxis_tickangle=-45
    )
    
    # Display in Streamlit
    st.plotly_chart(fig, use_container_width=True)
