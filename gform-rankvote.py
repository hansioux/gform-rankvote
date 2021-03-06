# -*- coding: utf-8 -*-
#!/usr/bin/env python
# -*- coding: utf8 -*-
"""Takes in a google form ranked choice voting result via google speadsheet and
goes through each round until one candidate has over 50% of the votes.

Implemented with pyrankvote https://github.com/jontingvold/pyrankvote

The original colab script is located at
    https://colab.research.google.com/drive/1HXtNgpnBggwiHjiJa5JHSCjkppWG1XCx
"""
import pandas as pd
import numpy as np
import re
from os import access, R_OK
from os.path import isfile

# To use import data from Google
# google colab authentication
from google.colab import auth
from oauth2client.client import GoogleCredentials

# For none colab usage, must create credential at https://console.developers.google.com/
import json
from oauth2client.service_account import ServiceAccountCredentials
import httplib2

import gspread

# To sort list
from operator import itemgetter

# To us the pyrankvote library
# !pip install pyrankvote
import pyrankvote
from pyrankvote import Candidate, Ballot

# To visualize Sankey Diagram
import plotly
import plotly.graph_objects as go
import matplotlib.pyplot as plt

# To visualize in jupyter notebook or ipython
import plotly.offline as pyo


def get_credentials():
    '''
    obtain google sheets credential
    '''

    json_key = 'gcloud/gform-rankvote-b7857000adb7.json'
    scope = ['https://spreadsheets.google.com/feeds']
    creds = ServiceAccountCredentials.from_json_keyfile_name(json_key, scope)

    http = httplib2.Http()
    http = creds.authorize(http)

    return creds


def retrieve_google_sheets():
    '''
    retrieve voting data generated by google forms from google sheets
    '''
    # google colab authentication
    # auth.authenticate_user()
    # gc = gspread.authorize(GoogleCredentials.get_application_default())

    # none google colab authentication
    creds = get_credentials()
    gc = gspread.authorize(creds)

    # worksheet = gc.open('Your spreadsheet name').sheet1
    wb = gc.open_by_url('https://docs.google.com/spreadsheets/d/1y7ID3rjDI-Ih1Sv1ZQO3m3syowdDIzZyObyzSAneIE0/edit?usp=sharing')

    # get_all_values gives a list of rows.
    wb = wb.worksheet('Form Responses 1')
    rows = wb.get_all_values()

    # Convert to a DataFrame and render.
    df = pd.DataFrame.from_records(rows)

    new_header = df.iloc[0] # grab the first row for the header
    df = df[1:] # take the data less the header row
    df.columns = new_header # set the header row as the df header
    df = df.iloc[:,1:] # Remove time stamp

    # Convert votes to int
    for col in df.columns:
        if col != 'Email Address':
            df[col] = df[col].astype(int)
        else:
            # If e-mail is recorded, remove from the df
            # df_email = df
            df = df.drop('Email Address', 1)

    df = df.reset_index().iloc[:,1:]

    return df


def read_csv_input(fn):
    '''
    Get input data from a csv file
    '''

    df = pd.read_csv(fn)

    df = df.iloc[:,1:] # Remove time stamp

    # Convert votes to int
    for col in df.columns:
        if col != 'Email Address':
            df[col] = df[col].astype(int)
        else:
            # If e-mail is recorded, remove from the df
            # df_email = df
            df = df.drop('Email Address', 1)

    df = df.reset_index().iloc[:,1:]

    return df


def genSankey(df,cat_cols=[],value_cols='',title='Sankey Diagram'):
    '''
    https://gist.github.com/ken333135/09f8793fff5a6df28558b17e516f91ab
    '''
    # maximum of 6 value cols -> 6 colors
    colorPalette = ['#4B8BBE','#306998','#FFE873','#FFD43B','#646464']
    labelList = []
    colorNumList = []
    for catCol in cat_cols:
        labelListTemp =  list(set(df[catCol].values))
        colorNumList.append(len(labelListTemp))
        labelList = labelList + labelListTemp

    # remove duplicates from labelList
    labelList = list(dict.fromkeys(labelList))

    # define colors based on number of levels
    colorList = []
    for idx, colorNum in enumerate(colorNumList):
      colorList = colorList + [colorPalette[idx]]*colorNum

    # transform df into a source-target pair
    for i in range(len(cat_cols)-1):
        if i==0:
            sourceTargetDf = df[[cat_cols[i],cat_cols[i+1],value_cols]]
            sourceTargetDf.columns = ['source','target','count']
        else:
            tempDf = df[[cat_cols[i],cat_cols[i+1],value_cols]]
            tempDf.columns = ['source','target','count']
            sourceTargetDf = pd.concat([sourceTargetDf,tempDf])
        sourceTargetDf = sourceTargetDf.groupby(['source','target']).agg({'count':'sum'}).reset_index()

    # add index for source-target pair
    sourceTargetDf['sourceID'] = sourceTargetDf['source'].apply(lambda x: labelList.index(x))
    sourceTargetDf['targetID'] = sourceTargetDf['target'].apply(lambda x: labelList.index(x))

    # creating the sankey diagram
    data = dict(type='sankey',
                node = dict(pad = 15,
                            thickness = 20,
                            line = dict(color = "black",
                                        width = 0.5
                                   ),
                            label = labelList,
                            color = colorList
                       ),
                link = dict(source = sourceTargetDf['sourceID'],
                            target = sourceTargetDf['targetID'],
                            value = sourceTargetDf['count']
                       )
           )

    layout = dict(title = title,
                   font = dict(size = 10)
              )

    fig = dict(data=[data], layout=layout)

    return fig


def plot_sankey(vote_rounds):
    '''
    plot sankey graph
    '''

    col_rounds = vote_rounds.columns.tolist()
    col_rounds.remove('value')
    df_sankey = vote_rounds.groupby(col_rounds).count().reset_index()
    for col in col_rounds:
        df_sankey[col] = df_sankey[col].apply(str) + str(col)
    df_sankey

    pyo.init_notebook_mode()

    sankey_title = 'Vote by Ranking'

    sankey_fig = genSankey(df_sankey,cat_cols=col_rounds,value_cols='value',title=sankey_title)
    # plotly.offline.plot(fig, validate=False)

    fig = go.Figure(sankey_fig)
    fig.update_layout(width=int(1200))

    fig.add_annotation(x=0,
                       y=1.1,
                       showarrow= False,
                       text="First round")

    fig.add_annotation(x=1,
                       y=1.1,
                       showarrow= False,
                       text="Final round")

    return fig


def org_sankey_data(election_result):
    '''
    Reshape election result from pyrankvote to a format that can be plotted
    into a sankey graph
    '''

    vote_rounds = pd.DataFrame()

    cnt = 0
    for r in election_result.rounds:
        vote_rounds[cnt] = list(np.concatenate([list(np.repeat(c.candidate.name, int(c.number_of_votes))) for c in r.candidate_results]).flat)
        cnt += 1

    vote_rounds['value'] = [1 for x in range(vote_rounds.shape[0])]

    fig = plot_sankey(vote_rounds)

    return fig


def pyrankvote_ballot(df):
    '''
    Shape df generated from google sheet into pyrankvote format.
    '''

    candidate_iterable = map(Candidate, df.columns.to_list())
    candidates = list(candidate_iterable)
    # print(candidates)

    carr = np.array(candidates)

    ballot_list = carr[(np.argsort(df.values, axis=1))].tolist()
    ballots = [Ballot(ranked_candidates=b) for b in ballot_list]

    return candidates, ballots


def instant_runoff(df):
    '''
    Generate result for a ranked election with a single winner.

    pyrankvote's instant_runoff_voting simply calles perferencial_block_voting
    with the number of seats set to 1.
    '''

    candidates, ballots = pyrankvote_ballot(df)
    election_result = pyrankvote.instant_runoff_voting(candidates, ballots)
    winners = election_result.get_winners()

    return election_result


def single_transferable(df, ns):
    '''
    Elections for more than one elected seats/options using STV.
    '''

    # Set numbers of seats to win
    # ns = 1
    # ns = 2

    candidates, ballots = pyrankvote_ballot(df)
    election_result = pyrankvote.single_transferable_vote(candidates, ballots, number_of_seats=ns)
    winners = election_result.get_winners()

    return election_result


def perferential_block(df, ns):
    '''
    Elections for more than one elected seats/options using PBV.
    '''

    # Set numbers of seats to win
    # ns = 1
    # ns = 2

    candidates, ballots = pyrankvote_ballot(df)
    election_result = pyrankvote.preferential_block_voting(candidates, ballots, number_of_seats=ns)
    winners = election_result.get_winners()

    return election_result


def main():
    '''
    Start counting the results from the preferred election method.
    '''
    # df = retrieve_google_sheets()

    fn = './tests/data/sample_data.csv'
    assert isfile(fn) and access(fn, R_OK), "File {} doesn't exist or isn't readable".format(fn)
    df = read_csv_input(fn)

    election_result = instant_runoff(df)
    print("Ranked-choice Voting Results:")

    # ns = 2
    # election_result = single_transferable(df, ns)
    #print("STV Results with %d spots:"%ns)
    # election_result = perferential_block(df, ns)
    #print("PBV Results with %d spots:"%ns)

    print(election_result)
    fig = org_sankey_data(election_result)
    fig.show()
    fig.write_image('tests/results/election_result.png')


if __name__ == "__main__":
    main()
