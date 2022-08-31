## Local Execution
Before execute is needed set GCP credentials using the command
export GOOGLE_APPLICATION_CREDENTIALS="C:\Users\alber\Documents\GoogleCloudCredentials\vacio-276411_service_account.json"

streamlit run app.py

## Deploy 
 -- Change version before execute next command
docker build -t eu.gcr.io/vacio-276411/strlit-gull:v1 .
docker push eu.gcr.io/vacio-276411/strlit-gull:v1

(If not done before do: gcloud auth configure-docker )

Or in the future Select from Google Cloud the respository and new versions will be autobuilded 
 - Problem with size of model on github

## Deploy OLD - App Engi flexible
Generate image --> docker build . -t streamlit-image
Build a container --> docker run -p 8080:8080 --name streamlit-container streamlit-image
Deploy to Google Cloud App engine: gcloud app deploy app.yaml

## Guide
Cloud run: https://www.artefact.com/blog/how-to-deploy-and-secure-your-streamlit-app-on-gcp/
App Engine Flexible: https://medium.com/analytics-vidhya/deploying-streamlit-apps-to-google-app-engine-in-5-simple-steps-5e2e2bd5b172


## Documentation streamlit:
Base map: https://github.com/streamlit/demo-uber-nyc-pickups
Districts by time: https://github.com/streamlit/example-app-cohort-analysis
Trips: https://github.com/streamlit/demo-pydeck-maps