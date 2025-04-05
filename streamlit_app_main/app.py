import streamlit as st
from db import db_utils
from modules import analytics
from modules import views

class BaseApp:
    def __init__(self):
        st.set_page_config(layout="wide")
        self.title = "Business Data Analysis"

    def run(self):
        self.navigation()

    def home(self):
        st.write("Welcome to the Business Data Analysis App!")

    def navigation(self):
        menu = ["Home", 
                "Overall Sales Analysis",
                "Overall Margin Analysis", 
                "YOY Analysis",
                "Purchase Analysis",
                "Collection Analysis",
                "Distribution & Histograms", 
                "Descriptive Statistics", 
                "Basket Analysis",
                "Financial Statements"
                ]
        self.current_page = st.sidebar.selectbox("Menu", menu)  # Modified this line

        if self.current_page == 'Financial Statements':
            st.sidebar.empty()
            self.financials()
        else:
            if 'zid' not in st.session_state:
                st.session_state.zid = '100001'  # Default zid

            # Dictionary of Zid
            zid_dict = {'100000' : 'GI Corporation', '100001': 'Gulshan Trading', '100005': 'Zepto Chemicals'}

            # Create a select box for zid in the sidebar or wherever you prefer
            selected_zid = st.sidebar.selectbox('Select Zid:', list(zid_dict.keys()), format_func=lambda x: zid_dict[x])
            st.session_state.zid = selected_zid  # Update the session_state with the selected zid
            
            # Display the name of the business being analyzed at the top of the page
            st.markdown(f"You are now analyzing: {zid_dict[selected_zid]}")

            if self.current_page == "Home":
                self.home()
            elif self.current_page == "Overall Sales Analysis":
                self.overall_sales_analysis()
            elif self.current_page == "Overall Margin Analysis":
                self.overall_margin_analysis()
            elif self.current_page == 'YOY Analysis':
                self.yoy_analysis()
            elif self.current_page == 'Purchase Analysis':
                self.purchase_analysis()
            elif self.current_page == 'Collection Analysis':
                self.collection_analysis()
            elif self.current_page == "Descriptive Statistics":
                self.descriptive_stats()
            elif self.current_page == 'Distribution & Histograms':
                self.histogram()
            elif self.current_page == 'Basket Analysis':
                self.basket_analysis()
            # elif self.current_page == 'Correlation Analysis':
            #     self.correlation_analysis()


    def overall_sales_analysis(self):
        views.display_overall_analysis_page(self.current_page)

    def overall_margin_analysis(self):
        views.display_margin_analysis_page(self.current_page)

    def yoy_analysis(self):
        views.display_yoy_analysis_page(self.current_page)
    
    def purchase_analysis(self):
        views.display_purchase_analysis_page(self.current_page)
    
    def collection_analysis(self):
        views.display_collection_analysis_page(self.current_page)

    def descriptive_stats(self):
        views.display_descriptive_stats_page(self.current_page)
    
    def histogram(self):
        views.display_histogram_page(self.current_page)
    
    def basket_analysis(self):
        views.display_basket_analysis_page(self.current_page)

    def financials(self):
        views.display_financial_statements(self.current_page)

    # def correlation_analysis(self):
    #     views.display_correlation_analysis_page(self.current_page)
    
if __name__ == "__main__":
    app = BaseApp()
    app.run()
