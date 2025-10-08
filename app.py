import streamlit as st
from streamlit_option_menu import option_menu

from components.production_request import ProductionRequestForm, ProductionRequestFormDB, load_production_info_data
from components.production_request_dashboad import ProductionDashboard

# ------------------ Initialize ------------------ #
prod_form = ProductionRequestForm()
prod_dashboard = ProductionDashboard()

df = load_production_info_data()
title = lambda x: df.iloc[x, 0]
logo = lambda x: df.iloc[x, 1]
st.set_page_config(
    page_title=f"{title(6)}",  # This changes the browser tab title
    page_icon=f"{title(7)}",  # Optional: emoji or path to an image
)

# ------------------ Sidebar ------------------ #
with st.sidebar:
    st.image(
        f"{logo(0)}",
        width=150,
    )  # Example online logo
    st.title(f"{title(5)}")

    main_menu = option_menu(
        menu_title="Main Menu",
        options=["Production", "Maintenance", "Settings"],
        icons=["house", "speedometer", "gear"],
        menu_icon="cast",
        default_index=0,
        orientation="vertical",
    )

# ------------------ Main Page ------------------ #
st.markdown(
    f"<h1 style='text-align: center; color: #2E7D32;'>{title(0)}</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    f"<p style='text-align: center; font-size:16px;'>{title(1)}</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ------------------ Production / Dashboard / Settings ------------------ #
if main_menu == "Production":
    selected_page = option_menu(
        menu_title=f"{title(2)}",  # No title
        options=[f"{title(3)}", f"{title(4)}"],
        icons=["pencil", "bar-chart"],
        menu_icon="cast",
        orientation="horizontal",
        default_index=0,
    )

    # Render the selected page
    if selected_page == title(3):
        prod_form.render_form()
    elif selected_page == title(4):
        prod_dashboard.render_dashboard()

elif main_menu == "Maintenance":
    st.info("🛠 Maintenance page coming soon!")

elif main_menu == "Settings":
    st.info("⚙️ Settings page coming soon!")

# ------------------ Quick Links Section ------------------ #
st.markdown("---")
st.subheader(title(8))
st.write(title(9))

col_a, col_b = st.columns(2)
with col_a:
    if st.button(title(10)):
        st.info("Pending Requests page coming soon!")
    if st.button(title(11)):
        st.info("Assigned Tasks page coming soon!")

with col_b:
    if st.button(title(12)):
        st.info("Completed Requests page coming soon!")
    if st.button(title(13)):
        st.info("Send Notifications feature coming soon!")
