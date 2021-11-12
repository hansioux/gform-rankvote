# gform-rankvote
Takes in a google forms ranked choice voting result via google sheets and goes through each round until one candidate has over 50% of the votes.

Ranked choice voting is implemented with pyrankvote https://github.com/jontingvold/pyrankvote

The original colab is located at
    https://colab.research.google.com/drive/1HXtNgpnBggwiHjiJa5JHSCjkppWG1XCx

Early versions were based on a script by rrosasl https://github.com/rrosasl/RankedVoting
and his write up https://rrosasl.medium.com/ranked-choice-voting-with-google-forms-and-python-c471ea568a60
It was modified to record e-mail addresses and added a tie breaker. However, that part of the code has since been removed in favor of pyrankvote.

## Google Forms and Sheets Templates

Google Forms Template
https://docs.google.com/forms/d/1WZLILsb0wO7Kqh4VadCq6HigoIgLTugd-6AIbMmc29c/viewform?edit_requested=true

### Setting up a Ranked Choice Voting Google Form

After creating a new Google Form for your election, naming your question, and listing options/candidates,
you must configure your question as the image below.

![How to config Google Forms question for ranked choice voting](https://github.com/hansioux/gform-rankvote/blob/main/question_config.png?raw=true)

1. Select 'Multiple Choice Grid'
2. For the column name, fill in 1, 2, to the number of total options/candidates you have in sequence
3. You must select 'Limit to one response per column' for ranked choice voting
4. Optional. you can choose to shuffle the order of options/candidates for each voter for a more fair result 
5. Optional. you can require an response for each row if yo do not wish to allow voters to skip ranking options/candidates

![How to config Google Forms settings](https://github.com/hansioux/gform-rankvote/blob/main/form_config.png?raw=true)

These settings are optional.  

If you want to limit each person to one vote, you can toggle Limit to 1 response. The election will remain anonymous but requires google login.
If you want to keep track of the people voting, you can collect e-mail addresses, however, the election will not remain anonymous.
Toggle allow vote editing so that voter can change their vote before polling is closed.

After sharing the form to voters, raw ballot result will be generated into a google spreadsheet.

Google Sheets Template
https://docs.google.com/spreadsheets/d/1y7ID3rjDI-Ih1Sv1ZQO3m3syowdDIzZyObyzSAneIE0/edit?usp=drivesdk

## Connecting to the Resulted Google Sheets

By default, the script opens a csv file under tests/data.

If you want to connect to a google spreadsheet with your election results, you have a couple of options:

### The Easy Way

Use the colab file, and paste the shared Google Sheets link to gc.open_by_url() in retrieve_google_sheets(), and run all.

### Running Outside Google Colab

In order to connect to and pull data from Google Sheets outside of google Colab, you will need to enable Google Sheets credentials in your GCP console. 
Then you can authenticate by creating a service account and generating a service account key.
GCP concole: https://console.cloud.google.com
Official GCP service account guide: https://cloud.google.com/docs/authentication/production

1. In GCP, create a project.
2. Under the project, select 'APIs and Services'→ 'Credentials' on the sidebar.
3. In the Credentials page, click 'Create Credentials' on the top, and select 'Service account'.
4. Search for Google Sheets, and enable credentials.
5. Back in the Credentials page, there should be a new service account.  Click into the account.
6. In the service account page, click 'Keys' at the top.
7. Select 'Add key'→ 'Create new key'.
8. Select 'JSON' and save the key under the gcloud folder.
9. In gform-rankvote.py, make sure google colab authentication is disabled in retrieve_google_sheets()
```python
    # google colab authentication
    # auth.authenticate_user()
    # gc = gspread.authorize(GoogleCredentials.get_application_default())

    # none google colab authentication
    creds = get_credentials()
    gc = gspread.authorize(creds)
```
10. Paste the filename of the service account key to json_key variable in get_credentials():
11. Paste the shared Google Sheets link to gc.open_by_url() in retrieve_google_sheets(), and run all.


## Tally Ranked Choice Voting Results

```bash
ipython gform_rankvote.py 
```
