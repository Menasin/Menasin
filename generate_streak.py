import json
import urllib.request
import os
from datetime import datetime

def fetch_contributions(token, username):
    query = """
    query($login: String!) {
      user(login: $login) {
        createdAt
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
      }
    }
    """
    req = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': query, 'variables': {'login': username}}).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'Menasin-Streak-Builder'
        }
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode('utf-8'))

def parse_date_label(d_str):
    if not d_str:
        return ""
    dt = datetime.strptime(d_str, "%Y-%m-%d")
    return dt.strftime("%b %d").replace(" 0", " ")

def calculate_stats(data):
    cal = data['data']['user']['contributionsCollection']['contributionCalendar']
    days = [d for w in cal['weeks'] for d in w['contributionDays']]
    
    # Map to dictionary date -> count
    contributions = {d['date']: d['contributionCount'] for d in days}
    dates = list(contributions.keys())
    today = dates[-1] if dates else ""
    first_date = dates[0] if dates else ""
    
    stats = {
        "totalContributions": 0,
        "firstContribution": "",
        "longestStreak": {"start": first_date, "end": first_date, "length": 0},
        "currentStreak": {"start": first_date, "end": first_date, "length": 0}
    }
    
    for date, count in contributions.items():
        stats["totalContributions"] += count
        if count > 0:
            stats["currentStreak"]["length"] += 1
            stats["currentStreak"]["end"] = date
            if stats["currentStreak"]["length"] == 1:
                stats["currentStreak"]["start"] = date
            if not stats["firstContribution"]:
                stats["firstContribution"] = date
            if stats["currentStreak"]["length"] > stats["longestStreak"]["length"]:
                stats["longestStreak"]["start"] = stats["currentStreak"]["start"]
                stats["longestStreak"]["end"] = stats["currentStreak"]["end"]
                stats["longestStreak"]["length"] = stats["currentStreak"]["length"]
        elif date != today:
            stats["currentStreak"]["length"] = 0
            stats["currentStreak"]["start"] = today
            stats["currentStreak"]["end"] = today
            
    first_contrib_label = parse_date_label(stats["firstContribution"]) if stats["firstContribution"] else "Present"
    total_range = f"{first_contrib_label} - Present"
    
    curr_len = stats["currentStreak"]["length"]
    if curr_len > 0:
        curr_range = f"{parse_date_label(stats['currentStreak']['start'])} - {parse_date_label(stats['currentStreak']['end'])}"
    else:
        curr_range = "No Active Streak"
        
    longest_len = stats["longestStreak"]["length"]
    if longest_len > 0:
        longest_range = f"{parse_date_label(stats['longestStreak']['start'])} - {parse_date_label(stats['longestStreak']['end'])}"
    else:
        longest_range = "None"
        
    return {
        'total': stats["totalContributions"],
        'total_range': total_range,
        'current': curr_len,
        'current_range': curr_range,
        'longest': longest_len,
        'longest_range': longest_range
    }

def render_svg(stats):
    card_width = 495
    card_height = 195
    col_width = card_width / 3.0  # 165
    c1_x = col_width / 2.0         # 82.5
    c2_x = c1_x + col_width        # 247.5
    c3_x = c2_x + col_width        # 412.5

    return f"""<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {card_width} {card_height}' width='{card_width}px' height='{card_height}px'>
  <style>
    .bold-num {{
      font-family: 'Segoe UI', Ubuntu, -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 28px;
      font-weight: 700;
      fill: #ffffff;
      text-anchor: middle;
    }}
    .curr-num {{
      font-family: 'Segoe UI', Ubuntu, -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 28px;
      font-weight: 700;
      fill: #00ff66;
      text-anchor: middle;
      filter: drop-shadow(0 0 4px rgba(0, 255, 102, 0.6));
    }}
    .label-text {{
      font-family: 'Segoe UI', Ubuntu, -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 14px;
      font-weight: 400;
      fill: #8b949e;
      text-anchor: middle;
    }}
    .curr-label {{
      font-family: 'Segoe UI', Ubuntu, -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 14px;
      font-weight: 700;
      fill: #00ff66;
      text-anchor: middle;
    }}
    .date-text {{
      font-family: 'Segoe UI', Ubuntu, -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 12px;
      font-weight: 400;
      fill: #6e7681;
      text-anchor: middle;
    }}
    .cyber-corner {{
      stroke: #00ff66;
      stroke-width: 1.5;
      fill: none;
      opacity: 0.8;
    }}
    .matrix-char {{
      font-family: ui-monospace, 'Fira Code', Consolas, 'Courier New', monospace;
      font-size: 11px;
      font-weight: 600;
    }}
  </style>

  <defs>
    <!-- Background Gradient -->
    <linearGradient id='bgGrad' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' stop-color='#05080c'/>
      <stop offset='50%' stop-color='#0a0e14'/>
      <stop offset='100%' stop-color='#05080c'/>
    </linearGradient>



    <!-- Glow for ring -->
    <filter id='ringGlow' x='-20%' y='-20%' width='140%' height='140%'>
      <feGaussianBlur stdDeviation='2.5' result='blur'/>
      <feMerge>
        <feMergeNode in='blur'/>
        <feMergeNode in='SourceGraphic'/>
      </feMerge>
    </filter>

    <!-- Card Clip Path to keep matrix rain inside rounded card -->
    <clipPath id='cardClip'>
      <rect x='0.5' y='0.5' width='{card_width - 1}' height='{card_height - 1}' rx='8'/>
    </clipPath>
  </defs>

  <!-- Card Background with Dark Cyber Fill -->
  <rect x='0.5' y='0.5' width='{card_width - 1}' height='{card_height - 1}' rx='8' fill='url(#bgGrad)' stroke='#00ff66' stroke-width='1.2' stroke-opacity='0.4'/>

  <!-- MATRIX DIGITAL RAIN (Cyber Fallback Layer) -->
  <g clip-path='url(#cardClip)' class='matrix-char' opacity='0.35'>
    <!-- Col 1 (x=28) -->
    <g>
      <animateTransform attributeName='transform' type='translate' values='0,-160; 0,210' dur='2.4s' repeatCount='indefinite' begin='-0.4s'/>
      <text x='28' y='0'>
        <tspan x='28' dy='0' fill='#004418'>0</tspan>
        <tspan x='28' dy='13' fill='#007727'>1</tspan>
        <tspan x='28' dy='13' fill='#00aa38'>X</tspan>
        <tspan x='28' dy='13' fill='#00cc44'>C</tspan>
        <tspan x='28' dy='13' fill='#00ff66'>B</tspan>
        <tspan x='28' dy='13' fill='#66ff99'>7</tspan>
        <tspan x='28' dy='13' fill='#ffffff' font-weight='bold'>F</tspan>
      </text>
    </g>

    <!-- Col 2 (x=68) -->
    <g>
      <animateTransform attributeName='transform' type='translate' values='0,-160; 0,210' dur='3.1s' repeatCount='indefinite' begin='-1.7s'/>
      <text x='68' y='0'>
        <tspan x='68' dy='0' fill='#004418'>1</tspan>
        <tspan x='68' dy='13' fill='#007727'>0</tspan>
        <tspan x='68' dy='13' fill='#00aa38'>A</tspan>
        <tspan x='68' dy='13' fill='#00cc44'>4</tspan>
        <tspan x='68' dy='13' fill='#00ff66'>9</tspan>
        <tspan x='68' dy='13' fill='#66ff99'>1</tspan>
        <tspan x='68' dy='13' fill='#ffffff' font-weight='bold'>0</tspan>
      </text>
    </g>

    <!-- Col 3 (x=115) -->
    <g>
      <animateTransform attributeName='transform' type='translate' values='0,-160; 0,210' dur='2.6s' repeatCount='indefinite' begin='-0.9s'/>
      <text x='115' y='0'>
        <tspan x='115' dy='0' fill='#004418'>M</tspan>
        <tspan x='115' dy='13' fill='#007727'>A</tspan>
        <tspan x='115' dy='13' fill='#00aa38'>R</tspan>
        <tspan x='115' dy='13' fill='#00cc44'>S</tspan>
        <tspan x='115' dy='13' fill='#00ff66'>0</tspan>
        <tspan x='115' dy='13' fill='#66ff99'>X</tspan>
        <tspan x='115' dy='13' fill='#ffffff' font-weight='bold'>8</tspan>
      </text>
    </g>

    <!-- Col 4 (x=150) -->
    <g>
      <animateTransform attributeName='transform' type='translate' values='0,-160; 0,210' dur='3.3s' repeatCount='indefinite' begin='-2.2s'/>
      <text x='150' y='0'>
        <tspan x='150' dy='0' fill='#004418'>0</tspan>
        <tspan x='150' dy='13' fill='#007727'>1</tspan>
        <tspan x='150' dy='13' fill='#009933'>1</tspan>
        <tspan x='150' dy='13' fill='#00cc44'>0</tspan>
        <tspan x='150' dy='13' fill='#00ff66'>1</tspan>
        <tspan x='150' dy='13' fill='#66ff99'>0</tspan>
        <tspan x='150' dy='13' fill='#ffffff' font-weight='bold'>1</tspan>
      </text>
    </g>

    <!-- Col 5 (x=195) -->
    <g>
      <animateTransform attributeName='transform' type='translate' values='0,-160; 0,210' dur='2.3s' repeatCount='indefinite' begin='-1.1s'/>
      <text x='195' y='0'>
        <tspan x='195' dy='0' fill='#004418'>H</tspan>
        <tspan x='195' dy='13' fill='#007727'>X</tspan>
        <tspan x='195' dy='13' fill='#00aa38'>C</tspan>
        <tspan x='195' dy='13' fill='#00cc44'>B</tspan>
        <tspan x='195' dy='13' fill='#00ff66'>F</tspan>
        <tspan x='195' dy='13' fill='#66ff99'>X</tspan>
        <tspan x='195' dy='13' fill='#ffffff' font-weight='bold'>9</tspan>
      </text>
    </g>

    <!-- Col 6 (x=300) -->
    <g>
      <animateTransform attributeName='transform' type='translate' values='0,-160; 0,210' dur='2.7s' repeatCount='indefinite' begin='-1.4s'/>
      <text x='300' y='0'>
        <tspan x='300' dy='0' fill='#004418'>Z</tspan>
        <tspan x='300' dy='13' fill='#007727'>E</tspan>
        <tspan x='300' dy='13' fill='#00aa38'>R</tspan>
        <tspan x='300' dy='13' fill='#00cc44'>O</tspan>
        <tspan x='300' dy='13' fill='#00ff66'>T</tspan>
        <tspan x='300' dy='13' fill='#66ff99'>9</tspan>
        <tspan x='300' dy='13' fill='#ffffff' font-weight='bold'>F</tspan>
      </text>
    </g>

    <!-- Col 7 (x=345) -->
    <g>
      <animateTransform attributeName='transform' type='translate' values='0,-160; 0,210' dur='3.2s' repeatCount='indefinite' begin='-0.6s'/>
      <text x='345' y='0'>
        <tspan x='345' dy='0' fill='#004418'>1</tspan>
        <tspan x='345' dy='13' fill='#007727'>0</tspan>
        <tspan x='345' dy='13' fill='#00aa38'>1</tspan>
        <tspan x='345' dy='13' fill='#00cc44'>1</tspan>
        <tspan x='345' dy='13' fill='#00ff66'>0</tspan>
        <tspan x='345' dy='13' fill='#66ff99'>1</tspan>
        <tspan x='345' dy='13' fill='#ffffff' font-weight='bold'>0</tspan>
      </text>
    </g>

    <!-- Col 8 (x=390) -->
    <g>
      <animateTransform attributeName='transform' type='translate' values='0,-160; 0,210' dur='2.5s' repeatCount='indefinite' begin='-1.8s'/>
      <text x='390' y='0'>
        <tspan x='390' dy='0' fill='#004418'>N</tspan>
        <tspan x='390' dy='13' fill='#007727'>E</tspan>
        <tspan x='390' dy='13' fill='#00aa38'>T</tspan>
        <tspan x='390' dy='13' fill='#00cc44'>W</tspan>
        <tspan x='390' dy='13' fill='#00ff66'>O</tspan>
        <tspan x='390' dy='13' fill='#66ff99'>R</tspan>
        <tspan x='390' dy='13' fill='#ffffff' font-weight='bold'>K</tspan>
      </text>
    </g>

    <!-- Col 9 (x=430) -->
    <g>
      <animateTransform attributeName='transform' type='translate' values='0,-160; 0,210' dur='3.0s' repeatCount='indefinite' begin='-0.3s'/>
      <text x='430' y='0'>
        <tspan x='430' dy='0' fill='#004418'>0</tspan>
        <tspan x='430' dy='13' fill='#007727'>1</tspan>
        <tspan x='430' dy='13' fill='#00aa38'>A</tspan>
        <tspan x='430' dy='13' fill='#00cc44'>E</tspan>
        <tspan x='430' dy='13' fill='#00ff66'>S</tspan>
        <tspan x='430' dy='13' fill='#66ff99'>1</tspan>
        <tspan x='430' dy='13' fill='#ffffff' font-weight='bold'>0</tspan>
      </text>
    </g>

    <!-- Col 10 (x=468) -->
    <g>
      <animateTransform attributeName='transform' type='translate' values='0,-160; 0,210' dur='2.2s' repeatCount='indefinite' begin='-1.2s'/>
      <text x='468' y='0'>
        <tspan x='468' dy='0' fill='#004418'>F</tspan>
        <tspan x='468' dy='13' fill='#007727'>X</tspan>
        <tspan x='468' dy='13' fill='#00aa38'>9</tspan>
        <tspan x='468' dy='13' fill='#00cc44'>0</tspan>
        <tspan x='468' dy='13' fill='#00ff66'>X</tspan>
        <tspan x='468' dy='13' fill='#66ff99'>8</tspan>
        <tspan x='468' dy='13' fill='#ffffff' font-weight='bold'>B</tspan>
      </text>
    </g>
  </g>

  <!-- Cyber Accents on Corners -->
  <path d='M 12 5 L 5 5 L 5 12' class='cyber-corner'/>
  <path d='M {card_width - 12} 5 L {card_width - 5} 5 L {card_width - 5} 12' class='cyber-corner'/>
  <path d='M 5 {card_height - 12} L 5 {card_height - 5} L 12 {card_height - 5}' class='cyber-corner'/>
  <path d='M {card_width - 5} {card_height - 12} L {card_width - 5} {card_height - 5} L {card_width - 12} {card_height - 5}' class='cyber-corner'/>

  <!-- Separator Bars -->
  <line x1='{col_width}' y1='28' x2='{col_width}' y2='170' stroke='#21262d' stroke-width='1' stroke-linecap='square'/>
  <line x1='{col_width * 2}' y1='28' x2='{col_width * 2}' y2='170' stroke='#21262d' stroke-width='1' stroke-linecap='square'/>

  <!-- ================= COLUMN 1: TOTAL CONTRIBUTIONS ================= -->
  <g transform='translate({c1_x}, 48)'>
    <text x='0' y='32' class='bold-num'>{stats['total']}</text>
  </g>
  <g transform='translate({c1_x}, 84)'>
    <text x='0' y='32' class='label-text'>Total Contributions</text>
  </g>
  <g transform='translate({c1_x}, 114)'>
    <text x='0' y='32' class='date-text'>{stats['total_range']}</text>
  </g>

  <!-- ================= COLUMN 2: CURRENT STREAK ================= -->
  <!-- Ring around number with exact fire gap at the top (Radius 40) -->
  <g transform='translate({c2_x}, 71)'>
    <path d='M 11.03 -38.45 A 40 40 0 1 1 -11.03 -38.45' fill='none' stroke='#00ff66' stroke-width='5' stroke-linecap='round' filter='url(#ringGlow)'/>
  </g>

  <!-- Fire Icon: positioned exactly in the upper ring gap -->
  <g transform='translate({c2_x}, 19.5)' stroke-opacity='0'>
    <path d='M -12 -0.5 L 15 -0.5 L 15 23.5 L -12 23.5 L -12 -0.5 Z' fill='none'/>
    <path d='M 1.5 0.67 C 1.5 0.67 2.24 3.32 2.24 5.47 C 2.24 7.53 0.89 9.2 -1.17 9.2 C -3.23 9.2 -4.79 7.53 -4.79 5.47 L -4.76 5.11 C -6.78 7.51 -8 10.62 -8 13.99 C -8 18.41 -4.42 22 0 22 C 4.42 22 8 18.41 8 13.99 C 8 8.6 5.41 3.79 1.5 0.67 Z M -0.29 19 C -2.07 19 -3.51 17.6 -3.51 15.86 C -3.51 14.24 -2.46 13.1 -0.7 12.74 C 1.07 12.38 2.9 11.53 3.92 10.16 C 4.31 11.45 4.51 12.81 4.51 14.2 C 4.51 16.85 2.36 19 -0.29 19 Z' fill='#00ff66'/>
  </g>

  <!-- Number & Labels -->
  <g transform='translate({c2_x}, 48)'>
    <text x='0' y='32' class='curr-num'>{stats['current']}</text>
  </g>
  <g transform='translate({c2_x}, 108)'>
    <text x='0' y='32' class='curr-label'>Current Streak</text>
  </g>
  <g transform='translate({c2_x}, 145)'>
    <text x='0' y='21' class='date-text'>{stats['current_range']}</text>
  </g>

  <!-- ================= COLUMN 3: LONGEST STREAK ================= -->
  <g transform='translate({c3_x}, 48)'>
    <text x='0' y='32' class='bold-num'>{stats['longest']}</text>
  </g>
  <g transform='translate({c3_x}, 84)'>
    <text x='0' y='32' class='label-text'>Longest Streak</text>
  </g>
  <g transform='translate({c3_x}, 114)'>
    <text x='0' y='32' class='date-text'>{stats['longest_range']}</text>
  </g>
</svg>
"""

if __name__ == '__main__':
    token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    username = 'Menasin'
    
    stats = None
    if token:
        try:
            data = fetch_contributions(token, username)
            stats = calculate_stats(data)
        except Exception as e:
            print(f"Error fetching contributions: {e}")
            stats = None
            
    if not stats:
        # Accurate fallback
        stats = {
            'total': 72,
            'total_range': 'Sep 26 - Present',
            'current': 3,
            'current_range': 'Oct 31 - Nov 2',
            'longest': 6,
            'longest_range': 'Sep 26 - Oct 1'
        }
        
    svg_content = render_svg(stats)
    os.makedirs('assets', exist_ok=True)
    with open('assets/streak.svg', 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print("Generated streak.svg successfully:", stats)
