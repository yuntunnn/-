import csv
import json
import os
from collections import defaultdict
from datetime import datetime

# Configuration
INPUT_FILE = '/Users/jennifer/LDS/26-Q1/AI应用推广模块/夸克弹窗推广数据0224.csv'
OUTPUT_FILE = '/Users/jennifer/LDS/26-Q1/AI应用推广模块/promotion_dashboard.html'

# CSS Colors
COLORS = {
    'bg': '#07090d',
    'surface': '#0e1117',
    'surface2': '#151820',
    'border': '#1a1f2c',
    'c1': '#3b82f6',    # Blue - start
    'c2': '#8b5cf6',    # Purple - pop_show
    'c3': '#10b981',    # Green - click/success
    'c4': '#f59e0b',    # Amber
    'c5': '#ef4444',    # Red
    'text': '#e2e8f0',
    'muted': '#4b5563'
}

def parse_int(s):
    if not s:
        return 0
    try:
        return int(s)
    except ValueError:
        return 0

def load_data(file_path):
    data = []
    try:
        with open(file_path, 'r', encoding='gb18030', errors='replace') as f:
            reader = csv.reader(f)
            headers = next(reader)
            for row in reader:
                if len(row) < 7:
                    continue
                if row[3] == '' or row[1] == '总计' or '�ϼ�' in row[1]:
                    continue
                
                record = {
                    'date': row[1],
                    'action': row[3],
                    'pv': parse_int(row[5]),
                    'uv': parse_int(row[6])
                }
                data.append(record)
    except Exception as e:
        print(f"Error reading file: {e}")
        return []
    return data

def process_data(data):
    daily_data = defaultdict(lambda: defaultdict(int))
    all_dates = set()
    
    for item in data:
        date = item['date']
        action = item['action']
        daily_data[date][action] += item['pv']
        all_dates.add(date)
    
    sorted_dates = sorted(list(all_dates))
    processed = []
    
    for date in sorted_dates:
        actions = daily_data[date]
        start = actions.get('start', 0)
        pop_show = actions.get('pop_show', 0)
        pop_click = actions.get('pop_click', 0)
        down_start = actions.get('down_start', 0)
        down_suc = actions.get('down_suc', 0)
        down_end_suc = actions.get('down_end_suc', 0)
        break_count = actions.get('break', 0)
        
        # Determine Stage
        stage = "Unknown"
        if start < 1000:
            stage = "灰测期"
        elif start < 10000:
            stage = "灰度扩量"
        else:
            stage = "正式放量"
            
        metrics = {
            'date': date,
            'stage': stage,
            'start': start,
            'pop_show': pop_show,
            'pop_click': pop_click,
            'down_start': down_start,
            'down_suc': down_suc,
            'down_end_suc': down_end_suc,
            'break': break_count,
            'actions': actions # Keep raw actions for detailed analysis
        }
        
        # Derived Metrics
        metrics['show_rate'] = (pop_show / start * 100) if start > 0 else 0
        metrics['ctr'] = (pop_click / pop_show * 100) if pop_show > 0 else 0
        metrics['install_rate'] = (down_end_suc / down_start * 100) if down_start > 0 else 0
        metrics['click_to_install_rate'] = (down_end_suc / pop_click * 100) if pop_click > 0 else 0
        metrics['break_rate'] = (break_count / start * 100) if start > 0 else 0
        
        processed.append(metrics)
        
    return processed

def generate_svg_trend(data):
    if not data:
        return ""
    
    width = 1000
    height = 300
    padding = 40
    
    dates = [d['date'] for d in data]
    starts = [d['start'] for d in data]
    shows = [d['pop_show'] for d in data]
    clicks = [d['pop_click'] for d in data]
    
    max_val = max(starts) if starts else 100
    if max_val == 0: max_val = 100
    
    # Click amplification factor
    max_click = max(clicks) if clicks else 10
    click_scale = (max_val / max_click) * 0.5 if max_click > 0 else 1
    
    x_step = (width - 2 * padding) / len(data)
    
    svg = [f'<svg viewBox="0 0 {width} {height}" class="chart">']
    
    # Background Grid
    for i in range(5):
        y = height - padding - (i * (height - 2 * padding) / 4)
        svg.append(f'<line x1="{padding}" y1="{y}" x2="{width-padding}" y2="{y}" stroke="{COLORS["border"]}" stroke-dasharray="4" />')
        val = int(max_val * i / 4)
        svg.append(f'<text x="{padding-5}" y="{y+5}" text-anchor="end" fill="{COLORS["muted"]}" font-size="10">{val}</text>')

    # Bars (Start & Show)
    bar_width = x_step * 0.3
    for i, d in enumerate(data):
        x = padding + i * x_step + x_step/2
        
        # Start Bar
        h_start = (d['start'] / max_val) * (height - 2 * padding)
        y_start = height - padding - h_start
        svg.append(f'<rect x="{x - bar_width}" y="{y_start}" width="{bar_width}" height="{h_start}" fill="{COLORS["c1"]}" opacity="0.8"><title>{d["date"]} Start: {d["start"]}</title></rect>')
        
        # Show Bar
        h_show = (d['pop_show'] / max_val) * (height - 2 * padding)
        y_show = height - padding - h_show
        svg.append(f'<rect x="{x}" y="{y_show}" width="{bar_width}" height="{h_show}" fill="{COLORS["c2"]}" opacity="0.8"><title>{d["date"]} Show: {d["pop_show"]}</title></rect>')
        
        # X Axis Labels (Every nth label to avoid clutter)
        if len(data) > 15:
            if i % 3 == 0:
                svg.append(f'<text x="{x}" y="{height-10}" text-anchor="middle" fill="{COLORS["muted"]}" font-size="10">{d["date"][5:]}</text>')
        else:
            svg.append(f'<text x="{x}" y="{height-10}" text-anchor="middle" fill="{COLORS["muted"]}" font-size="10">{d["date"][5:]}</text>')

    # Line (Clicks)
    points = []
    for i, d in enumerate(data):
        x = padding + i * x_step + x_step/2
        h_click = (d['pop_click'] * click_scale / max_val) * (height - 2 * padding)
        y_click = height - padding - h_click
        points.append(f'{x},{y_click}')
        svg.append(f'<circle cx="{x}" cy="{y_click}" r="3" fill="{COLORS["c3"]}" stroke="{COLORS["bg"]}" stroke-width="1"><title>{d["date"]} Click: {d["pop_click"]}</title></circle>')
        svg.append(f'<text x="{x}" y="{y_click-10}" text-anchor="middle" fill="{COLORS["c3"]}" font-size="10">{d["pop_click"]}</text>')
    
    svg.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{COLORS["c3"]}" stroke-width="2" />')
    
    # Legend
    svg.append(f'<rect x="{width-300}" y="10" width="10" height="10" fill="{COLORS["c1"]}" />')
    svg.append(f'<text x="{width-285}" y="19" fill="{COLORS["text"]}" font-size="12">Start</text>')
    svg.append(f'<rect x="{width-240}" y="10" width="10" height="10" fill="{COLORS["c2"]}" />')
    svg.append(f'<text x="{width-225}" y="19" fill="{COLORS["text"]}" font-size="12">Show</text>')
    svg.append(f'<line x1="{width-180}" y1="15" x2="{width-160}" y2="15" stroke="{COLORS["c3"]}" stroke-width="2" />')
    svg.append(f'<text x="{width-155}" y="19" fill="{COLORS["text"]}" font-size="12">Click (x{click_scale:.1f})</text>')
    
    svg.append('</svg>')
    return "".join(svg)

def generate_svg_ctr(data):
    if not data:
        return ""
    width = 1000
    height = 200
    padding = 40
    
    ctrs = [d['ctr'] for d in data]
    max_ctr = max(ctrs) if ctrs else 5
    if max_ctr < 2: max_ctr = 2 # Min scale
    
    x_step = (width - 2 * padding) / len(data)
    
    svg = [f'<svg viewBox="0 0 {width} {height}" class="chart">']
    
    # 1% Reference Line
    y_ref = height - padding - (1.0 / max_ctr) * (height - 2 * padding)
    svg.append(f'<line x1="{padding}" y1="{y_ref}" x2="{width-padding}" y2="{y_ref}" stroke="{COLORS["c4"]}" stroke-dasharray="4" opacity="0.5" />')
    svg.append(f'<text x="{width-padding+5}" y="{y_ref+4}" fill="{COLORS["c4"]}" font-size="10">1% Target</text>')
    
    points = []
    area_points = [f"{padding},{height-padding}"]
    
    for i, d in enumerate(data):
        x = padding + i * x_step + x_step/2
        h = (d['ctr'] / max_ctr) * (height - 2 * padding)
        y = height - padding - h
        points.append(f'{x},{y}')
        area_points.append(f'{x},{y}')
        
        # Color based on value
        color = COLORS['c5'] if d['ctr'] < 1 else (COLORS['c3'] if d['ctr'] > 2 else COLORS['c4'])
        
        svg.append(f'<circle cx="{x}" cy="{y}" r="3" fill="{color}" stroke="{COLORS["bg"]}" stroke-width="1"><title>{d["date"]} CTR: {d["ctr"]:.2f}%</title></circle>')
        svg.append(f'<text x="{x}" y="{y-10}" text-anchor="middle" fill="{color}" font-size="10">{d["ctr"]:.2f}%</text>')
    
    area_points.append(f"{padding + len(data) * x_step - x_step/2},{height-padding}")
    
    # Area
    svg.append(f'<polygon points="{" ".join(area_points)}" fill="{COLORS["c3"]}" fill-opacity="0.1" />')
    # Line
    svg.append(f'<polyline points="{" ".join(points)}" fill="none" stroke="{COLORS["text"]}" stroke-width="1" opacity="0.5" />')
    
    svg.append('</svg>')
    return "".join(svg)

def generate_svg_funnel(agg_data):
    width = 800
    height = 300
    padding = 20
    row_height = 35
    
    stages = [
        ('Start', agg_data['start'], COLORS['c1']),
        ('Trigger', agg_data['promotion_trigger'], COLORS['c1']),
        ('Show', agg_data['pop_show'], COLORS['c2']),
        ('Click', agg_data['pop_click'], COLORS['c3']),
        ('Download Start', agg_data['down_start'], COLORS['c4']),
        ('Install Success', agg_data['down_end_suc'], COLORS['c3'])
    ]
    
    max_val = stages[0][1] if stages[0][1] > 0 else 1
    
    svg = [f'<svg viewBox="0 0 {width} {height}" class="chart">']
    
    for i, (label, val, color) in enumerate(stages):
        y = padding + i * (row_height + 10)
        bar_width = (val / max_val) * (width - 200)
        if bar_width < 2: bar_width = 2
        
        svg.append(f'<text x="100" y="{y+20}" text-anchor="end" fill="{COLORS["text"]}" font-size="12">{label}</text>')
        svg.append(f'<rect x="110" y="{y}" width="{bar_width}" height="{row_height}" fill="{color}" rx="4" />')
        svg.append(f'<text x="{110+bar_width+10}" y="{y+22}" fill="{COLORS["text"]}" font-size="12">{val} ({(val/max_val*100):.1f}%)</text>')
        
        # Conversion Label
        if i > 0:
            prev_val = stages[i-1][1]
            conv = (val / prev_val * 100) if prev_val > 0 else 0
            svg.append(f'<text x="{110+bar_width+100}" y="{y+22}" fill="{COLORS["muted"]}" font-size="10">↓ {conv:.1f}% from prev</text>')

    svg.append('</svg>')
    return "".join(svg)

def generate_html(processed_data):
    # Aggregation
    total_metrics = defaultdict(int)
    for d in processed_data:
        for k, v in d['actions'].items():
            total_metrics[k] += v
    
    # HTML Template
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>推广模块放量埋点分析看板</title>
    <style>
        :root {{
            --bg: {COLORS['bg']};
            --surface: {COLORS['surface']};
            --surface2: {COLORS['surface2']};
            --border: {COLORS['border']};
            --c1: {COLORS['c1']};
            --c2: {COLORS['c2']};
            --c3: {COLORS['c3']};
            --c4: {COLORS['c4']};
            --c5: {COLORS['c5']};
            --text: {COLORS['text']};
            --muted: {COLORS['muted']};
        }}
        body {{
            background-color: var(--bg);
            color: var(--text);
            font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            margin: 0;
            padding: 20px;
        }}
        .container {{
            max_width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            margin-bottom: 30px;
            border-bottom: 1px solid var(--border);
            padding-bottom: 20px;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 20px;
        }}
        .kpi-card h3 {{
            margin: 0;
            font-size: 14px;
            color: var(--muted);
        }}
        .kpi-card .value {{
            font-size: 28px;
            font-weight: bold;
            margin: 10px 0 0;
        }}
        .chart-section {{
            margin-bottom: 30px;
        }}
        .chart-section h2 {{
            font-size: 18px;
            margin-bottom: 15px;
            border-left: 4px solid var(--c1);
            padding-left: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th, td {{
            text-align: left;
            padding: 12px;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            color: var(--muted);
        }}
        .badge {{
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 12px;
            background-color: var(--surface2);
        }}
        .text-green {{ color: var(--c3); }}
        .text-amber {{ color: var(--c4); }}
        .text-red {{ color: var(--c5); }}
        
        .insights-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .insight-card {{
            border-left: 4px solid var(--border);
        }}
        .insight-card.red {{ border-left-color: var(--c5); }}
        .insight-card.blue {{ border-left-color: var(--c1); }}
        .insight-card.green {{ border-left-color: var(--c3); }}
        .insight-card.amber {{ border-left-color: var(--c4); }}
        
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>推广模块放量埋点分析看板</h1>
            <p style="color: var(--muted)">数据周期: {processed_data[0]['date']} 至 {processed_data[-1]['date']} | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        </div>

        <div class="kpi-grid">
            <div class="card kpi-card">
                <h3>总启动 (Start)</h3>
                <div class="value" style="color: var(--c1)">{total_metrics['start']:,}</div>
            </div>
            <div class="card kpi-card">
                <h3>总曝光 (Show)</h3>
                <div class="value" style="color: var(--c2)">{total_metrics['pop_show']:,}</div>
            </div>
            <div class="card kpi-card">
                <h3>总点击 (Click)</h3>
                <div class="value" style="color: var(--c3)">{total_metrics['pop_click']:,}</div>
            </div>
            <div class="card kpi-card">
                <h3>总安装成功 (Install)</h3>
                <div class="value" style="color: var(--c4)">{total_metrics['down_end_suc']:,}</div>
            </div>
            <div class="card kpi-card">
                <h3>平均点击率 (CTR)</h3>
                <div class="value" style="color: {(COLORS['c5'] if (total_metrics['pop_click']/total_metrics['pop_show'] < 0.01) else COLORS['c3'])}">
                    {(total_metrics['pop_click'] / total_metrics['pop_show'] * 100 if total_metrics['pop_show'] > 0 else 0):.2f}%
                </div>
            </div>
        </div>

        <div class="chart-section card">
            <h2>每日流量趋势 (Show vs Click)</h2>
            {generate_svg_trend(processed_data)}
        </div>

        <div class="chart-section card">
            <h2>点击率 (CTR) 趋势</h2>
            {generate_svg_ctr(processed_data)}
        </div>
        
        <div class="chart-section card">
            <h2>全周期漏斗分析</h2>
            {generate_svg_funnel(total_metrics)}
        </div>

        <div class="chart-section card">
            <h2>关键洞察</h2>
            <div class="insights-grid">
                <div class="card insight-card red">
                    <h3 class="text-red">核心瓶颈: CTR { (total_metrics['pop_click'] / total_metrics['pop_show'] * 100 if total_metrics['pop_show'] > 0 else 0):.2f}%</h3>
                    <p>整体点击率持续低于 1%，远低于 3% 的健康基准。这是目前最大的流失环节，建议优先优化弹窗素材。</p>
                </div>
                <div class="card insight-card green">
                    <h3 class="text-green">亮点: 安装转化率 {(total_metrics['down_end_suc'] / total_metrics['pop_click'] * 100 if total_metrics['pop_click'] > 0 else 0):.1f}%</h3>
                    <p>点击后的用户有极高的意愿完成下载和安装（>80%），说明技术链路稳定，且点击用户精准。</p>
                </div>
                <div class="card insight-card blue">
                    <h3 style="color: var(--c1)">流量增长</h3>
                    <p>最近几日流量显著提升，已进入正式放量阶段，单日曝光突破 5 万。</p>
                </div>
            </div>
        </div>
        
        <div class="chart-section card">
            <h2>每日明细数据</h2>
            <table>
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>Start</th>
                        <th>Show</th>
                        <th>Show Rate</th>
                        <th>Click</th>
                        <th>CTR</th>
                        <th>Install</th>
                        <th>Click->Install</th>
                        <th>Break Rate</th>
                        <th>阶段</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    for d in processed_data:
        ctr_color = "text-green" if d['ctr'] > 1.5 else ("text-amber" if d['ctr'] > 1 else "text-red")
        install_rate_color = "text-green" if d['click_to_install_rate'] > 80 else "text-amber"
        
        html += f"""
                    <tr>
                        <td>{d['date']}</td>
                        <td>{d['start']}</td>
                        <td>{d['pop_show']}</td>
                        <td>{d['show_rate']:.1f}%</td>
                        <td>{d['pop_click']}</td>
                        <td class="{ctr_color}">{d['ctr']:.2f}%</td>
                        <td>{d['down_end_suc']}</td>
                        <td class="{install_rate_color}">{d['click_to_install_rate']:.1f}%</td>
                        <td>{d['break_rate']:.1f}%</td>
                        <td><span class="badge">{d['stage']}</span></td>
                    </tr>
        """

    html += """
                </tbody>
            </table>
        </div>
        
        <div class="chart-section card">
            <h2>优化建议</h2>
            <ol>
                <li><strong>突破弹窗 CTR (P0):</strong> 当前 CTR 不足 1%，建议立即进行 A/B 测试，尝试更具吸引力的文案或利益点（如强调免费、新功能）。</li>
                <li><strong>关注 Break 率:</strong> 部分日期 Break 率较高，需排查是否打扰用户体验。</li>
                <li><strong>保持下载链路:</strong> 继续监控下载成功率，维持当前的高水平转化。</li>
            </ol>
        </div>
    </div>
</body>
</html>
"""
    return html

def main():
    print(f"Reading data from {INPUT_FILE}...")
    data = load_data(INPUT_FILE)
    if not data:
        print("No data found.")
        return

    print(f"Processing {len(data)} records...")
    processed_data = process_data(data)
    
    print("Generating HTML...")
    html_content = generate_html(processed_data)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"Dashboard generated at: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
