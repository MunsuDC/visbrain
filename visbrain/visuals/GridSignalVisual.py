"""Display signals into a grid..

A large portion of this code was taken from the example developped by the vispy
team :
https://github.com/vispy/vispy/blob/master/examples/demo/gloo/realtime_signals.py
"""

import numpy as np

from vispy import gloo, visuals
from vispy.scene.visuals import create_visual_node

from visbrain.utils import color2vb, vispy_array, PrepareData, ndsubplot


__all__ = ('GridSignalMesh')


vertex_shader = """
#version 120
varying vec3 v_index;
varying vec4 v_color;
// Varying variables used for clipping in the fragment shader.
varying vec2 v_position;
varying vec4 v_ab;
varying vec3 a_pos;
void main() {
    float nrows = $u_size.x;
    float ncols = $u_size.y;
    // Compute the x coordinate from the time index.
    float x = -1 + 2*$a_index.z / ($u_n-1);
    // Turn position into a vec3 :
    a_pos = vec3($a_position, 1, 1);
    vec2 position = vec2(x - (1 - 1 / $u_scale.x), a_pos);
    // Find the affine transformation for the subplots.
    vec2 a = vec2(1./ncols, 1./nrows)*.98;
    vec2 b = vec2(-1 + $u_space*($a_index.x+.5) / ncols,
                  -1 + $u_space*($a_index.y+.5) / nrows);
    // Apply the static subplot transformation + scaling.
    gl_Position = $transform(vec4(a*$u_scale*position+b, 0.0, 1.0));
    v_color = vec4($a_color, 1.);
    v_index = $a_index;
    // For clipping test in the fragment shader.
    v_position = gl_Position.xy;
}
"""

fragment_shader = """
#version 120
varying vec4 v_color;
varying vec3 v_index;
varying vec2 v_position;
void main() {
    gl_FragColor = v_color;

    // Discard the fragments between the signals (emulate glMultiDrawArrays).
    if ((fract(v_index.x) > 0.) || (fract(v_index.y) > 0.))
        discard;
}
"""


class GridSignalVisual(visuals.Visual):
    """Visual class for grid of signals.

    Parameters
    ----------
    data : array_like
        Array of data. Could be 1-D, 2-D or 3-D.
    axis : int | -1
        Time axis location.
    sf : float | 1.
        The sampling frequency (used for filtering).
    random : array_like/string/tuple | 'random'
        Use 'random' for random colors or a color name for uniform color.
    space : float | 2.
        Space between subplots.
    scale : tuple | (1., 1.)
        Tuple descigin the scaling along the x and y-axis.
    """

    def __len__(self):
        """Return the number of time points."""
        return self._n

    def __init__(self, data, axis=-1, sf=1., color='random', space=2.,
                 scale=(1., 1.)):
        """Init."""
        # =========================== CHECKING ===========================
        assert isinstance(data, np.ndarray) and (data.ndim <= 3)
        assert isinstance(axis, int)
        assert isinstance(sf, (int, float))
        assert isinstance(space, (int, float))
        assert isinstance(scale, (tuple, list)) and len(scale) == 2

        # =========================== VISUALS ===========================
        visuals.Visual.__init__(self, vertex_shader, fragment_shader)

        self.set_gl_state('translucent', depth_test=True, cull_face=False,
                          blend=True, blend_func=('src_alpha',
                                                  'one_minus_src_alpha'))
        self._draw_mode = 'line_strip'

        # =========================== DATA ===========================
        # Keep some inputs :
        self._sh = data.shape
        self._n = self._sh[axis]
        self._axis = axis
        self._sf = sf
        self._color = color
        self.scale = scale
        self.space = space
        self._prep = PrepareData(axis=-1)

        # =========================== BUFFERS ===========================
        # Create buffers (for data, index and color)
        rnd_1 = np.zeros((3,), dtype=np.float32)
        rnd_3 = np.zeros((1, 3), dtype=np.float32)
        self._dbuffer = gloo.VertexBuffer(rnd_1)
        self._ibuffer = gloo.VertexBuffer(rnd_3)
        self._cbuffer = gloo.VertexBuffer(rnd_3)
        # Send to the program :
        self.shared_program.vert['a_position'] = self._dbuffer
        self.shared_program.vert['a_index'] = self._ibuffer
        self.shared_program.vert['a_color'] = self._cbuffer
        self.shared_program.vert['u_size'] = (1, 1)
        self.shared_program.vert['u_n'] = len(self)

        # Set data :
        self.set_data(data, axis, color)
        self.freeze()

    def set_data(self, data=None, axis=None, color=None):
        """Set data to the grid of signals.

        Parameters
        ----------
        data : None
            Array of data. Could be 1-D, 2-D or 3-D.
        axis : int | None
            Time axis location.
        random : array_like/string/tuple | 'random'
            Use 'random' for random colors or a color name for uniform color.
        space : float | None
            Space between subplots.
        scale : tuple | None
            Tuple descigin the scaling along the x and y-axis.
        """
        rnd_dyn = (.2, .8)  # random color range
        # ====================== CHECKING ======================
        # Axis :
        axis = axis if isinstance(axis, int) else self._axis
        axis = len(self._sh) - 1 if axis == -1 else axis

        # ====================== CHECKING ======================
        # Data :
        if isinstance(data, np.ndarray):
            # -------------- (n_rows, n_cols, n_time) --------------
            if data.ndim == 1:  # 1-D array
                data = data.reshape(1, 1, -1)
                g_size = (1, 1)
            elif data.ndim == 2:  # 2-D array
                if axis == 0:  # data need to be transposed
                    data = np.swapaxes(data, 0, 1)
                    axis = 1
                g_size = (data.shape[0], 1)  # (n_row, 1)
                data = data[np.newaxis, ...]
            elif data.ndim == 3:  # 3-D array
                if axis != data.ndim - 1:  # data need to be transposed
                    data = np.swapaxes(data, axis, -1)
                    axis = data.ndim - 1
                g_size = (data.shape[0], data.shape[1])

            # -------------- Signals index --------------
            m = np.prod(list(data.shape)[0:-1])
            sig_index = np.arange(m).reshape(*g_size)

            # -------------- Optimal 2-D --------------
            force_2d = True
            self._ori_shape = list(data.shape)[0:-1]
            if force_2d:
                opt_rows, opt_cols = ndsubplot(m)
                data = data.reshape(opt_rows, opt_cols, len(self))
                sig_index = sig_index.reshape(opt_rows, opt_cols)
                g_size = (opt_rows, opt_cols)
            self._opt_shape = list(data.shape)[0:-1]
            self._sig_index = np.flipud(sig_index)

            # -------------- (n_rows * n_cols, n_time) --------------
            data = np.reshape(data, (m, len(self)), order='F')

            # -------------- Prepare --------------
            # Force demean / detrend of _prep :
            self._prep.demean, self._prep.detrend = False, False
            data = self._prep._prepare_data(self._sf, data, 0)
            # Demean and normalize :
            kw = {'axis': -1, 'keepdims': True}
            data -= data.mean(**kw)
            data /= np.abs(data).max(**kw)

            # -------------- Index --------------
            (n_rows, n_cols), n = g_size, len(self)
            index = np.c_[np.repeat(np.repeat(np.arange(n_cols), n_rows), n),
                          np.repeat(np.tile(np.arange(n_rows), n_cols), n),
                          np.tile(np.arange(n), m)].astype(np.float32)

            # -------------- Buffer --------------
            self._dbuffer.set_data(vispy_array(data))
            self._ibuffer.set_data(vispy_array(index))
            self.shared_program.vert['u_size'] = g_size
            self._g_size = g_size

        # ====================== COLOR ======================
        if color is not None:
            g_size = np.array(self._g_size)
            m = g_size.prod()  # n_row x n_col
            n = len(self)
            if color == 'random':  # (m, 3) random color
                singcol = np.random.uniform(size=(m, 3), low=rnd_dyn[0],
                                            high=rnd_dyn[1]).astype(np.float32)
            elif color is not None:  # (m, 3) uniform color
                singcol = color2vb(color, length=m)[:, 0:3]
            # Repeat the array n_times to have a (m * n_times, 3) array :
            a_color = np.repeat(singcol, n, axis=0)
            # Send color to buffer :
            self._cbuffer.set_data(vispy_array(a_color))

    def clean(self):
        """Clean buffers."""
        self._dbuffer.delete()
        self._ibuffer.delete()
        self._cbuffer.delete()

    def _convert_row_cols(self, row, col):
        """Convert row and col according to the optimal grid."""
        try:
            index = self._sig_index[row, col]
            idx = np.where(self._sig_index.reshape(*self._ori_shape) == index)
            return idx[0][0], idx[1][0]
        except:
            return row, col

    def _prepare_transforms(self, view):
        """Call for the first rendering."""
        tr = view.transforms
        view_vert = view.view_program.vert
        view_vert['transform'] = tr.get_transform()

    # def _prepare_draw(self, view=None):
    #     """Function called everytime there's a camera update."""
    #     pass

    # ========================================================================
    # ========================================================================
    # PROPERTIES
    # ========================================================================
    # ========================================================================
    # ----------- SCALE -----------
    @property
    def scale(self):
        """Get the scale value."""
        return self._scale

    @scale.setter
    def scale(self, value):
        """Set scale value."""
        if isinstance(value, tuple):
            self._uscale = value
            self._scale = value
            self.shared_program.vert['u_scale'] = value
            self.update()

    # ----------- SPACE -----------
    @property
    def space(self):
        """Get the space value."""
        return self._space

    @space.setter
    def space(self, value):
        """Set space value."""
        if isinstance(value, float):
            self._space = value
            self.shared_program.vert['u_space'] = value
            self.update()

    # ----------- RECT -----------
    @property
    def rect(self):
        return (-1.05, -1.1, self._space + .1, self._space + .2)

    # ----------- COLOR -----------
    @property
    def color(self):
        """Get the color value."""
        return self._color

    @color.setter
    def color(self, value):
        """Set color value."""
        self._color = value
        self.set_data(color=value)


GridSignalMesh = create_visual_node(GridSignalVisual)
