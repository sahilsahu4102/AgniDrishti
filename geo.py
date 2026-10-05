import numpy as np

R = 6371.0


def km(lat1, lon1, lat2, lon2):
    """Haversine distance in km; works on scalars or numpy arrays."""
    p1, p2 = np.radians(lat1), np.radians(lat2)
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(np.subtract(lon2, lon1)) / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def bearing(lat1, lon1, lat2, lon2):
    """Initial great-circle bearing, degrees clockwise from north."""
    p1, p2, dl = np.radians(lat1), np.radians(lat2), np.radians(lon2 - lon1)
    y = np.sin(dl) * np.cos(p2)
    x = np.cos(p1) * np.sin(p2) - np.sin(p1) * np.cos(p2) * np.cos(dl)
    return float((np.degrees(np.arctan2(y, x)) + 360) % 360)


def offset(lat, lon, deg, dist_km):
    """The point dist_km away on initial bearing deg (great circle)."""
    p1, l1, b, d = np.radians(lat), np.radians(lon), np.radians(deg), dist_km / R
    p2 = np.arcsin(np.sin(p1) * np.cos(d) + np.cos(p1) * np.sin(d) * np.cos(b))
    l2 = l1 + np.arctan2(np.sin(b) * np.sin(d) * np.cos(p1), np.cos(d) - np.sin(p1) * np.sin(p2))
    return float(np.degrees(p2)), float(np.degrees(l2))


if __name__ == '__main__':
    lat, lon = offset(30.05, 78.20, 75, 5)
    assert abs(km(30.05, 78.20, lat, lon) - 5) < 1e-6 and abs(bearing(30.05, 78.20, lat, lon) - 75) < 0.01
    assert abs(km(0, 0, 1, 0) - 111.19) < 0.01
    assert abs(km(30.3165, 78.0322, 29.9457, 78.1642) - 43.2) < 0.5  # Dehradun - Haridwar
    assert round(bearing(0, 0, 1, 0)) == 0 and round(bearing(0, 0, 0, 1)) == 90 and round(bearing(0, 0, -1, 0)) == 180
    print('geo ok')
