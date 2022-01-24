# -*- coding: utf-8 -*-
# Import required libraries
import base64
import os
import io
import pandas as pd
import numpy as np
import dash
from dash.dependencies import Input, Output, State
from dash import dcc
from dash import html
from dash import dash_table as dt
import dash_bootstrap_components as dbc
from dash_extensions import Download
from dash_extensions.snippets import send_data_frame
import pybso.core as core
import pybso.charts as charts
import plotly.graph_objects as go
import config

# config variables
port = config.PORT
host = config.HOST
url_subpath = config.URL_SUBPATH

# Setup the app
app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}],
    external_stylesheets=[dbc.themes.COSMO],
    url_base_pathname=url_subpath
)
app.title = "Démonstrateur baromètre Open Access"
server = app.server

# COMPONENTS FUNCTIONS
## drag&drop upload div
def render_upload(id):
    return dcc.Upload(
            id=id,
            children=html.Div(
                ["Glisser-déposer ou cliquer pour importer un fichier"]
                    ),
            style={
            "height": "60px",
            "lineHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
            "textAlign": "center",
            "margin": "10px",
                   },
            multiple=True,
     )
## datatable
def render_datatable(id):
    return html.Div(dt.DataTable(
            id=id,
            sort_action="native",
            sort_mode="multi",
            page_action="native",
            page_current=0,
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_header={'backgroundColor': 'rgb(30, 30, 30)'},
            style_cell={
                'backgroundColor': 'rgb(82, 139, 145)',
                'color': 'white',
                'textAlign': 'left',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'minWidth': '180px', 'width': '180px', 'maxWidth': '180px',},
            )
            )
## empty layout graph before getting data
def empty_graph():
    fig = go.Figure()
    fig.update_layout(
        xaxis =  { "visible": False },
        yaxis = { "visible": False },
        annotations = [{
            "text": "Pas de données à afficher",
            "xref": "paper",
            "yref": "paper",
            "showarrow": False,
            "font": {
            "size": 28}
        }]
    )
    return fig

#LAYOUT
app.layout = dbc.Container(
    [
           dbc.Row(
            [
                dbc.Col(
                    [ 
                        html.Div(html.Img(src=app.get_asset_url('logo_UCA_bibliotheque_ligne_couleurs.png'), style={'height':'60px','width':'350px'})),                  
                    ],
                   width={"size": 3} ,
                ),
                 dbc.Col([
                     html.H3("Baromètre Open Access : démonstrateur en ligne"),
                 ], 
                 width={"size": 6} ,
                 )
            ],
        ),

        html.Hr(),
        dbc.Row([
        dbc.Col(
            [
   
                        dbc.Row(
                            [
                                html.H4("1. Importer un fichier de DOI"),
                                dbc.Alert(
                                [html.Ul([
                                    html.Li("Le fichier peut être au format CSV, Excel ou Json"),
                                    html.Li("Le fichier peut contenir plusieurs entrées mais doit avoir au minimum une colonne/entrée de DOI avec l'en-tête 'doi'")
                                ]                  
                                ),
                                dbc.Label("Si le fichier à importer est au format csv, précisez le séparateur :"),
                               dbc.RadioItems(
                                            id="csv_sep",
                                            options=[
                                                {'label': 'virgule ,', 'value': ','},
                                                {'label': 'point-virgule ;', 'value': ';'}
                                                ],
                                            value=';',
                                            )],
                                            color="secondary"),

                                 dcc.Store(id="intermediate-csvsep-value"),
                                 dbc.Spinner(id="loading-1",
                                          children=[
                                 render_upload("upload-data"),
                                 html.Div(id="import-error"),
                                 render_datatable("table-data"),]),
                               
                        ]),
                        html.Hr(),
                        dbc.Row(
                            [
                        html.H4("2. Moissonner les données Open Access"),
                         dbc.Button("Interroger Unpaywall", id="unpaywall_button", color="primary", className="me-1",n_clicks=0),
                        dcc.Store(id="intermediate-source-value"),
                        dbc.Spinner(id="loading-2",
                                    children=[render_datatable("table-result")]),
                        dcc.Store(id="intermediate-result-value"),
                    ]
                ),
                        html.Hr(),
                         dbc.Row(
                         [
                        html.H4("3. Sauvegarder les résultats"),
                        html.Div(
                           [
                        dbc.Button("Download CSV", id="csvdownload", color="link", className="me-1",n_clicks_timestamp='0'),
                        dbc.Button("Download Excel", id="xlsdownload", color="link", className="me-1",n_clicks_timestamp='0'),
                        dbc.Button("Download Json", id="jsondownload", color="link", className="me-1",n_clicks_timestamp='0'),
                           ]
                        ),
                         Download(id="download"),
                         ]),
      
                    ],
                    width={"size": 3} ,
                ),
                dbc.Col(
                    [
                         dbc.Row([
                            dbc.Col([dcc.Graph(id="oa_rate_graph")],width={"size": 6}),
                            dbc.Col([dcc.Graph(id="oa_rate_by_year_graph")],width={"size": 6})
                         ]),
                         dbc.Row([
                            dcc.Graph(id="rate_by_publisher_graph")
                         ]),
                         dbc.Row([
                            dbc.Col([dcc.Graph(id="by_status_graph")],width={"size": 6}),
                            dbc.Col([dcc.Graph(id="by_type_graph")],width={"size": 6})
                         ])
                    ],
                     width={"size": 9} ,
                ),
    
        ]
        ),
        html.Hr(),
        html.P(
           [
              "2022 - SCD Université Côte d'Azur. | Built with",
                html.Img(
                src=app.get_asset_url('dash-logo.png'),
                height='43 px',
                width='auto')
            ]
        ),
    ],
    fluid=True,
)

@app.callback(Output('intermediate-csvsep-value', 'data'),
              [Input('csv_sep','value')])
def save_sep(csv_sep):
    return csv_sep

@app.callback(Output('table-data', 'columns'),
              Output('table-data', 'data'),
              Output('intermediate-source-value', 'data'),
              Output('import-error','children'),
              [Input('upload-data', 'contents'),
              Input('upload-data', 'filename')],
              [State("intermediate-csvsep-value", "data"),],
              prevent_initial_call=True)
def update_table(contents, filename,csv_sep):
    if contents is not None:
        content_type, content_string = contents[0].split(',')
        decoded = base64.b64decode(content_string)
        try:
            if 'csv' in filename[0]:
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')),sep=csv_sep)
            elif (('xlsx' in filename[0]) | ('xls' in filename[0])):
                df = pd.read_excel(io.BytesIO(decoded))
            elif 'json' in filename[0]:
                df = pd.read_json(io.StringIO(decoded.decode('utf-8')))
            try:
                if df['doi'].isnull().sum() != 0:
                    return None,None,None,dbc.Alert("Votre fichier contient des DOI vides !",color="danger")
            except:
                pass
            columns = [{"name": i, "id": i} for i in df.columns]
            data = df.to_dict('records')
            return columns, data, df.to_json(),None
        except Exception as e:
            print(e)
            return None,None,None,dbc.Alert("Le format de fichier n'est pas valide !",color="danger")

@app.callback(
    Output('table-result', 'columns'),
    Output('table-result', 'data'),
    Output('intermediate-result-value', 'data'),
    Output("oa_rate_graph", "figure"),
    Output("oa_rate_by_year_graph", "figure"),
    Output("rate_by_publisher_graph", "figure"),
    Output("by_status_graph", "figure"),
    Output("by_type_graph", "figure"),
    [Input('unpaywall_button', 'n_clicks')],
    [State("intermediate-source-value", "data")],
    prevent_initial_call=True)
def get_result(n_upw_clicks,data):
    if n_upw_clicks != 0:
        dff = pd.read_json(data)
        df_result = core.unpaywall_data(dataframe=dff)
        columns = [{"name": i, "id": i} for i in df_result.columns]
        data = df_result.to_dict('records') 
        return columns, data, df_result.to_json(), charts.oa_rate(dataframe=df_result), charts.oa_rate_by_year(dataframe=df_result),charts.oa_rate_by_publisher(dataframe=df_result, publisher_field="publisher", n=10), charts.oa_by_status(dataframe=df_result), charts.oa_rate_by_type(dataframe=df_result)
    else:
        return [],[],[],empty_graph(),empty_graph(),empty_graph(),empty_graph(),empty_graph()

@app.callback(Output("download", "data"), 
             [Input("csvdownload", "n_clicks_timestamp"),
             Input("xlsdownload", "n_clicks_timestamp"),
             Input("jsondownload", "n_clicks_timestamp")], 
             [State("intermediate-result-value", "data")],
             prevent_initial_call=True)
def download_table(csvdownload, xlsdownload,jsondownload, data):
    df = pd.read_json(data,orient="records")
    if int(csvdownload) > int(xlsdownload) and int(csvdownload) > int(jsondownload):
        return send_data_frame(df.to_csv, "data.csv", index=False)
    elif int(xlsdownload) > int(csvdownload) and int(xlsdownload) > int(jsondownload):
        return send_data_frame(df.to_excel, r"data.xlsx", index=False)
    elif int(jsondownload) > int(csvdownload) and int(jsondownload) > int(xlsdownload):
        return send_data_frame(df.to_json, "data.json", orient="records")

if __name__ == "__main__":
    app.run_server(port=port, host=host)