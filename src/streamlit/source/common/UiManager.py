import streamlit as st

# --- UI Components ---
class UIComponents:

    @staticmethod
    def format_value(val: int) -> str:
        if val >= 1_000_000:
            return f"{round(val/1_000_000,2)}M"
        if val >= 1_000:
            return f"{round(val/1_000,2)}K"
        return str(val)
    
    @staticmethod
    def format_compare(val: int) -> str:
        return f"{round((val * 100),2)}%"

    @staticmethod
    def render_metrics(metrics: dict[str, int], compare: str, type: str):
        cols = st.columns(len(metrics)+1)
        with cols[0]:
            with st.container(border=True,height=130):
                st.metric(label=type ,value=type ,label_visibility="hidden")
        for idx, (title, val) in enumerate(metrics.items()):
            with cols[idx+1]:
                with st.container(border=True,height=130):
                    formatted = UIComponents.format_value(val)
                    formatted_compare = UIComponents.format_compare(compare[idx])
                    st.metric(title.capitalize(), formatted, delta = formatted_compare)