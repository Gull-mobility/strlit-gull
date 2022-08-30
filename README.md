# --

## Deploy
Generate image --> docker build . -t streamlit-image
Build a container --> docker run -p 8080:8080 --name streamlit-container streamlit-image
Deploy to Google Cloud App engine: gcloud app deploy app.yaml

## Guide
https://medium.com/analytics-vidhya/deploying-streamlit-apps-to-google-app-engine-in-5-simple-steps-5e2e2bd5b172