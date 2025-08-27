import streamlit as st
from streamlit_option_menu import option_menu

from components.production_request import ProductionRequestForm
from components.production_request_dashboad import ProductionDashboard

# ------------------ Initialize ------------------ #
prod_form = ProductionRequestForm()
prod_dashboard = ProductionDashboard()

st.set_page_config(
    page_title="Factory Dashboard",  # This changes the browser tab title
    page_icon="🏭",                 # Optional: emoji or path to an image
)

# ------------------ Sidebar ------------------ #
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/4/44/Google-flutter-logo.svg",
        width=150,
    )  # Example online logo
    st.title("🏭 Factory Dashboard")

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
    "<h1 style='text-align: center; color: #2E7D32;'>Welcome to the Factory Dashboard</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; font-size:16px;'>Manage production requests, track reports, and monitor equipment efficiently.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# ------------------ Production / Dashboard / Settings ------------------ #
if main_menu == "Production":
    selected_page = option_menu(
        menu_title="🚀 Production Menu",  # No title
        options=["📝 Request Form", "📊 Production Reports"],
        icons=["pencil", "bar-chart"],
        menu_icon="cast",
        orientation="horizontal",
        default_index=0,
    )

    # Render the selected page
    if selected_page == "📝 Request Form":
        prod_form.render_form()
    elif selected_page == "📊 Production Reports":
        prod_dashboard.render_dashboard()

elif main_menu == "Maintenance":
    st.info("🛠 Maintenance page coming soon!")

elif main_menu == "Settings":
    st.info("⚙️ Settings page coming soon!")

# ------------------ Quick Links Section ------------------ #
st.markdown("---")
st.subheader("🔗 Quick Links")
st.write("Quick access to commonly used sections:")

col_a, col_b = st.columns(2)
with col_a:
    if st.button("📌 Pending Requests"):
        st.info("Pending Requests page coming soon!")
    if st.button("👤 Assigned Tasks"):
        st.info("Assigned Tasks page coming soon!")

with col_b:
    if st.button("✅ Completed Requests"):
        st.info("Completed Requests page coming soon!")
    if st.button("📩 Send Notifications"):
        st.info("Send Notifications feature coming soon!")
