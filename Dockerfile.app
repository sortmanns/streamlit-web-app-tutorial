# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Copy app code
COPY src /src

# Set working directory
WORKDIR /src

# Install pipenv
RUN pip install pipenv

# Copy the Pipfile and Pipfile.lock into the container at /usr/src/app
COPY Pipfile Pipfile.lock ./

# Install dependencies using pipenv
RUN pipenv install --deploy --ignore-pipfile

# Copy the rest of your application's code
COPY . .

# Expose port you want your app on
EXPOSE 8501

# Run with multi-stage build considerations (if applicable)
ENTRYPOINT ["streamlit", "run", "./dhac_streamlit_demo/propel_auth_app.py", "--server.port=8501", "--server.address=0.0.0.0"]


