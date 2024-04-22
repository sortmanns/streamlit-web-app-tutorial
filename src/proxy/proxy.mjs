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
