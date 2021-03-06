#!/usr/bin/env python
# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
from dash.dependencies import Input, Output, State
import dash_table
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import os
import tweepy
import logging

import core.coletar_dados as core_cd
import core.processar_dados as core_pd

# carregar variaveis de ambiente do .env caso exista
from dotenv import load_dotenv
load_dotenv()

# inicializa api do twitter
auth = tweepy.OAuthHandler(os.environ['API_KEY'], os.environ['API_SECRET_KEY'])
auth.set_access_token(os.environ['ACCESS_TOKEN'],
                      os.environ['ACCESS_TOKEN_SECRET'])
api = tweepy.API(auth)

# inicializando dataframe
df = pd.DataFrame(columns=['user', 'num_likes',
                           'num_replies', 'num_retweets', 'score'])

# inicializa uma aplicacao em Dash
app = dash.Dash(__name__, title='Interaciômetro | GP2W', external_stylesheets=[dbc.themes.BOOTSTRAP], meta_tags=[{
    'http-equiv': 'X-UA-Compatible',
    'content': 'IE=edge'
}, {
    'name': 'viewport',
    'content': 'width=device-width, initial-scale=1.0'
}, {
    'name': 'description',
    'content': 'Um medidor de interação de perfis no Twitter.'
}, {
    'property': 'og:url',
    'content': 'https://interaciometro.herokuapp.com/'
}, {
    'property': 'og:site_name',
    'content': 'Interaciômetro | GP2W'
}, {
    'property': 'og:type',
    'content': 'website'
}, {
    'property': 'og:image',
    'content': 'https://interaciometro.herokuapp.com/assets/logo.png'
}, {
    'property': 'og:title',
    'content': 'Interaciômetro | GP2W'
}, {
    'property': 'og:description',
    'content': 'Um medidor de interação de perfis no Twitter.'
}, {
    'property': 'twitter:title',
    'content': 'Interaciômetro | GP2W'
}, {
    'property': 'twitter:description',
    'content': 'Um medidor de interação de perfis no Twitter.'
}, {
    'property': 'twitter:image',
    'content': 'https://interaciometro.herokuapp.com/assets/logo.png'
}, {
    'property': 'twitter:card',
    'content': 'summary_large_image'
},
])

server = app.server  # the Flask app

alert = dbc.Alert(["No momento não é possivel realizar novas requisições.",
                    html.Br(),
                    "Por favor, tente mais tarde."],
                    style={
                        'margin-left':'50px',
                        'margin-right':'50px'
                    },
                    color="danger",
                    dismissable=True)  # use dismissable or duration=5000 for alert to close in x milliseconds

app.layout = html.Div([
    html.H2("Interaciômetro"),
    html.H5("Digite um usuário do twitter para realizar uma busca"),
    html.Div([
        "@ ",
        dcc.Input(id='user-input', value='', type='text', n_submit=0),
        html.Button(id='submit-button-state', type="submit",
                    n_clicks=0, children='Buscar', style={'margin-left': 10},),
    ], style={'padding': 10}),
    html.Br(),
    html.Div(id="the-alert", children=[]),
    html.Br(),
    dcc.Loading(
        id="loading",
        type="graph",
        children=[
            dash_table.DataTable(
                id='datatable-row-ids',
                columns=[
                    {'name': 'Usuário', 'id': 'user'},
                    {'name': 'Likes', 'id': 'num_likes'},
                    {'name': 'Replies', 'id': 'num_replies'},
                    {'name': 'Retweets', 'id': 'num_retweets'},
                    {'name': 'Score', 'id': 'score'},
                ],
                data=df.to_dict('records'),
                filter_action="native",
                sort_action="native",
                sort_mode='multi',
                page_action='native',
                page_current=0,
                page_size=15,
            ),
            html.Div([], style={'margin': 50}),
            html.Div(id='datatable-row-ids-container')
        ]
    )
])


@app.callback([Output('the-alert', 'children'),
               Output('datatable-row-ids', 'data')],
              # n_clicks é somente para a callback ser ativada com o click do botão
              [Input('submit-button-state', 'n_clicks')],
              [State('user-input', 'value')])
def update_username(n_clicks, username):
    # reseta dataframe
    df = pd.DataFrame(columns=['user', 'num_likes'])
    retornos = [dash.no_update, dash.no_update]

    if username != '':

        tweets = core_cd.get_tweets(api=api, username=username)

        if(tweets is not None):
            likes = core_cd.get_likes(api=api, username=username)

            likes_df = core_pd.top_users_likes(likes=likes)

            replies_df = core_pd.top_users_replies(tweets=tweets)
            # tratamento para retirar o próprio usuário das replies
            index = replies_df['user'] == username
            replies_df = replies_df.drop(replies_df.index[index])

            retweets_df = core_pd.top_users_retweets(tweets=tweets)

            df = core_pd.score(likes_df, replies_df, retweets_df)

            # filtrar scores maiores que 10
            index = pd.to_numeric(df['score']) > 10.0
            df = df[index]

            retornos = [dash.no_update, df.to_dict('records')]
        else:
            logging.info(f'Token Inválido ou Expirado.')
            retornos = [alert, dash.no_update]

    return retornos


@app.callback(
    Output('datatable-row-ids-container', 'children'),
    [Input('datatable-row-ids', 'derived_virtual_data')])
def update_graphs(rows):

    dff = pd.DataFrame(data=rows, columns=[
                       'user', 'num_likes', 'num_replies', 'num_retweets', 'score'])

    return [
        # gráfico com likes, replies e retweets
        dcc.Graph(
            id='interações',
            figure={
                'data': [
                    {
                        'x': dff['user'],
                        'y': dff['num_likes'],
                        'type': 'bar',
                        'name': 'Likes'
                    },
                    {
                        'x': dff['user'],
                        'y': dff['num_replies'],
                        'type': 'bar',
                        'name': 'Replies'
                    },
                    {
                        'x': dff['user'],
                        'y': dff['num_retweets'],
                        'type': 'bar',
                        'name': 'Retweets'
                    }
                ],
                'layout': {
                    'xaxis': {
                        'automargin': True,
                    },
                    'yaxis': {
                        'automargin': True,
                        'title': {'text': 'interações'}
                    },
                    'height': 250,
                    'margin': {'t': 10, 'l': 10, 'r': 10},
                },
            },
        ),
        # gráfico com o score de interação
        dcc.Graph(
            id='score',
            figure={
                'data': [
                    {
                        'x': dff['user'],
                        'y': dff['score'],
                        'type': 'bar'
                    }
                ],
                'layout': {
                    'xaxis': {
                        'automargin': True,
                    },
                    'yaxis': {
                        'automargin': True,
                        'title': {'text': 'score'}
                    },
                    'height': 250,
                    'margin': {'t': 10, 'l': 10, 'r': 10},
                },
            },
        )
        # for column in ['num_likes', 'num_replies', 'num_retweets', 'score'] if column in dff
    ]


if __name__ == '__main__':
    app.run_server(debug=True)
