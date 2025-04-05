from db import db_utils, sql_scripts
from modules.data_process_files import common
import streamlit as st

# modules/analytics.py

class Analytics:
    def __init__(self, table_name):
        self.data = None
        if not table_name == 'payments':
            selected_zid = int(st.session_state.zid)
        else:
            selected_zid = st.session_state.zid

        query_map = {
            "sales": sql_scripts.get_sales_data,
            "return": sql_scripts.get_return_data,
            "stock": sql_scripts.get_product_inventory_data,
            "stock_value": sql_scripts.get_inventory_value_data,
            "purchase":sql_scripts.get_purchase_data,
            "collection":sql_scripts.get_collection_data,
            "payments":sql_scripts.get_payment_data
        }
        
        if table_name == 'purchase' or table_name == 'stock' and selected_zid == 100001:
            second_zid = 100009
            data, columns = db_utils.get_data(query_map[table_name](), selected_zid, second_zid)
        else:
            data, columns = db_utils.get_data(query_map[table_name](), selected_zid)

        if data is None or columns is None:
            # Handle the None case, maybe display a message or log it
            print(data,columns)
            st.error('Error fetching data. Please check the logs for more details.')
        else:
            self.data = common.to_dataframe(data, columns)

    

