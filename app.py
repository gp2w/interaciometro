# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
from dash.dependencies import Input, Output, State
import dash_table
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import os
import tweepy

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
df = pd.DataFrame(columns=['user','num_likes'])

# inicializa uma aplicacao em Dash
app = dash.Dash(__name__, title='Interaciômetro')

server = app.server # the Flask app

app.layout = html.Div([
    html.H2("Interaciômetro"),
    html.H5("Digite um usuario do twitter para realizar uma busca"),
    html.Div([
        "Usuario: ", 
        dcc.Input(id='user-input', value='', type='text'),
        html.Button(id='submit-button-state', n_clicks=0, children='Buscar', style={'margin-left': 10},),
    ],style={'padding': 10}),
    html.Br(),
    dash_table.DataTable(
        id='datatable-row-ids',
        columns=[
            {'name': 'Usuário', 'id': 'user'},
            {'name': 'Quantidade de Likes', 'id': 'num_likes'}
        ],
        data=df.to_dict('records'),
        # editable=False,
        filter_action="native",
        sort_action="native",
        sort_mode='multi',
        # row_selectable='multi',
        # row_deletable=True,
        # selected_rows=[],
        page_action='native',
        page_current= 0,
        page_size= 15,
    ),
    html.Div([],style={'margin': 50}),
    html.Div(id='datatable-row-ids-container')
])

@app.callback(Output('datatable-row-ids', 'data'),
              [Input('submit-button-state', 'n_clicks')], # n_clicks é somente para a callback ser ativada com o click do botão
              [State('user-input', 'value')])
def update_username(n_clicks, username):
    # reseta dataframe
    df = pd.DataFrame(columns=['user','num_likes'])
    
    if username != '':
        # tweets = core_cd.get_tweets(api=api, username='weversonvn')
        likes = core_cd.get_likes(api=api, username=username)
        df = core_pd.top_users_likes(likes=likes)

    return df.to_dict('records')

@app.callback(
    Output('datatable-row-ids-container', 'children'),
    [Input('datatable-row-ids', 'derived_virtual_data')])
def update_graphs(rows):
    
    if rows is None:
        dff = pd.DataFrame(columns=['user','num_likes'])
    else:
        dff = pd.DataFrame(data=rows,columns=['user','num_likes'])
    
    return [
        dcc.Graph(
            id='likes',
            figure={
                'data': [
                    {
                        "x": dff["user"],
                        "y": dff["num_likes"],
                        "type": "bar",
                    }
                ],
                'layout': {
                    'xaxis': {
                        'automargin': True,
                    },
                    'yaxis': {
                        'automargin': True,
                        'title': {'text': 'Likes'}
                    },
                    'height': 250,
                    'margin': {'t': 10, 'l': 10, 'r': 10},
                },
            },
        )
    ]

if __name__ == '__main__':
    app.run_server(debug=True)