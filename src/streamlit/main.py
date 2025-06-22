from pathlib import Path
import os
import streamlit as st
import yaml
import time


dir_path = Path(__file__).parent
source_path = os.path.join(os.getcwd(),'source')

def run():
    page = {
        "Default":
        [
            st.Page(dir_path / "Home.py", icon="🏠"),
        ],
        "Sales":[
            st.Page(os.path.join(source_path,"Sales.py"), icon="📈"),
            st.Page(os.path.join(source_path,"SuperStore.py"), icon=":material/animation:")
        ]
    }
    pg = st.navigation(page)
    pg.run()

st.set_page_config(page_title="POC",layout = 'wide',initial_sidebar_state='auto')

run()
