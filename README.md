# jira_metrics_eazybi
This a simple API that captures a public report from Eazybi and do calculations to output the Monte Carlo metrics to be imported to Eazybi source.
This api is deployable in GCP Cloud Run


## How to use
### Eazybi public report
Create an Eazybi report to be consumed by this api, example:
- Rows
    - Project dimension, Project hierarchy level
    - Time dimension, Day hierarchy level
    - Issue dimension, Issue hierarchy level
- Columns
    - Measure cycle time (in days)

Your table/data should look like this:

| Project | Time | Issue | Cycle time |
| ----------- | ----------- | ----------- | ----------- |
| JP | Aug 25 2022 | JP-105 | 24
| JP | Aug 29 2022 | JP-110 | 30

Save the report and make it public with an access token

### Config file
Open config_file_sample.yml and paste all info from the public report: Account_number, Report_number, Report_token
Make any changes necessary to the yaml file.
Use the GCP Secrets Manager to create a secret paste the contents of the updated config_file_sample.yml
Give permissions for your Cloud run to access secret.

### Configure API Eazybi project
Go to your account Source Data tab and add a new source aplication as a Rest:API
- Your source data URL should be <your_gcp_server_url>/eazybi/<your_secret_name>
    - Example: https://jira-metrics-eazybi.app/eazybi/jp
- Set request method to GET
- Content type to JSON
- Data path to $.data

## How to setup dev enviroment
### Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
### Local Flask
```bash
python3 main.py
```
