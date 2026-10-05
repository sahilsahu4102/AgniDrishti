import os
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / 'data'

for line in (ROOT / '.env').read_text(encoding='utf-8').splitlines() if (ROOT / '.env').exists() else []:
    k, _, v = line.partition('=')
    if k.strip() and v.strip():
        os.environ.setdefault(k.strip(), v.strip())
FIRMS_KEY = os.getenv('FIRMS_KEY', '')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
CHAT_ID = os.getenv('CHAT_ID', '')
LAPTOP_IP = os.getenv('LAPTOP_IP', '127.0.0.1')

# Region and data windows (§4.1). Window B uses NOAA-20: S-NPP has no data 28 Apr - early Jun 2026 (Phase 0).
BOX = (77.5, 28.7, 81.1, 31.5)  # west, south, east, north
STATE_ISO = 'IN-UT'  # the boundary file spells the name 'Uttarākhand'
WINDOWS = {
    'win_a': ('VIIRS_SNPP_SP', '2025-11-01', '2026-01-31'),
    'win_b': ('VIIRS_NOAA20_SP', '2026-04-01', '2026-05-31'),
    'hist': ('VIIRS_SNPP_SP', '2023-01-01', '2025-10-31'),
}
LIVE_SOURCES = ['VIIRS_NOAA20_NRT', 'VIIRS_NOAA21_NRT']

# Files (§8)
WORLDCOVER = DATA / 'worldcover'
DEM = DATA / 'dem'
STATE = DATA / 'state.geojson'
VILLAGES = DATA / 'villages.csv'
CELLS = DATA / 'cells.csv'
WEATHER = DATA / 'weather'
BURNS = ROOT / 'burns.csv'
OUTCOMES = DATA / 'outcomes.csv'
SCORED = DATA / 'scored.csv'
LIVE = DATA / 'live.csv'
LIVE_SCORED = DATA / 'live_scored.csv'

# Features (§10.1)
CELL_DEG = 0.005  # ~500 m recurrence cells
SEEN_KM = 1
SEEN_HOURS = 12  # D2: count earlier alerts only (same pass included), so replay can't see the future
WEATHER_CELL_DEG = 0.25
LIVE_WEATHER_DAYS = 5  # the archive lags a few days; newer alerts use the forecast API's current values

# Probability p (§10.2). Starting guesses: tune once in Phase 3 and note why here.
P_START = 0.5
VEG_MIN, VEG_PENALTY = 0.30, 0.30
FARM_MAX, FARM_PENALTY = 0.50, 0.30
BURN_PENALTY = 0.40
RECUR_MIN, RECUR_PENALTY = 8, 0.25
SEEN_STEP, SEEN_CAP = 0.15, 0.30
CONF_BONUS = 0.10
FRP_MIN, FRP_BONUS = 10, 0.10
SMOKE_P, NOSMOKE_DROP, FIRE_P, NOFIRE_P = 0.90, 0.10, 1.0, 0.05

# Risk r (§10.3)
VILLAGE_NEAR_KM, VILLAGE_KM = 2, 5
SLOPE_STEEP = 20
TREE_DENSE = 0.6
WIND_STRONG = 15
RH_DRY = 30
SEEN_EVENT = 2  # 3+ pixels, FSI's large-fire rule

# Tiers (§10.4)
DISPATCH_P, DISPATCH_P_RISKY, DISPATCH_R = 0.9, 0.6, 2
VERIFY_P = 0.35

# Dispatch (§12.2)
REPLAY_SEND_TOP = 3
API_PORT = 8000

# Camera node (§11.2): phone camera (option C), no servo. Location gets picked in Phase 2 (demo-point rule).
NODE_ID = 'AG-01'
NODE_LAT, NODE_LON = 30.05, 78.20
NODE_HEADING = 0  # compass bearing the phone faces
NODE_FOV_DEG = 60  # phone's horizontal field of view; alerts outside it are skipped
NODE_RANGE_KM = 10
CAMERA_SOURCE = os.getenv('CAMERA_SOURCE', '0')  # phone IP Webcam URL (http://<ip>:8080/video), a video file, or a webcam index
CAMERA_SOURCE = int(CAMERA_SOURCE) if CAMERA_SOURCE.isdigit() else CAMERA_SOURCE
CAMERA_MODEL = DATA / 'models/pyronear/yolo11s_rapid-raccoon_v8.1.0/best.pt'
# Locked 6 Oct 2026 by camtest.py over 10 smoke clips and 42.6 min of no-smoke footage (thresholds chosen on that same set):
# conf 0.20 (model card) gave 25/29 smoke checks and 10 false confirmations; 0.30 plus the darkness guard gives 22/29
# (9 of 10 clips still caught) and 2 false confirmations. The guard: a 6-frame check whose median brightness is under
# DARK_LUMA gets no verdict (night lights fooled the model), so the alert stays in VERIFY for a photo.
CAMERA_IMGSZ, CAMERA_CONF, CAMERA_IOU = 1024, 0.30, 0.01
DARK_LUMA = 30  # 0-255 grey level
FRAMES, FRAME_GAP_S, FRAMES_NEEDED = 6, 2, 4

# Field photo bot (§11.3)
PHOTO_MODEL = DATA / 'models/dfire_yolo11n_best.pt'
PHOTO_CONF = 0.40
BOT_RADIUS_KM = 3
