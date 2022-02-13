"""
Dashboard for Yahoo Finance indices

@author: Wai Lun

"""
# Run in command prompt: "C:\Users\wailu\Documents\Git\Models\market_dashboard_prototype\app\index.py"

# Import libraries
from app import app, server
from support.dash_layouts import start_layout
import support.dash_callbacks

# Start app
app.layout = start_layout

if __name__ == '__main__':
    app.run_server(debug=False)
