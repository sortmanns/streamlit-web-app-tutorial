import streamlit as st
from snowflake.snowpark import functions as F
from snowflake.snowpark.types import (IntegerType, StringType,
                                      StructField, StructType)

import requests
import yaml
from propelauth_py import UnauthorizedException, init_base_auth
from streamlit.web.server.websocket_headers import _get_websocket_headers


# Load the YAML file
with open('/Users/sortmanns/git/work/dhac_streamlit_demo/src/.secrets/propelAuthKey.yaml', 'r') as file:
    data = yaml.safe_load(file)

api_key = data['api_key']


class Auth:
    def __init__(self, auth_url, integration_api_key):
        self.auth = init_base_auth(auth_url, integration_api_key)
        self.auth_url = auth_url
        self.integration_api_key = integration_api_key

    def get_user(self):
        access_token = get_access_token()

        if not access_token:
            return None

        try:
            return self.auth.validate_access_token_and_get_user("Bearer " + access_token)
        except UnauthorizedException as err:
            print("Error validating access token", err)
            return None

    def get_account_url(self):
        return self.auth_url + "/account"

    def logout(self):
        refresh_token = get_refresh_token()
        if not refresh_token:
            return False

        logout_body = {"refresh_token": refresh_token}
        url = f"{self.auth_url}/api/backend/v1/logout"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.integration_api_key,
        }

        response = requests.post(url, json=logout_body, headers=headers)

        return response.ok


def get_access_token():
    return get_cookie("__pa_at")


def get_refresh_token():
    return get_cookie("__pa_rt")


def get_cookie(cookie_name):
    headers = _get_websocket_headers()
    if headers is None:
        return None

    cookies = headers.get("Cookie") or headers.get("cookie") or ""
    for cookie in cookies.split(";"):
        split_cookie = cookie.split("=")
        if len(split_cookie) == 2 and split_cookie[0].strip() == cookie_name:
            return split_cookie[1].strip()

    return None


auth = Auth(
    "https://560282212.propelauthtest.com",
    api_key,
)

user = auth.get_user()
if user is None:
    st.error("Unauthorized")
    st.stop()

# Connect to Snowflake
conn = st.connection('snowflake')
session = conn.session()

st.title('Patient Data Form')

# Form fields arranged in two columns
col1, col2 = st.columns(2)

# Column 1
with col1:
    geschlecht = st.selectbox('Geschlecht', ['Male', 'Female', 'n.a.'])
# Column 2
with col2:
    alter = st.selectbox('Alter', [x for x in range(0, 100)])

# Customizing the Submit button inside st.form
with st.form(key='my_form', clear_on_submit=True):
    submit_button = st.form_submit_button('Submit', help='Click to submit the form')

    # Check if the form is submitted
    if submit_button:
        # Get form data
        form_data = {
            'geschlecht': geschlecht,
            'alter': alter,
        }

        # Define dataframe schema
        schema = StructType([
            StructField('geschlecht', StringType()),
            StructField('alter', IntegerType()),
        ])

        df = session.createDataFrame(data=[form_data], schema=schema)

        df.write.mode("append").save_as_table('ingress.input_data')

        # Display the result in the app
        st.write('New patients data loaded.')
        st.dataframe(df.select("id", F.current_date().alias("created_at")))
        st.success('Data successfully submitted to Snowflake!')
