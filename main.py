import os
import random
import tkinter as tk
from tkinter import messagebox

# --- 🎥 GIFアニメーション制御用の変数 ---
gif_frames = []
gif_index = 0
is_playing = False  # 現在アニメーション中かどうかを管理するフラグ


def load_weapons(filename):
    """ファイルから武器データを読み込む関数"""
    weapons = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                size = 1
                if line.startswith("[1]"):
                    size = 1
                elif line.startswith("[2]"):
                    size = 2
                elif line.startswith("[3]"):
                    size = 3
                else:
                    line = f"[1]{line}"

                weapons.append({"name": line, "size": size})

                if "[Dual]" in line:
                    clean_name = line.replace(" [Dual]", "")
                    dual_name = clean_name.replace("[1]", "[2]二丁拳銃: ")
                    weapons.append({"name": dual_name, "size": 2})
    except FileNotFoundError:
        pass
    return weapons


def get_random_lines(filename, count, allow_duplicates=False):
    """ツール・消耗品用の汎用読み込み関数"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            return ["（ファイルが空です）"]
        if allow_duplicates:
            return random.choices(lines, k=count)
        if len(lines) < count:
            return random.choices(lines, k=count)
        return random.sample(lines, count)
    except FileNotFoundError:
        return [f"（{filename} が見つかりません）"]


def select_weapons(weapons, max_slots):
    """スロット制限に収まるようにメイン・サブ武器を選ぶ"""
    if not weapons:
        return ["（武器データがありません）", "（武器データがありません）"]

    w1 = random.choice(weapons)
    remaining_slots = max_slots - w1["size"]
    available_w2 = [w for w in weapons if w["size"] <= remaining_slots]

    if not available_w2:
        available_w2 = [w for w in weapons if w["size"] == 1]

    w2 = random.choice(available_w2)
    return [w1["name"], w2["name"]]


def update_gif():
    """GIFアニメをパラパラ動かす関数"""
    global gif_index, is_playing
    if gif_frames and is_playing:
        gif_index = (gif_index + 1) % len(gif_frames)
        image_label.config(image=gif_frames[gif_index])
        # 100ミリ秒（0.1秒）ごとに次のコマへ
        root.after(100, update_gif)


def stop_gif():
    """アニメーションを停止して、最初のコマ（静止画）に戻す関数"""
    global gif_index, is_playing
    is_playing = False
    gif_index = 0
    if gif_frames:
        image_label.config(image=gif_frames[0])


def generate_text():
    """ロードアウトを生成して画面に表示する（ボタンを押したときの処理）"""
    global is_playing

    # 1. まず装備をランダム生成して表示
    result = []
    max_slots = 5 if qm_var.get() else 4
    weapons_list = load_weapons("Data/weapons.txt")

    if not weapons_list:
        primary, secondary = (
            "（Data/weapons.txt が見つかりません）",
            "（Data/weapons.txt が見つかりません）",
        )
    else:
        primary, secondary = select_weapons(weapons_list, max_slots)

    result.append("＝＝１から（メイン武器）＝＝")
    result.append(primary)
    result.append("")

    result.append("＝＝２から（サブ武器）＝＝")
    result.append(secondary)
    result.append("")

    result.append("＝＝３から（ツール）＝＝")
    result.append("救急キット")
    result.extend(get_random_lines("Data/03_Tool.txt", 3))
    result.append("")

    result.append("＝＝４から（消耗品）＝＝")
    result.extend(
        get_random_lines("Data/04_Consumable.txt", 4, allow_duplicates=True)
    )

    text_area.config(state=tk.NORMAL)
    text_area.delete("1.0", tk.END)
    text_area.insert(tk.END, "\n".join(result))
    text_area.config(state=tk.DISABLED)

    # 2. ★ 同時にGIFアニメーションを再生開始する
    if gif_frames and not is_playing:
        is_playing = True
        update_gif()
        # 1000ミリ秒（1秒）後に自動で止めるタイマーをセット
        root.after(1000, stop_gif)


def show_welcome_message():
    """起動時に表示する案内テキスト"""
    welcome_text = (
        "上のチェックボックスを確認して下の生成を押してね！\n"
        "Please check the checkbox above and click the button below to generate!\n"
        "\n"
        "--------------------------------------------------\n"
        "【Hunt: Showdown Loadout Randomizer】"
    )
    text_area.config(state=tk.NORMAL)
    text_area.delete("1.0", tk.END)
    text_area.insert(tk.END, welcome_text)
    text_area.config(state=tk.DISABLED)


# --- 画面（GUI）の作成 ---
root = tk.Tk()
root.title("Hunt: Showdown ロードアウト抽選")
root.geometry("480x600")

# クォーターマスターのチェックボックス
qm_var = tk.BooleanVar()
qm_check = tk.Checkbutton(
    root,
    text="Quartermaster (特性あり・最大5スロット)",
    variable=qm_var,
    font=("MS Gothic", 11, "bold"),
    pady=5,
)
qm_check.pack()

# メイン表示エリア
main_frame = tk.Frame(root)
main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

# 結果を表示するテキストエリア
text_area = tk.Text(main_frame, wrap=tk.WORD, font=("MS Gothic", 12))
text_area.pack(expand=True, fill=tk.BOTH)

# 再試行ボタン
retry_button = tk.Button(
    root,
    text="ロードアウトを生成 / 再試行 (Generate / Retry)",
    font=("MS Gothic", 12, "bold"),
    bg="#1f77b4",
    fg="white",
    command=generate_text,
)
retry_button.pack(fill=tk.X, padx=10, pady=10)

# GIFアニメーション画像の読み込み処理
gif_path = "Data/character.gif"
if os.path.exists(gif_path):
    try:
        idx = 0
        while True:
            frame = tk.PhotoImage(file=gif_path, format=f"gif -index {idx}")
            gif_frames.append(frame)
            idx += 1
    except tk.TclError:
        pass

# 画像を表示するラベル（オレンジの部分に固定配置）
if gif_frames:
    image_label = tk.Label(root, bd=0, highlightthickness=0)
    image_label.place(relx=1.0, rely=1.0, anchor="se", x=-25, y=-80)
    # 最初は最初のコマ（静止状態）を表示しておく
    image_label.config(image=gif_frames[0])

# 起動時のセットアップ
show_welcome_message()

root.mainloop()