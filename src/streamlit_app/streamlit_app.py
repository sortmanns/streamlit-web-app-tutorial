import streamlit as st
from snowflake.snowpark import functions as F
from snowflake.snowpark.types import (IntegerType, StringType,
                                      StructField, StructType)
import yaml
import uuid

from custom_auth import Auth

# Load the YAML file
with open('/src/.secrets/propelAuthKey.yaml', 'r') as file:
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


# Function for generating random patient ids
def generate_id():
    return str(uuid.uuid4())


# Connect to Snowflake
conn = st.connection('snowflake')
session = conn.session()

st.title('Patient Data Form')

# Form fields arranged in two columns
col1, col2 = st.columns(2)

# Column 1
with col1:
    gender = st.selectbox('gender', ['Male', 'Female', 'n.a.'])
    age = st.selectbox('age', [x for x in range(0, 100)])
# Column 2
with col2:
    user = st.selectbox('user', ['mysterious_user'])
    patient_id = generate_id()

# Customizing the Submit button inside st.form
with st.form(key='my_form', clear_on_submit=True):
    submit_button = st.form_submit_button('Submit', help='Click to submit the form')

    # Check if the form is submitted
    if submit_button:
        # Get form data
        form_data = {
            'gender': gender,
            'age': age,
            'user': user,
            'patient_id': patient_id,
        }

        # Define dataframe schema
        schema = StructType([
            StructField('geschlecht', StringType()),
            StructField('alter', IntegerType()),
            StructField('user', StringType()),
            StructField('patient_id', StringType()),
        ])

        # Create dataframe from form data
        df = session.createDataFrame(data=[form_data], schema=schema)

        # Add current date to dataframe. Make sure you have the right timezone here, if necessary.
        df = df.withColumn(
            'created_at',
            F.current_date(),

        )

        # Write data to Snowflake
        df.write.mode("append").save_as_table('ingress.input_data')

        # Display the result in the app. Show the user the ID for the entry, as we won't store any
        # data, which can identify the patient.
        st.write('New patients data loaded.')
        st.dataframe(df.select("*"))
        st.success('Data successfully submitted to Snowflake!')
