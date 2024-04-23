import streamlit as st
from snowflake.snowpark import functions as F
from snowflake.snowpark.types import (IntegerType, StringType,
                                      StructField, StructType)
import yaml

from custom_auth import Auth

# Load the YAML file
with open('/Users/sortmanns/git/work/streamlit-web-app-tutorial/src/.secrets/propelAuthKey.yaml', 'r') as file:
    data = yaml.safe_load(file)

api_key = data['api_key']
auth_url = data['auth_url']

auth = Auth(
    auth_url,
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
