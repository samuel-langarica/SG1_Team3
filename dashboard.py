import dash
from dash import dcc, html
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from data_processor import (
    calculate_overall_production,
    calculate_workstation_occupancy,
    calculate_average_waiting_time,
    get_workstation_status_partition
)

def create_dashboard(factory, simulation_time):
    app = dash.Dash(__name__)
    
    # Calculate all required metrics
    total_production, production_rate = calculate_overall_production(factory, simulation_time)
    faulty_rate = (factory.faulty_products / (factory.faulty_products + total_production)) * 100
    occupancy_rates = calculate_workstation_occupancy(factory, simulation_time)
    waiting_times = calculate_average_waiting_time(factory)
    status_partitions = get_workstation_status_partition(factory, [(0, simulation_time)])
    
    # Create occupancy rate bar chart
    occupancy_df = pd.DataFrame({
        'Station': list(occupancy_rates.keys()),
        'Occupancy Rate': [rate * 100 for rate in occupancy_rates.values()]
    }).sort_values('Occupancy Rate', ascending=False)
    
    occupancy_fig = go.Figure(data=[
        go.Bar(
            x=occupancy_df['Station'],
            y=occupancy_df['Occupancy Rate'],
            marker_color='rgb(55, 83, 109)'
        )
    ])
    occupancy_fig.update_layout(
        title='Workstation Occupancy Rates',
        xaxis_title='Station ID',
        yaxis_title='Occupancy Rate (%)',
        yaxis_range=[0, 100]
    )
    
    # Waiting time bar chart
    waiting_df = pd.DataFrame({
        'Station': list(waiting_times.keys()),
        'Average Waiting Time': list(waiting_times.values())
    }).sort_values('Average Waiting Time', ascending=False)
    
    # list of colors, highlighting station 3
    colors = ['rgb(55, 83, 109)' if station != 3 else 'rgb(255, 0, 0)' 
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
        yaxis_title='Average Waiting Time (time units)'
    )
    
    # status partition visualization
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
        labels={'Percentage': 'Percentage of Time (%)'}
    )
    
    # dashboard layout
    app.layout = html.Div([
        # Top Section: KPIs
        html.Div([
            html.H1('Manufacturing Process Dashboard', style={'textAlign': 'center'}),
            html.Div([
                html.Div([
                    html.H2('Total Production'),
                    html.H3(f"{total_production:,}", style={'color': 'rgb(55, 83, 109)'})
                ], style={'textAlign': 'center', 'padding': '20px'}),
                html.Div([
                    html.H2('Faulty Product Rate'),
                    html.H3(f"{faulty_rate:.2f}%", style={'color': 'rgb(255, 0, 0)'})
                ], style={'textAlign': 'center', 'padding': '20px'})
            ], style={'display': 'flex', 'justifyContent': 'space-around'})
        ], style={'marginBottom': '30px'}),
        
        # Middle Section: Bottleneck Analysis
        html.Div([
            # Row 1: Occupancy and Waiting Time
            html.Div([
                html.Div([
                    dcc.Graph(figure=occupancy_fig)
                ], style={'width': '48%', 'display': 'inline-block'}),
                html.Div([
                    dcc.Graph(figure=waiting_fig)
                ], style={'width': '48%', 'display': 'inline-block'})
            ], style={'display': 'flex', 'justifyContent': 'space-between'}),
            
            # Row 2: Status Partition
            html.Div([
                dcc.Graph(figure=status_fig)
            ], style={'marginTop': '30px'})
        ]),
        
        # Bottom Section: Key Findings
        html.Div([
            html.H2('Key Findings and Recommendations'),
            html.P("""
                The dashboard indicates that while all workstations are highly occupied, Station 3 experiences 
                the highest average waiting time, suggesting it is a primary bottleneck. Addressing potential 
                issues leading to delays before Station 3 could improve overall production flow. Downtime and 
                waiting for restock appear to be less significant factors currently.
            """),
            html.H3('Recommended Next Steps:'),
            html.Ul([
                html.Li('Investigate processes leading to delays before Station 3'),
                html.Li('Analyze the workload and capacity of Station 3'),
                html.Li('Consider process optimization or resource reallocation for Station 3'),
                html.Li('Monitor the impact of any changes on the overall production flow')
            ])
        ], style={'marginTop': '30px', 'padding': '20px', 'backgroundColor': '#f8f9fa'})
    ], style={'padding': '20px'})
    
    return app

if __name__ == '__main__':
    from main import Factory, simpy
    env = simpy.Environment()
    factory = Factory(env)
    env.run(until=5000)
    
    app = create_dashboard(factory, env.now)
    app.run_server(debug=True) 