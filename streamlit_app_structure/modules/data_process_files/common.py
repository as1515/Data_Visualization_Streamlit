import streamlit as st
import pandas as pd
import io
import base64
import decimal
import math
import json

def to_dataframe(data, columns):
    """Convert the fetched data to a pandas dataframe."""
    df = pd.DataFrame(data, columns=columns)
    return df

def load_json(filepath):
    with open(filepath, 'r') as file:
        return json.load(file)

def find_unique_overtime(data,group_criteria,count_criteria):
    unique_data = data.groupby(group_criteria)[count_criteria].nunique().reset_index()
    return unique_data

def make_aggregates(data,group_criteria,sum_criteria):
    grouped_data = data.groupby(group_criteria)[sum_criteria].sum().reset_index()
    return grouped_data

def find_mean(data,group_criteria,mean_criteria):
    mean_data = data.groupby(group_criteria)[mean_criteria].mean().reset_index()
    return mean_data

def find_median(data,group_criteria,median_criteria):
    median_data = data.groupby(group_criteria)[median_criteria].median().reset_index()
    return median_data

def numerise_columns(data,non_numeric_list):
    # List of all columns that are not in the non-numeric columns list
    numeric_cols = [col for col in data.columns if col not in non_numeric_list]
    # Convert specific columns to numeric
    for col in numeric_cols:
        data[col] = pd.to_numeric(data[col], errors='coerce')
    return data

def handle_infinity_and_round(x):
    # Check if x is a number (either int or float)
    if isinstance(x, (int, float)):
        # If x is infinite, return NaN
        if math.isinf(x):
            return float('nan')
        # If x is finite, round it
        return round(x)
    # If x is not a number, return it as-is
    return x

def filter_data_by_column(df, column, selected_values):
    if selected_values:
        return df[df[column].isin(selected_values)]
    return df

def create_download_link(df, filename="data.xlsx"):
        # If the columns have multiple levels, convert them to a single level
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [f"{str(col[0])}_{str(col[1]).strip()}" if col[1] else str(col[0]) for col in df.columns.values]
    
    towrite = io.BytesIO()
    df.to_excel(towrite, index=True, encoding='utf-8')
    towrite.seek(0)
    b64 = base64.b64encode(towrite.read()).decode()
    link = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download Excel File</a>'
    return link

def update_single_options(data, col):
    return data[col].unique().tolist()

# Define a function to update filter options for ID + Name columns
def update_pair_options(data, col1, col2):
    unique_pairs = data.drop_duplicates(subset=[col1, col2])[[col1, col2]]
    pairs = (unique_pairs[col1].astype(str) + " - " + unique_pairs[col2]).tolist()
    return pairs

def decimal_to_float(data):
    # Convert all decimal.Decimal columns to float
    """
    Convert all decimal columns in a dataframe to float.

    Args:
    - df: Input dataframe.

    Returns:
    - Dataframe with decimal columns converted to float.
    """
    for col in data.columns:
        if any(isinstance(x, decimal.Decimal) for x in data[col]):
            data[col] = data[col].astype(float)

    return data

def find_stats(grouped_data,metric):
    variance = round(grouped_data[metric].var(),2)
    std_dev = round(grouped_data[metric].std(),2)
    minimum = round(grouped_data[metric].min(),2)
    maximum = round(grouped_data[metric].max(),2)
    # Compute the Interquartile Range (IQR) for the 'totalsales' column again
    Q1 = grouped_data[metric].quantile(0.25)
    Q3 = grouped_data[metric].quantile(0.75)
    IQR = round(Q3 - Q1,2)

    skew = round(grouped_data[metric].skew(),2)
    kurt = round(grouped_data[metric].kurt(),2)

    return variance,std_dev,minimum,maximum,IQR,skew,kurt

def time_filtered_data_purchase(sales_data, purchase_data, selected_time):
    days = selected_time * 365
    sales_data['date'] = pd.to_datetime(sales_data['date'], errors='coerce')
    year_ago = sales_data['date'].max() - pd.Timedelta(days=days)
    
    sales_data = sales_data[sales_data['date'].notna() & (sales_data['date'] > year_ago)]
    
    purchase_data['combinedate'] = pd.to_datetime(purchase_data['combinedate'], errors='coerce')
    purchase_data = purchase_data[purchase_data['grnvoucher'].notna() & purchase_data['combinedate'].notna() & (purchase_data['combinedate'] > year_ago)]
    
    return sales_data, purchase_data, year_ago

def net_pivot(data1,data2, params1,current_page):
    pivot1 = data1.pivot_table(values=params1['valuesales'],
                            index=params1['index'], 
                            columns=params1['column'], 
                            aggfunc='sum').fillna(0)
    
    pivot2 = data2.pivot_table(values=params1['valuereturn'],
                            index=params1['index'], 
                            columns=params1['column'],  #
                            aggfunc='sum').fillna(0)
    
    pivot1 = decimal_to_float(pivot1)
    pivot2 = decimal_to_float(pivot2)
  
    # Ensure both pivot tables have the same columns
    all_columns = pivot1.columns.union(pivot2.columns)
    pivot1 = pivot1.reindex(columns=all_columns).fillna(0)
    pivot2 = pivot2.reindex(columns=all_columns).fillna(0)
        
    # Ensure both pivot tables have the same indices
    all_indices = pivot1.index.union(pivot2.index)
    pivot1 = pivot1.reindex(all_indices).fillna(0)
    pivot2 = pivot2.reindex(all_indices).fillna(0)
        
    # Now, the subtraction should work without introducing NaNs
    if current_page == "Overall Margin Analysis":
        pivot = pivot1.add(pivot2).fillna(0)
    else:
        pivot = pivot1.subtract(pivot2).fillna(0)
 
    # Sorting multi-level columns
    months_order = ["January", "February", "March", "April", "May", "June", "July", "August", 
                    "September", "October", "November", "December"]

    if current_page == 'YOY Analysis':
        sorted_columns = sorted(pivot.columns, key=lambda x: (months_order.index(x[1]),int(x[0])))#if str(x[0]).isnumeric() else (-1, -1)
    else:
        sorted_columns = sorted(pivot.columns, key=lambda x: (int(x[0]), months_order.index(x[1]))) #if str(x[0]).isnumeric() else (-1, -1))
    
    pivot = pivot[sorted_columns]
    
    # Calculating the grand total
    pivot['Grand Total'] = pivot.sum(axis=1)
    pivot = pivot.sort_values(by='Grand Total', ascending=False)

    # Convert all decimal.Decimal columns to float
    pivot = decimal_to_float(pivot)

    # pivot = pivot.applymap(lambda x: '{:,.0f}'.format(x) if isinstance(x, (int, float)) else x).fillna(0)
    pivot = pivot.applymap(lambda x: round(x) if isinstance(x, (int, float)) else x).fillna(0)

    return pivot

def net_sales_vertical(data1,data2,xaxis,yaxis1,yaxis2,current_page):
    # Grouping for Sales Data
    data1_grouped = data1.groupby(xaxis)[yaxis1].sum().reset_index()

    # Grouping for Returns Data
    data2_grouped = data2.groupby(xaxis)[yaxis2].sum().reset_index()

    # Merging the grouped data on 'year' and 'month'
    merged_df = pd.merge(data1_grouped, data2_grouped, on=xaxis, how='left')

    # Filling NaN values with 0 for months without returns
    merged_df[yaxis2].fillna(0, inplace=True)

    # Calculating net sales
    merged_df['net_sales'] = merged_df[yaxis1] - merged_df[yaxis2]

        # Defining the correct order for months
    month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

    # Setting the month column as a categorical variable with the defined order
    merged_df['month'] = pd.Categorical(merged_df['month'], categories=month_order, ordered=True)

    if current_page == 'YOY Analysis': 
           merged_df = merged_df.sort_values(['month', 'year']).reset_index()
           print(merged_df.columns)
    # Sorting the DataFrame by year and month
    else:
        merged_df = merged_df.sort_values(['year', 'month']).reset_index(drop=True)

        # Creating the xaxis column
        merged_df['xaxis'] = merged_df['month'].astype(str) + "_" + merged_df['year'].astype(str)


    return merged_df,'net_sales'

def get_pair_columns(column):
    """
    Return the paired ID and Name columns based on the provided column name.

    Args:
    - column: The provided column name.

    Returns:
    - Tuple containing the paired ID and Name columns.
    """
    if column.endswith("name"):
        if "item" in column:  # Special case for 'itemcode' and 'itemname'
            return "itemcode", "itemname"
        return column[:-4] + "id", column
    elif column.endswith("id"):
        return column, column[:-2] + "name"
    elif column.endswith("code"):  # Condition for 'code'
        return column, column[:-4] + "name"
    else:
        return f"{column}id", f"{column}name"


def apply_filter_and_update_options(df, df_r, column, display_name, is_pair=False, default=None):
    """
    Apply selected filter to dataframes and update options.

    Args:
    - df: Sales dataframe.
    - df_r: Returns dataframe.
    - column: Column name to apply the filter on.
    - display_name: Name to display on the Streamlit sidebar.
    - is_pair: If True, expects paired options (e.g., 'id - name').
    - default: Default value for the filter.

    Returns:
    - Filtered dataframes: df, df_r.
    """
    if is_pair:
        col1, col2 = get_pair_columns(column)
        options = update_pair_options(df, col1, col2)
    else:
        options = update_single_options(df, column)

    if column == "year" and default is None:
        current_year = max(set([int(value) for value in options]))
        last_year = current_year - 1
        default = [last_year, current_year]
    
    selected = st.sidebar.multiselect(f"Select {display_name}", options, default=default)
    
    if selected:
        if is_pair:
            selected_values = [x.split(" - ")[1] for x in selected]  # Extract the name part from 'id - name'
            df = df[df[f"{column}"].isin(selected_values)]
            df_r = df_r[df_r[f"{column}"].isin(selected_values)]
        else:
            df = df[df[column].isin(selected)]
            df_r = df_r[df_r[column].isin(selected)]
    
    return df, df_r

def filtered_options(filtered_data, filtered_data_r):
    """
    Filter dataframes based on user selections in Streamlit interface.

    Args:
    - filtered_data: Sales dataframe.
    - filtered_data_r: Returns dataframe.

    Returns:
    - Filtered dataframes: filtered_data, filtered_data_r.
    """
    # Apply filters in sequence: 'year', 'month', 'spname' (salesman), 'cusname' (customer), 'itemname' (product), 'area', 'itemgroup' (product group)
    filters_sequence = [
        ('year', 'Year', False),
        ('month', 'Month', False),
        ('spname', 'Salesman', True),
        ('cusname', 'Customer', True),
        ('itemname', 'Product', True),
        ('area', 'Area', False),
        ('itemgroup', 'Product Group', False)
    ]

    for column, display_name, is_pair in filters_sequence:
        filtered_data, filtered_data_r = apply_filter_and_update_options(filtered_data, filtered_data_r, column, display_name, is_pair)
    
    return filtered_data, filtered_data_r

def data_copy_add_columns(*dfs):
    """
    Process and clean the provided dataframes.

    Args:
    - *dfs: Variable number of dataframes to process.

    Returns:
    - Tuple containing the processed dataframes.
    """

    month_name_map = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December"
    }

    processed_dfs = []

    for df in dfs:
        df = df.copy()
        
        if 'totalsales' in df.columns:
            df['totalsales'] = pd.to_numeric(df['totalsales'], errors='coerce')
        if 'treturnamt' in df.columns:
            df['treturnamt'] = pd.to_numeric(df['treturnamt'], errors='coerce')
        if 'value' in df.columns:
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
        if 'quantity' in df.columns:
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        if 'cost' in df.columns:
            df['cost'] = pd.to_numeric(df['cost'], errors='coerce')
            df['gross_margin'] = df.get('totalsales', 0) - df['cost']
            df['rate'] = df.get('totalsales', 0) / df['quantity']

        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df[df['date'].notna()]
        df['DOM'] = df['date'].dt.day
        df['DOW'] = df['date'].dt.day_name()
        if 'month' in df.columns:
            df['month'] = df['month'].map(month_name_map)
        df = decimal_to_float(df)

        processed_dfs.append(df)

    return tuple(processed_dfs)

