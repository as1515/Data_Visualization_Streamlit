import pandas as pd
from datetime import datetime
from db import db_utils
import streamlit as st
import numpy as np

def get_filtered_master(zid, excluded_acctypes):
    df_master = db_utils.get_gl_master(zid)
    return df_master[~df_master['ac_type'].isin(excluded_acctypes)]

def process_data_month(zid, year, start_month, end_month, label_col, label_df, project=None, account_types=None):
    df_master = get_filtered_master(zid, account_types)
    df_new = df_master.copy()

    cs_month = 1
    now = datetime.now()
    if now.month == 1:  # Check if the current month is January
        ce_month = 12  # Set the previous month to December
    else:
        ce_month = now.month - 1
    if 'Balance Sheet' in label_col:
        df = db_utils.get_gl_details(zid=zid, project=project, year=year, smonth=cs_month, emonth=ce_month, is_bs='Balance Sheet' in label_col, is_project=bool(project))
        
        for item,m in enumerate(range(int(df['month'].max())+1)):
            df_m = df[df['month']<=m].groupby(['ac_code'])['sum'].sum().reset_index().round(1)
            if item == 0:
                df_new_c = df_new.merge(df_m[['ac_code','sum']],on=['ac_code'],how='left').fillna(0).rename(columns={'sum':(year,m)})
            else:
                df_new_c = df_new_c.merge(df_m[['ac_code','sum']],on=['ac_code'],how='left').fillna(0).rename(columns={'sum':(year,m)})

        df = db_utils.get_gl_details(zid=zid, project=project, year=year-1, smonth=start_month, emonth=end_month, is_bs='Balance Sheet' in label_col, is_project=bool(project))
 
        for item,m in enumerate(range(int(df['month'].max())+1)):
            df_m = df[df['month']<=m].groupby(['ac_code'])['sum'].sum().reset_index().round(1)
            if item == 0:
                df_new = df_new.merge(df_m[['ac_code','sum']],on=['ac_code'],how='left').fillna(0).rename(columns={'sum':(year-1,m)})
            else:
                df_new = df_new.merge(df_m[['ac_code','sum']],on=['ac_code'],how='left').fillna(0).rename(columns={'sum':(year-1,m)})
        df_l = df_new_c.merge(df_new,on=['ac_code'],how='left')
        df_l = df_l.drop(['ac_name_y','ac_type_y','ac_lv1_y','ac_lv2_y','ac_lv3_y','ac_lv4_y',(year,0),(year-1,0)],axis=1).rename(columns={'ac_name_x':'ac_name','ac_type_x':'ac_type','ac_lv1_x':'ac_lv1','ac_lv2_x':'ac_lv2','ac_lv3_x':'ac_lv3','ac_lv4_x':'ac_lv4'})
        
        return df_l.merge(label_df[['ac_lv4', label_col]], on=['ac_lv4'], how='left').sort_values(['ac_type'], ascending=True).fillna(0).rename(columns={'Balance Sheet':'ac_lv5'})
    else:
        df = db_utils.get_gl_details(zid=zid, project=project, year=year, smonth=cs_month, emonth=ce_month, is_bs='Balance Sheet' in label_col, is_project=bool(project))
        if zid == '100001':
            print(df[df['ac_code']=='04010020'])
        df2 = db_utils.get_gl_details(zid=zid, project=project, year=year-1, smonth=start_month, emonth=end_month, is_bs='Balance Sheet' in label_col, is_project=bool(project))
        df = df.append(df2)
        df = df.pivot_table(['sum'],index=['ac_code'],columns=['year','month'],aggfunc='sum').reset_index()

        df_new = df.merge(df_new[['ac_code','ac_name','ac_type','ac_lv1','ac_lv2','ac_lv3','ac_lv4']],on=['ac_code'],how='right').merge(label_df[['ac_lv4','Income Statement']],on=['ac_lv4'],how='left').fillna(0)
        # Drop ('ac_code', '', '') and rename 'Income Statement_y' to 'Income Statement'
        df_new = df_new.drop(columns=[('ac_code', '', '')])
        # Rename columns ('sum', year, month) to (year, month)
        df_new.columns = [col[1:] if col[0] == 'sum' else col for col in df_new.columns]

        # Rearrange the columns
        new_columns = ['ac_code', 'ac_name', 'ac_type', 'ac_lv1', 'ac_lv2', 'ac_lv3', 'ac_lv4'] + sorted([col for col in df_new.columns if isinstance(col, tuple)]) + ['Income Statement']
        df_new = df_new[new_columns]
        return df_new.rename(columns={'Income Statement':'ac_lv5'})

def process_data(zid, year_list, start_month, end_month, label_col, label_df, project=None, account_types=None):
    df_master = get_filtered_master(zid, account_types)
    df_new = df_master.copy()
    
    for item, year in enumerate(year_list):
        df = db_utils.get_gl_details(
            zid=zid, 
            project=project, 
            year=year, 
            smonth=start_month, 
            emonth=end_month, 
            is_bs='Balance Sheet' in label_col, 
            is_project=bool(project)
        )
        
        df = df.groupby(['ac_code'])['sum'].sum().reset_index().round(1)
        col_name = year if item == 0 else f'{year}'
        df_new = df_new.merge(df[['ac_code', 'sum']], left_on='ac_code', right_on='ac_code', how='left').rename(columns={'sum': col_name}).fillna(0)
    
    # Ensure all years are in the columns of df_new
    for year in year_list:
        col_name = year if year == year_list[0] else f'{year}'
        if col_name not in df_new.columns:
            df_new[col_name] = 0.0  # Fill with zeros if no data for that year
    if 'Balance Sheet' in label_col:
        return df_new.merge(label_df[['ac_lv4', label_col]], on=['ac_lv4'], how='left').sort_values(['ac_type'], ascending=True).rename(columns={'Balance Sheet':'ac_lv5'})
    else:
        return df_new.merge(label_df[['ac_lv4', label_col]], on=['ac_lv4'], how='left').sort_values(['ac_type'], ascending=True).rename(columns={'Income Statement':'ac_lv5'})

def make_income_statement(df_i):
    df_i = df_i.groupby(['ac_lv5']).sum().reset_index().rename(columns={'index':'ac_lv5'}).round(1)
    df_i.loc[len(df_i.index),:]=df_i.sum(axis=0,numeric_only = True)
    df_i.at[len(df_i.index)-1,'ac_lv5'] = '10-1-Net Income'
    df_i = df_i
    
    if ~df_i['ac_lv5'].isin(['06-1-Unusual Expenses (Income)']).any():
        new = ['06-1-Unusual Expenses (Income)']
        df_i = df_i.append(pd.Series(new, index=df_i.columns[:len(new)]), ignore_index=True)
    new = ['02-2-Gross Profit']
    df_i = df_i.append(pd.Series(new, index=df_i.columns[:len(new)]), ignore_index=True)
    new = ['07-2-EBIT']
    df_i = df_i.append(pd.Series(new, index=df_i.columns[:len(new)]), ignore_index=True)
    new = ['08-2-EBT']
    df_i = df_i.append(pd.Series(new, index=df_i.columns[:len(new)]), ignore_index=True)
    
    df_i = df_i.set_index('ac_lv5').fillna(0)
    try:
        df_i.loc['02-2-Gross Profit'] = df_i.loc['01-1-Revenue']+df_i.loc['02-1-Cost of Revenue']
        try:
            df_i.loc['07-2-EBIT'] = df_i.loc['02-2-Gross Profit'] + df_i.loc['03-1-Office & Administrative Expenses'] + df_i.loc['04-1-Sales & Distribution Expenses'] + df_i.loc['05-1-Depreciation/Amortization'] + df_i.loc['06-1-Unusual Expenses (Income)'] + df_i.loc['07-1-Other Operating Expenses, Total'] + df_i.loc['04-2-MRP Discount'] + df_i.loc['04-3-Discount Expense']
        except Exception as e:
            df_i.loc['07-2-EBIT'] = df_i.loc['02-2-Gross Profit'] + df_i.loc['03-1-Office & Administrative Expenses'] + df_i.loc['04-1-Sales & Distribution Expenses'] + df_i.loc['05-1-Depreciation/Amortization'] + df_i.loc['06-1-Unusual Expenses (Income)'] + df_i.loc['07-1-Other Operating Expenses, Total'] + df_i.loc['04-2-MRP Discount']
            st.markdown(e)
        df_i.loc['08-2-EBT'] = df_i.loc['07-2-EBIT'] + df_i.loc['08-1-Interest Expense']
        df_i = df_i.sort_index().reset_index()
    except Exception as e:
        st.markdown('Income Statement Error')
        st.markdown(e)
        pass
    return df_i.applymap(lambda x: round(x) if isinstance(x, (int, float)) else x).fillna(0)

def make_balance_sheet(df_b,df_i):
    df_b = df_b.groupby(['ac_lv5']).sum().reset_index().round(1)
    df_b.loc[len(df_b.index),:]=df_b.sum(axis=0,numeric_only = True)
    df_b.at[len(df_b.index)-1,'ac_lv5'] = 'Balance'
    
    new = ['01-1-Assets']
    df_b = df_b.append(pd.Series(new, index=df_b.columns[:len(new)]), ignore_index=True)
    new = ['01-2-Current Assets']
    df_b = df_b.append(pd.Series(new, index=df_b.columns[:len(new)]), ignore_index=True)
    new = ['04-2-Total Current Assets']
    df_b = df_b.append(pd.Series(new, index=df_b.columns[:len(new)]), ignore_index=True)
    new = ['04-3-Non-Current Assets']
    df_b = df_b.append(pd.Series(new, index=df_b.columns[:len(new)]), ignore_index=True)
    new = ['07-2-Total Non-Current Assets']
    df_b = df_b.append(pd.Series(new, index=df_b.columns[:len(new)]), ignore_index=True)
    new = ['07-3-Current Liabilities']
    df_b = df_b.append(pd.Series(new, index=df_b.columns[:len(new)]), ignore_index=True)
    new = ['11-2-Total Current Liabilities']
    df_b = df_b.append(pd.Series(new, index=df_b.columns[:len(new)]), ignore_index=True)
    new = ['11-4-Non-Current Liabilities']
    df_b = df_b.append(pd.Series(new, index=df_b.columns[:len(new)]), ignore_index=True)
    new = ['12-2-Total Non-Current Liabilities']
    df_b = df_b.append(pd.Series(new, index=df_b.columns[:len(new)]), ignore_index=True)
    new = ['13-2-Retained Earnings']
    df_b = df_b.append(pd.Series(new, index=df_b.columns[:len(new)]), ignore_index=True)
    new = ['13-3-Balance Check']
    df_b = df_b.append(pd.Series(new, index=df_b.columns[:len(new)]), ignore_index=True)
    
    
    df_b = df_b.set_index('ac_lv5').fillna(0)
    # df_b = df_b[sorted(df_b.columns), key=lambda x: str(x)] 
    try:
        df_b.loc['04-2-Total Current Assets'] = df_b.loc['01-3-Cash']+df_b.loc['02-1-Accounts Receivable']+df_b.loc['03-1-Inventories']+df_b.loc['04-1-Prepaid Expenses']
        df_b.loc['07-2-Total Non-Current Assets'] = df_b.loc['05-1-Other Assets']+df_b.loc['06-1-Property, Plant & Equipment']+df_b.loc['07-1-Goodwill & Intangible Asset']
        df_b.loc['11-2-Total Current Liabilities'] = df_b.loc['08-1-Accounts Payable']+df_b.loc['09-1-Accrued Liabilities']+df_b.loc['10-1-Other Short Term Liabilities']+df_b.loc['11-1-Debt']
        df_b.loc['12-2-Total Non-Current Liabilities'] = df_b.loc['12-1-Other Long Term Liabilities']
        df1 = df_i.set_index('ac_lv5')
        df_b.loc['13-2-Retained Earnings'] = df1.loc['10-1-Net Income']
        df_b.loc['13-3-Balance Check'] = df_b.loc['04-2-Total Current Assets'] + df_b.loc['07-2-Total Non-Current Assets'] + df_b.loc['11-2-Total Current Liabilities'] + df_b.loc['12-2-Total Non-Current Liabilities'] + df_b.loc['13-1-Total Shareholders Equity'] + df_b.loc['13-2-Retained Earnings']
    except Exception as e:
        st.markdown('Balance Sheet Error')
        st.markdown(e)
        pass
    
    
    # Sort the DataFrame based on the 'ac_lv5' column
    # Reset the index before sorting
    # st.markdown(df_b['ac_lv5'])
    df_b.index = df_b.index.astype(str)
    df_b = df_b.sort_index().reset_index().round(0)  # Sort based on the 'ac_lv5' column
    return df_b.applymap(lambda x: round(x) if isinstance(x, (int, float)) else x).fillna(0)

def make_cashflow_statement(df_i,df_b):
    df_i2= df_i.set_index('ac_lv5').replace('-',0)
    df_b2 = df_b.set_index('ac_lv5').replace('-',0)
    df_b22 = df_b2
    #create a temporary dataframe which caluclates the difference between the 2 years
    df_b2 = df_b2.diff(axis=1).fillna(0)
    
    df2 = pd.DataFrame(columns=df_b.columns).rename(columns={'ac_lv5':'Description'})
    
    new = ['01-Operating Activities']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)
    new = ['02-Net Income']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)
    new = ['03-Depreciation and amortization']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)
    new = ['04-1-Accounts Receivable']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)
    new = ['04-2-Inventories']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)
    new = ['04-3-Prepaid Expenses']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)

    new = ['05-1-Accounts Payable']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)
    new = ['05-2-Accrued Liabilities']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)
    new = ['05-3-Other Short Term Liabilities']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)
    new = ['06-Other operating cash flow adjustments']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    new = ['07-Total Operating Cashflow']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    new = ['08']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    
    #investing cashflow
    new = ['09-Investing Cashflow']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    new = ['10-Capital asset acquisitions/disposal']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    new = ['11-Other investing cash flows']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    new = ['12-Total Investing Cashflow']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    new = ['13']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           

    #financing cashflow
    new = ['14-Financing Cashflow']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    new = ['15-Increase/Decrease in Debt']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    new = ['16-Increase/Decrease in Equity']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    new = ['16-1-Increase/Decrease in Retained Earning']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    new = ['17-Other financing cash flows']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    new = ['18-Total Financing Cashflow']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    new = ['19']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    
    ##change in cash calculations
    new = ['20-Year Opening Cash']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    new = ['21-Change in Cash']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)                           
    new = ['22-Year Ending Cash']
    df2 = df2.append(pd.Series(new, index=df2.columns[:len(new)]), ignore_index=True)
    
    df2 = df2.set_index('Description')
    
    try:
        #operating cashflow calculations
        df2.loc['02-Net Income'] = df_i2.loc['10-1-Net Income']
        df2.loc['03-Depreciation and amortization'] = df_i2.loc['05-1-Depreciation/Amortization']

        df2.loc['04-1-Accounts Receivable'] = df_b2.loc['02-1-Accounts Receivable']
        df2.loc['04-2-Inventories'] = df_b2.loc['03-1-Inventories']
        df2.loc['04-3-Prepaid Expenses'] = df_b2.loc['04-1-Prepaid Expenses']

        df2.loc['05-1-Accounts Payable'] = df_b2.loc['08-1-Accounts Payable']
        df2.loc['05-2-Accrued Liabilities'] = df_b2.loc['09-1-Accrued Liabilities']
        df2.loc['05-3-Other Short Term Liabilities'] = df_b2.loc['10-1-Other Short Term Liabilities']
        
        df2.loc['06-Other operating cash flow adjustments'] = 0
        df2.loc['07-Total Operating Cashflow'] = df2.loc['02-Net Income'] + df2.loc['03-Depreciation and amortization'] + df2.loc['04-1-Accounts Receivable'] + df2.loc['04-2-Inventories'] + df2.loc['04-3-Prepaid Expenses'] + df2.loc['05-1-Accounts Payable'] + df2.loc['05-2-Accrued Liabilities'] + df2.loc['05-3-Other Short Term Liabilities']
        
        #investing cashflow calculations
        df2.loc['10-Capital asset acquisitions/disposal'] = df_b2.loc['07-2-Total Non-Current Assets']
        df2.loc['11-Other investing cash flows'] = 0
        df2.loc['12-Total Investing Cashflow'] = df2.loc['10-Capital asset acquisitions/disposal'] + df2.loc['11-Other investing cash flows']

        #financing cashflow calculations
        df2.loc['15-Increase/Decrease in Debt'] = df_b2.loc['11-1-Debt']
        df2.loc['16-Increase/Decrease in Equity'] = df_b2.loc['13-1-Total Shareholders Equity']
        df2.loc['16-1-Increase/Decrease in Retained Earning'] = df_b2.loc['13-2-Retained Earnings']
        df2.loc['17-Other financing cash flows'] = df_b2.loc['12-2-Total Non-Current Liabilities']
        df2.loc['18-Total Financing Cashflow'] = df2.loc['15-Increase/Decrease in Debt'] + df2.loc['16-Increase/Decrease in Equity'] + df2.loc['16-1-Increase/Decrease in Retained Earning'] + df2.loc['17-Other financing cash flows']
        
        ##change in cash calculations
        df2.loc['20-Year Opening Cash'] = df_b22.loc['01-3-Cash'].shift(periods=1,axis=0)
        df2.loc['21-Change in Cash'] = -(df2.loc['07-Total Operating Cashflow'] + df2.loc['12-Total Investing Cashflow'] + df2.loc['18-Total Financing Cashflow'] - df2.loc['16-1-Increase/Decrease in Retained Earning'] - df2.loc['03-Depreciation and amortization'])
        df2.loc['22-Year Ending Cash'] = df2.loc['20-Year Opening Cash'] + df2.loc['21-Change in Cash']
    except Exception as e:
        st.markdown(e)
        pass
    
    df_c = df2.sort_index().reset_index().fillna(0)
    return df_c.applymap(lambda x: round(x) if isinstance(x, (int, float)) else x)

def make_three_statement(df_i,df_b,df_c):
    df_i3 = df_i.rename(columns={'ac_lv5':'Description'})
    df_b3 = df_b.rename(columns={'ac_lv5':'Description'})
    # df_ap3 = ap_final_dict[key].rename(columns={'AP_TYPE':'Description'})
    # df12 = pd.concat([df_i3,df_b3,df_ap3,df_c]).reset_index(drop=True)
    df12 = pd.concat([df_i3,df_b3,df_c]).reset_index(drop=True)
    daysinyear = 365
    #ratios
    new = ['Ratios']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['COGS Ratio']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Gross Profit Ratio']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Operating Profit']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Net Profit Ratio']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)

    ##coverages
    new = ['Tax Coverage']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Interest Coverage']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)

    #expense ratios
    new = ['OAE Ratio']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['S&D Ratio']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Deprication Ratio']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Unusual Expense Ratio']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Other Operating Ratio']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Interest Ratio']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Tax Ratio']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)

    #efficiency ratios
    new = ['Quick Ratio']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Quick Ratio Adjusted']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Current Ratio']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Current Ratio Adjusted']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)

    #asset ratios
    new = ['Total Asset Turnover Ratio']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Net Asset Turnover Ratio']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)

    #working capital days
    new = ['Inventory Turnover']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Inventory Days']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Accounts Receivable Turnover']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Accounts Receivable Days']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Accounts Payable Turnover']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Accounts Payable Turnover*']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Accounts Payable Days']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Accounts Payable Days*']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)

    #other ratios
    new = ['PP&E Ratio']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Working Capital Turnover']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Working Capital Turnover*']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)

    #debt ratios
    new = ['Cash Turnover']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Debt/Equity']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Debt/Capital']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Debt/TNW']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Total Liabilities/Equity']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Total Liabilities/Equity*']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Total Assets to Equity']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)


    new = ['Debt/EBITDA']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Capital Structure Impact']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Acid Test']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['Acid Test*']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['ROE']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)
    new = ['ROA']
    df12 = df12.append(pd.Series(new, index=df12.columns[:len(new)]), ignore_index=True)

    df12 = df12.set_index('Description').replace(0,np.nan)
    #ratio calculation
    try:
        ##profitability ratios
        df12.loc['COGS Ratio'] = df12.loc['02-1-Cost of Revenue']*100/df12.loc['01-1-Revenue']
        df12.loc['Gross Profit Ratio'] = df12.loc['02-2-Gross Profit']*100/df12.loc['01-1-Revenue']
        df12.loc['Operating Profit'] = df12.loc['07-2-EBIT']*100/df12.loc['01-1-Revenue']
        df12.loc['Net Profit Ratio'] = df12.loc['10-1-Net Income']*100/df12.loc['01-1-Revenue']

        ##coverages
        df12.loc['Tax Coverage'] = df12.loc['09-1-Income Tax & VAT']*100/df12.loc['08-2-EBT']
        df12.loc['Interest Coverage'] = df12.loc['08-1-Interest Expense']*100/df12.loc['07-2-EBIT']

        #expense ratios
        df12.loc['OAE Ratio'] = df12.loc['03-1-Office & Administrative Expenses']*100/df12.loc['01-1-Revenue']
        df12.loc['S&D Ratio'] = df12.loc['04-1-Sales & Distribution Expenses']*100/df12.loc['01-1-Revenue']
        df12.loc['Deprication Ratio'] = df12.loc['05-1-Depreciation/Amortization']*100/df12.loc['01-1-Revenue']
        df12.loc['Unusual Expense Ratio'] = df12.loc['06-1-Unusual Expenses (Income)']*100/df12.loc['01-1-Revenue']
        df12.loc['Other Operating Ratio'] = df12.loc['07-1-Other Operating Expenses, Total']*100/df12.loc['01-1-Revenue']
        df12.loc['Interest Ratio'] = df12.loc['08-1-Interest Expense']*100/df12.loc['01-1-Revenue']
        df12.loc['Tax Ratio'] = df12.loc['09-1-Income Tax & VAT']*100/df12.loc['01-1-Revenue']

        #efficiency ratios
        df12.loc['Quick Ratio'] = df12.loc['04-2-Total Current Assets']/df12.loc['11-2-Total Current Liabilities']
        # df12.loc['Quick Ratio Adjusted'] = df12.loc['04-2-Total Current Assets']/(df12.loc['11-2-Total Current Liabilities']-df12.loc['EXTERNAL'])
        df12.loc['Current Ratio'] = df12.loc['04-2-Total Current Assets']/df12.loc['11-2-Total Current Liabilities']
        # df12.loc['Current Ratio Adjusted'] = df12.loc['04-2-Total Current Assets']/(df12.loc['11-2-Total Current Liabilities']-df12.loc['EXTERNAL'])

        #asset ratios
        df12.loc['Total Asset Turnover Ratio'] = df12.loc['01-1-Revenue']/(df12.loc['04-2-Total Current Assets']+df12.loc['07-2-Total Non-Current Assets'])
        df12.loc['Net Asset Turnover Ratio'] = df12.loc['01-1-Revenue']/(df12.loc['04-2-Total Current Assets']+df12.loc['07-2-Total Non-Current Assets']+df12.loc['11-2-Total Current Liabilities']+df12.loc['12-2-Total Non-Current Liabilities'])

        #working capital days
        df12.loc['Inventory Turnover'] = df12.loc['02-1-Cost of Revenue']/df12.loc['03-1-Inventories']
        df12.loc['Inventory Days'] = df12.loc['03-1-Inventories']*daysinyear/df12.loc['02-1-Cost of Revenue']
        df12.loc['Accounts Receivable Turnover'] = df12.loc['01-1-Revenue']/df12.loc['02-1-Accounts Receivable']
        df12.loc['Accounts Receivable Days'] = df12.loc['02-1-Accounts Receivable']*daysinyear/df12.loc['01-1-Revenue']
        df12.loc['Accounts Payable Turnover'] = df12.loc['02-1-Cost of Revenue']/df12.loc['08-1-Accounts Payable']
        # df12.loc['Accounts Payable Turnover*'] = df12.loc['02-1-Cost of Revenue']/df12.loc['EXTERNAL']
        df12.loc['Accounts Payable Days'] = df12.loc['08-1-Accounts Payable']*daysinyear/df12.loc['02-1-Cost of Revenue']
        # df12.loc['Accounts Payable Days*'] = df12.loc['EXTERNAL']*daysinyear/df12.loc['02-1-Cost of Revenue']

        #other ratios
        df12.loc['PP&E Ratio'] = df12.loc['06-1-Property, Plant & Equipment']/df12.loc['01-1-Revenue']
        df12.loc['Working Capital Turnover'] = df12.loc['01-1-Revenue']/(df12.loc['02-1-Accounts Receivable']+df12.loc['03-1-Inventories']+df12.loc['08-1-Accounts Payable'])
        # df12.loc['Working Capital Turnover*'] = df12.loc['01-1-Revenue']/(df12.loc['02-1-Accounts Receivable']+df12.loc['03-1-Inventories']+df12.loc['EXTERNAL'])

        total_debt = df12.loc['11-1-Debt'] + df12.loc['10-1-Other Short Term Liabilities'] + df12.loc['12-1-Other Long Term Liabilities']
        #debt ratios
        df12.loc['Cash Turnover'] = df12.loc['01-1-Revenue']/df12.loc['01-3-Cash']
        df12.loc['Debt/Equity'] = total_debt/(df12.loc['13-1-Total Shareholders Equity'])
        df12.loc['Debt/Capital'] = total_debt/(df12.loc['13-1-Total Shareholders Equity']-total_debt)
        df12.loc['Debt/TNW'] = total_debt/(df12.loc['07-2-Total Non-Current Assets']-df12.loc['07-1-Goodwill & Intangible Asset'])
        df12.loc['Total Liabilities/Equity'] = (df12.loc['11-2-Total Current Liabilities']+df12.loc['12-2-Total Non-Current Liabilities'])/(df12.loc['13-1-Total Shareholders Equity']-total_debt)
        # df12.loc['Total Liabilities/Equity*'] = (df12.loc['11-2-Total Current Liabilities']-df12.loc['EXTERNAL']+df12.loc['12-2-Total Non-Current Liabilities'])/(df12.loc['13-1-Total Shareholders Equity']-total_debt)
        df12.loc['Total Assets to Equity'] = (df12.loc['04-2-Total Current Assets']+df12.loc['07-2-Total Non-Current Assets'])/df12.loc['13-1-Total Shareholders Equity']

        df12.loc['Debt/EBITDA'] = total_debt/(df12.loc['07-2-EBIT']+df12.loc['05-1-Depreciation/Amortization'])
        df12.loc['Capital Structure Impact'] = df12.loc['08-2-EBT']/df12.loc['07-2-EBIT']
        df12.loc['Acid Test'] = (df12.loc['04-2-Total Current Assets']-df12.loc['03-1-Inventories'])/df12.loc['11-2-Total Current Liabilities']
        # df12.loc['Acid Test*'] =(df12.loc['04-2-Total Current Assets']-df12.loc['03-1-Inventories'])/(df12.loc['11-2-Total Current Liabilities']-df12.loc['EXTERNAL'])
        df12.loc['ROE'] = df12.loc['10-1-Net Income']/df12.loc['13-1-Total Shareholders Equity']
        df12.loc['ROA'] = df12.loc['10-1-Net Income']/(df12.loc['04-2-Total Current Assets']+df12.loc['07-2-Total Non-Current Assets'])
    except Exception as e:
        st.markdown(e)
        pass
    
    df12 = (df12*-1).round(3).reset_index().fillna(0)

    return df12.applymap(lambda x: round(x) if isinstance(x, (int, float)) else x)