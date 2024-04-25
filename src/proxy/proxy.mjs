import { readFile } from 'fs/promises';
import yaml from 'js-yaml';
import { initializeAuthProxy } from '@propelauth/auth-proxy';

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
  const credentials = await loadCredentialsFromYaml('/Users/sortmanns/git/work/streamlit-web-app-tutorial/src/.secrets/propelAuthKey.yaml');

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
