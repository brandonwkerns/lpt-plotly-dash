import os
os.environ['MPLCONFIGDIR'] = "/var/www/FLASKAPPS/lpt/graph"
import matplotlib
matplotlib.use('Agg')

from httplib2 import Response
import numpy as np
import xarray as xr
from netCDF4 import Dataset
import pandas as pd
import datetime as dt
import cftime
import plotly.express as px
import plotly.graph_objects as go
import colorcet as cc
from dash import Dash, html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import datashader as ds
from datashader import transfer_functions as tf

import glob
import sys

## In order to run as WSGI under Apache,
## the requests_pathname_prefix needs to be set.
## Otherwise, the application will only display "loading" and hang!
## For the interactive version for development purposes
##    (__name__ is '__main__') run on command line, use '/'.
## For deployment, use the directory under http://orca, e.g., '/lpt/'.

if __name__ == '__main__':
    ## Use this for development.
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
        requests_pathname_prefix='/')
else:
    ## Use this for deployment on orca.
    app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
        meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
        requests_pathname_prefix='/lpt/')

## Generate the application for WSGI.
## "server" gets imported as "application" for WSGI, in app.wsgi.
server = app.server
mapbox_access_token = 'pk.eyJ1IjoiYnJhbmRvbndrZXJucyIsImEiOiJja3ZyOGNlZmcydTdrMm5xZ3d4ZWNlZXZpIn0.OkA0r6XFSY-Dx0bk7UPPZQ'


##
## Function Definitions
##

def get_list_of_times(data_dir='/home/orca/bkerns/realtime/analysis/lpt-python-public/IMERG/data/imerg/g50_72h/thresh13/systems'):
    file_list = sorted(glob.glob(data_dir + '/lpt_systems_imerg_*.nc'))
    time_range_list = [x[-24:-3] for x in file_list]
    return time_range_list


def get_datetime_range_from_str(time_range_str):
    date_str_split = time_range_str.split('_')
    date0 = dt.datetime.strptime(date_str_split[0], '%Y%m%d%H')
    date1 = dt.datetime.strptime(date_str_split[1], '%Y%m%d%H')
    return (date0, date1)


##
## Set up layout.
##

## Top Banner
banner = html.Div(
    children = [
        html.H1('Large-Scale Precipitation Tracking (LPT)', className='banner-header'),
        html.P('Realtime tracking of MJO and large-scale convective systems.')],
    id='banner', style={'backgroundColor':'pink'})

list_of_times = get_list_of_times()

## Selections
selections = html.Div([
    dbc.Container(children=[
        dbc.Row(children=[
            dbc.Col(dcc.Dropdown(
                    options=[x for x in reversed(list_of_times)], value=list_of_times[-1],
                    id='time_period_selection', clearable=False), md=3),
            dbc.Col(html.P('<-- Select a time period.', id='time-indicator'), md=9),
        ]),
        dbc.Row(children=[
            dbc.Col(html.P('LPT Systems to Display: ', style={'textAlign':'right'}), md=3),
            dbc.Col(dbc.RadioItems(
                options = [
                    {'label':'MJO LPTs', 'value':'mjo'},
                    {'label':'All LPTs', 'value':'all'}
                ],
                value='mjo',
                id='mjo_or_all_input',
                inline=True
                ), md=6),
        ]),
        dbc.Row(children=[
            dbc.Col(html.P('Longitude Range: ', style={'textAlign':'right'}), md=3),
            dbc.Col(dcc.RangeSlider(0.0, 360.0, # 1.0,
                value=[50, 200],
                # marks={x:{'label':str(x)} for x in np.arange(0,370,10)},
                allowCross=False,
                tooltip={"placement": "bottom", "always_visible": True},
                id='lon_range_slider',
                ), md=6),
        ]),
        dbc.Row(children=[
            dbc.Col(html.P('Lon range applies to map? ', style={'textAlign':'right'}), md=3),
            dbc.Col(dbc.RadioItems(
                options = [
                    {'label':'Yes', 'value':'y'},
                    {'label':'No', 'value':'n'}
                ],
                value='n',
                id='lon_range_to_map',
                inline=True
                ), md=6),
        ]),
    ])
])

## Graphs
time_lon_section = html.Div(dcc.Loading(dcc.Graph(id='time-lon-graph'), id='time-lon-section'))

map_section = html.Div(dcc.Loading(dcc.Graph(id='map-graph'), id='map-section'))



## Combine into website
## In order to dynamically adapt to the date range selections available,
## Need to set the layout to a function.
def serve_layout():
    return dbc.Container(children=[
            dbc.Row([dbc.Col(banner, md=12),]),
            dbc.Row([dbc.Col(selections, md=12),]),
            dbc.Row([dbc.Col(time_lon_section, md=5), dbc.Col(map_section, md=7)]),
        ], fluid=True)

app.layout = serve_layout

## Callbacks.

@app.callback(
    Output(component_id='time-indicator', component_property='children'),
    Input(component_id='time_period_selection', component_property='value')
)
def update_time_display(time_range_str):

    date_str_split = time_range_str.split('_')
    pretty_date0 = dt.datetime.strptime(date_str_split[0], '%Y%m%d%H').strftime('%H00 UTC %Y-%m-%d')
    pretty_date1 = dt.datetime.strptime(date_str_split[1], '%Y%m%d%H').strftime('%H00 UTC %Y-%m-%d')

    pretty_time_range_str = ('Selected Time Period: ',pretty_date0 , ' to ' , pretty_date1 + '.')

    return pretty_time_range_str


@app.callback(
    [Output(component_id='time-lon-graph', component_property='figure'),
    Output(component_id='map-graph', component_property='figure')],
    [Input(component_id='time_period_selection', component_property='value'),
    Input(component_id='mjo_or_all_input', component_property='value'),
    Input(component_id='lon_range_slider', component_property='value'),
    Input(component_id='lon_range_to_map', component_property='value')]
)
def update_time_lon_plot(time_range_str, mjo_or_all, lon_range, lon_range_to_map):

    fn = ('/home/orca/bkerns/realtime/analysis/lpt-python-public/IMERG/data/imerg/g50_72h/thresh13/systems/'+
            'lpt_systems_imerg_'+time_range_str+'.nc')

    ## Read in MJO LPT stuff, if needed.
    fn_mjo = ('/home/orca/bkerns/realtime/analysis/lpt-python-public/IMERG/data/imerg/g50_72h/thresh13/systems/'+
            'mjo_lpt_list_imerg_'+time_range_str+'.txt')

    if mjo_or_all == 'mjo':
        mjo = pd.read_fwf(fn_mjo)

    with xr.open_dataset(fn, use_cftime=True, cache=False) as DS:

        Y = np.array([(x - dt.datetime(1990,1,1,0,0,0)).total_seconds()/3600.0 for x in DS['timestamp_stitched'].values])
        skip = 3
        if mjo_or_all == 'mjo':
            for n, lptid in enumerate(mjo['lptid']):
                this_lptid_idx = np.argwhere(10000*DS['lptid_stitched'].values == 10000*lptid).flatten()
                if n == 0:
                    fig = go.Figure(data=go.Scatter(x=DS['centroid_lon_stitched'].values[this_lptid_idx][::skip], y=Y[this_lptid_idx][::skip], mode='markers+lines', name=str(lptid)))
                    fig_map = go.Figure(data=go.Scattergeo(lon=DS['centroid_lon_stitched'].values[this_lptid_idx][::skip], lat=DS['centroid_lat_stitched'].values[this_lptid_idx][::skip], mode='markers+lines', name=str(lptid))) #, projection="natural earth"))
                else:
                    fig.add_trace(go.Scatter(x=DS['centroid_lon_stitched'].values[this_lptid_idx][::skip], y=Y[this_lptid_idx][::skip], mode='markers+lines', name=str(lptid)))
                    fig_map.add_trace(go.Scattergeo(lon=DS['centroid_lon_stitched'].values[this_lptid_idx][::skip], lat=DS['centroid_lat_stitched'].values[this_lptid_idx][::skip], mode='markers+lines', name=str(lptid)))
        else:
            for n, lptid in enumerate(DS['lptid'].values):
                this_lptid_idx = np.argwhere(10000*DS['lptid_stitched'].values == 10000*lptid).flatten()
                if n == 0:
                    fig = go.Figure(data=go.Scatter(x=DS['centroid_lon_stitched'].values[this_lptid_idx], y=Y[this_lptid_idx], mode='markers+lines', name=str(lptid)))
                    fig_map = go.Figure(data=go.Scattergeo(lon=DS['centroid_lon_stitched'].values[this_lptid_idx], lat=DS['centroid_lat_stitched'].values[this_lptid_idx], mode='markers+lines', name=str(lptid)))
                else:
                    fig.add_trace(go.Scatter(x=DS['centroid_lon_stitched'].values[this_lptid_idx], y=Y[this_lptid_idx], mode='markers+lines', name=str(lptid)))
                    fig_map.add_trace(go.Scattergeo(lon=DS['centroid_lon_stitched'].values[this_lptid_idx], lat=DS['centroid_lat_stitched'].values[this_lptid_idx], mode='markers+lines', name=str(lptid))) #, projection="natural earth"))

        ## Add time-lon.
        fn_time_lon = ('/home/orca/bkerns/realtime/analysis/lpt-python-public/IMERG/data/imerg/timelon/'+
            'imerg_time_lon.'+time_range_str+'.nc')
        with xr.open_dataset(fn_time_lon, use_cftime=True, cache=False) as DS:
            Z = np.double(DS['precip'].data)
            X = DS['lon'].data
            Y = [(x - dt.datetime(1990,1,1,0,0,0)).total_seconds()/3600 for x in DS['time'].values] #  np.arange(len(DS['time'].data))
            cvs = ds.Canvas(plot_width=200, plot_height=1000, x_range=(0, 360.0), y_range=(Y[0], Y[-1]))
            da = xr.DataArray(data=Z, coords={'y':(['y',], Y),'x':(['x',], X)}, name='Test')
            da['_file_obj'] = None #Throws an error without this HACK.
            da_img = cvs.raster(da)
            fig.add_trace(go.Heatmap(x=da_img.x, y=da_img.y, z=da_img.data, zmin=0.0, zmax=3.0, colorscale=[[0, 'rgb(255,255,255)'], [1, 'rgb(0,0,0)']]))
            
    ## Axes range.
    fig.update_layout(xaxis_range=lon_range, yaxis_range=(Y[0], Y[-1]), #get_datetime_range_from_str(time_range_str),
        height=800, margin={"r":0,"t":0,"l":0,"b":0})
    fig.update_xaxes(showline=True, linewidth=1, linecolor='black', mirror=True,
        showgrid=True,gridwidth=0.5, gridcolor='LightPink',
        title_text='Longitude')
    fig.update_coloraxes(colorbar_orientation='h')
    fig.data[-1].colorbar.title='Rain Rate [mm/h]'
    fig.data[-1].colorbar.y=1.005
    fig.data[-1].colorbar.orientation='h'
    fig.data[-1].colorbar.thickness=20

    yticks = Y[::168]
    yticklabels=[(dt.datetime(1990,1,1,0,0,0) + dt.timedelta(hours=x)).strftime('%m/%d<br>%Y') for x in yticks]
    fig.update_yaxes(showline=True, linewidth=1, linecolor='black', mirror=True,
        showgrid=True,gridwidth=0.5, gridcolor='LightPink',
        tickmode='array', tickvals=yticks, ticktext=yticklabels)

    if lon_range_to_map == 'y':
        map_lon_range = lon_range
    else:
        map_lon_range = [0,360]
    fig_map.update_geos(projection_type="natural earth2",
                    lataxis_showgrid=True, lonaxis_showgrid=True,
                    lataxis={'dtick':15,'gridcolor':'darkgrey','gridwidth':0.5,'griddash':'2px'},
                    lonaxis={'dtick':15,'gridcolor':'darkgrey','gridwidth':0.5,'griddash':'2px'},
                    lonaxis_range=map_lon_range)
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    fig_map.update_layout(legend={'yanchor':'top', 'y':0.90})

    return fig, fig_map


############### 4. Initialize the app. ###################
if __name__ == '__main__':
    app.run_server(debug=True)





    
