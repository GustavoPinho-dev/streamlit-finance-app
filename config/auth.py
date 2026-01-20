import streamlit as st
import streamlit_authenticator as stauth

def autenticar():

    # Converte secrets (read-only) em dict Python comum
    credentials = {
      "usernames": {
        username: {
          "name": user["name"],
          "password": user["password"],
        }
        for username, user in st.secrets["auth"]["credentials"]["usernames"].items()
      }
    }

    cookie = st.secrets["auth"]["cookie"]

    authenticator = stauth.Authenticate(
      credentials,
      cookie["name"],
      cookie["key"],
      cookie["expire_days"],
    )

    authenticator.login()
    return authenticator
