#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""推广模块放量打点数据看板生成器 - 读取CSV埋点数据，生成交互式HTML看板"""
import csv, json, os
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, '夸克弹窗推广数据0224.csv')
OUTPUT_PATH = os.path.join(BASE_DIR, 'promotion_dashboard.html')

def parse_csv(path):
    daily = defaultdict(lambda: defaultdict(lambda: {'pv': 0, 'uv': 0}))
    with open(path, 'r', encoding='gb18030', errors='replace') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) < 7 or not row[3].strip():
                continue
            date, action = row[1].strip(), row[3].strip()
            if not date or not date.startswith('202'):
                continue
            pv = int(row[5]) if row[5].strip() else 0
            uv = int(row[6]) if row[6].strip() else 0
            daily[date][action]['pv'] += pv
            daily[date][action]['uv'] += uv
    return daily

def get_uv(daily, d, a):
    return daily[d].get(a, {}).get('uv', 0)

def classify_phase(start_uv):
    if start_uv < 500: return '灰测期'
    if start_uv < 5000: return '灰度扩量'
    if start_uv < 30000: return '稳定期'
    return '正式放量'

def compute_metrics(daily):
    dates = sorted(daily.keys())
    rows = []
    for d in dates:
        g = lambda a: get_uv(daily, d, a)
        s, sh, cl = g('start'), g('pop_show'), g('pop_click')
        ds, desuc = g('down_start'), g('down_end_suc')
        brk = g('break')
        rows.append({
            'date': d, 'phase': classify_phase(s),
            'start': s, 'trigger': g('promotion_trigger'), 'show': sh,
            'click': cl, 'close': g('pop_close'), 'notips': g('pop_notips'),
            'timeout': g('kk_pop_timeout'), 'down_start': ds,
            'down_suc': g('down_suc'), 'down_fail': g('down_fail'),
            'down_end_suc': desuc, 'down_end_fail': g('down_end_fail'),
            'break_count': brk,
            'show_rate': round(sh/s*100, 2) if s else 0,
            'ctr': round(cl/sh*100, 2) if sh else 0,
            'install_rate': round(desuc/cl*100, 2) if cl else 0,
            'brk_rate': round(brk/s*100, 2) if s else 0,
        })
    return rows

def gen_insights(rows):
    """生成关键洞察"""
    insights = []
    # 排除灰测期
    valid = [r for r in rows if r['phase'] != '灰测期']
    if not valid:
        return insights

    # 1. CTR 瓶颈
    avg_ctr = sum(r['ctr'] for r in valid) / len(valid)
    total_show = sum(r['show'] for r in valid)
    total_click = sum(r['click'] for r in valid)
    if avg_ctr < 2:
        insights.append({
            'tag': '核心瓶颈', 'color': '#ef4444',
            'metric': f'{avg_ctr:.2f}%',
            'title': '弹窗 CTR 持续低于 2%',
            'desc': f'排除灰测期后，平均 CTR 仅 {avg_ctr:.2f}%。累计展示 {total_show:,} 人，仅 {total_click:,} 人点击。弹窗吸引力是当前最大瓶颈。'
        })

    # 2. 流量增长
    if len(valid) >= 3:
        first3 = sum(r['start'] for r in valid[:3]) / 3
        last3 = sum(r['start'] for r in valid[-3:]) / 3
        if last3 > first3 * 2:
            insights.append({
                'tag': '流量增长', 'color': '#3b82f6',
                'metric': f'{last3/first3:.1f}x',
                'title': '推广流量大幅放量',
                'desc': f'近 3 日日均启动 {last3:,.0f} 人，较初期 {first3:,.0f} 人增长 {last3/first3:.1f} 倍，覆盖能力持续扩大。'
            })

    # 3. 安装成功率亮点
    install_valid = [r for r in valid if r['click'] > 0]
    if install_valid:
        avg_install = sum(r['install_rate'] for r in install_valid) / len(install_valid)
        if avg_install > 85:
            insights.append({
                'tag': '亮点', 'color': '#10b981',
                'metric': f'{avg_install:.1f}%',
                'title': '安装成功率表现优秀',
                'desc': f'点击后安装成功率平均 {avg_install:.1f}%，下载链路健康，无需重点优化。'
            })

    # 4. break 率关注
    avg_brk = sum(r['brk_rate'] for r in valid) / len(valid)
    total_brk = sum(r['break_count'] for r in valid)
    if avg_brk > 15:
        insights.append({
            'tag': '关注', 'color': '#f59e0b',
            'metric': f'{avg_brk:.1f}%',
            'title': 'break 中断率偏高',
            'desc': f'平均 break 率 {avg_brk:.1f}%，累计 {total_brk:,} 人中断退出。建议细化埋点区分弹窗前/后中断。'
        })

    # 5. 不再提示累计
    total_notips = sum(r['notips'] for r in valid)
    if total_notips > 1000:
        insights.append({
            'tag': '关注', 'color': '#f59e0b',
            'metric': f'{total_notips:,}',
            'title': '"不再提示"用户持续累积',
            'desc': f'已有 {total_notips:,} 人勾选"不再提示"，这部分用户永久流失，随推广持续可触达用户池将逐渐缩小。'
        })

    # 6. 趋势：最近持续放量
    if len(valid) >= 4:
        last4 = valid[-4:]
        increasing = all(last4[i]['start'] <= last4[i+1]['start'] for i in range(3))
        if increasing:
            insights.append({
                'tag': '趋势', 'color': '#3b82f6',
                'metric': f'{last4[-1]["start"]:,}',
                'title': '连续放量中',
                'desc': f'最近 4 天 start 量持续增长，最新一天达 {last4[-1]["start"]:,} 人。'
            })

    return insights[:6]

def gen_suggestions(rows):
    """生成优化建议"""
    valid = [r for r in rows if r['phase'] != '灰测期']
    if not valid:
        return []
    suggestions = []
    avg_ctr = sum(r['ctr'] for r in valid) / len(valid)
    total_show = sum(r['show'] for r in valid)
    total_click = sum(r['click'] for r in valid)
    lost = total_show - total_click

    suggestions.append({
        'priority': 'P0', 'title': '突破弹窗 CTR',
        'desc': f'当前平均 CTR {avg_ctr:.2f}%，累计 {lost:,} 人看到弹窗但未点击。建议：A/B 测试不同文案（利益点前置）、优化视觉 CTA 按钮、调整触发时机（如用户空闲时弹出）。'
    })

    avg_brk = sum(r['brk_rate'] for r in valid) / len(valid)
    total_brk = sum(r['break_count'] for r in valid)
    if avg_brk > 15:
        suggestions.append({
            'priority': 'P1', 'title': '治理 break 中断',
            'desc': f'平均 break 率 {avg_brk:.1f}%，累计 {total_brk:,} 人。建议细化埋点区分「弹窗前中断」和「弹窗后中断」，针对性优化触发场景和页面加载性能。'
        })

    total_notips = sum(r['notips'] for r in valid)
    if total_notips > 500:
        suggestions.append({
            'priority': 'P1', 'title': '管理"不再提示"用户',
            'desc': f'累计 {total_notips:,} 人勾选不再提示。建议：加入免推名单避免无效曝光，分析这部分用户画像，评估是否需要调整弹窗频率策略。'
        })

    install_valid = [r for r in valid if r['down_start'] > 0]
    if install_valid:
        total_fail = sum(r['down_fail'] + r['down_end_fail'] for r in install_valid)
        total_ds = sum(r['down_start'] for r in install_valid)
        fail_rate = total_fail / total_ds * 100 if total_ds else 0
        if fail_rate > 5:
            suggestions.append({
                'priority': 'P2', 'title': '排查下载/安装失败',
                'desc': f'下载+安装失败率 {fail_rate:.1f}%（{total_fail} 次失败）。建议排查具体失败原因（网络超时、包损坏、存储空间不足等）。'
            })

    suggestions.append({
        'priority': 'P2', 'title': '优化触发→展示转化',
        'desc': f'start→pop_show 整体转化约 {sum(r["show"] for r in valid)/sum(r["start"] for r in valid)*100:.1f}%，约 {sum(r["start"] for r in valid)-sum(r["show"] for r in valid):,} 人未看到弹窗。建议检查触发条件是否过严、频控策略是否合理。'
    })

    return suggestions[:5]


def generate_html(rows, insights, suggestions):
    """生成单文件 HTML 看板，所有 CSS/JS 内联，无外部依赖（字体除外）"""
    import json as _json

    dates = [r['date'] for r in rows]
    date_range = f"{dates[0]} ~ {dates[-1]}" if dates else '-'

    # 全周期汇总
    total_start  = sum(r['start'] for r in rows)
    total_show   = sum(r['show'] for r in rows)
    total_click  = sum(r['click'] for r in rows)
    total_install= sum(r['down_end_suc'] for r in rows)
    total_brk    = sum(r['break_count'] for r in rows)

    # 全周期漏斗（排除灰测期）
    valid = [r for r in rows if r['phase'] != '灰测期']
    f_start   = sum(r['start']       for r in valid)
    f_trigger = sum(r['trigger']     for r in valid)
    f_show    = sum(r['show']        for r in valid)
    f_click   = sum(r['click']       for r in valid)
    f_ds      = sum(r['down_start']  for r in valid)
    f_dsuc    = sum(r['down_suc']    for r in valid)
    f_desuc   = sum(r['down_end_suc']for r in valid)

    # 关闭行为
    f_close   = sum(r['close']   for r in valid)
    f_timeout = sum(r['timeout'] for r in valid)
    f_notips  = sum(r['notips']  for r in valid)
    f_bclick  = sum(r['click']   for r in valid)

    rows_json       = _json.dumps(rows,        ensure_ascii=False)
    insights_json   = _json.dumps(insights,    ensure_ascii=False)
    suggestions_json= _json.dumps(suggestions, ensure_ascii=False)

    def pct(a, b): return f"{a/b*100:.1f}%" if b else "-"

    # Phase badge colors
    phase_colors = {
        '灰测期':   ('gray',   '#6b7280', '#1f2937'),
        '灰度扩量': ('blue',   '#3b82f6', '#1e3a5f'),
        '稳定期':   ('amber',  '#f59e0b', '#3d2e00'),
        '正式放量': ('green',  '#10b981', '#052e16'),
    }

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>推广模块放量数据看板</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root{{
  --bg:#07090d;--surface:#0e1117;--surface2:#151820;--border:#1a1f2c;
  --c1:#3b82f6;--c2:#8b5cf6;--c3:#10b981;--c4:#f59e0b;--c5:#ef4444;
  --text:#e2e8f0;--muted:#4b5563;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--text);font-family:'Noto Sans SC',sans-serif;font-size:14px;line-height:1.6}}
.mono{{font-family:'IBM Plex Mono',monospace}}
.container{{max-width:1400px;margin:0 auto;padding:24px 20px}}
/* Header */
.header{{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:28px 32px;margin-bottom:24px}}
.header h1{{font-size:22px;font-weight:700;color:var(--text);margin-bottom:6px}}
.header .sub{{color:var(--muted);font-size:13px;margin-bottom:16px}}
.header-kpi{{display:flex;gap:32px;flex-wrap:wrap}}
.header-kpi-item{{display:flex;flex-direction:column;gap:2px}}
.header-kpi-item .label{{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}}
.header-kpi-item .val{{font-size:18px;font-weight:600;font-family:'IBM Plex Mono',monospace}}
/* KPI cards */
.kpi-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:24px}}
@media(max-width:900px){{.kpi-grid{{grid-template-columns:repeat(3,1fr)}}}}
.kpi-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px;position:relative;overflow:hidden}}
.kpi-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px}}
.kpi-card.c1::before{{background:var(--c1)}}
.kpi-card.c2::before{{background:var(--c2)}}
.kpi-card.c3::before{{background:var(--c3)}}
.kpi-card.c4::before{{background:var(--c4)}}
.kpi-card.c5::before{{background:var(--c5)}}
.kpi-card .kpi-label{{font-size:12px;color:var(--muted);margin-bottom:8px}}
.kpi-card .kpi-val{{font-size:28px;font-weight:700;font-family:'IBM Plex Mono',monospace;line-height:1}}
.kpi-card .kpi-sub{{font-size:11px;color:var(--muted);margin-top:6px}}
/* Chart sections */
.section{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:24px;margin-bottom:24px}}
.section-title{{font-size:15px;font-weight:600;margin-bottom:20px;color:var(--text)}}
.chart-wrap{{width:100%;overflow-x:auto}}
svg.chart{{display:block;width:100%;height:auto}}
/* Table */
.tbl-wrap{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{background:var(--surface2);color:var(--muted);font-weight:500;padding:10px 12px;text-align:right;border-bottom:1px solid var(--border);white-space:nowrap}}
th:first-child{{text-align:left}}
td{{padding:9px 12px;text-align:right;border-bottom:1px solid var(--border);font-family:'IBM Plex Mono',monospace;font-size:12px}}
td:first-child{{text-align:left;font-family:'Noto Sans SC',sans-serif;font-size:13px}}
tr:hover td{{background:var(--surface2)}}
.badge{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-family:'Noto Sans SC',sans-serif;font-weight:500}}
.ctr-blue{{color:#93c5fd}}.ctr-green{{color:#6ee7b7}}.ctr-amber{{color:#fcd34d}}
.inst-green{{color:#6ee7b7}}.inst-amber{{color:#fcd34d}}.inst-red{{color:#fca5a5}}
.brk-red{{color:#fca5a5}}.brk-amber{{color:#fcd34d}}
/* Insights */
.insights-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px}}
@media(max-width:900px){{.insights-grid{{grid-template-columns:1fr 1fr}}}}
.insight-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px;border-left:3px solid}}
.insight-tag{{font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-bottom:8px}}
.insight-metric{{font-size:32px;font-weight:700;font-family:'IBM Plex Mono',monospace;line-height:1;margin-bottom:8px}}
.insight-title{{font-size:14px;font-weight:600;margin-bottom:6px}}
.insight-desc{{font-size:12px;color:var(--muted);line-height:1.7}}
/* Suggestions */
.sugg-list{{display:flex;flex-direction:column;gap:12px}}
.sugg-item{{background:var(--surface2);border:1px solid var(--border);border-radius:8px;padding:16px 20px;display:flex;gap:16px;align-items:flex-start}}
.sugg-priority{{font-size:11px;font-weight:700;font-family:'IBM Plex Mono',monospace;padding:3px 8px;border-radius:4px;white-space:nowrap;margin-top:2px}}
.p0{{background:#3f0f0f;color:#fca5a5}}.p1{{background:#3d2e00;color:#fcd34d}}.p2{{background:#052e16;color:#6ee7b7}}
.sugg-body .sugg-title{{font-size:14px;font-weight:600;margin-bottom:4px}}
.sugg-body .sugg-desc{{font-size:12px;color:var(--muted);line-height:1.7}}
/* Legend */
.legend{{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:12px;font-size:12px;color:var(--muted)}}
.legend-item{{display:flex;align-items:center;gap:6px}}
.legend-dot{{width:10px;height:10px;border-radius:2px}}
.legend-line{{width:20px;height:2px}}
</style>
</head>
<body>
<div class="container">
<!-- Header -->
<div class="header">
  <h1>推广模块放量数据看板</h1>
  <div class="sub">数据周期：{date_range} &nbsp;|&nbsp; 生成时间：{__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
  <div class="header-kpi">
    <div class="header-kpi-item"><span class="label">总启动</span><span class="val mono">{total_start:,}</span></div>
    <div class="header-kpi-item"><span class="label">总展示</span><span class="val mono">{total_show:,}</span></div>
    <div class="header-kpi-item"><span class="label">总点击</span><span class="val mono">{total_click:,}</span></div>
    <div class="header-kpi-item"><span class="label">总安装</span><span class="val mono">{total_install:,}</span></div>
    <div class="header-kpi-item"><span class="label">整体CTR</span><span class="val mono">{pct(total_click,total_show)}</span></div>
    <div class="header-kpi-item"><span class="label">点击→安装</span><span class="val mono">{pct(total_install,total_click)}</span></div>
  </div>
</div>
<!-- KPI Cards -->
<div class="kpi-grid">
  <div class="kpi-card c1">
    <div class="kpi-label">总启动 start</div>
    <div class="kpi-val">{total_start:,}</div>
    <div class="kpi-sub">全周期累计用户</div>
  </div>
  <div class="kpi-card c2">
    <div class="kpi-label">总展示 pop_show</div>
    <div class="kpi-val">{total_show:,}</div>
    <div class="kpi-sub">展示率 {pct(total_show,total_start)}</div>
  </div>
  <div class="kpi-card c3">
    <div class="kpi-label">总点击 pop_click</div>
    <div class="kpi-val">{total_click:,}</div>
    <div class="kpi-sub">CTR {pct(total_click,total_show)}</div>
  </div>
  <div class="kpi-card c4">
    <div class="kpi-label">总安装 down_end_suc</div>
    <div class="kpi-val">{total_install:,}</div>
    <div class="kpi-sub">点击→安装 {pct(total_install,total_click)}</div>
  </div>
  <div class="kpi-card c5">
    <div class="kpi-label">总 break</div>
    <div class="kpi-val">{total_brk:,}</div>
    <div class="kpi-sub">break率 {pct(total_brk,total_start)}</div>
  </div>
</div>
<!-- Daily Traffic Trend -->
<div class="section">
  <div class="section-title">每日流量趋势</div>
  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#3b82f6"></div>start（启动）</div>
    <div class="legend-item"><div class="legend-dot" style="background:#8b5cf6"></div>pop_show（展示）</div>
    <div class="legend-item"><div class="legend-line" style="background:#10b981"></div>pop_click ×10（点击放大）</div>
    <div class="legend-item"><span style="font-size:11px;opacity:.6">虚线/空心点 = 灰测期</span></div>
  </div>
  <div class="chart-wrap"><svg id="chart-traffic" class="chart" viewBox="0 0 1200 320"></svg></div>
</div>
<!-- CTR Trend -->
<div class="section">
  <div class="section-title">每日弹窗 CTR 趋势</div>
  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#3b82f6"></div>CTR%</div>
    <div class="legend-item"><div class="legend-line" style="background:#ef4444;border-top:2px dashed #ef4444"></div>1% 参考线</div>
  </div>
  <div class="chart-wrap"><svg id="chart-ctr" class="chart" viewBox="0 0 1200 280"></svg></div>
</div>
<!-- Install Rate -->
<div class="section">
  <div class="section-title">每日点击→安装转化率</div>
  <div class="legend">
    <div class="legend-item"><div class="legend-dot" style="background:#10b981"></div>≥80% 优秀</div>
    <div class="legend-item"><div class="legend-dot" style="background:#f59e0b"></div>60–79% 一般</div>
    <div class="legend-item"><div class="legend-dot" style="background:#ef4444"></div>&lt;60% 需关注</div>
  </div>
  <div class="chart-wrap"><svg id="chart-install" class="chart" viewBox="0 0 1200 280"></svg></div>
</div>
<!-- Funnel -->
<div class="section">
  <div class="section-title">全周期汇总漏斗（排除灰测期）</div>
  <div class="chart-wrap"><svg id="chart-funnel" class="chart" viewBox="0 0 1200 340"></svg></div>
</div>
<!-- Close Behavior -->
<div class="section">
  <div class="section-title">弹窗关闭行为分布（排除灰测期）</div>
  <div class="chart-wrap"><svg id="chart-close" class="chart" viewBox="0 0 1200 220"></svg></div>
</div>
<!-- Data Table -->
<div class="section">
  <div class="section-title">每日明细数据</div>
  <div class="tbl-wrap">
    <table id="detail-table">
      <thead><tr>
        <th>日期</th><th>start</th><th>pop_show</th><th>展示率</th>
        <th>pop_click</th><th>CTR</th><th>安装成功</th><th>点击→安装</th>
        <th>break</th><th>break率</th><th>阶段</th>
      </tr></thead>
      <tbody id="table-body"></tbody>
    </table>
  </div>
</div>
<!-- Insights -->
<div class="section-title" style="margin-bottom:16px">关键洞察</div>
<div class="insights-grid" id="insights-grid"></div>
<!-- Suggestions -->
<div class="section">
  <div class="section-title">优化建议</div>
  <div class="sugg-list" id="sugg-list"></div>
</div>
</div><!-- /container -->
<script>
const ROWS = {rows_json};
const INSIGHTS = {insights_json};
const SUGGESTIONS = {suggestions_json};

const PHASE_COLORS = {{
  '灰测期':  {{badge:'#6b7280', bg:'#1f2937'}},
  '灰度扩量':{{badge:'#3b82f6', bg:'#1e3a5f'}},
  '稳定期':  {{badge:'#f59e0b', bg:'#3d2e00'}},
  '正式放量':{{badge:'#10b981', bg:'#052e16'}},
}};

// ── helpers ──────────────────────────────────────────────
function fmt(n){{ return n==null||n===''?'-':Number(n).toLocaleString(); }}
function pct(a,b){{ return b?((a/b)*100).toFixed(1)+'%':'-'; }}
function clamp(v,lo,hi){{ return Math.max(lo,Math.min(hi,v)); }}

// ── Table ─────────────────────────────────────────────────
(function buildTable(){{
  const tbody = document.getElementById('table-body');
  ROWS.forEach(r=>{{
    const pc = PHASE_COLORS[r.phase]||{{badge:'#6b7280',bg:'#1f2937'}};
    const ctrVal = r.ctr;
    const ctrCls = ctrVal>2?'ctr-blue':ctrVal>=1?'ctr-green':'ctr-amber';
    const instVal = r.install_rate;
    const instCls = instVal>=80?'inst-green':instVal>=60?'inst-amber':'inst-red';
    const brkVal = r.brk_rate;
    const brkCls = brkVal>20?'brk-red':brkVal>15?'brk-amber':'';
    const isGray = r.phase==='灰测期';
    tbody.innerHTML += `<tr style="${{isGray?'opacity:.55':''}}">
      <td>${{r.date}}</td>
      <td>${{fmt(r.start)}}</td>
      <td>${{fmt(r.show)}}</td>
      <td>${{r.show_rate}}%</td>
      <td>${{fmt(r.click)}}</td>
      <td class="${{ctrCls}}">${{r.ctr}}%${{isGray?' <span style="font-size:10px;color:#6b7280">[灰测]</span>':''}}</td>
      <td>${{fmt(r.down_end_suc)}}</td>
      <td class="${{instCls}}">${{r.click>0?r.install_rate+'%':'-'}}</td>
      <td>${{fmt(r.break_count)}}</td>
      <td class="${{brkCls}}">${{r.brk_rate}}%</td>
      <td><span class="badge" style="background:${{pc.bg}};color:${{pc.badge}}">${{r.phase}}</span></td>
    </tr>`;
  }});
}})();

// ── Insights ──────────────────────────────────────────────
(function buildInsights(){{
  const grid = document.getElementById('insights-grid');
  if(!INSIGHTS.length){{ grid.innerHTML='<p style="color:var(--muted)">暂无洞察数据</p>'; return; }}
  INSIGHTS.forEach(ins=>{{
    grid.innerHTML += `<div class="insight-card" style="border-left-color:${{ins.color}}">
      <div class="insight-tag" style="color:${{ins.color}}">${{ins.tag}}</div>
      <div class="insight-metric" style="color:${{ins.color}}">${{ins.metric}}</div>
      <div class="insight-title">${{ins.title}}</div>
      <div class="insight-desc">${{ins.desc}}</div>
    </div>`;
  }});
}})();

// ── Suggestions ───────────────────────────────────────────
(function buildSugg(){{
  const list = document.getElementById('sugg-list');
  SUGGESTIONS.forEach(s=>{{
    const cls = s.priority==='P0'?'p0':s.priority==='P1'?'p1':'p2';
    list.innerHTML += `<div class="sugg-item">
      <span class="sugg-priority ${{cls}}">${{s.priority}}</span>
      <div class="sugg-body">
        <div class="sugg-title">${{s.title}}</div>
        <div class="sugg-desc">${{s.desc}}</div>
      </div>
    </div>`;
  }});
}})();
</script>
<script>
// ── SVG utils ─────────────────────────────────────────────
function svgEl(tag, attrs){{
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  Object.entries(attrs||{{}}).forEach(([k,v])=>el.setAttribute(k,v));
  return el;
}}
function svgText(svg, x, y, txt, attrs){{
  const el = svgEl('text', Object.assign({{x,y,'text-anchor':'middle','dominant-baseline':'middle',fill:'#4b5563','font-size':'11','font-family':'IBM Plex Mono,monospace'}}, attrs));
  el.textContent = txt;
  svg.appendChild(el);
  return el;
}}
function svgLine(svg, x1,y1,x2,y2, attrs){{
  svg.appendChild(svgEl('line', Object.assign({{x1,y1,x2,y2,stroke:'#1a1f2c'}}, attrs)));
}}

// ── Chart 1: Daily Traffic (bar+line) ────────────────────
(function drawTraffic(){{
  const svg = document.getElementById('chart-traffic');
  const W=1200, H=320, PAD={{l:60,r:20,t:20,b:50}};
  const cW=W-PAD.l-PAD.r, cH=H-PAD.t-PAD.b;
  const n=ROWS.length; if(!n) return;

  const maxVal = Math.max(...ROWS.map(r=>Math.max(r.start,r.show)));
  const clickScale = 10;
  const maxClick = Math.max(...ROWS.map(r=>r.click))*clickScale;
  const yMax = Math.max(maxVal, maxClick)*1.1||1;

  const slotW = cW/n;
  const barW = Math.max(4, slotW*0.35);
  const y = v => PAD.t + cH - (v/yMax)*cH;
  const xMid = i => PAD.l + (i+0.5)*slotW;

  // Phase background bands
  let phaseStart=0, curPhase=ROWS[0].phase;
  const drawBand=(from,to,phase)=>{{
    const pc=PHASE_COLORS[phase]||{{bg:'#1f2937'}};
    const rx=PAD.l+from*slotW, rw=(to-from)*slotW;
    const rect=svgEl('rect',{{x:rx,y:PAD.t,width:rw,height:cH,fill:pc.bg,opacity:'0.35'}});
    svg.appendChild(rect);
  }};
  ROWS.forEach((r,i)=>{{
    if(r.phase!==curPhase||i===n-1){{
      drawBand(phaseStart, i===n-1?n:i, curPhase);
      phaseStart=i; curPhase=r.phase;
    }}
  }});

  // Y grid lines
  for(let t=0;t<=4;t++){{
    const yv=PAD.t+cH*(1-t/4);
    svgLine(svg,PAD.l,yv,W-PAD.r,yv,{{stroke:'#1a1f2c','stroke-dasharray':'3,3'}});
    const label=((yMax*t/4)/1000).toFixed(0)+'K';
    svgText(svg,PAD.l-8,yv,label,{{'text-anchor':'end','dominant-baseline':'middle',fill:'#4b5563','font-size':'10'}});
  }}

  // Bars: start (blue) + show (purple)
  ROWS.forEach((r,i)=>{{
    const cx=xMid(i);
    const isGray=r.phase==='灰测期';
    // start bar
    const sh=Math.max(1,(r.start/yMax)*cH);
    const sb=svgEl('rect',{{x:cx-barW-1,y:y(r.start),width:barW,height:sh,fill:'#3b82f6',opacity:isGray?'0.4':'0.85',rx:'2'}});
    svg.appendChild(sb);
    // show bar
    const shh=Math.max(1,(r.show/yMax)*cH);
    const shb=svgEl('rect',{{x:cx+1,y:y(r.show),width:barW,height:shh,fill:'#8b5cf6',opacity:isGray?'0.4':'0.85',rx:'2'}});
    svg.appendChild(shb);
  }});

  // Click line (scaled)
  const pts=ROWS.map((r,i)=>`${{xMid(i)}},${{y(r.click*clickScale)}}`).join(' ');
  const polyline=svgEl('polyline',{{points:pts,fill:'none',stroke:'#10b981','stroke-width':'2','stroke-linejoin':'round'}});
  svg.appendChild(polyline);
  ROWS.forEach((r,i)=>{{
    const isGray=r.phase==='灰测期';
    const cx=xMid(i), cy=y(r.click*clickScale);
    const dot=svgEl('circle',{{cx,cy,r:'3',fill:isGray?'none':'#10b981',stroke:'#10b981','stroke-width':'1.5'}});
    svg.appendChild(dot);
  }});

  // X axis labels
  ROWS.forEach((r,i)=>{{
    const cx=xMid(i);
    const lbl=r.date.slice(5); // MM-DD
    svgText(svg,cx,H-PAD.b+16,lbl,{{'font-size':'10',fill:'#4b5563'}});
  }});
}})();

// ── Chart 2: CTR trend (area line) ───────────────────────
(function drawCTR(){{
  const svg = document.getElementById('chart-ctr');
  const W=1200,H=280,PAD={{l:60,r:20,t:20,b:50}};
  const cW=W-PAD.l-PAD.r, cH=H-PAD.t-PAD.b;
  const n=ROWS.length; if(!n) return;

  const maxCTR=Math.max(...ROWS.map(r=>r.ctr),3)*1.2||5;
  const y=v=>PAD.t+cH-(v/maxCTR)*cH;
  const xMid=i=>PAD.l+(i+0.5)*(cW/n);

  // Y grid
  for(let t=0;t<=4;t++){{
    const yv=PAD.t+cH*(1-t/4);
    svgLine(svg,PAD.l,yv,W-PAD.r,yv,{{stroke:'#1a1f2c','stroke-dasharray':'3,3'}});
    svgText(svg,PAD.l-8,yv,(maxCTR*t/4).toFixed(1)+'%',{{'text-anchor':'end','dominant-baseline':'middle',fill:'#4b5563','font-size':'10'}});
  }}

  // 1% reference line
  const ref1y=y(1);
  svgLine(svg,PAD.l,ref1y,W-PAD.r,ref1y,{{stroke:'#ef4444','stroke-dasharray':'6,4','stroke-width':'1.5'}});
  svgText(svg,W-PAD.r+2,ref1y,'1%',{{'text-anchor':'start',fill:'#ef4444','font-size':'10','dominant-baseline':'middle'}});

  // Area fill
  const pts=ROWS.map((r,i)=>`${{xMid(i)}},${{y(r.ctr)}}`).join(' ');
  const areaPath=`M${{xMid(0)}},${{PAD.t+cH}} L${{pts.split(' ').join(' L')}} L${{xMid(n-1)}},${{PAD.t+cH}} Z`;
  const grad=svgEl('defs',{{}});
  grad.innerHTML=`<linearGradient id="ctrGrad" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#3b82f6" stop-opacity="0.3"/><stop offset="100%" stop-color="#3b82f6" stop-opacity="0.02"/></linearGradient>`;
  svg.appendChild(grad);
  svg.appendChild(svgEl('path',{{d:areaPath,fill:'url(#ctrGrad)'}}));

  // Line
  const isGrayArr=ROWS.map(r=>r.phase==='灰测期');
  for(let i=0;i<n-1;i++){{
    const x1=xMid(i),y1=y(ROWS[i].ctr),x2=xMid(i+1),y2=y(ROWS[i+1].ctr);
    svg.appendChild(svgEl('line',{{x1,y1,x2,y2,stroke:'#3b82f6','stroke-width':'2',
      'stroke-dasharray':isGrayArr[i]?'4,3':'none'}}));
  }}

  // Points + labels
  ROWS.forEach((r,i)=>{{
    const cx=xMid(i),cy=y(r.ctr);
    const isGray=r.phase==='灰测期';
    svg.appendChild(svgEl('circle',{{cx,cy,r:'4',fill:isGray?'none':'#3b82f6',stroke:'#3b82f6','stroke-width':'2'}}));
    svgText(svg,cx,cy-12,r.ctr+'%',{{'font-size':'10',fill:isGray?'#4b5563':'#93c5fd','font-weight':'600'}});
  }});

  // X labels
  ROWS.forEach((r,i)=>svgText(svg,xMid(i),H-PAD.b+16,r.date.slice(5),{{'font-size':'10',fill:'#4b5563'}}));
}})();

// ── Chart 3: Install rate bars ────────────────────────────
(function drawInstall(){{
  const svg=document.getElementById('chart-install');
  const W=1200,H=280,PAD={{l:60,r:20,t:20,b:50}};
  const cW=W-PAD.l-PAD.r,cH=H-PAD.t-PAD.b;
  const data=ROWS.filter(r=>r.click>0);
  const n=data.length; if(!n) return;
  const slotW=cW/n, barW=Math.max(6,slotW*0.6);
  const y=v=>PAD.t+cH-(v/100)*cH;
  const xMid=i=>PAD.l+(i+0.5)*slotW;

  // Y grid
  [0,25,50,75,100].forEach(t=>{{
    const yv=y(t);
    svgLine(svg,PAD.l,yv,W-PAD.r,yv,{{stroke:'#1a1f2c','stroke-dasharray':'3,3'}});
    svgText(svg,PAD.l-8,yv,t+'%',{{'text-anchor':'end','dominant-baseline':'middle',fill:'#4b5563','font-size':'10'}});
  }});

  data.forEach((r,i)=>{{
    const v=r.install_rate;
    const color=v>=80?'#10b981':v>=60?'#f59e0b':'#ef4444';
    const bh=Math.max(2,(v/100)*cH);
    const cx=xMid(i);
    svg.appendChild(svgEl('rect',{{x:cx-barW/2,y:y(v),width:barW,height:bh,fill:color,opacity:'0.85',rx:'2'}}));
    svgText(svg,cx,y(v)-8,v+'%',{{'font-size':'10',fill:color,'font-weight':'600'}});
    svgText(svg,cx,H-PAD.b+16,r.date.slice(5),{{'font-size':'10',fill:'#4b5563'}});
  }});
}})();
</script>
// ── Chart 4: Funnel (horizontal bars) ────────────────────
(function drawFunnel(){{
  const svg=document.getElementById('chart-funnel');
  const W=1200,H=340,PAD={{l:120,r:160,t:20,b:20}};
  const cW=W-PAD.l-PAD.r, cH=H-PAD.t-PAD.b;

  const steps=[
    {{label:'start',       val:{f_start}}},
    {{label:'trigger',     val:{f_trigger}}},
    {{label:'pop_show',    val:{f_show}}},
    {{label:'pop_click',   val:{f_click}}},
    {{label:'down_start',  val:{f_ds}}},
    {{label:'down_suc',    val:{f_dsuc}}},
    {{label:'down_end_suc',val:{f_desuc}}},
  ];
  const colors=['#3b82f6','#6366f1','#8b5cf6','#10b981','#f59e0b','#f97316','#ef4444'];
  const maxVal=steps[0].val||1;
  const rowH=cH/steps.length;

  steps.forEach((s,i)=>{{
    const barW=Math.max(2,(s.val/maxVal)*cW);
    const ry=PAD.t+i*rowH+rowH*0.15;
    const bh=rowH*0.55;
    svg.appendChild(svgEl('rect',{{x:PAD.l,y:ry,width:barW,height:bh,fill:colors[i],rx:'3',opacity:'0.85'}}));
    // label left
    svgText(svg,PAD.l-6,ry+bh/2,s.label,{{'text-anchor':'end','dominant-baseline':'middle',fill:'#e2e8f0','font-size':'12','font-family':'IBM Plex Mono,monospace'}});
    // value right
    svgText(svg,PAD.l+barW+8,ry+bh/2,s.val.toLocaleString(),{{'text-anchor':'start','dominant-baseline':'middle',fill:'#e2e8f0','font-size':'12','font-family':'IBM Plex Mono,monospace'}});
    // conversion rate between steps
    if(i>0){{
      const prev=steps[i-1].val;
      const rate=prev?((s.val/prev)*100).toFixed(1)+'%':'-';
      const isBottleneck=(i===3); // pop_click is biggest bottleneck
      svgText(svg,W-PAD.r+60,ry-rowH*0.15,'↓ '+rate,{{'text-anchor':'middle','dominant-baseline':'middle',fill:isBottleneck?'#ef4444':'#4b5563','font-size':'11','font-weight':isBottleneck?'700':'400','font-family':'IBM Plex Mono,monospace'}});
    }}
  }});
}})();

// ── Chart 5: Close behavior (horizontal bars) ────────────
(function drawClose(){{
  const svg=document.getElementById('chart-close');
  const W=1200,H=220,PAD={{l:140,r:160,t:20,b:20}};
  const cW=W-PAD.l-PAD.r, cH=H-PAD.t-PAD.b;

  const items=[
    {{label:'pop_close（主动关闭）',  val:{f_close},  color:'#8b5cf6'}},
    {{label:'kk_pop_timeout（超时）', val:{f_timeout}, color:'#f59e0b'}},
    {{label:'pop_notips（不再提示）', val:{f_notips},  color:'#ef4444'}},
    {{label:'pop_click（点击）',      val:{f_bclick},  color:'#10b981'}},
  ];
  const maxVal=Math.max(...items.map(it=>it.val))||1;
  const rowH=cH/items.length;

  items.forEach((it,i)=>{{
    const barW=Math.max(2,(it.val/maxVal)*cW);
    const ry=PAD.t+i*rowH+rowH*0.15;
    const bh=rowH*0.55;
    svg.appendChild(svgEl('rect',{{x:PAD.l,y:ry,width:barW,height:bh,fill:it.color,rx:'3',opacity:'0.85'}}));
    svgText(svg,PAD.l-6,ry+bh/2,it.label,{{'text-anchor':'end','dominant-baseline':'middle',fill:'#e2e8f0','font-size':'12','font-family':'Noto Sans SC,sans-serif'}});
    svgText(svg,PAD.l+barW+8,ry+bh/2,it.val.toLocaleString(),{{'text-anchor':'start','dominant-baseline':'middle',fill:'#e2e8f0','font-size':'12','font-family':'IBM Plex Mono,monospace'}});
  }});
}})();
</script>
</body>
</html>"""
    return html


if __name__ == '__main__':
    print(f"读取数据: {CSV_PATH}")
    daily = parse_csv(CSV_PATH)
    rows = compute_metrics(daily)
    print(f"共 {len(rows)} 天数据，日期范围: {rows[0]['date']} ~ {rows[-1]['date']}" if rows else "无数据")
    insights = gen_insights(rows)
    suggestions = gen_suggestions(rows)
    html = generate_html(rows, insights, suggestions)
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"看板已生成: {OUTPUT_PATH}")
