from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates


class MplCanvas(FigureCanvas):
    """Enhanced matplotlib canvas with interactive features"""

    def __init__(self, parent=None, width=12, height=8, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax = self.fig.add_subplot(111)

        super().__init__(self.fig)

        # Style the plot
        self.fig.patch.set_facecolor('#FFFFFF')
        self.ax.set_facecolor('#FAFBFC')

        # Interactive features
        self.plot_line = None
        self.hover_annotation = None
        self.current_data = None
        self.zoom_scale = 1.1  # 10% zoom per scroll

        # Connect events
        self.mpl_connect('scroll_event', self.on_scroll)
        self.mpl_connect('motion_notify_event', self.on_hover)

        # Initialize annotation (invisible by default)
        self.setup_annotation()

    def setup_annotation(self):
        """Setup the hover annotation box"""
        self.hover_annotation = self.ax.annotate(
            '',
            xy=(0, 0),
            xytext=(20, 20),
            textcoords='offset points',
            bbox=dict(
                boxstyle='round,pad=0.8',
                facecolor='#2c3e50',
                edgecolor='#007BFF',
                alpha=0.95,
                linewidth=2
            ),
            color='white',
            fontsize=10,
            fontweight='bold',
            arrowprops=dict(
                arrowstyle='->',
                connectionstyle='arc3,rad=0.3',
                color='#007BFF',
                linewidth=2
            ),
            zorder=1000,
            visible=False
        )

    def on_scroll(self, event):
        """Handle mouse scroll for zooming"""
        if event.inaxes != self.ax:
            return

        # Get current axis limits
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        # Get mouse position in data coordinates
        xdata = event.xdata
        ydata = event.ydata

        if xdata is None or ydata is None:
            return

        # Determine zoom direction
        if event.button == 'up':
            # Zoom in
            scale_factor = 1 / self.zoom_scale
        elif event.button == 'down':
            # Zoom out
            scale_factor = self.zoom_scale
        else:
            return

        # Calculate new limits centered on mouse position
        new_width = (xlim[1] - xlim[0]) * scale_factor
        new_height = (ylim[1] - ylim[0]) * scale_factor

        relx = (xlim[1] - xdata) / (xlim[1] - xlim[0])
        rely = (ylim[1] - ydata) / (ylim[1] - ylim[0])

        new_xlim = [
            xdata - new_width * (1 - relx),
            xdata + new_width * relx
        ]
        new_ylim = [
            ydata - new_height * (1 - rely),
            ydata + new_height * rely
        ]

        # Apply new limits
        self.ax.set_xlim(new_xlim)
        self.ax.set_ylim(new_ylim)

        # Redraw
        self.draw_idle()

    def on_hover(self, event):
        """Handle mouse hover to show data point values"""
        if event.inaxes != self.ax or self.current_data is None:
            if self.hover_annotation:
                self.hover_annotation.set_visible(False)
                self.draw_idle()
            return

        # Check if we have plot data
        if self.plot_line is None:
            return

        # Get the data from the line
        x_data, y_data = self.current_data

        if len(x_data) == 0 or len(y_data) == 0:
            return

        # Find the closest point
        mouse_x = event.xdata
        mouse_y = event.ydata

        if mouse_x is None or mouse_y is None:
            return

        # Convert datetime to numeric for distance calculation
        if hasattr(x_data.iloc[0], 'timestamp'):
            x_numeric = [x.timestamp() for x in x_data]
            mouse_x_numeric = mdates.date2num(mouse_x)
            # Convert back to timestamp scale
            mouse_x_numeric = mdates.num2date(mouse_x_numeric).timestamp()
        else:
            x_numeric = x_data
            mouse_x_numeric = mouse_x

        # Calculate distances to all points
        distances = []
        for i, (x, y) in enumerate(zip(x_numeric, y_data)):
            # Normalize by axis ranges for fair comparison
            xlim = self.ax.get_xlim()
            ylim = self.ax.get_ylim()

            if hasattr(xlim[0], 'timestamp'):
                x_range = mdates.date2num(xlim[1]) - mdates.date2num(xlim[0])
            else:
                x_range = xlim[1] - xlim[0]

            y_range = ylim[1] - ylim[0]

            if x_range == 0 or y_range == 0:
                continue

            dx = (x - mouse_x_numeric) / x_range
            dy = (y - mouse_y) / y_range

            dist = (dx**2 + dy**2)**0.5
            distances.append((dist, i))

        if not distances:
            return

        # Get closest point
        distances.sort()
        _, closest_idx = distances[0]

        # Only show annotation if mouse is close enough to a point
        if distances[0][0] > 0.1:  # Threshold for showing tooltip
            self.hover_annotation.set_visible(False)
            self.draw_idle()
            return

        # Get the closest point data
        closest_x = x_data.iloc[closest_idx]
        closest_y = y_data.iloc[closest_idx]

        # Format the annotation text
        if hasattr(closest_x, 'strftime'):
            time_str = closest_x.strftime('%Y-%m-%d %H:%M:%S')
        else:
            time_str = str(closest_x)

        # Determine the unit based on axis label
        ylabel = self.ax.get_ylabel().lower()
        if 'temp' in ylabel:
            unit = '°C'
        elif 'pressure' in ylabel:
            unit = ' Pa'
        elif 'humidity' in ylabel:
            unit = '%'
        elif 'wind' in ylabel:
            unit = ' m/s'
        else:
            unit = ''

        annotation_text = f'{time_str}\nValue: {closest_y:.2f}{unit}'

        # Update annotation
        self.hover_annotation.set_text(annotation_text)
        self.hover_annotation.xy = (closest_x, closest_y)
        self.hover_annotation.set_visible(True)

        # Adjust annotation position to stay within plot
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        # Calculate relative position
        if hasattr(closest_x, 'timestamp'):
            x_numeric = mdates.date2num(closest_x)
            x_range_num = mdates.date2num(xlim[1]) - mdates.date2num(xlim[0])
            x_rel = (x_numeric - mdates.date2num(xlim[0])) / x_range_num
        else:
            x_rel = (closest_x - xlim[0]) / (xlim[1] - xlim[0])

        y_rel = (closest_y - ylim[0]) / (ylim[1] - ylim[0])

        # Flip annotation to left if point is on right side
        if x_rel > 0.7:
            self.hover_annotation.set_position((-100, 20))
        else:
            self.hover_annotation.set_position((20, 20))

        # Flip annotation down if point is on top
        if y_rel > 0.7:
            self.hover_annotation.set_position((self.hover_annotation.xyann[0], -60))

        # Redraw
        self.draw_idle()

    def plot_data(self, x, y, **kwargs):
        """Plot data and store for hover functionality"""
        self.current_data = (x, y)
        self.plot_line = self.ax.plot(x, y, **kwargs)
        return self.plot_line

    def reset_view(self):
        """Reset zoom to show all data"""
        self.ax.autoscale()
        self.draw_idle()