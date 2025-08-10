from components.production_request import data_loader, option_menu, request_form, st
from components.production_request_dashboad import dashboard

with st.sidebar:
    options = option_menu(
        menu_title=None,
        options=["Production", "Maintenance", "Settings"],
        icons=["house", "speedometer", "gear"],
        styles={
            "container": {"padding": "0!important", "background-color": "#f8f9fa"},
            "icon": {"color": "blue", "font-size": "18px"},
            "nav-link": {"font-size": "14px", "text-align": "center", "margin": "0px"},
            "nav-link-selected": {"background-color": "#02ab21"},
        },
    )
if options == "Production":
    selected = option_menu(
        menu_title=None,  # No title
        options=["Request Form", "Reports"],
        icons=["pencil", "bar-chart"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#f8f9fa"},
            "icon": {"color": "blue", "font-size": "18px"},
            "nav-link": {"font-size": "14px", "text-align": "center", "margin": "0px"},
            "nav-link-selected": {"background-color": "#02ab21"},
        },
    )

    if selected == "Request Form":
        st.set_page_config(
            page_title="KFP", layout="centered", initial_sidebar_state="auto"
        )
        request_form()
    elif selected == "Reports":
        st.set_page_config(
            page_title="KFP", layout="wide", initial_sidebar_state="auto"
        )

        dashboard()
