# Implementierung einer Streamlit KI App mit Nutzermanagement
In einer Welt, in der die Digitalisierung in allen Lebensbereichen zunehmend 
an Bedeutung gewinnt, ist das Gesundheitswesen kein Ausnahmefall. 
Der Einsatz von künstlicher Intelligenz (KI) im Gesundheitswesen verspricht, 
einige der drängendsten Probleme zu lösen, 
mit denen der Sektor heute konfrontiert ist: 
Fachkräftemangel und Unterfinanzierung. 
Durch die Automatisierung von Routineaufgaben und die Bereitstellung 
fortschrittlicher Diagnosetools kann KI medizinisches Personal entlasten 
und die Effizienz steigern. Doch das Entwickeln von Applikationen und das Sammeln von Daten
ist häufig ein aufwändiges Unterfangen. Dies brachte mich im Rahmen eines Forschungsprojektes 
in der Augenheilkunde auf die Frage, wie ich als Data Scientist, möglichst kostengünstig 
und mit wenig Aufwand eine KI App mit einem Mindestmaß an Funktionalität bereitstellen kann.
</br></br>
Das ultimative Ziel dieses Blogposts ist die Bereitstellung eines 
Machine Learning (ML) Modells innerhalb einer Web-App, 
die nicht nur die Funktionen des Modells zugänglich macht, 
sondern auch die Sammlung neuer Trainingsdaten ermöglicht. 
Dies schafft eine Grundlage für kontinuierliches Lernen und Verbesserung 
der KI-Leistung.
</br></br>
Um dieses Ziel zu erreichen, haben wir eine Reihe von Anforderungen:
- Ein einfaches, zweckorientiertes Frontend, das für Nutzer intuitiv zu bedienen und für den Entwickler leicht wartbar ist.
- Nutzermanagement nach Industriestandards, um eine sichere und regulierte Zugriffssteuerung zu gewährleisten.
- GDPR-konforme Datenverarbeitung medizinischer Daten, um den Datenschutz und die Sicherheit der Patienteninformationen zu gewährleisten.
- Skalierbarkeit und einfache Wartung der Lösung, um zukünftiges Wachstum und Entwicklungen zu unterstützen.
- Sichere Zugänglichkeit über das öffentliche Internet, um eine breite Nutzbarkeit zu ermöglichen.
</br></br>

Zur Erfüllung dieser Anforderungen, werden wir einen modernen Techstack einsetzen,
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

Wir werden uns diesem Ziel in vier Iterationen nähern.
1. Lokales Deployment mit Snowflake als Remote Datenbank
2. Lokales Docker-Deployment, ebenfalls mit Snowflake als Datenbank
3. Serverless Cloud Deployment mit GCP und Snowflake
4. CI/CD und MLOps zum Einbinden eines ML-Modells

## 1.1 Lokales Streamlit Deployment mit Snowflake als Datenbank
Für die lokale Entwicklung setzen zuerst ein Virtual Environment (Venv) mit Pipenv oder
dem Virtualisierungstool eurer Wahl auf. Dafür legen wir eine Pipfile im 
Wurzelverzeichnis unseres Projektes an. Achtet darauf die Abhängigkeiten in der Pipfile
auf dem Laufenden zu halten.
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
Nun legen wir unser Streamlit Skript an. Für ausführlichere Erklärungen empfehlen wir die 
[Dokumention](https://docs.streamlit.io/develop/tutorials/databases/snowflake).
```python
import streamlit as st
from snowflake.snowpark import functions as F
from snowflake.snowpark.types import (IntegerType, StringType,
                                      StructField, StructType)
import uuid


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
```
Die Methode `st.connection('snowflake')` wird in der Wurzel eures Projektes
unter `.streamlit` nach einer `secrets.toml` suchen. In dieser sollte es dann einen Abschnitt mit
den Snowflake Credentials geben. Stellt sicher, dass ihr die Credentials nicht ins Remote Repo pusht. Ein weiterer Faktor, der 
mir zu Beginn Probleme bereitet hat, ist das Erstellen der Patienten ID. Diese muss randomisiert gewählt sein und 
jeder einzelne Eintrag soll eine eigene ID erhalten. Wenn man diese ID allerdings in einem ´with_column´ Statement
erzeugt, wird diese pro Session persistiert. Um dies zu umgehen, ist es notwendig, dass wir die ID schon im Formular
erstellen und den ´clear_on_submit´ Parameter auf ´True´ setzen. So wird das Formular nach jedem Submit neu geladen und
die ´generate_id´ Funktion erneut ausgeführt.
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
die App an, um das Prinzip der geringsten Privilegien umzusetzen. Legt in Snowflake ein entsprechendes 
Schema an, für das euer technischer Nutzer die nötigen Rechte hat.
</br></br>
Ihr solltet nun die Streamlit App mit folgendem Befehl aus dem Wurzelverzeichnis ausführen können.
```bash
pipenv run streamlit run src/streamlit_app/streamlit_app.py
```
Probiert mit dem Submit Button Daten in eure Snowflake Tabelle zu schreiben und stellt
sicher, dass ihr die korrekten Rechte habt.
### 1.2 Authentifikation und Nutzermanagement
Für State-of-the-Art Authentifizierung setzen wir auf einen Proxyserver und Propelauth
als Identity Provider und Nutzermanagement Tool. Für ein detailliertes Tutorial zu 
Streamlit und Propelauth verweisen wir auf diesen [Blogpost](https://www.propelauth.com/post/streamlit-authentication). Wir werden die einzelnen 
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
Anstatt den API-Key hier direkt anzugeben, lesen wir diesen von einer YAML ein. Dies werden wir später
für ein sicheres Cloud-Deployment brauchen. Legt dazu in eurem `src` Verzeichnis einen Folder 
`.secrets` an und in diesem eine Datei `propelAuthKey.yaml` mit folgendem Inhalt.
```yaml
api_key: <your-key-here>
auth_url: <your-url-here>
```
Erweitert eure `proxy.mjs` dann wie folgt.
```node
import { initializeAuthProxy } from '@propelauth/auth-proxy';
import { readFile } from 'fs/promises';
import yaml from 'js-yaml';

// Function to load the API key from a YAML file
async function loadCredentialsFromYaml(filePath) {
  try {
    const fileContents = await readFile(filePath, 'utf8');
    const data = yaml.load(fileContents);
    return {
      apiKey: data.api_key,  // Adjust the key names according to your YAML structure
      authUrl: data.auth_url  // Similarly, adjust if your YAML key is different
    };
  } catch (e) {
    console.error('Failed to load credentials from YAML', e);
    throw e;
  }
}

async function init() {
  const credentials = await loadCredentialsFromYaml('<path-to-yaml>');

  // Now initialize your auth proxy with the loaded API key
    await initializeAuthProxy({
        authUrl: credentials.authUrl,
        integrationApiKey: credentials.apiKey,
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
Nun erweitern wir unsere Streamlit App um Methoden zur Authentifizierung. Installiert zuerst das 
Propelauth Modul in euer Venv. Achtet darauf, dass eure Pipfile auf dem neuesten Stand bleibt.
```bash
pip install propelauth_py
```
Darauf folgend erstellen wir ein Modul `customs_auth.py`, welches die nötigen Funktionen
für die Authentifikation bereitstellt.
```python
import requests
from propelauth_py import UnauthorizedException, init_base_auth
from streamlit.web.server.websocket_headers import _get_websocket_headers


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
```
Nun importieren wir die entsprechenden Klassen das Streamlit Skript und lesen die nötigen Credentials
aus der YAML ein. Dazu fügen wir im oberen Teil des Skripts folgendes ein.
```python
import streamlit as st
from snowflake.snowpark import functions as F
from snowflake.snowpark.types import (IntegerType, StringType,
                                      StructField, StructType)
import yaml

from custom_auth import Auth

# Load the YAML file
with open('<path-to-yaml>', 'r') as file:
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
...
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
│       ├── custom_auth.py
│       └── streamlit_app.py
├── .gitignore
├── Pipfile
└── Pipfile.lock
```
Je nachdem wie ihr den Code ausführt, kann es sein, dass ihr den `src` Order zum
Python Pfad hinzufügen müsst, damit das `custom_auth` Modul gefunden wird.
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
Authentifiziert euch, um zu eurer Streamlit App weitergeleitet zu werden.