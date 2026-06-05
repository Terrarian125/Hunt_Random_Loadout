import glob
import os
import random
import re
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# --- 🎥 GIFアニメーション制御用のグローバル変数 ---
gif_frames = []
gif_index = 0
is_playing = False


def parse_ammo(line):
    """武器の行から（[数]弾薬）や（[数]近接）の部分をすべて解析して、ランダムに選ぶ関数"""
    matches = list(re.finditer(r"（(.*?)）", line))

    if not matches:
        return line, ""

    clean_name = line[: matches[0].start()].strip()
    all_ammo_texts = []

    for match in matches:
        ammo_content = match.group(1)

        # 「近接」などの特殊タグの場合は、そのままカッコ付きで残す
        if "近接" in ammo_content:
            all_ammo_texts.append(ammo_content)
            continue

        count = 1
        count_match = re.search(r"\[([12])\]", ammo_content)
        if count_match:
            count = int(count_match.group(1))
            ammo_options_str = ammo_content[count_match.end() :]
        else:
            ammo_options_str = ammo_content

        ammo_options = [
            a.strip() for a in ammo_options_str.split("｜") if a.strip()
        ]

        if not ammo_options:
            continue

        if "二丁拳銃:" in clean_name and count > 1:
            count = 1

        if len(ammo_options) < count:
            count = len(ammo_options)

        selected_ammo = random.sample(ammo_options, count)
        all_ammo_texts.append("/".join(selected_ammo))

    final_ammo_text = " ＋ ".join(all_ammo_texts)
    return clean_name, f" （{final_ammo_text}）"


def load_weapons(filename):
    """ファイルから武器データを読み込む関数（サイズ1〜5に対応）"""
    weapons = []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                size = 1
                size_match = re.match(r"^\[([1-5])\]", line)
                if size_match:
                    size = int(size_match.group(1))
                else:
                    line = f"[1]{line}"

                weapons.append({"raw_line": line, "size": size})

                if "[Dual]" in line:
                    dual_line = line.replace(" [Dual]", "")
                    dual_line = re.sub(r"^\[[1-5]\]", "[2]二丁拳銃: ", dual_line)
                    # 二丁拳銃化しても近接タグが残るように末尾に（近接）を補正
                    if "近接" in line and not dual_line.endswith("（近接）"):
                        dual_line += "（近接）"
                    weapons.append({"raw_line": dual_line, "size": 2})
    except FileNotFoundError:
        pass
    return weapons


def get_integrated_items(tool_file, consumable_file, count, exclude_medkit=False):
    """ツールと消耗品ファイルを統合し、ランダムに指定個数抽出する（重複あり）"""
    combined_items = []

    # ツールファイルの読み込み
    try:
        with open(tool_file, "r", encoding="utf-8") as f:
            for line in f:
                item = line.strip()
                if item:
                    if exclude_medkit and "救急キット" in item:
                        continue
                    combined_items.append(item)
    except FileNotFoundError:
        pass

    # 消耗品ファイルの読み込み
    try:
        with open(consumable_file, "r", encoding="utf-8") as f:
            for line in f:
                item = line.strip()
                if item:
                    combined_items.append(item)
    except FileNotFoundError:
        pass

    if not combined_items:
        return ["（アイテムデータが見つかりません）"] * count

    return random.choices(combined_items, k=count)


def select_weapons(weapons, max_slots):
    """新仕様（合計5〜6スロット）に収まるようにメイン・サブ武器を選ぶ"""
    if not weapons:
        return None, None

    available_w1 = [w for w in weapons if w["size"] <= (max_slots - 1)]
    if not available_w1:
        available_w1 = weapons

    w1 = random.choice(available_w1)
    remaining_slots = max_slots - w1["size"]

    available_w2 = [w for w in weapons if w["size"] <= remaining_slots]
    if not available_w2:
        available_w2 = [w for w in weapons if w["size"] == 1]

    w2 = random.choice(available_w2)
    return w1, w2


def update_gif():
    """GIFアニメを1回だけ最後まで再生し、最後のコマで止まる関数"""
    global gif_index, is_playing
    if gif_frames and is_playing:
        if gif_index < len(gif_frames):
            image_label.config(image=gif_frames[gif_index])
            gif_index += 1
            root.after(50, update_gif)
        else:
            is_playing = False


def load_random_gif():
    """Data/Image フォルダ内のGIFからランダムに1つ選んでフレームを読み込む"""
    global gif_frames
    gif_frames = []

    image_dir = "Data/Image"
    if not os.path.exists(image_dir):
        return

    gif_files = glob.glob(os.path.join(image_dir, "*.gif"))
    if not gif_files:
        return

    chosen_gif = random.choice(gif_files)

    try:
        img = Image.open(chosen_gif)
        try:
            while True:
                frame_img = img.convert("RGBA")
                resized_img = frame_img.resize((220, 220), Image.Resampling.LANCZOS)
                gif_frames.append(ImageTk.PhotoImage(resized_img))
                img.seek(img.tell() + 1)
        except EOFError:
            pass
    except Exception as e:
        print(f"GIF読み込みエラー ({chosen_gif}): {e}")


def generate_text():
    """ロードアウトを生成して画面に表示する"""
    global is_playing, gif_index
    
    max_slots = 6 if qm_var.get() else 5
    weapons_list = load_weapons("Data/weapons.txt")

    # 条件を満たすまで最大100回リトライするループ
    for _ in range(100):
        result_items = []
        
        # 1. 武器の選択
        w1_data, w2_data = select_weapons(weapons_list, max_slots)
        if w1_data and w2_data:
            w1_name, w1_ammo = parse_ammo(w1_data["raw_line"])
            w2_name, w2_ammo = parse_ammo(w2_data["raw_line"])
            primary = f"{w1_name}{w1_ammo}"
            secondary = f"{w2_name}{w2_ammo}"
        else:
            primary = "（Data/weapons.txt が見つかりません）"
            secondary = "（Data/weapons.txt が見つかりません）"

        # 2. ツール＆消耗品の選択
        if medkit_var.get():
            result_items.append("救急キット")
            random_items = get_integrated_items(
                "Data/03_Tool.txt", "Data/04_Consumable.txt", 7, exclude_medkit=True
            )
            result_items.extend(random_items)
        else:
            random_items = get_integrated_items(
                "Data/03_Tool.txt", "Data/04_Consumable.txt", 8, exclude_medkit=False
            )
            result_items.extend(random_items)

        # 3. 近接武器必須オプションの判定（★ 統一された「近接」の文字があるかだけで判定）
        if melee_var.get():
            has_melee = ("近接" in primary) or ("近接" in secondary) or any("近接" in item for item in result_items)
            if not has_melee:
                continue  # 近接がどこにも無ければリトライ

        break

    # テキスト出力用に整形
    final_output = []
    final_output.append("＝＝１から（メイン武器）＝＝")
    final_output.append(primary)
    final_output.append("")
    final_output.append("＝＝２から（サブ武器）＝＝")
    final_output.append(secondary)
    final_output.append("")
    final_output.append("＝＝３から（ツール＆消耗品 - 計８枠）＝＝")
    final_output.extend(result_items)

    # 画面への描画
    text_area.config(state=tk.NORMAL)
    text_area.delete("1.0", tk.END)
    text_area.insert(tk.END, "\n".join(final_output))
    text_area.config(state=tk.DISABLED)

    # ランダムにGIFを読み込んで再生
    load_random_gif()
    if gif_frames:
        is_playing = True
        gif_index = 0
        update_gif()


def show_welcome_message():
    """起動時に表示する案内テキスト"""
    welcome_text = (
        "設定を確認して下の生成ボタンを押してね！\n"
        "Configure settings and click the button below to generate!\n"
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
root.geometry("540x670")

# オプション設定エリア
options_frame = tk.Frame(root)
options_frame.pack(pady=5)

qm_var = tk.BooleanVar(value=False)
qm_check = tk.Checkbutton(
    options_frame,
    text="Quartermaster (最大6スロット)",
    variable=qm_var,
    font=("MS Gothic", 10, "bold"),
)
qm_check.grid(row=0, column=0, padx=5, sticky="w")

melee_var = tk.BooleanVar(value=True)
melee_check = tk.Checkbutton(
    options_frame,
    text="近接装備を最低1つ確定",
    variable=melee_var,
    font=("MS Gothic", 10, "bold"),
)
melee_check.grid(row=0, column=1, padx=5, sticky="w")

medkit_var = tk.BooleanVar(value=True)
medkit_check = tk.Checkbutton(
    options_frame,
    text="救急キット枠を固定化",
    variable=medkit_var,
    font=("MS Gothic", 10, "bold"),
)
medkit_check.grid(row=1, column=0, columnspan=2, padx=5, sticky="w", pady=2)

# メイン表示エリア
main_frame = tk.Frame(root)
main_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

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

# 初期状態のGIF読み込み
load_random_gif()

# 画像を表示するラベル
if gif_frames:
    image_label = tk.Label(root, bd=0, highlightthickness=0, bg=text_area["bg"])
    image_label.place(relx=1.0, rely=1.0, anchor="se", x=-25, y=-80)
    image_label.config(image=gif_frames[0])

show_welcome_message()
root.mainloop()