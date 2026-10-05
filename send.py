from datetime import datetime, timezone
from html import escape

import requests

import config as c
import store


def text(a):
    """The dispatch message (§10.6)."""
    return '\n'.join([f"{a['tier']}  p {a['p']:.2f}  risk {a['r']}", a['why'],
                      f"Map: https://maps.google.com/?q={a['latitude']:.5f},{a['longitude']:.5f}",
                      f"Alert {a['id']}: share location, send a photo, then tap an outcome."])


def cap(a):
    """CAP 1.2 alert (§12.3). CAP forbids 'Z', so UTC is written as -00:00; status stays Exercise."""
    sent = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S-00:00')
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2">
  <identifier>agni-{a['id']}</identifier>
  <sender>agnidrishti@example.org</sender>
  <sent>{sent}</sent>
  <status>Exercise</status>
  <msgType>Alert</msgType>
  <scope>Restricted</scope>
  <restriction>Forest department field staff</restriction>
  <info>
    <category>Fire</category>
    <event>Forest fire</event>
    <urgency>Immediate</urgency>
    <severity>Severe</severity>
    <certainty>Likely</certainty>
    <headline>Likely forest fire, risk {a['r']} of 7</headline>
    <description>{escape(a['why'])}</description>
    <area>
      <areaDesc>Alert {a['id']}</areaDesc>
      <circle>{a['latitude']:.5f},{a['longitude']:.5f} 1</circle>
    </area>
  </info>
</alert>
'''


def push(a):
    """Send one DISPATCH at most once. The CAP file is written only after Telegram accepts, so it marks 'sent' (D4)."""
    path = c.DATA / f"cap_{a['id']}.xml"
    if path.exists():
        return False
    r = requests.post(f'https://api.telegram.org/bot{c.BOT_TOKEN}/sendMessage',
                      data={'chat_id': c.CHAT_ID, 'text': text(a)}, timeout=30)
    if not r.ok or not r.json().get('ok'):
        print(f"telegram refused {a['id']}: {r.status_code} {r.text[:200]}")
        return False
    path.write_text(cap(a), encoding='utf-8')
    return True


if __name__ == '__main__':
    # Replay: pick the top N DISPATCH alerts by p first, then skip the ones already sent (§12.2).
    df = store.load()
    top = df[df.tier == 'DISPATCH'].sort_values(['p', 't'], ascending=False).head(c.REPLAY_SEND_TOP)
    sent = sum(push(a) for a in top.to_dict('records'))
    print(f'sent {sent} of the top {len(top)} DISPATCH alerts; {len(top) - sent} were already sent or refused')
