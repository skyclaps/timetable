import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from matplotlib import rcParams
import re
import sys
import platform

# クロスプラットフォーム対応のフォント設定
if platform.system() == 'Darwin':  # macOS
    fonts = ['Hiragino Sans', 'Arial Unicode MS', 'DejaVu Sans']
elif platform.system() == 'Windows':  # Windows
    fonts = ['MS Gothic', 'Yu Gothic', 'Hiragino Sans', 'DejaVu Sans']
else:  # Linux
    fonts = ['Noto Sans CJK JP', 'Hiragino Sans', 'DejaVu Sans']

rcParams['font.sans-serif'] = fonts
rcParams['axes.unicode_minus'] = False

root = tk.Tk()
root.title("Timetable Visualizer")
root.geometry("1000x700")
root.resizable(True, True)
root.configure(bg="#1a1a2e")

# 定期更新のIDを保持
update_id = None

def on_closing():
    """ウィンドウを閉じる際のクリーンアップ処理"""
    global update_id
    if update_id is not None:
        root.after_cancel(update_id)
    plt.close('all')
    root.destroy()
    sys.exit(0)

root.protocol("WM_DELETE_WINDOW", on_closing)

# 上部フレーム（入力欄と現在時刻）
top_frame = tk.Frame(root, bg="#1a1a2e")
top_frame.pack(fill=tk.X, padx=15, pady=10)

# 左側フレーム（入力欄）
left_frame = tk.Frame(top_frame, bg="#16213e", relief=tk.SUNKEN, bd=1)
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

# 入力欄ラベル
label = tk.Label(left_frame, text="Schedule", font=("Arial", 12, "bold"), fg="#00d4ff", bg="#16213e")
label.pack(anchor="w", padx=8, pady=(8, 4))

input_box = tk.Text(left_frame, height=8, width=30, bg="#0f3460", fg="#00d4ff", 
                     font=("Courier", 9), insertbackground="#00d4ff", relief=tk.FLAT, bd=0)
input_box.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

input_box.insert(tk.END,
"""17:00 act 1
18:30 act 2
19:10 act 3
20:00 act 4
21:00 act 5
22:00 act 6
23:00 act 7
25:00 act 8
02:00 act 9""")

# 右側フレーム（現在時刻）
right_frame = tk.Frame(top_frame, bg="#16213e", relief=tk.SUNKEN, bd=1)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=(10, 0), ipadx=20, ipady=10)

time_label = tk.Label(right_frame, text="--:--:--", font=("Courier", 56, "bold"), 
                      fg="#ff006e", bg="#16213e")
time_label.pack(expand=True)

fig, ax = plt.subplots(figsize=(8,4), facecolor="#1a1a2e", edgecolor="#00d4ff", linewidth=2)
ax.set_facecolor("#0f3460")
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 15))

def parse_task_list():
    from datetime import timedelta
    rows = []
    
    # 時間表記をパース（25時以上に対応）
    # 秒単位での値も返す
    def parse_time(time_str):
        parts = time_str.split(":")
        hours = int(parts[0])
        minutes = int(parts[1])
        total_seconds = hours * 3600 + minutes * 60
        # datetimeオブジェクト用
        base = datetime.strptime("00:00", "%H:%M")
        dt = base + timedelta(seconds=total_seconds)
        return dt, total_seconds  # (datetime, 秒単位)
    
    lines = input_box.get("1.0", tk.END).splitlines()
    
    for i, line in enumerate(lines):
        # 「HH:MM タスク名」形式で入力
        m = re.match(r"(\d{1,2}:\d{2})\s+(.+)", line)
        if not m:
            continue
        start_str, label = m.groups()
        
        s, s_seconds = parse_time(start_str)
        
        # 終了時刻は次のタスクの開始時刻、または24時以上の場合はそのまま
        if i + 1 < len(lines):
            next_m = re.match(r"(\d{1,2}:\d{2})\s+(.+)", lines[i + 1])
            if next_m:
                e, e_seconds = parse_time(next_m.group(1))
            else:
                continue  # フォーマットが不正なら無視
        else:
            # 最後のタスク：デフォルトで1時間後
            e, e_seconds = s + __import__('datetime').timedelta(hours=1), s_seconds + 3600
        
        rows.append((s, s_seconds, e, e_seconds, label))
    
    return rows

def draw():
    try:
        ax.clear()
        rows = parse_task_list()
        if not rows:
            return

    # 基準時刻（最初のタスク開始時刻）
    base_time = rows[0][0]
    
    # 現在時刻を取得
    current_time = datetime.now()
    
    # タスクを入力順に積み上げる
    cumulative_sec = 0
    
    # 現在時刻を秒単位で取得
    current_time_seconds = current_time.hour * 3600 + current_time.minute * 60 + current_time.second
    
    for i, (s, s_seconds, e, e_seconds, label) in enumerate(rows):
        # 終了時刻が開始時刻より前の場合は翌日として処理
        duration_seconds = e_seconds - s_seconds
        if duration_seconds < 0:
            # 日付跨ぎの場合：翌日までの秒数を計算
            duration_seconds = 86400 - s_seconds + e_seconds
        
        # 入力順に積み上げていく
        s_sec = cumulative_sec
        e_sec = cumulative_sec + duration_seconds
        cumulative_sec = e_sec
        
        # 現在時刻判定：秒単位で比較
        is_active = False
        if e_seconds >= s_seconds:
            # 日付跨ぎでない場合
            if s_seconds <= current_time_seconds <= e_seconds:
                is_active = True
        else:
            # 日付跨ぎの場合（例：25:00-02:00）
            if current_time_seconds >= s_seconds or current_time_seconds <= e_seconds:
                is_active = True

        ax.bar(
            0,
            duration_seconds,
            bottom=s_sec,
            width=0.6,
            color="#00d4ff" if is_active else "#533483",
            edgecolor="#00d4ff" if is_active else "#8f4fa6",
            linewidth=2
        )
        
        # バーの中にタスク名を表示
        mid_time = s_sec + duration_seconds / 2
        ax.text(0, mid_time, label, ha='center', va='center', 
                fontsize=11, fontweight='bold', color="white" if is_active else "#e0e0e0")
        
        # タスク終了時刻に線を引く（最後のタスク以外）
        if i < len(rows) - 1:
            ax.axhline(e_sec, linestyle="-", color="#444466", linewidth=0.8, alpha=0.5)

    # 現在時刻ラインの計算
    current_sec = None
    cumulative_sec = 0
    
    for s, s_seconds, e, e_seconds, _ in rows:
        duration_seconds = e_seconds - s_seconds
        if duration_seconds < 0:
            # 日付跨ぎの場合
            duration_seconds = 86400 - s_seconds + e_seconds
        
        # 日付跨ぎでない場合
        if e_seconds >= s_seconds:
            if s_seconds <= current_time_seconds <= e_seconds:
                # このタスク内に現在時刻がある
                time_within_task = current_time_seconds - s_seconds
                current_sec = cumulative_sec + time_within_task
                break
        else:
            # 日付跨ぎの場合
            if current_time_seconds >= s_seconds or current_time_seconds <= e_seconds:
                # このタスク内に現在時刻がある
                if current_time_seconds >= s_seconds:
                    # 開始時刻以降の時間帯
                    time_within_task = current_time_seconds - s_seconds
                else:
                    # 翌日の時間帯（00:00～終了時刻）
                    time_within_task = duration_seconds - (86400 - s_seconds) + current_time_seconds
                
                current_sec = cumulative_sec + time_within_task
                break
        
        cumulative_sec += duration_seconds
    
    if current_sec is not None:
        ax.axhline(current_sec, linestyle="--", color="#ff006e", linewidth=3, alpha=0.8)

    # Y軸を時間表記で表示（タスク時刻ベース）
    yticks = []
    yticklabels = []
    cumulative_sec = 0
    for s, s_seconds, e, e_seconds, _ in rows:
        duration_seconds = e_seconds - s_seconds
        if duration_seconds < 0:
            duration_seconds = 86400 - s_seconds + e_seconds
        
        # 開始時刻をティックに追加
        yticks.append(cumulative_sec)
        yticklabels.append(s.strftime("%H:%M"))
        cumulative_sec += duration_seconds
    
    # 最後のタスク終了時刻をティックに追加
    yticks.append(cumulative_sec)
    yticklabels.append(rows[-1][2].strftime("%H:%M"))
    
    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels, color="#00d4ff", fontsize=9, weight='bold')
    ax.invert_yaxis()
    # Y軸の範囲を動的に調整してすべてのタスクを表示
    ax.set_ylim(cumulative_sec + 500, -500)
    ax.set_xlim(-0.5, 0.5)
    ax.set_xticks([])
    ax.set_ylabel("Time", color="#00d4ff", fontsize=11, fontweight='bold')
    ax.set_title("Timetable", color="#00d4ff", fontsize=14, fontweight='bold', pad=15)
    ax.tick_params(colors="#00d4ff", labelsize=8)
    
    # 枠線を改善
    for spine in ax.spines.values():
        spine.set_edgecolor("#00d4ff")
        spine.set_linewidth(2)
    
    # グリッドを追加
    ax.grid(axis='y', color="#444466", alpha=0.2, linestyle='-', linewidth=0.5)
    
    # 右側のラベルに現在時刻を表示
        current_time_str = current_time.strftime("%H:%M:%S")
        time_label.config(text=current_time_str)

        canvas.draw()
        global update_id
        update_id = root.after(1000, draw)
    
    except Exception as e:
        error_msg = f"エラーが発生しました:\n\n{str(e)}"
        messagebox.showerror("エラー", error_msg)
        # エラー後も再度試行
        global update_id
        update_id = root.after(1000, draw)

draw()
root.mainloop()
