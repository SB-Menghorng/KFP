from components.production_request import data_loader, option_menu, request_form, st
from components.production_request_dashboad import dashboard
# from auth.authentication import get_authenticator, stauth

# authenticator, worksheet = get_authenticator()

with st.sidebar:
    options = option_menu(
        menu_title=None,
        options=["Production", "Maintenance", "Settings"],
        icons=["house", "speedometer", "gear"],
    )
if options == "Production":
    selected = option_menu(
        menu_title=None,
        options=["Request Form", "Reports"],
        icons=["pencil", "bar-chart"],
        orientation="horizontal",
    )
    if selected == "Request Form":
        request_form()
    elif selected == "Reports":
        dashboard()

