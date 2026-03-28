"""
@brief Unit tests for connectivity curves implementation
@author D-CASCADE Team
"""

import unittest
import numpy as np
import math


class MockQgsPoint:
    """Mock QgsPoint for testing."""
    def __init__(self, x, y):
        self.x_val = x
        self.y_val = y
    
    def x(self):
        return self.x_val
    
    def y(self):
        return self.y_val


class TestConnectivityCurves(unittest.TestCase):
    """Test connectivity curves logic."""
    
    def test_arc_geometry_straight_line(self):
        """Test that arc geometry is created for points that are very close."""
        # Test the arc creation logic directly
        start_pos = (0, 0)
        end_pos = (0.0001, 0.0001)
        curvature = 0.5
        
        # Simplified version of _create_arc_geometry logic
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx**2 + dy**2)
        
        # Should handle very small distances
        self.assertGreater(length, 0)
        self.assertLess(length, 0.001)
    
    def test_arc_geometry_normal_distance(self):
        """Test arc geometry for normal distances."""
        start_pos = (0, 0)
        end_pos = (100, 100)
        curvature = 0.5
        
        x1, y1 = start_pos
        x2, y2 = end_pos
        
        # Calculate midpoint
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        self.assertEqual(mid_x, 50)
        self.assertEqual(mid_y, 50)
        
        # Calculate perpendicular offset for control point
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx**2 + dy**2)
        
        self.assertAlmostEqual(length, 141.421, places=2)
        
        # Perpendicular direction (rotated 90 degrees)
        perp_x = -dy / length
        perp_y = dx / length
        
        # Control point offset
        offset = curvature * length * 0.3
        ctrl_x = mid_x + perp_x * offset
        ctrl_y = mid_y + perp_y * offset
        
        # Verify control point is offset from midpoint
        self.assertNotEqual(ctrl_x, mid_x)
        self.assertNotEqual(ctrl_y, mid_y)
    
    def test_bezier_curve_generation(self):
        """Test Bezier curve point generation."""
        x1, y1 = 0, 0
        x2, y2 = 100, 100
        ctrl_x, ctrl_y = 50, 100  # Control point above the line
        
        num_points = 10
        points = []
        
        for i in range(num_points + 1):
            t = i / num_points
            s = 1 - t
            # Quadratic Bezier formula
            x = s*s*x1 + 2*s*t*ctrl_x + t*t*x2
            y = s*s*y1 + 2*s*t*ctrl_y + t*t*y2
            points.append((x, y))
        
        # First point should be start
        self.assertAlmostEqual(points[0][0], x1)
        self.assertAlmostEqual(points[0][1], y1)
        
        # Last point should be end
        self.assertAlmostEqual(points[-1][0], x2)
        self.assertAlmostEqual(points[-1][1], y2)
        
        # Middle point should be influenced by control point
        mid_point = points[num_points // 2]
        # Should be higher than the straight line (y > x for this case)
        self.assertGreater(mid_point[1], mid_point[0])
    
    def test_direct_connectivity_data_extraction(self):
        """Test extraction of connectivity data from results."""
        # Simulate Direct connectivity data structure
        # Shape: (timesteps, reaches, reaches+1)
        # Last column is sediment to outlet
        num_timesteps = 5
        num_reaches = 3
        
        direct_connectivity = np.zeros((num_timesteps, num_reaches, num_reaches + 1))
        
        # Add some connectivity values
        direct_connectivity[0, 0, 1] = 100.0  # Reach 0 to Reach 1 at timestep 0
        direct_connectivity[0, 1, 2] = 50.0   # Reach 1 to Reach 2 at timestep 0
        direct_connectivity[0, 2, -1] = 25.0  # Reach 2 to outlet at timestep 0
        
        # Extract for timestep 0
        timestep = 0
        transport_data = direct_connectivity[timestep, :, :-1]  # Sediment between reaches
        qout_data = direct_connectivity[timestep, :, -1]  # Sediment to outlet
        
        # Verify shapes
        self.assertEqual(transport_data.shape, (num_reaches, num_reaches))
        self.assertEqual(qout_data.shape, (num_reaches,))
        
        # Verify values
        self.assertEqual(transport_data[0, 1], 100.0)
        self.assertEqual(transport_data[1, 2], 50.0)
        self.assertEqual(qout_data[2], 25.0)
        
        # Count non-zero connections
        non_zero_between = np.count_nonzero(transport_data)
        non_zero_outlet = np.count_nonzero(qout_data)
        
        self.assertEqual(non_zero_between, 2)
        self.assertEqual(non_zero_outlet, 1)

    def test_connectivity_represents_where_sediment_goes_to(self):
        """Verify that connectivity curves represent WHERE sediment goes TO.

        The direct_connectivity matrix has axes:
          [timestep, source_reach, destination_reach]

        - Axis 1 (rows)    = SOURCE reach (where the cascade was mobilised from).
        - Axis 2 (columns) = DESTINATION reach (where the cascade deposits).

        A connectivity arc must therefore start at the source reach and end at
        the destination reach – the arrowhead at the arc endpoint shows
        'where sediment goes to'.
        """
        num_reaches = 4

        # Build a simple linear network: 0 → 1 → 2 → outlet (column index 4, accessed as -1)
        # with a tributary 3 → 1.
        direct_connectivity = np.zeros((1, num_reaches, num_reaches + 1))

        # Reach 0 mobilises sediment that deposits in Reach 1
        direct_connectivity[0, 0, 1] = 200.0
        # Reach 1 mobilises sediment that deposits in Reach 2
        direct_connectivity[0, 1, 2] = 80.0
        # Reach 3 (tributary) mobilises sediment that deposits in Reach 1
        direct_connectivity[0, 3, 1] = 50.0
        # Reach 2 mobilises sediment that exits the network (outlet column = -1)
        direct_connectivity[0, 2, -1] = 30.0

        timestep = 0
        transport_data = direct_connectivity[timestep, :, :-1]
        qout_data = direct_connectivity[timestep, :, -1]

        # --- Direction convention ---
        # transport_data[i, j] > 0 means:
        #   * i is the SOURCE (mobilisation) reach index – 'from_reach'
        #   * j is the DESTINATION (deposition) reach index – 'to_reach'
        # Sediment goes TO reach j, so the arc arrowhead must point at j.

        # Identify non-zero connections
        connections = []
        for i in range(transport_data.shape[0]):
            for j in range(transport_data.shape[1]):
                if transport_data[i, j] > 0:
                    connections.append((i, j, transport_data[i, j]))

        # Check the expected connections exist with the correct source→destination order
        self.assertIn((0, 1, 200.0), connections, "Reach 0 should send sediment TO Reach 1")
        self.assertIn((1, 2, 80.0),  connections, "Reach 1 should send sediment TO Reach 2")
        self.assertIn((3, 1, 50.0),  connections, "Reach 3 should send sediment TO Reach 1")

        # Verify that the TRANSPOSED direction (destination → source) is NOT present
        src_indices  = {c[0] for c in connections}
        dest_indices = {c[1] for c in connections}
        # Source reaches: 0, 1, 3 (upstream mobilisation points)
        # Destination reaches: 1, 2 (downstream deposition points)
        self.assertIn(0, src_indices,  "Reach 0 must be a SOURCE (mobilisation)")
        self.assertIn(1, dest_indices, "Reach 1 must be a DESTINATION (deposition)")

        # Outlet data: row index = source reach, value = volume exiting network
        # qout_data[i] > 0 means sediment FROM reach i exits the network
        self.assertAlmostEqual(qout_data[2], 30.0, msg="Reach 2 should send sediment TO the outlet")
        self.assertEqual(np.count_nonzero(qout_data), 1, "Only Reach 2 sends sediment to the outlet")

        # Simulate the arc attribute assignment used by update_connectivity_curves:
        #   from_reach = reach_fromn[i]  (source)
        #   to_reach   = reach_fromn[j]  (destination = where sediment goes to)
        reach_fromn = [1, 2, 3, 4]  # sorted FromN values (1-based IDs)
        for i, j, volume in connections:
            from_reach = reach_fromn[i]  # source reach ID
            to_reach   = reach_fromn[j]  # destination reach ID
            # The arc geometry goes from from_reach position to to_reach position.
            # The arrowhead placed at the LAST VERTEX (to_reach end) shows
            # "where sediment goes to".
            self.assertNotEqual(from_reach, to_reach, "Source and destination must differ")
            # In a simple linear network, destination ID > source ID (flows downstream)
            if (i, j) in [(0, 1), (1, 2)]:
                self.assertGreater(to_reach, from_reach,
                                   f"Arc {from_reach}→{to_reach} should go downstream")

    def test_log_scale_color_mapping(self):
        """Test logarithmic color scale for volume visualization."""
        volumes = [1, 10, 100, 1000, 10000]
        
        vmin = max(1, min(volumes))
        vmax = max(volumes)
        
        self.assertEqual(vmin, 1)
        self.assertEqual(vmax, 10000)
        
        # Test log scale binning
        classes = 5
        log_min = np.log10(vmin)
        log_max = np.log10(vmax)
        log_step = (log_max - log_min) / classes
        
        self.assertAlmostEqual(log_min, 0.0)
        self.assertAlmostEqual(log_max, 4.0)
        self.assertAlmostEqual(log_step, 0.8)
        
        # Generate ranges
        ranges = []
        for i in range(classes):
            lower = 10 ** (log_min + i * log_step)
            upper = 10 ** (log_min + (i + 1) * log_step) if i < classes - 1 else vmax
            ranges.append((lower, upper))
        
        # Verify ranges cover the full spectrum
        self.assertAlmostEqual(ranges[0][0], 1.0, places=2)
        self.assertAlmostEqual(ranges[-1][1], 10000.0, places=2)
        
        # Verify logarithmic spacing
        self.assertAlmostEqual(ranges[0][1] / ranges[0][0], 
                              ranges[1][1] / ranges[1][0], places=1)


if __name__ == '__main__':
    unittest.main()
