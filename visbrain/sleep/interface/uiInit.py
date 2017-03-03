"""This script group the diffrent graphical components.

Grouped components :
    * PyQt elements (window, Pyqt functions...)
    * Vispy canvas functions
    * User shortcuts
"""

from PyQt4 import QtGui
from vispy import app, scene

from .gui import Ui_MainWindow

__all__ = ['uiInit']


class uiInit(QtGui.QMainWindow, Ui_MainWindow, app.Canvas):
    """Group and initialize the graphical elements and interactions."""

    def __init__(self):
        """Init."""
        # Create the main window :
        super(uiInit, self).__init__(None)
        self.setupUi(self)

        # Initialize shortcuts :
        # vbShortcuts.__init__(self, self._ndCanvas.canvas)


class AxisCanvas(object):
    """Create a canvas with an embeded axis."""

    def __init__(self, axis=True, x_label='', x_heightMax=80, y_label='',
                 y_widthMax=80, font_size=12, color='white', title='',
                 axis_label_margin=50, tick_label_margin=5, name='',
                 bgcolor=(.9, .9, .9), cargs={}, xargs={}, yargs={}):
        """Init."""
        # Save variables :
        self._axis = axis
        self._title = title
        self._xlabel = x_label
        self._ylabel = y_label

        # Create the main canvas :
        self.canvas = scene.SceneCanvas(keys='interactive', bgcolor=bgcolor,
                                        show=True, title=name, **cargs)

        # Add axis :
        if axis:
            # Create a grid :
            grid = self.canvas.central_widget.add_grid(margin=10)
            grid.spacing = 0

            # Add a title :
            self._titleObj = scene.Label(title, color=color)
            self._titleObj.height_max = 40
            grid.add_widget(self._titleObj, row=0, col=0, col_span=2)

            # Add y-axis :
            self.yaxis = scene.AxisWidget(orientation='left', domain=(0, 129),
                                          axis_label=y_label,
                                          axis_font_size=font_size,
                                          axis_label_margin=axis_label_margin,
                                          tick_label_margin=tick_label_margin,
                                          **yargs)
            self.yaxis.width_max = y_widthMax
            grid.add_widget(self.yaxis, row=1, col=0)

            # Add x-axis :
            self.xaxis = scene.AxisWidget(orientation='bottom',
                                          axis_label=x_label,
                                          axis_font_size=font_size,
                                          axis_label_margin=axis_label_margin,
                                          tick_label_margin=tick_label_margin,
                                          **xargs)
            self.xaxis.height_max = x_heightMax
            grid.add_widget(self.xaxis, row=2, col=1)

            # Add right padding :
            self._rpad = grid.add_widget(row=1, col=2, row_span=1)
            self._rpad.width_max = 50

            # Main plot :
            self.wc = grid.add_view(row=1, col=1, border_color=color)

        # Ignore axis :
        else:
            self.wc = self.canvas.central_widget.add_view()

    def set_camera(self, camera):
        """Set a camera and link all objects inside."""
        # Set camera to the main widget :
        self.wc.camera = camera
        # Link transformations with axis :
        if self._axis:
            self.xaxis.link_view(self.wc)
            self.yaxis.link_view(self.wc)

    def set_info(self, title=None, xlabel=None, ylabel=None):
        """Set title and labels for the axis of the canvas."""
        # Set label / title only for grid axis :
        if self._axis:
            # X-label :
            if xlabel is not None:
                self.xaxis.axis.axis_label = xlabel
                self.xaxis.update()
            # Y-label :
            if ylabel is not None:
                self.yaxis.axis.axis_label = ylabel
                self.yaxis.update()
            # Title :
            if title is not None:
                self._titleObj.text = title
            self.canvas.update()
        else:
            raise ValueError("For defining infos, you must use an axis canvas")

    def visible_axis(self, visible=True):
        """Display or hide the axis."""
        self._axis = visible
        self.xaxis.visible = visible
        self.yaxis.visible = visible
        self._titleObj.visible = visible
        self._rpad.visible = visible


class vbShortcuts(object):
    """This class add some shortcuts to the main canvas of vbrain.

    It's also use to initialize to panel of shortcuts.

    Args:
        canvas: vispy canvas
            Vispy canvas to add the shortcuts.
    """

    def __init__(self, canvas):
        """Init."""
        # Add shortcuts to vbCanvas :
        @canvas.events.key_press.connect
        def on_key_press(event):
            """Executed function when a key is pressed on a keyboard over vbrain canvas.

            :event: the trigger event
            """
            if event.text == ' ':
                pass
            if event.text == 'r':
                pass
            if event.text == '0':
                pass

        @canvas.events.mouse_release.connect
        def on_mouse_release(event):
            """Executed function when the mouse is pressed over vbrain canvas.

            :event: the trigger event
            """
            pass

        @canvas.events.mouse_double_click.connect
        def on_mouse_double_click(event):
            """Executed function when double click mouse over vbrain canvas.

            :event: the trigger event
            """
            pass

        @canvas.events.mouse_move.connect
        def on_mouse_move(event):
            """Executed function when the mouse move over vbrain canvas.

            :event: the trigger event
            """
            # Display the rotation panel and set informations :
            pass

        @canvas.events.mouse_press.connect
        def on_mouse_press(event):
            """Executed function when single click mouse over vbrain canvas.

            :event: the trigger event
            """
            # Display the rotation panel :
            pass
