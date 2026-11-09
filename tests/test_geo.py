import numpy as np
import pytest

import geo


def test_one_degree_of_latitude_is_about_111_km():
    assert geo.km(0, 0, 1, 0) == pytest.approx(111.19, abs=0.01)


def test_dehradun_to_haridwar():
    assert geo.km(30.3165, 78.0322, 29.9457, 78.1642) == pytest.approx(43.2, abs=0.5)


def test_distance_is_symmetric_and_zero_for_the_same_point():
    assert geo.km(30.1, 78.2, 30.1, 78.2) == 0
    assert geo.km(30.1, 78.2, 29.5, 79.0) == pytest.approx(geo.km(29.5, 79.0, 30.1, 78.2))


def test_distance_works_on_arrays():
    d = geo.km(30.0, 78.0, np.array([30.0, 31.0]), np.array([78.0, 78.0]))
    assert d[0] == 0 and d[1] == pytest.approx(111.19, abs=0.01)


@pytest.mark.parametrize('to, expected', [((1, 0), 0), ((0, 1), 90), ((-1, 0), 180), ((0, -1), 270)])
def test_bearing_of_the_four_compass_points(to, expected):
    assert geo.bearing(0, 0, *to) == pytest.approx(expected, abs=0.01)


@pytest.mark.parametrize('deg, dist', [(0, 1), (75, 5), (200, 12.5), (359, 3)])
def test_offset_then_measure_round_trips(deg, dist):
    lat, lon = geo.offset(30.05, 78.20, deg, dist)
    assert geo.km(30.05, 78.20, lat, lon) == pytest.approx(dist, abs=1e-6)
    assert geo.bearing(30.05, 78.20, lat, lon) == pytest.approx(deg, abs=0.01)
