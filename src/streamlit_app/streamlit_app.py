import streamlit as st
from snowflake.snowpark import functions as F
from snowflake.snowpark.types import (DoubleType, IntegerType, StringType,
                                      StructField, StructType)


# Connect to Snowflake
conn = st.connection('snowflake')
session = conn.session()

st.title('Patient Data Form')

# Form fields arranged in three columns
col1, col2 = st.columns(2)

# Column 1
with col1:
    geschlecht = st.selectbox('Geschlecht', ['Male', 'Female', 'n.a.'])
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

        schema = StructType([
            StructField('geschlecht', StringType()),
            StructField('alter', IntegerType()),
        ])

        df = session.createDataFrame(data=[form_data], schema=schema)

        df.write.mode("append").save_as_table('dhac_ingress.input_data')

        # Display the result in the app
        st.write('New patients data loaded.')
        st.dataframe(df.select("id", F.current_date().alias("created_at")))
        st.success('Data successfully submitted to Snowflake!')
