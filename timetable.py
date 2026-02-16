import tkinter as tk
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
root.geometry("800x600")
root.resizable(True, True)
root.configure(bg="black")

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
top_frame = tk.Frame(root, bg="black")
top_frame.pack(fill=tk.X, padx=10, pady=5)

# 左側フレーム（入力欄）
left_frame = tk.Frame(top_frame, bg="black")
left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

input_box = tk.Text(left_frame, height=6, width=30)
input_box.pack(fill=tk.BOTH, expand=True)

input_box.insert(tk.END,
"""18:00-18:30 act 1
18:30-19:00 act 2
19:00-20:00 act 3
20:00-21:00 act 4
21:00-22:00 act 5
22:00-23:00 act 6
23:00-24:00 act 7""")

# 右側フレーム（現在時刻）
right_frame = tk.Frame(top_frame, bg="black")
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(20, 0))

time_label = tk.Label(right_frame, text="", font=("Arial", 48, "bold"), fg="red", bg="black")
time_label.pack(expand=True)

fig, ax = plt.subplots(figsize=(8,4))
fig.patch.set_facecolor("black")
ax.set_facecolor("black")
canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def parse_text():
    rows = []
    for line in input_box.get("1.0", tk.END).splitlines():
        m = re.match(r"(\d{1,2}:\d{2})-(\d{1,2}:\d{2})\s+(.+)", line)
        if not m:
            continue
        start, end, label = m.groups()
        # 24:00を00:00として扱い、翌日として処理
        if end == "24:00":
            s = datetime.strptime(start, "%H:%M")
            e = datetime.strptime("00:00", "%H:%M")
            from datetime import timedelta
            e += timedelta(days=1)
        else:
            s = datetime.strptime(start, "%H:%M")
            e = datetime.strptime(end, "%H:%M")
        rows.append((s, e, label))
    return rows

def draw():
    ax.clear()
    rows = parse_text()
    if not rows:
        return

    now = datetime.now().replace(
        year=rows[0][0].year,
        month=rows[0][0].month,
        day=rows[0][0].day
    )

    # 基準時刻（最初のタスク開始時刻）を設定４
    base_time = rows[0][0]
    
    # datetimeを秒単位に変換する関数
    def to_seconds(dt):
        return (dt - base_time).total_seconds()

    for i, (s, e, label) in enumerate(rows):
        duration = (e - s).seconds
        s_sec = to_seconds(s)
        
        active = s <= now <= e

        ax.bar(
            0,
            duration,
            bottom=s_sec,
            width=0.5,
            color="orange" if active else "skyblue"
        )
        
        # バーの中にタスク名を表示
        mid_time = s_sec + duration / 2
        ax.text(0, mid_time, label, ha='center', va='center', 
                fontsize=10, fontweight='bold', color='black')
        
        # タスク終了時刻に線を引く（最後のタスク以外）
        if i < len(rows) - 1:
            e_sec = to_seconds(e)
            ax.axhline(e_sec, linestyle="-", color="black", linewidth=1)

    now_sec = to_seconds(now)
    ax.axhline(now_sec, linestyle="--", color="red")

    # Y軸を時間表記で表示
    min_sec = 0
    max_sec = to_seconds(rows[-1][1])
    
    # Y軸のティック位置と時間表記を設定
    yticks = []
    yticklabels = []
    for hours in range(0, int(max_sec // 3600) + 2):
        tick_sec = hours * 3600
        if tick_sec <= max_sec:
            yticks.append(tick_sec)
            tick_time = base_time + __import__('datetime').timedelta(seconds=tick_sec)
            yticklabels.append(tick_time.strftime("%H:%M"))
    
    ax.set_yticks(yticks)
    ax.set_yticklabels(yticklabels, color="white")
    ax.invert_yaxis()
    ax.set_xlim(-0.5, 0.5)
    ax.set_xticks([])
    ax.set_ylabel("Time", color="white")
    ax.set_title("Timetable", color="white")
    ax.tick_params(colors="white")
    
    # 右側のラベルに現在時刻を表示
    current_time_str = now.strftime("%H:%M:%S")
    time_label.config(text=current_time_str)

    canvas.draw()
    global update_id
    update_id = root.after(1000, draw)

draw()
root.mainloop()
