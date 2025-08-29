import streamlit as st
from streamlit_option_menu import option_menu

from components.production_request import ProductionRequestForm
from components.production_request_dashboad import ProductionDashboard

# ------------------ Initialize ------------------ #
prod_form = ProductionRequestForm()
prod_dashboard = ProductionDashboard()

st.set_page_config(
    page_title="Kirirom Food Production",  # This changes the browser tab title
    page_icon="🏭",  # Optional: emoji or path to an image
)

# ------------------ Sidebar ------------------ #
with st.sidebar:
    st.image(
        "data:image/jpeg;base64,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",
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
