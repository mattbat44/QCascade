import plotly.graph_objects as go
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import QDockWidget, QVBoxLayout, QWidget

class PlotWidget(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Plot", parent)
        
        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)
        
        self.setWidget(self.container)
        
        # Show empty plot initially
        self.show_empty_plot()

    def show_empty_plot(self):
        fig = go.Figure()
        fig.update_layout(
            title="No Results Loaded",
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[
                {
                    "text": "Run a simulation to see results",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 20}
                }
            ]
        )
        self.set_plot(fig)

    def set_plot(self, fig):
        html = fig.to_html(include_plotlyjs='cdn')
        self.web_view.setHtml(html)

    def update_plot(self, data):
        # Placeholder for actual data plotting logic
        # 'data' would be the loaded results (e.g., from pickle files)
        pass
