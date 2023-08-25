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

Copy the Account_number, Report_number, and Report_token from the Eazybi report to the config file named <your_squad_name>.yml

### Config file
The config file should be in the secrets/ folder

You can change other settings inside the config file

If you are using GCP Cloud Run you can use the Secrets Manager and mount as a filename

### Configure API Eazybi project
Go to your account Source Data tab and add a new source aplication as a Rest:API
- Your source data URL should be <your_gcp_server_url>/eazybi/<your_squad_name_without.yml>
    - Example: https://jira-metrics-eazybi.app/eazybi/jp
- Set request method to GET
- Content type to JSON
- Data path to $.data

## How to setup dev enviroment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
