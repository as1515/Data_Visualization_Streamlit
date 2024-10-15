import streamlit as st
import pandas as pd
import functools
from modules.data_process_files import common
from collections import defaultdict
pd.set_option('display.float_format', '{:.2f}'.format)


def customer_segmentation_by_collection_days(average_collection_df):
    # Define bin edges and labels
    bin_edges = [0, 2, 5, 10, 20, 30, 50, 100]  # Adjust according to your needs
    bin_labels = ['0-2 days', '3-5 days', '6-10 days', '11-20 days', '21-30 days', '31-50 days', '51-100 days']  # Adjust according to your needs

    # Assign each row to a bin
    average_collection_df['range_of_average_days'] = pd.cut(average_collection_df['average_days_to_collection'], bins=bin_edges, labels=bin_labels, right=True)

    # Group by the bins and calculate the count, total sales, total return, and total collection for each bin
    summary_df = average_collection_df.groupby('range_of_average_days').agg(
        count=pd.NamedAgg(column='average_days_to_collection', aggfunc='count'),
        total_sales=pd.NamedAgg(column='total_sale', aggfunc='sum'),  # Replace 'sales' with the actual column name for sales
        total_return=pd.NamedAgg(column='total_return', aggfunc='sum'),  # Replace 'return' with the actual column name for return
        total_collection=pd.NamedAgg(column='total_collection', aggfunc='sum')  # Replace 'collection' with the actual column name for collection
    ).reset_index()

    return summary_df

def filtered_options_for_collection_payments(sales_data, returns_data, collections_data, payments_data):
    datasets = {
        'sales': sales_data,
        'returns': returns_data,
        'collections': collections_data,
        'payments': payments_data
    }

    # Year Filter
    year_options = common.update_single_options(sales_data, 'year')
    current_year = max(set([int(value) for value in year_options]))
    selected_year = st.sidebar.multiselect("Select Year", year_options, default=current_year)
    
    # Month Filter
    month_options = common.update_single_options(sales_data, 'month')
    selected_month = st.sidebar.multiselect("Select Month", month_options)
    
    # Customer Filter
    customer_options = common.update_pair_options(sales_data, 'cusid', 'cusname')
    selected_customers = st.sidebar.multiselect("Select Customer", customer_options)
    selected_cusnames = [x.split(" - ")[1] for x in selected_customers]
    selected_cusids = [x.split(" - ")[0] for x in selected_customers]

    for key, data in datasets.items():
        data = common.filter_data_by_column(data, 'year', selected_year)
        data = common.filter_data_by_column(data, 'month', selected_month)
        if key not in ('collections', 'payments'):
            data = common.filter_data_by_column(data, 'cusname', selected_cusnames)
        elif key == 'collections':
            data = common.filter_data_by_column(data, 'cusid', selected_cusids)
        else:
            data
        datasets[key] = data

    # Salesman Filter 
    salesman_options = common.update_pair_options(sales_data, 'spid', 'spname')
    selected_salesman = st.sidebar.multiselect("Select Salesman", salesman_options)
    selected_spnames = [x.split(" - ")[1] for x in selected_salesman]
    selected_spids = [x.split(" - ")[0] for x in selected_salesman]

    for key, data in datasets.items():
        data = common.filter_data_by_column(data, 'year', selected_year)
        data = common.filter_data_by_column(data, 'month', selected_month)
        if key not in ('collections', 'payments'):
            data = common.filter_data_by_column(data, 'spname', selected_spnames)
        elif key == 'collections':
            selected_cusids = sales_data.loc[sales_data['spid'].isin(selected_spids), 'cusid'].tolist()
            data = common.filter_data_by_column(data, 'cusid', selected_cusids)
        else:
            data
        datasets[key] = data

    return datasets['sales'], datasets['returns'], datasets['collections'], datasets['payments']

def get_grouped_df_collection(sales_df, returns_df, collection_df, payment_df, timeframe):
    freq_map = {
        'Daily': 'D',
        'Weekly': 'W',
        'Monthly': 'M',
        'Yearly': 'Y'
    }
    freq = freq_map.get(timeframe, 'D')  # Default to 'D' if the timeframe is not recognized

    def process_df(df, value_col, type_suffix):
        df['timeframe'] = df['date'].dt.to_period(freq).apply(lambda r: r.start_time)
        
        # Group by both 'timeframe' and 'DOM'
        grouped = df.groupby(['timeframe', 'DOM'])[value_col].sum().reset_index()

        # Separate groups for 'timeframe' and 'DOM'
        grouped_timeframe = grouped.groupby('timeframe')[value_col].sum().reset_index()
        grouped_DOM = grouped.groupby('DOM')[value_col].sum().reset_index()
        grouped_DOW = df.groupby('DOW')[value_col].sum().reset_index()
        
        return grouped_timeframe, grouped_DOM, grouped_DOW, value_col + type_suffix

    dfs = [
        process_df(sales_df, 'totalsales', '_sales'),
        process_df(returns_df, 'treturnamt', '_returns'),
        process_df(collection_df.assign(value=collection_df['value'].abs()), 'value', '_collection'),
        process_df(payment_df, 'value', '_payment')
    ]

    def merge_dataframes_on_key(dfs, key):
        merged = dfs[0][0].copy()
        for df, suffix in dfs[1:]:
            merged = pd.merge(merged, df, on=key, how='outer', suffixes=('', suffix))
        return merged

    merged_df = merge_dataframes_on_key([(df[0], df[3]) for df in dfs], 'timeframe')
    merged_df_DOM = merge_dataframes_on_key([(df[1], df[3]) for df in dfs], 'DOM')
    merged_df_DOW = merge_dataframes_on_key([(df[2], df[3]) for df in dfs], 'DOW')

    merged_df['timeframe'] = merged_df['timeframe'].dt.strftime('%Y-%m-%d')
    return merged_df.fillna(0), merged_df_DOM.fillna(0), merged_df_DOW.fillna(0)

def average_days_to_collection(sales_df, returns_df, collection_df):
    # Combine and sort data
    combined_df = pd.concat([
        sales_df.assign(type='sale'),
        returns_df.assign(type='return'),
        collection_df.assign(type='collection')
    ], ignore_index=True).sort_values(by=['cusid', 'date'])
    
    # Create a mapping for customer names
    cusname_mapping = sales_df.drop_duplicates(subset=['cusid']).set_index('cusid')['cusname'].to_dict()

    # Process combined data
    ongoing_calculations = defaultdict(lambda: {'last_sale_date': None, 'adjusted_sales_amount': 0, 'total_days': 0, 'count': 0})
    collection_days_list = defaultdict(list)

    for _, row in combined_df.iterrows():
        cusid = row['cusid']
        ongoing = ongoing_calculations[cusid]
        ongoing['cusname'] = cusname_mapping.get(cusid, '<Unknown>')
        
        if row['type'] == 'sale':
            ongoing['last_sale_date'] = row['date']
            ongoing['adjusted_sales_amount'] += row['totalsales']
        elif row['type'] == 'return' and ongoing['last_sale_date']:
            ongoing['adjusted_sales_amount'] -= row['treturnamt']
        elif row['type'] == 'collection' and ongoing['last_sale_date'] and ongoing['adjusted_sales_amount'] > 0:
            days = (row['date'] - ongoing['last_sale_date']).days
            ongoing['total_days'] += days
            ongoing['count'] += 1
            collection_days_list[cusid].append({'cusname': ongoing['cusname'], 'year': row['date'].year, 'month_of_collection': row['date'].month, 'collection_days': days})

    # Create average days dataframe
    avg_days_data = {k: {'cusname': v['cusname'], 'average_days_to_collection': v['total_days'] / v['count']} for k, v in ongoing_calculations.items() if v['count'] > 0}
    average_days_df = pd.DataFrame.from_dict(avg_days_data, orient='index').reset_index().rename(columns={'index': 'cusid'})
    
    # Create collection days dataframe
    collection_days_data = [(k, v['cusname'], v['year'], v['month_of_collection'], v['collection_days']) for k, vals in collection_days_list.items() for v in vals]
    collection_days_df = pd.DataFrame(collection_days_data, columns=['cusid', 'cusname', 'year', 'month_of_collection', 'collection_days'])
    
    # Create pivot table
    pivot_df = pd.pivot_table(collection_days_df, values='collection_days', index=['cusid', 'cusname'], columns=['year', 'month_of_collection'], aggfunc='mean').fillna(0)
    pivot_df['Average'] = pivot_df.apply(lambda row: row[row != 0].mean(), axis=1)
    pivot_df.reset_index(inplace=True)
    
    # Merge totals
    totals = {
        'total_sale': sales_df.groupby('cusid')['totalsales'].sum(),
        'total_return': returns_df.groupby('cusid')['treturnamt'].sum(),
        'total_collection': collection_df.groupby('cusid')['value'].sum()
    }
    
    for col, series in totals.items():
        average_days_df = average_days_df.merge(series.rename(col), on='cusid', how='left').fillna(0)
        pivot_df = pivot_df.merge(series.reset_index(name=col), on='cusid', how='left').fillna(0)
    
    # Process collection data for average days between collections
    collection_data = combined_df[combined_df['type'] == 'collection'].copy()
    collection_data['cusname'].fillna(collection_data['cusid'].map(cusname_mapping), inplace=True)
    collection_data.sort_values(by=['cusid', 'cusname', 'date'], inplace=True)
    collection_data['days_between'] = collection_data.groupby(['cusid', 'cusname'])['date'].diff().dt.days
    
    avg_days_between = collection_data.groupby(['cusid', 'cusname']).agg(average_days_between=('days_between', 'mean'), average_collection=('value', 'mean')).reset_index()
    
    return average_days_df, pivot_df, avg_days_between, combined_df
