import streamlit as st

default_avatar_url = "https://ui-avatars.com/api/?name=John+Doe&background=random&size=128"

def profiles(username, role):
    st.image(default_avatar_url, width=60, caption=username)
    st.write(role)