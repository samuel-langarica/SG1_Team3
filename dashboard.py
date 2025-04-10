import dash
from dash import dcc, html
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from data_processor import (
    calculate_overall_production,
    calculate_workstation_occupancy,
    calculate_average_waiting_time,
    get_workstation_status_partition,
    get_time_period_range
)
from datetime import datetime, timedelta

# Theme colors
THEME = {
    'background': '#1a1a1a',
    'text': '#ffffff',
    'accent': '#00ff9d',
    'secondary': '#00b8ff',
    'card': '#2d2d2d',
    'border': '#404040',
    'warning': '#ff4d4d'
}

def create_dashboard(factory, simulation_time):
    app = dash.Dash(__name__)
    
    # Calculate all required metrics
    total_production, production_rate = calculate_overall_production(factory, simulation_time)
    faulty_rate = (factory.faulty_products / (factory.faulty_products + total_production)) * 100
    occupancy_rates = calculate_workstation_occupancy(factory, simulation_time)
    waiting_times = calculate_average_waiting_time(factory)
    status_partitions = get_workstation_status_partition(factory, [(0, simulation_time)])
    
    # Create production trend data
    production_trend = []
    for station in factory.stations:
        for event in station.status_history:
            if event['status'] == 'Operational':
                production_trend.append({
                    'timestamp': event['timestamp'],
                    'production': 1
                })
    
    production_df = pd.DataFrame(production_trend)
    production_df['timestamp'] = pd.to_datetime(production_df['timestamp'], unit='s')
    production_df = production_df.sort_values('timestamp')
    production_df['cumulative_production'] = production_df['production'].cumsum()
    
    # Create production trend figure with dark theme
    production_trend_fig = go.Figure(data=[
        go.Scatter(
            x=production_df['timestamp'],
            y=production_df['cumulative_production'],
            mode='lines',
            name='Total Production',
            line=dict(color=THEME['accent'], width=2)
        )
    ])
    production_trend_fig.update_layout(
        title='Production Trend Over Time',
        xaxis_title='Time',
        yaxis_title='Total Production',
        showlegend=True,
        plot_bgcolor=THEME['card'],
        paper_bgcolor=THEME['background'],
        font=dict(color=THEME['text']),
        xaxis=dict(gridcolor=THEME['border']),
        yaxis=dict(gridcolor=THEME['border'])
    )
    
    # Create occupancy rate bar chart with dark theme
    occupancy_df = pd.DataFrame({
        'Station': list(occupancy_rates.keys()),
        'Occupancy Rate': [rate * 100 for rate in occupancy_rates.values()]
    }).sort_values('Occupancy Rate', ascending=False)
    
    occupancy_fig = go.Figure(data=[
        go.Bar(
            x=occupancy_df['Station'],
            y=occupancy_df['Occupancy Rate'],
            marker_color=THEME['secondary']
        )
    ])
    occupancy_fig.update_layout(
        title='Workstation Occupancy Rates',
        xaxis_title='Station ID',
        yaxis_title='Occupancy Rate (%)',
        yaxis_range=[0, 100],
        plot_bgcolor=THEME['card'],
        paper_bgcolor=THEME['background'],
        font=dict(color=THEME['text']),
        xaxis=dict(gridcolor=THEME['border']),
        yaxis=dict(gridcolor=THEME['border'])
    )
    
    # Waiting time bar chart with dark theme
    waiting_df = pd.DataFrame({
        'Station': list(waiting_times.keys()),
        'Average Waiting Time': list(waiting_times.values())
    }).sort_values('Average Waiting Time', ascending=False)
    
    colors = [THEME['secondary'] if station != 3 else THEME['warning'] 
              for station in waiting_df['Station']]
    
    waiting_fig = go.Figure(data=[
        go.Bar(
            x=waiting_df['Station'],
            y=waiting_df['Average Waiting Time'],
            marker_color=colors
        )
    ])
    waiting_fig.update_layout(
        title='Average Waiting Time per Workstation',
        xaxis_title='Station ID',
        yaxis_title='Average Waiting Time (hours)',
        plot_bgcolor=THEME['card'],
        paper_bgcolor=THEME['background'],
        font=dict(color=THEME['text']),
        xaxis=dict(gridcolor=THEME['border']),
        yaxis=dict(gridcolor=THEME['border'])
    )
    
    # status partition visualization with dark theme
    status_data = []
    for station_id, statuses in status_partitions.items():
        for status, percentage in statuses.items():
            status_data.append({
                'Station': station_id,
                'Status': status,
                'Percentage': percentage * 100
            })
    
    status_df = pd.DataFrame(status_data)
    status_fig = px.bar(
        status_df,
        x='Station',
        y='Percentage',
        color='Status',
        barmode='group',
        title='Workstation Status Partition',
        labels={'Percentage': 'Percentage of Time (%)'},
        color_discrete_sequence=[THEME['accent'], THEME['warning'], THEME['secondary']]
    )
    status_fig.update_layout(
        plot_bgcolor=THEME['card'],
        paper_bgcolor=THEME['background'],
        font=dict(color=THEME['text']),
        xaxis=dict(gridcolor=THEME['border']),
        yaxis=dict(gridcolor=THEME['border'])
    )
    
    # dashboard layout
    app.layout = html.Div([
        # Fixed Header with Title and Time Period Selection
        html.Div([
            html.H1('The Factory 🏭', style={
                'textAlign': 'center', 
                'marginBottom': '10px',
                'color': THEME['accent'],
                'fontFamily': 'monospace',
                'letterSpacing': '2px'
            }),
            html.Div([
                html.Label('Select Time Period:', style={
                    'marginRight': '10px', 
                    'fontSize': '20px',
                    'color': THEME['text'],
                    'fontFamily': 'monospace'
                }),
                dcc.Dropdown(
                    id='time-period-dropdown',
                    options=[
                        {'label': 'Day', 'value': 'day'},
                        {'label': 'Week', 'value': 'week'},
                        {'label': 'Month', 'value': 'month'},
                        {'label': 'Quarter', 'value': 'quarter'},
                        {'label': 'Year', 'value': 'year'}
                    ],
                    value='day',
                    style={
                        'width': '200px', 
                        'display': 'inline-block',
                        'backgroundColor': THEME['card'],
                        'color': THEME['text'],
                        'border': f'1px solid {THEME["border"]}'
                    }
                )
            ], style={'textAlign': 'center', 'marginBottom': '20px'})
        ], style={
            'position': 'fixed',
            'top': '0',
            'width': '100%',
            'backgroundColor': THEME['background'],
            'padding': '20px',
            'zIndex': '1000',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.3)'
        }),
        
        # Main Content (with padding to account for fixed header)
        html.Div([
            # Welcome Message
            html.Div([
                html.H2('Welcome to Your Factory Dashboard! 👋', style={
                    'textAlign': 'center', 
                    'color': THEME['accent'],
                    'fontFamily': 'monospace',
                    'letterSpacing': '1px'
                }),
                html.Div([
                    html.P([
                        "Hey there! This dashboard gives you a complete overview of your factory's performance. ",
                        html.Span("📊", style={'fontSize': '20px'}),
                        " You can see how things are going at a glance with our key metrics, or dive deep into the details. ",
                        html.Span("🔍", style={'fontSize': '20px'}),
                    ], style={'textAlign': 'center', 'fontSize': '18px', 'marginBottom': '10px', 'color': THEME['text']}),
                    html.P([
                        "Use the time period selector above to view data for different timeframes - from a day to a full year. ",
                        html.Span("⏰", style={'fontSize': '20px'}),
                        " All the charts and numbers will update automatically! ",
                        html.Span("✨", style={'fontSize': '20px'}),
                    ], style={'textAlign': 'center', 'fontSize': '18px', 'marginBottom': '10px', 'color': THEME['text']}),
                    html.P([
                        "Keep an eye on Station 3, it is highlighted in red because it is the current bottleneck. ",
                        html.Span("⚠️", style={'fontSize': '20px'}),
                        " We got some recommendations at the bottom to help improve things! ",
                        html.Span("💡", style={'fontSize': '20px'}),
                    ], style={'textAlign': 'center', 'fontSize': '18px', 'color': THEME['text']})
                ], style={
                    'backgroundColor': THEME['card'],
                    'padding': '20px',
                    'borderRadius': '10px',
                    'marginBottom': '30px',
                    'border': f'1px solid {THEME["border"]}'
                })
            ], style={'marginTop': '180px'}),
            
            # Top Section: KPIs
            html.Div([
                html.Div([
                    html.Div([
                        html.H2('Total Production', style={'color': THEME['text'], 'fontFamily': 'monospace'}),
                        html.H3(id='total-production', children=f"{total_production:,}", 
                               style={'color': THEME['accent'], 'fontSize': '32px', 'marginTop': '10px'})
                    ], style={
                        'textAlign': 'center', 
                        'padding': '30px',
                        'backgroundColor': THEME['card'],
                        'borderRadius': '10px',
                        'border': f'1px solid {THEME["border"]}',
                        'margin': '10px',
                        'flex': '1'
                    }),
                    html.Div([
                        html.H2('Faulty Product Rate', style={'color': THEME['text'], 'fontFamily': 'monospace'}),
                        html.H3(id='faulty-rate', children=f"{faulty_rate:.2f}%", 
                               style={'color': THEME['warning'], 'fontSize': '32px', 'marginTop': '10px'})
                    ], style={
                        'textAlign': 'center', 
                        'padding': '30px',
                        'backgroundColor': THEME['card'],
                        'borderRadius': '10px',
                        'border': f'1px solid {THEME["border"]}',
                        'margin': '10px',
                        'flex': '1'
                    })
                ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '30px'})
            ]),
            
            # Production Trend Graph
            html.Div([
                dcc.Graph(id='production-trend-graph', figure=production_trend_fig)
            ], style={'marginBottom': '30px'}),
            
            # Middle Section: Bottleneck Analysis
            html.Div([
                # Row 1: Occupancy and Waiting Time
                html.Div([
                    html.Div([
                        dcc.Graph(id='occupancy-graph', figure=occupancy_fig)
                    ], style={'width': '48%', 'display': 'inline-block'}),
                    html.Div([
                        dcc.Graph(id='waiting-graph', figure=waiting_fig)
                    ], style={'width': '48%', 'display': 'inline-block'})
                ], style={'display': 'flex', 'justifyContent': 'space-between'}),
                
                # Row 2: Status Partition
                html.Div([
                    dcc.Graph(id='status-graph', figure=status_fig)
                ], style={'marginTop': '30px'})
            ]),
            
            # Bottom Section: Key Findings
            html.Div([
                html.H2('Key Findings and Recommendations', style={'color': THEME['text'], 'fontFamily': 'monospace'}),
                html.P("""
                    The dashboard indicates that while all workstations are highly occupied, Station 3 experiences 
                    the highest average waiting time, suggesting it is a primary bottleneck. Addressing potential 
                    issues leading to delays before Station 3 could improve overall production flow. Downtime and 
                    waiting for restock appear to be less significant factors currently.
                """, style={'color': THEME['text']}),
                html.H3('Recommended Next Steps:', style={'color': THEME['text'], 'fontFamily': 'monospace'}),
                html.Ul([
                    html.Li('Investigate processes leading to delays before Station 3', style={'color': THEME['text']}),
                    html.Li('Analyze the workload and capacity of Station 3', style={'color': THEME['text']}),
                    html.Li('Consider process optimization or resource reallocation for Station 3', style={'color': THEME['text']}),
                    html.Li('Monitor the impact of any changes on the overall production flow', style={'color': THEME['text']})
                ])
            ], style={
                'marginTop': '30px', 
                'padding': '20px', 
                'backgroundColor': THEME['card'],
                'borderRadius': '10px',
                'border': f'1px solid {THEME["border"]}'
            })
        ], style={'padding': '20px', 'backgroundColor': THEME['background']})
    ], style={'backgroundColor': THEME['background']})
    
    # Callback to update all metrics and graphs based on time period selection
    @app.callback(
        [dash.dependencies.Output('total-production', 'children'),
         dash.dependencies.Output('faulty-rate', 'children'),
         dash.dependencies.Output('production-trend-graph', 'figure'),
         dash.dependencies.Output('occupancy-graph', 'figure'),
         dash.dependencies.Output('waiting-graph', 'figure'),
         dash.dependencies.Output('status-graph', 'figure')],
        [dash.dependencies.Input('time-period-dropdown', 'value')]
    )
    def update_metrics(time_period):
        # Calculate metrics for the selected time period
        total_production, production_rate = calculate_overall_production(factory, simulation_time, time_period)
        faulty_rate = (factory.faulty_products / (factory.faulty_products + total_production)) * 100
        occupancy_rates = calculate_workstation_occupancy(factory, simulation_time, time_period)
        waiting_times = calculate_average_waiting_time(factory, time_period)
        status_partitions = get_workstation_status_partition(factory, [(0, simulation_time)], time_period)
        
        # Update production trend graph
        if time_period:
            start_time, end_time = get_time_period_range(time_period, simulation_time)
            filtered_trend = [event for event in production_trend 
                            if start_time <= event['timestamp'] <= end_time]
            trend_df = pd.DataFrame(filtered_trend)
            trend_df['timestamp'] = pd.to_datetime(trend_df['timestamp'], unit='s')
            trend_df = trend_df.sort_values('timestamp')
            trend_df['cumulative_production'] = trend_df['production'].cumsum()
        else:
            trend_df = production_df
        
        production_trend_fig = go.Figure(data=[
            go.Scatter(
                x=trend_df['timestamp'],
                y=trend_df['cumulative_production'],
                mode='lines',
                name='Total Production',
                line=dict(color=THEME['accent'], width=2)
            )
        ])
        production_trend_fig.update_layout(
            title=f'Production Trend Over Time ({time_period.capitalize()})',
            xaxis_title='Time',
            yaxis_title='Total Production',
            showlegend=True,
            plot_bgcolor=THEME['card'],
            paper_bgcolor=THEME['background'],
            font=dict(color=THEME['text']),
            xaxis=dict(gridcolor=THEME['border']),
            yaxis=dict(gridcolor=THEME['border'])
        )
        
        # Update occupancy chart
        occupancy_df = pd.DataFrame({
            'Station': list(occupancy_rates.keys()),
            'Occupancy Rate': [rate * 100 for rate in occupancy_rates.values()]
        }).sort_values('Occupancy Rate', ascending=False)
        
        occupancy_fig = go.Figure(data=[
            go.Bar(
                x=occupancy_df['Station'],
                y=occupancy_df['Occupancy Rate'],
                marker_color=THEME['secondary']
            )
        ])
        occupancy_fig.update_layout(
            title=f'Workstation Occupancy Rates ({time_period.capitalize()})',
            xaxis_title='Station ID',
            yaxis_title='Occupancy Rate (%)',
            yaxis_range=[0, 100],
            plot_bgcolor=THEME['card'],
            paper_bgcolor=THEME['background'],
            font=dict(color=THEME['text']),
            xaxis=dict(gridcolor=THEME['border']),
            yaxis=dict(gridcolor=THEME['border'])
        )
        
        # Update waiting time chart
        waiting_df = pd.DataFrame({
            'Station': list(waiting_times.keys()),
            'Average Waiting Time': list(waiting_times.values())
        }).sort_values('Average Waiting Time', ascending=False)
        
        colors = [THEME['secondary'] if station != 3 else THEME['warning'] 
                  for station in waiting_df['Station']]
        
        waiting_fig = go.Figure(data=[
            go.Bar(
                x=waiting_df['Station'],
                y=waiting_df['Average Waiting Time'],
                marker_color=colors
            )
        ])
        waiting_fig.update_layout(
            title=f'Average Waiting Time per Workstation ({time_period.capitalize()})',
            xaxis_title='Station ID',
            yaxis_title='Average Waiting Time (hours)',
            plot_bgcolor=THEME['card'],
            paper_bgcolor=THEME['background'],
            font=dict(color=THEME['text']),
            xaxis=dict(gridcolor=THEME['border']),
            yaxis=dict(gridcolor=THEME['border'])
        )
        
        # Update status partition chart
        status_data = []
        for station_id, statuses in status_partitions.items():
            for status, percentage in statuses.items():
                status_data.append({
                    'Station': station_id,
                    'Status': status,
                    'Percentage': percentage * 100
                })
        
        status_df = pd.DataFrame(status_data)
        status_fig = px.bar(
            status_df,
            x='Station',
            y='Percentage',
            color='Status',
            barmode='group',
            title=f'Workstation Status Partition ({time_period.capitalize()})',
            labels={'Percentage': 'Percentage of Time (%)'},
            color_discrete_sequence=[THEME['accent'], THEME['warning'], THEME['secondary']]
        )
        status_fig.update_layout(
            plot_bgcolor=THEME['card'],
            paper_bgcolor=THEME['background'],
            font=dict(color=THEME['text']),
            xaxis=dict(gridcolor=THEME['border']),
            yaxis=dict(gridcolor=THEME['border'])
        )
        
        return (f"{total_production:,}", 
                f"{faulty_rate:.2f}%", 
                production_trend_fig, 
                occupancy_fig, 
                waiting_fig, 
                status_fig)
    
    return app

if __name__ == '__main__':
    from main import Factory, simpy, YEAR
    env = simpy.Environment()
    factory = Factory(env)
    # Run simulation for 1 year
    env.run(until=YEAR)
    
    app = create_dashboard(factory, env.now)
    app.run_server(debug=True) 