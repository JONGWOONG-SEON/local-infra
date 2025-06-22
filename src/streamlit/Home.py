import streamlit as st
import streamlit_authenticator as stauth

st.write("# 검증용")


st.markdown(
    """  
    안녕하세요. 검증용 BI 입니다.
    문의사항이 있으시면 dominic.seon@cheilpengtai.com 으로 연락바랍니다.
"""
)
st.page_link("http://www.google.com", label="Google", icon="🌎")
st.page_link("http://www.naver.com", label="Naver")

print(st.session_state)
