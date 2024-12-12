from app.dashboard_server import OWLDashboardServer

if __name__ == "__main__":
    dashboard = OWLDashboardServer(port=5000)
    dashboard.run()