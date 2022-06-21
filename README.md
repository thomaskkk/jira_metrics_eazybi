# jira_metrics_eazybi
This a simple API that captures a public report from Eazybi and do calculations to output the Monte Carlo metrics to be imported to Eazybi source.
This api is deployable in GCP Cloud Run


How to configure
Eazybi public report
Create an Eazybi report
Add the corresponding Title rows
Your table/data should have the headers:
Save the report and make it public
Copy the Account_number, Report_number, and Report_token to the config file

Config file
The config file should be in the secrets/ folder
You can change other settings of the script
If you are using GCP Cloud Run you can use the Secrets Manager and mount as a filename

