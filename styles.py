APP_CSS = """
<style>
.stApp { background: #0b0d12; color: #e7e9ed; }
[data-testid="stSidebar"] { background: #10141b; }
div[data-testid="stMetric"] {
    background: #131720;
    border: 1px solid #2b3340;
    border-radius: 12px;
    padding: 12px;
}
.stButton > button {
    border: 1px solid #424b5a;
    border-radius: 9px;
    background: #1b222e;
    color: #e7e9ed;
}
.panel {
    background: #171c26;
    border: 1px solid #2b3340;
    border-radius: 14px;
    padding: 16px;
    margin: 8px 0 14px;
}
.badge {
    display: inline-block;
    padding: 3px 10px;
    margin: 3px;
    border-radius: 999px;
    border: 1px solid #444d5b;
    background: #202633;
}
.badge.red { color: #ff9da2; }
.badge.blue { color: #93d2ff; }
.badge.gold { color: #f3d18d; }
.meter-label {
    display: flex;
    justify-content: space-between;
    margin: 8px 0 3px;
}
.meter {
    height: 12px;
    background: #272d38;
    border-radius: 99px;
    overflow: hidden;
}
.meter > div { height: 100%; }
.hp-fill { background: #ef555d; }
.chakra-fill { background: #4ab8f0; }
.storm-fill { background: #f0c156; }
.kawarimi-slot {
    display: inline-flex;
    width: 25px;
    height: 25px;
    border: 1px solid #555f70;
    border-radius: 6px;
    align-items: center;
    justify-content: center;
    margin: 2px;
}
.kawarimi-slot.ready { color: #8dd7ff; }
.small-muted { color: #9ca5b4; }
</style>
"""


def render_meter(label: str, current: int, maximum: int, css_class: str) -> str:
    maximum = max(1, int(maximum))
    current = max(0, min(int(current), maximum))
    pct = int(current / maximum * 100)
    return (
        f'<div class="meter-label"><span>{label}</span>'
        f'<span>{current}/{maximum}</span></div>'
        f'<div class="meter"><div class="{css_class}" '
        f'style="width:{pct}%"></div></div>'
    )


def render_kawarimi_slots(current: int, maximum: int) -> str:
    slots = []
    for index in range(maximum):
        ready = index < current
        symbol = "替" if ready else "×"
        css_class = "ready" if ready else ""
        slots.append(
            f'<span class="kawarimi-slot {css_class}">{symbol}</span>'
        )
    return (
        '<div class="meter-label"><span>خانات الكاواريمي</span></div>'
        + "".join(slots)
    )
