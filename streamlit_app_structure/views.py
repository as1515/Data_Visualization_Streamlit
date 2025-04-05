import streamlit as st
import pandas as pd
from .analytics import Analytics
from modules.data_process_files import common,overall_sales, overall_margin, collection, yoy, purchase, histogram,descriptive_stats,basket,financial
from modules.visualization_files import common_v, yoy_v, basket_v
from datetime import datetime
from io import BytesIO
pd.set_option('display.float_format', '{:.2f}'.format)

def display_overall_analysis_page(current_page):
    """
    Display the overall sales analysis page in the Streamlit app.

    Args:
    - current_page: Currently selected page or filter in the Streamlit app.
    """

    # Fetch data for sales and returns
    sales_data = Analytics('sales').data
    returns_data = Analytics('return').data

    # Filters
    # Streamlit Widgets for User Input
    st.sidebar.title("Overall Sales Analysis")

    # Process data and filter based on user's selection in Streamlit app
    filtered_data, filtered_data_r = common.data_copy_add_columns(sales_data, returns_data)
    filtered_data, filtered_data_r = common.filtered_options(filtered_data, filtered_data_r)

    col1, col2 = st.sidebar.columns(2)
    with col1:
        try:
            # Create an in-memory Excel writer
            sales_excel_buffer = BytesIO()
            with pd.ExcelWriter(sales_excel_buffer) as writer:
                filtered_data.to_excel(writer, index=False, sheet_name='Filtered Sales Data')
            sales_excel_buffer.seek(0)
            
            st.download_button(
                label="Download Sales Data",
                data=sales_excel_buffer,
                file_name=f'filtered_sales_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        except ImportError:
            st.warning("Install 'openpyxl' to enable Excel downloads: `pip install openpyxl`")
    
    with col2:
        try:
            # Create an in-memory Excel writer
            returns_excel_buffer = BytesIO()
            with pd.ExcelWriter(returns_excel_buffer) as writer:
                filtered_data_r.to_excel(writer, index=False, sheet_name='Filtered Returns Data')
            returns_excel_buffer.seek(0)
            
            st.download_button(
                label="Download Returns Data",
                data=returns_excel_buffer,
                file_name=f'filtered_returns_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            )
        except ImportError:
            st.warning("Install 'openpyxl' to enable Excel downloads: `pip install openpyxl`")

    # Dropdown for selecting plot type
    st.subheader("Select Plot Type")
    plot_options = [
        'Net Sales',
        'Number of Orders',
        'Number of Returns',
        'Number of Customers',
        'Number of Customer Returns',
        'Number of Products',
        'Number of Product Returns'
    ]
    selected_plot = st.selectbox("Choose a plot to display:", plot_options)
    
    # Display selected plot
    if selected_plot == 'Net Sales':
        common_v.plot_net_sales(filtered_data, filtered_data_r, ['year', 'month'], 'totalsales', 'treturnamt', 'Net Sales (filtered)', current_page)
    elif selected_plot == 'Number of Orders':
        common_v.plot_number_of_orders(filtered_data, current_page)
    elif selected_plot == 'Number of Returns':
        common_v.plot_number_of_returns(filtered_data_r, current_page)
    elif selected_plot == 'Number of Customers':
        common_v.plot_number_of_customers(filtered_data, current_page)
    elif selected_plot == 'Number of Customer Returns':
        common_v.plot_number_of_customer_returns(filtered_data_r, current_page)
    elif selected_plot == 'Number of Products':
        common_v.plot_number_of_products(filtered_data, current_page)
    elif selected_plot == 'Number of Product Returns':
        common_v.plot_number_of_product_returns(filtered_data_r, current_page)

    # Calculate summary statistics
    summary_stats = overall_sales.calculate_summary_statistics(filtered_data, filtered_data_r)
    

    # Calculate and display performance ratios table
    st.subheader("Sales Performance Ratios")
    performance_ratios = overall_sales.prepare_sales_performance_ratios(filtered_data, filtered_data_r)
    
    # Display table
    st.write(performance_ratios, use_container_width=True)
    # Display summary statistics in Streamlit
    overall_sales.display_summary_statistics(summary_stats)

    # Display pivoted tables for various categories
    overall_sales.display_pivot_tables(filtered_data, filtered_data_r, current_page)


def display_margin_analysis_page(current_page):
    sales_data = Analytics('sales').data
    returns_data = Analytics('return').data
    
    # Filters
    # Streamlit Widgets for User Input
    st.sidebar.title("Overall Margin Analysis")

    # Start with the full dataset
    filtered_data,filtered_data_r = common.data_copy_add_columns(sales_data,returns_data)
    filtered_data, filtered_data_r = common.filtered_options(filtered_data,filtered_data_r)

    #need to change this to common
    common_v.plot_net_sales(filtered_data,filtered_data_r,['year','month'],'gross_margin','treturnamt','Net Gross Margin (filtered)',current_page)

    # Calculate summary statistics
    summary_stats = overall_margin.calculate_summary_statistics(filtered_data,filtered_data_r)

    #Display overall margin analysis
    overall_margin.display_summary_statistics(summary_stats)

        # Display pivoted tables for various categories
    overall_margin.display_pivot_tables(filtered_data, filtered_data_r, current_page)

def display_yoy_analysis_page(current_page):
    sales_data = Analytics('sales').data
    returns_data = Analytics('return').data
    
    # Filters
    # Streamlit Widgets for User Input
    st.sidebar.title("YOY Analysis")

    # Start with the full dataset
    filtered_data,filtered_data_r = common.data_copy_add_columns(sales_data,returns_data)
    filtered_data, filtered_data_r = common.filtered_options(filtered_data,filtered_data_r)


    yoy_v.plot_yoy(filtered_data,filtered_data_r,['year','month'],'year','gross_margin','treturnamt','Net Gross Margin (filtered)',current_page)
    yoy_v.plot_yoy(filtered_data,filtered_data_r,['year','month'],'year','totalsales','treturnamt','Net Sales (filtered)',current_page)
    
            # Display pivoted tables for various categories
    yoy.display_pivot_tables(filtered_data, filtered_data_r, current_page)

def display_purchase_analysis_page(current_page):
    sales_data = Analytics('sales').data
    purchase_data = Analytics('purchase').data 
    inventory_data = Analytics('stock').data
    
    options =  [i for i in range(10)]
    default_option = 2
    default_index = options.index(default_option)
    selected_time = st.sidebar.selectbox("Select Time Frame",options,index= default_index)

    sales_df,purchase_df,year_ago = common.time_filtered_data_purchase(sales_data,purchase_data,selected_time)
    cohort_df = purchase.main_purchase_product_cohort_process(sales_df,purchase_df)

    selected_products = st.sidebar.multiselect("Select Product", common.update_pair_options(cohort_df,'itemcode','itemname'))
    if selected_products:
        selected_itemnames = [x.split(" - ")[0] for x in selected_products]
        cohort_df = cohort_df[cohort_df['itemcode'].isin(selected_itemnames)]

    cohort_df = cohort_df.applymap(common.handle_infinity_and_round).fillna(0)
    st.markdown("Product-Based Purchase Cohort")
    st.write(cohort_df)

    st.markdown(common.create_download_link(cohort_df), unsafe_allow_html=True)
    
    if st.button("Generate Purchase Requirement"):
        result_df = purchase.generate_cohort(purchase_data,year_ago,inventory_data,sales_df,cohort_df)
        st.markdown("Generated Purchase Requisition")
        st.write(result_df)
        st.markdown(common.create_download_link(result_df), unsafe_allow_html=True)

def display_collection_analysis_page(current_page):
    # Load data and preprocess
    modules = ['sales', 'return', 'collection', 'payments']
    data_frames = {}
    for module in modules:
        stats = Analytics(module)
        data_frames[module] = stats.data

    sales_df, returns_df, collection_df, payment_df = common.data_copy_add_columns(
        data_frames['sales'][['date', 'year', 'month', 'spid', 'spname','cusid', 'cusname', 'totalsales']],
        data_frames['return'][['date', 'year', 'month', 'spid', 'spname','cusid', 'cusname', 'treturnamt']],
        data_frames['collection'][['date', 'year', 'month', 'cusid', 'value']],
        data_frames['payments'][['date', 'year', 'month', 'account', 'description', 'value']]
    )

    sales_df, returns_df, collection_df, payment_df = collection.filtered_options_for_collection_payments(sales_df, returns_df, collection_df, payment_df)

    sales_df = sales_df.groupby(['date', 'year', 'month', 'cusid', 'cusname', 'DOM', 'DOW']).totalsales.sum().reset_index()
    returns_df = returns_df.groupby(['date', 'year', 'month', 'cusid', 'cusname', 'DOM', 'DOW']).treturnamt.sum().reset_index()

    # Compute average days and other metrics
    avg_days, pivot_df, avg_days_between, _ = collection.average_days_to_collection(sales_df, returns_df, collection_df)
    summary_df = collection.customer_segmentation_by_collection_days(avg_days)

    # Display metrics
    for title, df in {
        "Average Days to Collection": avg_days,
        "Customer Segmentation by Days to Collection": summary_df,
        "Collection Days by Year/Month": pivot_df,
        "Average Days to Collection": avg_days_between
    }.items():
        st.markdown(title)
        st.write(df)
        st.markdown(common.create_download_link(df), unsafe_allow_html=True)

    # Analysis and Metric Selection
    timeframe = st.selectbox('Select Time Range', ['Daily', 'Weekly', 'Monthly', 'Yearly'], index=2)
    grouped_df, grouped_df_DOM, grouped_df_DOW = collection.get_grouped_df_collection(sales_df, returns_df, collection_df, payment_df, timeframe)

    # Display and visualize data
    for title, (df, x_axis) in {
            f"Comparison of Sales/Collection/Payment {timeframe}": (grouped_df, 'timeframe'),
            "Comparison of Sales/Collection/Payment DOM": (grouped_df_DOM, 'DOM'),
            "Comparison of Sales/Collection/Payment DOW": (grouped_df_DOW, 'DOW')
    }.items():
        st.markdown(title)
        df = df.rename(columns={'value':'value_collection','valuevalue_payment':'value_payment'})
        st.write(df)
        st.markdown(common.create_download_link(df), unsafe_allow_html=True)
        long_df = df.melt(id_vars=[x_axis], value_vars=['totalsales', 'treturnamt', 'value_collection', 'value_payment'], var_name='category', value_name='value')
        common_v.plot_bar_chart(data=long_df, x_axis=x_axis, y_axis='value', color='category', title=f'{x_axis} Collection Analysis')

def display_histogram_page(current_page):
    sales_data = Analytics('sales').data
    returns_data = Analytics('return').data
    
    st.sidebar.title("Histograms & Distribution")

    filtered_data,filtered_data_r = common.data_copy_add_columns(sales_data,returns_data)
    filtered_data, filtered_data_r = common.filtered_options(filtered_data,filtered_data_r)

    metric_to_column = {
        'Customer':['Voucher Count','Sales','Returns','Margin','Cost'],  ### count -- voucher
        'Products':['Counts','Sales','Returns','Cost','Margin','Quantity'],
        'Sales':['Voucher','Counts'],
        'Returns':['Voucher','Counts'],
        'Cost':['Voucher','Counts'],
        'Margin':['Voucher','Counts'],
        'Quantity':['Counts']
    }

    cols = st.columns(5)
    # Analysis and Metric Selection
    with cols[0]:
        selected_column = st.selectbox("Select a Column", list(metric_to_column.keys()))

    metric_options = metric_to_column.get(selected_column, [])

    with cols[1]:
        selected_metric= st.selectbox("Select a Metric", (metric_options))

    if selected_column != 'Returns' and selected_metric != 'Returns':
        ###visualization element on the histogram page
        histogram.visualize_histogram(filtered_data, selected_column, selected_metric)
    else:
        histogram.visualize_histogram(filtered_data_r, selected_column, selected_metric)

def display_descriptive_stats_page(current_page):
    sales_data = Analytics('sales').data
    returns_data = Analytics('return').data

    st.sidebar.title("Descriptive Statistics")

    filtered_data,filtered_data_r= common.data_copy_add_columns(sales_data,returns_data)
    filtered_data, filtered_data_r = common.filtered_options(filtered_data,filtered_data_r)

    ## mean median calculation section over time and filtered data 
    cols = st.columns(5)

    with cols[0]:
        metric = st.selectbox("Metrics", ('Orders','Customers','Products','Sales','Return','Margins'))
    
    # Create a dictionary to map 'timing' options to 'pective' options
    timing_to_pective = {
        'Year/Month/Date': ['Year/Month/Date','Year/Month','Year/Date','Month/Date','Month','Year','Date'],
        'Year/Month/Day': ['Year/Month/Day','Year/Month','Year/Day','Month/Day','Month','Year','Day'],
        'Year/Month': ['Year/Month', 'Year', 'Month'],
        'Year/Date': ['Year/Date','Year','Date'],
        'Year/Day': ['Year/Day','Year','Day'],
        'Month/Date': ['Month/Date','Month','Date'],
        'Month/Day': ['Month/Day','Month','Day'],
        'Month':['Month'],
        'Year':['Year'],
        'Date':['Date'],
        'Day':['Day']
        # Add other mappings as needed
    }

    # Get the 'timing' selection from the first selectbox
    with cols[1]:
        timing = st.selectbox("Time Period", list(timing_to_pective.keys()))

    # Get the corresponding 'pective' options based on the 'timing' selection
    pective_options = timing_to_pective.get(timing, [])

    # Update the 'pective' selectbox with the filtered options
    with cols[2]:
        pective = st.selectbox("Perspective", pective_options)

    with cols[3]:
        stats = st.selectbox("Statistics", ('Mean','Median','Total'))

    metric_mapping = {
                    'Orders':'voucher',
                    'Customers':'cusid',
                    'Products':'itemcode',
                    'Sales':'totalsales',
                    'Return':'treturnamt',
                    'Margins':'gross_margin'
    }

    if metric != 'Return':
        descriptive_stats.process_and_visualize_v3(filtered_data,pective,metric_mapping[metric],metric,timing,stats)
    else:
        descriptive_stats.process_and_visualize_v3(filtered_data_r,pective,metric_mapping[metric],timing,stats)

def display_basket_analysis_page(current_page):
    sales_data = Analytics('sales').data
    purchase_data = Analytics('purchase').data
    inventory_data = Analytics('stock').data
    inventory_data = inventory_data[['itemcode','stockqty']]

    options =  [i for i in range(10)]
    default_option = 2
    default_index = options.index(default_option)
    selected_time = st.sidebar.selectbox("Select Time Frame",options,index= default_index)

    sales_df,purchase_df = common.time_filtered_data_purchase(sales_data,purchase_data,selected_time)
    purchase_basket = basket.purchase_basket_analysis(purchase_df)

    # products_to_order
    st.markdown("Purchase Basket Analysis")
    st.write(purchase_basket)

    st.markdown(common.create_download_link(purchase_basket), unsafe_allow_html=True)
    sales_basket = basket.sales_basket_analysis(sales_df,inventory_data)

    # products_to_order
    st.markdown("Sales Basket Analysis")
    st.write(sales_basket)

    st.markdown(common.create_download_link(sales_basket), unsafe_allow_html=True)
    basket_v.market_basket_heatmap(sales_basket)

def display_financial_statements(current_page):
    st.sidebar.title("Financial Statements")
    selected_perspective = st.sidebar.selectbox("Timeframe",['Yearly','Monthly'],index=0)

    main_data_dict_pl = {}
    main_data_dict_bs = {}
    # Get the current year
    current_year = datetime.now().year
    # Generate a list of the 10 years starting from the most recent year
    options = [current_year - i for i in range(10)]
    default_option = current_year
    default_index = options.index(default_option)
    selected_year = st.sidebar.selectbox("Select End Year",options,index= default_index)
    year_list = [selected_year - i for i in range(4, -1, -1)]

    month_list = [i for i in range(1, 13)]

    start_month = st.sidebar.selectbox("Select Start Month",month_list)
    end_month = st.sidebar.selectbox("Select End Month",month_list,index=len(month_list)-1)
    
    if start_month < 1 or start_month > 12 or end_month < 1 or end_month > 12:
        st.markedown("Month should be an integer between 1 and 12")
        raise ValueError("Month should be an integer between 1 and 12")
    
    data = common.load_json('modules/businesses.json')
    businesses = data.get('businesses', {})
    
    income_label = common.load_json('modules/labels.json')['income_statement_label']
    income_label_df = pd.DataFrame(list(income_label.items()), columns=['ac_lv4', 'Income Statement'])
    
    balance_label = common.load_json('modules/labels.json')['balance_sheet_label']
    balance_label_df = pd.DataFrame(list(balance_label.items()), columns=['ac_lv4', 'Balance Sheet'])

    
    if selected_perspective == 'Yearly':
        # Process Profit and Loss Data
        for zid, details in businesses.items():
            for project in details.get('projects', [None]):
                main_data_dict_pl[(zid, project)] = financial.process_data(zid, year_list, start_month, end_month, 'Income Statement', income_label_df, project, {'Asset', 'Liability'})
        
        # Process Balance Sheet Data
        for zid, details in businesses.items():
            for project in details.get('projects', [None]):
                main_data_dict_bs[(zid, project)] = financial.process_data(zid, year_list,start_month, end_month, 'Balance Sheet', balance_label_df, project, {'Income', 'Expenditure'})          
    # Return the dictionaries for inspection
    else:
        year = year_list[-1]
        # Process Profit and Loss Data
        for zid, details in businesses.items():
            for project in details.get('projects', [None]):
                main_data_dict_pl[(zid, project)] = financial.process_data_month(zid, year, start_month, end_month, 'Income Statement', income_label_df, project, {'Asset', 'Liability'})
        
        # Process Balance Sheet Data
        for zid, details in businesses.items():
            for project in details.get('projects', [None]):
                main_data_dict_bs[(zid, project)] = financial.process_data_month(zid, year, start_month, end_month, 'Balance Sheet', balance_label_df, project, {'Income', 'Expenditure'})


    st.title("Financial Statement Analysis")
    # choice of streamlit
    cols = st.columns(4)
    with cols[0]:
        analyse_zid = st.selectbox("Select Business",[k for k,v in main_data_dict_pl.items()],index=1)

    with cols[1]:
        selected_level = st.selectbox("Select Level",['Level 0 (More Details)','Level 1','Level 2','Level 3','Level 4','Level 5 (Summary)'],index=0)

        level_map = {'Level 0 (More Details)':['ac_code','ac_name'],'Level 1':'ac_lv1','Level 2':'ac_lv2','Level 3':'ac_lv3','Level 4':'ac_lv4','Level 5 (Summary)':'ac_lv5'}

        selected_level = level_map[selected_level]
    
    # Add a button in column 3
    if selected_level == 'ac_lv5':
        pl = main_data_dict_pl[analyse_zid]
        pl = financial.make_income_statement(pl)
        # st.write(pl,width = 800)

        bs = main_data_dict_bs[analyse_zid]
        bs = financial.make_balance_sheet(bs,pl)
        # st.write(bs,width = 800)

        cfs = financial.make_cashflow_statement(pl,bs)
        # st.write(cfs,width = 800)

        state = financial.make_three_statement(pl,bs,cfs)
        st.write(state,use_container_width=True)
        st.markdown(common.create_download_link(state), unsafe_allow_html=True)


        cols = st.columns(4)
        with cols[0]:
            selected_index = st.selectbox("Select Account",state['Description'].to_list(),index=1)

        # Select the row you want to convert into a dictionary
        selected_row = state[state['Description'] == selected_index]

        result_dict = selected_row.to_dict(orient='list') 
        first_key = list(result_dict.keys())[0]  # Get the first key
        result_dict.pop(first_key)

        common_v.plot_histogram(result_dict, selected_index)

    elif selected_level == ['ac_code','ac_name']:
        pl = main_data_dict_pl[analyse_zid]
        bs = main_data_dict_bs[analyse_zid]

        pl = pl.drop(columns=['ac_type','ac_lv1','ac_lv2','ac_lv3','ac_lv4','ac_lv5'])
        bs = bs.drop(columns=['ac_type','ac_lv1','ac_lv2','ac_lv3','ac_lv4','ac_lv5'])

        st.write(pl,use_container_width = True)
        st.markdown(common.create_download_link(pl), unsafe_allow_html=True)
        st.write(bs,use_container_width = True)
        st.markdown(common.create_download_link(bs), unsafe_allow_html=True)

        state = pd.concat([pl, bs], axis=0)
        cols = st.columns(4)
        with cols[0]:
            selected_index = st.selectbox("Select Account",state['ac_name'].to_list(),index=1)

        # Select the row you want to convert into a dictionary
        selected_row = state[state['ac_name'] == selected_index]

        result_dict = selected_row.to_dict(orient='list') 
        first_key = list(result_dict.keys())[0] 
        second_key = list(result_dict.keys())[1]  # Get the first key
        result_dict.pop(first_key)
        result_dict.pop(second_key)

        if selected_perspective == 'Monthly':
            result_dict = {f"{year}_{month}": value for (year, month), value in result_dict.items()}

        common_v.plot_histogram(result_dict, selected_index)

    else:
        pl = main_data_dict_pl[analyse_zid]
        pl = pl.groupby(selected_level).sum().sort_index().reset_index()
        st.write(pl,use_container_width = True)
        st.markdown(common.create_download_link(pl), unsafe_allow_html=True)

        bs = main_data_dict_bs[analyse_zid]
        bs = bs.groupby(selected_level).sum().sort_index().reset_index()
        st.write(bs,use_container_width = True)
        st.markdown(common.create_download_link(bs), unsafe_allow_html=True)

        state = pd.concat([pl, bs], axis=0)
        cols = st.columns(4)
        with cols[0]:
            selected_index = st.selectbox("Select Account",state[selected_level].to_list(),index=1)

        # Select the row you want to convert into a dictionary
        selected_row = state[state[selected_level] == selected_index]

        result_dict = selected_row.to_dict(orient='list') 
        first_key = list(result_dict.keys())[0] 
        # second_key = list(result_dict.keys())[1]  # Get the first key
        result_dict.pop(first_key)
        # result_dict.pop(second_key)

        result_dict = {f"{year}_{month}": value for (year, month), value in result_dict.items()}
        common_v.plot_histogram(result_dict, selected_index)
