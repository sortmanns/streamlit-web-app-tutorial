# Implementierung einer KI App im Gesundheitswesen
In einer Welt, in der die Digitalisierung in allen Lebensbereichen zunehmend 
an Bedeutung gewinnt, ist das Gesundheitswesen kein Ausnahmefall. 
Der Einsatz von künstlicher Intelligenz (KI) im Gesundheitswesen verspricht, 
einige der drängendsten Probleme zu lösen, 
mit denen der Sektor heute konfrontiert ist: 
Fachkräftemangel und Unterfinanzierung. 
Durch die Automatisierung von Routineaufgaben und die Bereitstellung 
fortschrittlicher Diagnosetools kann KI medizinisches Personal entlasten 
und die Effizienz steigern. 
</br></br>
Das ultimative Ziel dieser Blogpostserie ist die Bereitstellung eines 
Machine Learning (ML) Modells innerhalb einer Web App, 
die nicht nur die Funktionen des Modells zugänglich macht, 
sondern auch die Sammlung neuer Trainingsdaten ermöglicht. 
Dies schafft eine Grundlage für kontinuierliches Lernen und Verbesserung 
der KI-Leistung.
</br></br>
Um dieses Ziel zu erreichen, müssen wir eine Reihe von Anforderungen erfüllen:
- Ein einfaches, zweckorientiertes Frontend, das für Nutzer intuitiv zu bedienen und für den Entwickler leicht wartbar ist.
- Nutzermanagement nach Industriestandards, um eine sichere und regulierte Zugriffssteuerung zu gewährleisten.
- GDPR-konforme Datenverarbeitung medizinischer Daten, um den Datenschutz und die Sicherheit der Patienteninformationen zu gewährleisten.
- Skalierbarkeit und einfache Wartung der Lösung, um zukünftiges Wachstum und Entwicklungen zu unterstützen.
- Sichere Zugänglichkeit über das öffentliche Internet, um eine breite Nutzbarkeit zu ermöglichen.
</br></br>

Zur Erfüllung dieser Anforderungen, werden wir einen modernen Techstack nutzen,
welcher uns die nötige Flexibilität und Performance bietet. Im Einzelnen werden 
wir folgende Technologien einsetzen:
- Streamlit für einfaches Frontend-Development.
- Propelauth für Security und Nutzermanagement.
- Google Cloud Platform (GCP) für ein skalierbares, kostengünstiges Deployment.
- Artifact Registry zum Verwalten der Docker-Images.
- Secret Manager zum Verwalten und Ausspielen der Secrets.
- Cloud Run Sidecar Containers zum Deployen der Microservices.
- Snowflake als Datenbank.
- Python und SciKit Learn für die Machine Learning Komponente.

Im ersten Teil des Blogposts implementieren wir ein Dummy Streamlit App und sichern diese
mit einem Proxyserver und Propelauth.

## 1.1 Lokales Streamlit Deployment mit Snowflake als Datenbank
Für die lokale Entwicklung setzen zuerst ein Virtual Environment (Venv) mit Pipenv oder
dem Virtualisierungstool eurer Wahl auf. Dafür legen wir eine Pipfile im 
Wurzelverzeichnis unseres Projektes an.
``` [Pipfile]
[[source]]
url = "https://pypi.org/simple"
verify_ssl = true
name = "pypi"

[packages]
streamlit = "*"
pandas = "*"
snowflake-connector-python = "*"
snowflake-snowpark-python = "*"

[requires]
python_version = "3.10.13"
```
Dann können wir unsere Venv mit nur einem Befehl aus dem Terminal anlegen.
```bash
pipenv install
```
Nun legen wir unser Streamlit Skript an.
```python
import streamlit as st
from snowflake.snowpark import functions as F
from snowflake.snowpark.types import (IntegerType, StringType,
                                      StructField, StructType)


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
```
Die Methode `st.connection('snowflake')` wird unter `.streamlit` 
nach einer `secrets.toml` suchen. In dieser sollte es dann einen Abschnitt mit
den Snowflake Credentials geben.
```toml
[connections.snowflake]
account = "..."
user = "..."
password = "..."
role = "..."
warehouse = "..."
database = "..."
schema = "..."
client_session_keep_alive = true
```
Im besten Fall legt euch euer Snowflake Admin einen technischen Nutzer für
die App an, um das Prinzip der geringsten Privilegien umzusetzen.
</br></br>
Ihr solltet nun die Streamlit App mit folgendem Befehl aus dem Wurzelverzeichnis
ausführen können.
```bash
pipenv run streamlit run src/streamlit_app/streamlit_app.py
```

### 1.2 Authentifizierung und Nutzermanagement
Für State-of-the-Art Authentifizierung setzen wir auf einen Proxyserver und Propelauth
als Identity Provider und Nutzermanagement Tool. Für ein detailliertes Tutorial zu 
Streamlit und Propelauth verweisen wir auf diesen [Blogpost](todo). Wir werden die einzelnen 
Schritte hier zusammenfassen und um das Feature erweitern, den API-Key von einer YAML Datei 
aus einzulesen. 
</br></br>
Im ersten Schritt besucht ihr die Propelauth Website und erstellt einen Account. Folgt dann den
Anweisungen zum Erstellen eines Projektes. Danach initialisiert ihr ein Node Projekt in eurem 
Wurzelverzeichnis mit dem Befehl 
```bash
npm i @propelauth/auth-proxy
```
Als Nächstes legt unter `src` einen Ordner `proxy`an und in diesem eine Datei `proxy.mjs`.
```node
import { initializeAuthProxy } from '@propelauth/auth-proxy'

// Replace with your configuration
await initializeAuthProxy({
    authUrl: "YOUR_AUTH_URL",
    integrationApiKey: "YOUR_API_KEY",
    proxyPort: 8000,
    urlWhereYourProxyIsRunning: 'http://localhost:8000',
    target: {
        host: 'localhost',
        port: 8501,
        protocol: 'http:'
    },
})
```
Nun erweitern wir unsere Streamlit App um Methoden zur Authentifizierung. Installiert zuerst das 
Propelauth Modul in euer Venv. Achtet darauf, dass eure Pipfile auf dem neuesten Stand bleibt.
```bash
pip install propelauth_py
```
Nun ändert das Streamlit Skript.
```python
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
```
Anstatt den API-Key hier direkt anzugeben, lesen wir diesen von einer YAML ein. Dies werden wir später
beim Cloud Deployment brauchen. Legt dazu in eurem `src` Verzeichnis einen Folder 
`.secrets` an und in diesem eine Datei `propelAuthKey.yaml` mit folgendem Inhalt.
```yaml
api_key: <your-key-here>
```
Erweitert eure `proxy.mjs` dann wie folgt.
```node
import { readFile } from 'fs/promises';
import yaml from 'js-yaml';
import { initializeAuthProxy } from '@propelauth/auth-proxy';

// Function to load the API key from a YAML file
async function loadApiKeyFromYaml(filePath) {
  try {
    const fileContents = await readFile(filePath, 'utf8');
    const data = yaml.load(fileContents);
    return data.api_key;
  } catch (e) {
    console.error('Failed to load API key from YAML', e);
    throw e;
  }
}

async function init() {
  const api_key = await loadApiKeyFromYaml('/Users/sortmanns/git/work/dhac_streamlit_demo/src/.secrets/propelAuthKey.yaml');

  // Now initialize your auth proxy with the loaded API key
    await initializeAuthProxy({
        authUrl: "https://560282212.propelauthtest.com",
        integrationApiKey: api_key,
        proxyPort: 8000,
        urlWhereYourProxyIsRunning: 'http://localhost:8000',
        target: {
            host: 'localhost',
            port: 8501,
            protocol: 'http:'
        },
    });
}

// Execute the initialization function
init();
```
Zu diesem Zeitpunkt sollte euer Projekt die folgende Struktur haben.
```
.
├── .streamlit
│   └── secrets.toml
├── src
│   ├── .secrets
│   │   └── propelAuthKey.yaml
│   ├── proxy
│   │   └── proxy.mjs
│   └── streamlit_app
│       ├── __init__.py
│       └── streamlit_app.py
├── .gitignore
├── Pipfile
└── Pipfile.lock
```
Führt nun folgende Befehle zum Initialisieren eures Node Projektes aus.
```bash
npm i @propelauth/auth-proxy
npm install js-yaml
```
Startet nun eure Streamlit App, wie gewohnt. Ihr solltet jetzt im Browser die Meldung `Unauthorized`
sehen. Öffnet ein zusätzliches Fenster im Terminal und startet euren Node Proxyserver.
```bash
node src/proxy/proxy.mjs
```
Geht jetzt im Browser auf `localhost:8000`. Ihr solltet nun euren Login Screen von Propelauth sehen.
Authentifiziert euch, um zu euerer Streamlit App weitergeleitet zu werden.