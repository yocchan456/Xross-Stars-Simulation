import random
import statistics
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib_fontja
import streamlit as st

# ==========================================
# ページ設定・タイトル・安全性アピール
# ==========================================
st.set_page_config(
    page_title="デッキ比較シミュレーター",
    page_icon="👑",
    layout="wide"
)

st.title("👑 デッキ比較シミュレーター")
st.info(
    "🔒 **安全設計のお知らせ**: このツールはブラウザ上で動作する計算専用Webアプリです。"
    "Googleアカウントへのログインや権限の許可、個人データの収集・保存は一切行いません。"
)

# ==========================================
# 1. カードスペック・基本設定
# ==========================================
TURNS_PER_ROUND = (5, 5, 5)

CARD_SPECS = {
    "魔王再臨": {"cost": 0, "type": "memoria", "ace": True},
    "アブソリュートドミニオン": {"cost": 1, "type": "attack", "ace": True},
    "シンクロトリニティ": {"cost": 1, "type": "attack", "ace": False},
    "アルティメットツモ": {"cost": 0, "type": "memoria", "ace": False},
    "焦土の王者": {"cost": 0, "type": "memoria", "ace": False},
    "シンリャク開始": {"cost": 1, "type": "attack", "ace": False},
    "対空射撃": {"cost": 1, "type": "attack", "ace": False},
    "彼こそがロック": {"cost": 1, "type": "memoria", "ace": False},
    "1TAP": {"cost": 1, "type": "attack", "ace": False},
    "花火づくり": {"cost": 1, "type": "memoria", "ace": False},
    "ノーネーム0コス": {"cost": 0, "type": "memoria", "ace": False},
    "ノーネーム1コスアタック": {"cost": 1, "type": "attack", "ace": False},
}

DEFAULT_PRESETS = [
    {
        "name": "デフォルト構築 (ツモ8枚)",
        "counts": {
            "魔王再臨": 4, "アブソリュートドミニオン": 4, "シンクロトリニティ": 0,
            "アルティメットツモ": 8, "焦土の王者": 4, "シンリャク開始": 4,
            "対空射撃": 0, "彼こそがロック": 0, "1TAP": 0,
            "花火づくり": 0, "ノーネーム0コス": 10, "ノーネーム1コスアタック": 16,
        }
    },
    {
        "name": "1TAP入り",
        "counts": {
            "魔王再臨": 4, "アブソリュートドミニオン": 4, "シンクロトリニティ": 0,
            "アルティメットツモ": 8, "焦土の王者": 4, "シンリャク開始": 4,
            "対空射撃": 0, "彼こそがロック": 0, "1TAP": 4,
            "花火づくり": 0, "ノーネーム0コス": 10, "ノーネーム1コスアタック": 12,
        }
    },
    {
        "name": "平岩・こはく・No.1005・つな",
        "counts": {
            "魔王再臨": 4, "アブソリュートドミニオン": 4, "シンクロトリニティ": 0,
            "アルティメットツモ": 0, "焦土の王者": 4, "シンリャク開始": 4,
            "対空射撃": 8, "彼こそがロック": 2, "1TAP": 0,
            "花火づくり": 0, "ノーネーム0コス": 20, "ノーネーム1コスアタック": 4,
        }
    },
    {
        "name": "パターン4",
        "counts": {
            "魔王再臨": 4, "アブソリュートドミニオン": 4, "シンクロトリニティ": 0,
            "アルティメットツモ": 6, "焦土の王者": 4, "シンリャク開始": 4,
            "対空射撃": 0, "彼こそがロック": 0, "1TAP": 0,
            "花火づくり": 0, "ノーネーム0コス": 8, "ノーネーム1コスアタック": 20,
        }
    },
    {
        "name": "パターン5",
        "counts": {
            "魔王再臨": 4, "アブソリュートドミニオン": 4, "シンクロトリニティ": 0,
            "アルティメットツモ": 8, "焦土の王者": 4, "シンリャク開始": 4,
            "対空射撃": 0, "彼こそがロック": 0, "1TAP": 0,
            "花火づくり": 0, "ノーネーム0コス": 8, "ノーネーム1コスアタック": 18,
        }
    }
]

# ==========================================
# 2. サイドバー：共通設定＆出力項目選択
# ==========================================
with st.sidebar:
    st.header("⚙️ シミュレーション設定")
    compare_count = st.selectbox("比較するパターン数", [1, 2, 3, 4, 5], index=2)
    shinryaku_rate = st.slider("シンリャク成功率", min_value=0.0, max_value=1.0, value=0.5, step=0.05)

    st.divider()
    st.subheader("📊 表示するグラフ・表")
    show_summary = st.checkbox("簡易サマリーを表示", value=True)
    show_detail_stats = st.checkbox("詳細統計を表示", value=True)
    show_round_table = st.checkbox("ラウンド別詳細テーブルを表示", value=False)
    show_turn_table = st.checkbox("ターン別詳細テーブルを表示", value=False)
    show_keycard_graph = st.checkbox("キーカード接触グラフを表示", value=True)
    show_indiv_graph = st.checkbox("キーカード別_個別接触グラフを表示", value=True)
    show_draw_graph = st.checkbox("山札ドロー挙動グラフを表示", value=True)
    show_round_net_graph = st.checkbox("ラウンド毎リセット_手札純増減グラフを表示", value=True)
    show_round_deck_graph = st.checkbox("ラウンド毎リセット_山札掘削グラフを表示", value=True)
    show_round_dist = st.checkbox("ラウンド毎新規接触分布を表示", value=False)
    show_turn_dist = st.checkbox("ターン毎新規接触分布を表示", value=False)
    show_cum_dist = st.checkbox("ラウンド内累積接触分布を表示", value=False)

# ==========================================
# 3. メイン画面：各パターンのデッキ構築入力
# ==========================================
st.subheader("🃏 各パターンのデッキ構築（合計50枚）")
tabs = st.tabs([f"パターン {i+1}" for i in range(compare_count)])

patterns_input = []
all_valid_50 = True

for i in range(compare_count):
    with tabs[i]:
        preset = DEFAULT_PRESETS[i]
        col_top1, col_top2 = st.columns([2, 1])
        with col_top1:
            p_name = st.text_input("パターン名称", value=preset["name"], key=f"name_{i}")
        with col_top2:
            p_trials = st.slider("試行回数", min_value=1000, max_value=20000, value=10000, step=1000, key=f"trials_{i}")

        st.markdown("**カード枚数設定**")
        card_names = list(CARD_SPECS.keys())
        cols = st.columns(4)
        counts = {}
        for idx, c_name in enumerate(card_names):
            with cols[idx % 4]:
                counts[c_name] = st.number_input(
                    c_name,
                    min_value=0,
                    max_value=50,
                    value=preset["counts"][c_name],
                    step=1,
                    key=f"card_{i}_{c_name}"
                )

        total_cards = sum(counts.values())
        if total_cards == 50:
            st.success(f"✅ 現在の合計枚数: **{total_cards} / 50枚**（OK）")
        else:
            st.error(f"⚠️ 現在の合計枚数: **{total_cards} / 50枚**（あと {50 - total_cards:+d} 枚調整してください）")
            all_valid_50 = False

        patterns_input.append({
            "name": p_name.strip() if p_name.strip() else f"パターン {i+1}",
            "trials": int(p_trials),
            "counts": counts,
        })

# ==========================================
# 4. ディスカード・ユーティリティ処理
# ==========================================
def get_discard_priority(card, hand, ref_pp):
    name = card["name"]
    if name == "ノーネーム0コス":
        return 1
    noname_atk_count = sum(1 for c in hand if c["name"] == "ノーネーム1コスアタック")
    if name == "ノーネーム1コスアタック" and noname_atk_count >= max(1, ref_pp):
        return 2
    if name == "焦土の王者":
        return 3
    if name == "花火づくり":
        return 4
    if name == "彼こそがロック":
        return 5
    if name == "ノーネーム1コスアタック":
        return 6
    if name == "1TAP":
        return 7
    if name == "シンリャク開始":
        return 8
    if name in ("対空射撃", "シンクロトリニティ"):
        return 9
    if name == "アルティメットツモ":
        return 10
    if name == "魔王再臨":
        return 11
    if name == "アブソリュートドミニオン":
        return 12
    return 13

def discard_one_card(hand, trash, ref_pp, on_discard=None):
    if not hand:
        return False
    target = min(hand, key=lambda c: get_discard_priority(c, hand, ref_pp))
    hand.remove(target)
    trash.append(target)
    if on_discard:
        on_discard()
    return True

def discard_zero_cost_card(hand, trash, ref_pp, on_discard=None):
    zero_cands = [c for c in hand if c["cost"] == 0]
    if not zero_cands:
        return False
    target = min(zero_cands, key=lambda c: get_discard_priority(c, hand, ref_pp))
    hand.remove(target)
    trash.append(target)
    if on_discard:
        on_discard()
    return True

def discard_to_limit(hand, trash, ref_pp, on_discard=None):
    while len(hand) > 7:
        discard_one_card(hand, trash, ref_pp, on_discard)

# ==========================================
# 5. 1試合シミュレーションロジック
# ==========================================
def simulate_match(counts, shin_rate):
    deck = []
    for name, count in counts.items():
        for _ in range(count):
            c = CARD_SPECS[name].copy()
            c["name"] = name
            deck.append(c)
    random.shuffle(deck)

    trash = []
    turn_played_zone = []
    echo_field = []

    seen_cards = set()
    touch_counts = {"魔王再臨": 0, "アブソリュートドミニオン": 0}
    first_touch_turn = {"魔王再臨": None, "アブソリュートドミニオン": None}
    refresh_count = 0

    current_global_turn = 0
    cur_r_idx = 0

    total_turns = sum(TURNS_PER_ROUND)
    num_rounds = len(TURNS_PER_ROUND)

    turn_added = [0] * total_turns
    turn_discarded = [0] * total_turns
    turn_deck_reduced = [0] * total_turns

    turn_maou_touches = [0] * total_turns
    turn_dom_touches = [0] * total_turns

    round_added = [0] * num_rounds
    round_discarded = [0] * num_rounds
    round_deck_reduced = [0] * num_rounds
    round_maou_touches = [0] * num_rounds
    round_dom_touches = [0] * num_rounds

    def record_add():
        if current_global_turn >= 1:
            turn_added[min(current_global_turn, total_turns) - 1] += 1
        round_added[cur_r_idx] += 1

    def record_discard():
        if current_global_turn >= 1:
            turn_discarded[min(current_global_turn, total_turns) - 1] += 1
        round_discarded[cur_r_idx] += 1

    def record_deck_reduce():
        if current_global_turn >= 1:
            turn_deck_reduced[min(current_global_turn, total_turns) - 1] += 1
        round_deck_reduced[cur_r_idx] += 1

    def refresh_deck():
        nonlocal refresh_count
        if trash:
            deck.extend(trash)
            trash.clear()
            random.shuffle(deck)
            refresh_count += 1

    def pop_deck_one():
        if not deck:
            refresh_deck()
        if deck:
            record_deck_reduce()
            return deck.pop()
        return None

    def register_card(card):
        if card is None:
            return
        hand.append(card)
        record_add()
        name = card["name"]
        seen_cards.add(name)
        if name in touch_counts:
            touch_counts[name] += 1
            if first_touch_turn[name] is None:
                first_touch_turn[name] = max(1, current_global_turn)

    def draw_one():
        register_card(pop_deck_one())

    def look_cards(n):
        looked = []
        for _ in range(n):
            c = pop_deck_one()
            if c is not None:
                looked.append(c)
        return looked

    hand = []
    for _ in range(4):
        draw_one()

    for r_idx, num_turns in enumerate(TURNS_PER_ROUND):
        cur_r_idx = r_idx
        round_pp = 3 + r_idx
        if echo_field:
            trash.extend(echo_field)
            echo_field.clear()
        if r_idx > 0:
            current_global_turn += 1
            while hand:
                trash.append(hand.pop())
                record_discard()
            for _ in range(4):
                draw_one()
            current_global_turn -= 1
        for t_idx in range(num_turns):
            current_global_turn += 1
            draw_one()
            if echo_field:
                echo_num = len(echo_field)
                turn_played_zone.extend(echo_field)
                echo_field.clear()
                for _ in range(echo_num):
                    draw_one()
            pp = round_pp
            tsumo_count = 0
            def trigger_tsumo():
                nonlocal tsumo_count
                for _ in range(tsumo_count):
                    draw_one()
                tsumo_count = 0
            def play_attack(card, use_taiku_effect=False):
                nonlocal pp
                hand.remove(card)
                turn_played_zone.append(card)
                pp -= 1
                trigger_tsumo()
                name = card["name"]
                if name == "シンリャク開始":
                    if random.random() < shin_rate:
                        draw_one()
                elif name == "対空射撃" and use_taiku_effect:
                    if discard_zero_cost_card(hand, trash, pp, on_discard=record_discard):
                        draw_one()
                elif name == "1TAP":
                    draw_one()
                    discard_one_card(hand, trash, pp, on_discard=record_discard)
            while True:
                has_zero = any(c["cost"] == 0 for c in hand)
                if len(hand) > 0 and tsumo_count == 0:
                    def is_hold_only_card(c):
                        if c["name"] == "ノーネーム1コスアタック":
                            return True
                        if c["name"] == "対空射撃" and not has_zero:
                            return True
                        if c["name"] == "花火づくり" and pp <= 1:
                            return True
                        return False
                    if all(is_hold_only_card(c) for c in hand):
                        break
                maou = [c for c in hand if c["name"] == "魔王再臨"]
                if maou:
                    hand.remove(maou[0])
                    echo_field.append(maou[0])
                    draw_one()
                    continue
                dom = [c for c in hand if c["name"] == "アブソリュートドミニオン"]
                if dom and pp >= 1:
                    hand.remove(dom[0])
                    turn_played_zone.append(dom[0])
                    pp -= 1
                    trigger_tsumo()
                    looked = look_cards(5)
                    hits = [c for c in looked if c["cost"] == 0 and c["type"] == "memoria"][:3]
                    for h in hits:
                        register_card(h)
                    for h in hits:
                        if h in looked:
                            looked.remove(h)
                    trash.extend(looked)
                    continue
                has_attack_in_hand = any(c["type"] == "attack" for c in hand)
                tsumo = [c for c in hand if c["name"] == "アルティメットツモ"]
                if tsumo and has_attack_in_hand and pp >= 1:
                    hand.remove(tsumo[0])
                    turn_played_zone.append(tsumo[0])
                    tsumo_count += 1
                    continue
                shodo = [c for c in hand if c["name"] == "焦土の王者"]
                if shodo:
                    hand.remove(shodo[0])
                    turn_played_zone.append(shodo[0])
                    draw_one()
                    discard_one_card(hand, trash, pp, on_discard=record_discard)
                    continue
                hanabi = [c for c in hand if c["name"] == "花火づくり"]
                if hanabi and pp >= 2 and len(hand) >= 2:
                    hand.remove(hanabi[0])
                    turn_played_zone.append(hanabi[0])
                    pp -= 1
                    draw_one()
                    draw_one()
                    continue
                rock = [c for c in hand if c["name"] == "彼こそがロック"]
                if rock and pp >= 1:
                    hand.remove(rock[0])
                    turn_played_zone.append(rock[0])
                    pp -= 1
                    draw_one()
                    continue
                syn = [c for c in hand if c["name"] == "シンクロトリニティ"]
                if syn and pp >= 1:
                    play_attack(syn[0])
                    continue
                shin = [c for c in hand if c["name"] == "シンリャク開始"]
                if shin and pp >= 1:
                    play_attack(shin[0])
                    continue
                onetap = [c for c in hand if c["name"] == "1TAP"]
                if onetap and pp >= 1:
                    play_attack(onetap[0])
                    continue
                taiku = [c for c in hand if c["name"] == "対空射撃"]
                if taiku and pp >= 1 and has_zero:
                    play_attack(taiku[0], use_taiku_effect=True)
                    continue
                noname1 = [c for c in hand if c["name"] == "ノーネーム1コスアタック"]
                if noname1 and pp >= 1 and tsumo_count > 0:
                    play_attack(noname1[0])
                    continue
                break
            if turn_played_zone:
                trash.extend(turn_played_zone)
                turn_played_zone.clear()
            discard_to_limit(hand, trash, round_pp, on_discard=record_discard)
            idx = min(current_global_turn, total_turns) - 1
            turn_maou_touches[idx] = touch_counts["魔王再臨"]
            turn_dom_touches[idx] = touch_counts["アブソリュートドミニオン"]
        round_maou_touches[r_idx] = touch_counts["魔王再臨"]
        round_dom_touches[r_idx] = touch_counts["アブソリュートドミニオン"]

    round_net = [round_added[i] - round_discarded[i] for i in range(num_rounds)]
    turn_net = [a - d for a, d in zip(turn_added, turn_discarded)]
    return {
        "touch_maou": touch_counts["魔王再臨"],
        "touch_dom": touch_counts["アブソリュートドミニオン"],
        "seen_maou": 1 if touch_counts["魔王再臨"] > 0 else 0,
        "seen_dom": 1 if touch_counts["アブソリュートドミニオン"] > 0 else 0,
        "first_turn_maou": first_touch_turn["魔王再臨"],
        "first_turn_dom": first_touch_turn["アブソリュートドミニオン"],
        "refresh_count": refresh_count,
        "final_hand_size": len(hand),
        "turn_maou_touches": turn_maou_touches,
        "turn_dom_touches": turn_dom_touches,
        "turn_added": turn_added,
        "turn_discarded": turn_discarded,
        "turn_net": turn_net,
        "turn_deck_reduced": turn_deck_reduced,
        "round_added": round_added,
        "round_discarded": round_discarded,
        "round_net": round_net,
        "round_deck_reduced": round_deck_reduced,
        "round_maou_touches": round_maou_touches,
        "round_dom_touches": round_dom_touches,
    }

# ==========================================
# 6. 統計計算・テキスト整形ヘルパー
# ==========================================
def calc_stats(data_list):
    valid = [x for x in data_list if x is not None]
    if not valid:
        return None
    n = len(valid)
    return {
        "count": n,
        "mean": statistics.mean(valid),
        "median": statistics.median(valid),
        "mode": min(statistics.multimode(valid)),
        "min": min(valid),
        "max": max(valid),
        "var": statistics.pvariance(valid) if n > 1 else 0.0,
        "std": statistics.pstdev(valid) if n > 1 else 0.0,
    }

def format_stat_row(label, data_list, trials, show_hit_rate=False):
    st_val = calc_stats(data_list)
    if st_val is None:
        return f"{label:<28} | データなし（該当0回）"
    rate_str = f" (到達率:{st_val['count']/trials*100:5.1f}%)" if show_hit_rate else ""
    return (
        f"{label:<28} | "
        f"平均:{st_val['mean']:6.2f} | "
        f"中央:{st_val['median']:5.1f} | "
        f"最頻:{st_val['mode']:5.1f} | "
        f"最小:{st_val['min']:5.1f} | "
        f"最大:{st_val['max']:5.1f} | "
        f"分散:{st_val['var']:6.2f} | "
        f"標準偏差:{st_val['std']:5.2f}"
        f"{rate_str}"
    )

# ==========================================
# 7. 実行ボタン＆結果描画
# ==========================================
st.divider()
run_btn = st.button("🚀 シミュレーションを実行する", type="primary", use_container_width=True, disabled=not all_valid_50)
if not all_valid_50:
    st.warning("すべてのパターンのデッキ枚数をちょうど50枚にすると実行ボタンが有効になります。")

if run_btn and all_valid_50:
    any_output = any([
        show_summary, show_detail_stats, show_round_table, show_turn_table,
        show_keycard_graph, show_indiv_graph, show_draw_graph,
        show_round_net_graph, show_round_deck_graph,
        show_round_dist, show_turn_dist, show_cum_dist
    ])
    if not any_output:
        st.warning("⚠️ 左側のメニューで表示するグラフ・表を1つ以上チェックしてください。")
        st.stop()

    comparison_data = {}
    total_turns = sum(TURNS_PER_ROUND)
    num_rounds = len(TURNS_PER_ROUND)
    max_turns_in_round = max(TURNS_PER_ROUND)
    cum_turns = [0] + list(np.cumsum(TURNS_PER_ROUND))

    with st.spinner("シミュレーションを計算中です...（数秒かかります）"):
        for p in patterns_input:
            trials = p["trials"]
            results = [simulate_match(p["counts"], shinryaku_rate) for _ in range(trials)]
            
            round_combined_hits = np.zeros((trials, num_rounds, max_turns_in_round), dtype=int)
            round_combined_counts = np.zeros((trials, num_rounds, max_turns_in_round), dtype=int)
            round_maou_hits = np.zeros((trials, num_rounds, max_turns_in_round), dtype=int)
            round_dom_hits = np.zeros((trials, num_rounds, max_turns_in_round), dtype=int)
            
            round_maou_pure = np.zeros((trials, num_rounds), dtype=int)
            round_dom_pure = np.zeros((trials, num_rounds), dtype=int)
            turn_maou_pure = np.zeros((trials, total_turns), dtype=int)
            turn_dom_pure = np.zeros((trials, total_turns), dtype=int)
            
            round_maou_cum_reset = np.zeros((trials, num_rounds, max_turns_in_round), dtype=int)
            round_dom_cum_reset = np.zeros((trials, num_rounds, max_turns_in_round), dtype=int)
            round_net_reset = np.zeros((trials, num_rounds, max_turns_in_round), dtype=float)
            round_deck_reduced_cum_reset = np.zeros((trials, num_rounds, max_turns_in_round), dtype=float)
            
            for i, r in enumerate(results):
                for r_idx, num_turns in enumerate(TURNS_PER_ROUND):
                    maou_offset = r["turn_maou_touches"][cum_turns[r_idx] - 1] if r_idx > 0 else 0
                    dom_offset = r["turn_dom_touches"][cum_turns[r_idx] - 1] if r_idx > 0 else 0
                    r_deck_cum = 0
                    
                    for t_idx in range(num_turns):
                        global_t = cum_turns[r_idx] + t_idx
                        r_maou = r["turn_maou_touches"][global_t] - maou_offset
                        r_dom = r["turn_dom_touches"][global_t] - dom_offset
                        
                        if (r_maou + r_dom) > 0:
                            round_combined_hits[i, r_idx, t_idx] = 1
                        if r_maou > 0:
                            round_maou_hits[i, r_idx, t_idx] = 1
                        if r_dom > 0:
                            round_dom_hits[i, r_idx, t_idx] = 1
                            
                        round_combined_counts[i, r_idx, t_idx] = r_maou + r_dom
                        round_maou_cum_reset[i, r_idx, t_idx] = r_maou
                        round_dom_cum_reset[i, r_idx, t_idx] = r_dom
                        round_net_reset[i, r_idx, t_idx] = r["turn_net"][global_t]
                        
                        r_deck_cum += r["turn_deck_reduced"][global_t]
                        round_deck_reduced_cum_reset[i, r_idx, t_idx] = r_deck_cum
                
                round_maou_pure[i, 0] = r["round_maou_touches"][0]
                round_dom_pure[i, 0] = r["round_dom_touches"][0]
                for r_idx in range(1, num_rounds):
                    round_maou_pure[i, r_idx] = r["round_maou_touches"][r_idx] - r["round_maou_touches"][r_idx - 1]
                    round_dom_pure[i, r_idx] = r["round_dom_touches"][r_idx] - r["round_dom_touches"][r_idx - 1]
                
                turn_maou_pure[i, 0] = r["turn_maou_touches"][0]
                turn_dom_pure[i, 0] = r["turn_dom_touches"][0]
                for t_idx in range(1, total_turns):
                    turn_maou_pure[i, t_idx] = r["turn_maou_touches"][t_idx] - r["turn_maou_touches"][t_idx - 1]
                    turn_dom_pure[i, t_idx] = r["turn_dom_touches"][t_idx] - r["turn_dom_touches"][t_idx - 1]
            
            maou_first = [r["first_turn_maou"] for r in results if r["first_turn_maou"] is not None]
            dom_first = [r["first_turn_dom"] for r in results if r["first_turn_dom" ] is not None]
            
            comparison_data[p["name"]] = {
                "probs": np.mean(round_combined_hits, axis=0) * 100,
                "counts": np.mean(round_combined_counts, axis=0),
                "maou_probs": np.mean(round_maou_hits, axis=0) * 100,
                "maou_counts": np.mean(round_maou_cum_reset, axis=0),
                "dom_probs": np.mean(round_dom_hits, axis=0) * 100,
                "dom_counts": np.mean(round_dom_cum_reset, axis=0),
                "mean_round_net_reset": np.mean(round_net_reset, axis=0),
                "mean_round_deck_reduced_cum_reset": np.mean(round_deck_reduced_cum_reset, axis=0),
                "maou_hit_rate": len(maou_first) / trials * 100,
                "maou_avg_turn": statistics.mean(maou_first) if maou_first else 0,
                "dom_hit_rate": len(dom_first) / trials * 100,
                "dom_avg_turn": statistics.mean(dom_first) if dom_first else 0,
                "avg_refresh": statistics.mean(r["refresh_count"] for r in results),
                "avg_deck_reduced": statistics.mean(sum(r["round_deck_reduced"]) for r in results),
                "mean_turn_added": np.mean([r["turn_added"] for r in results], axis=0),
                "mean_turn_discarded": np.mean([r["turn_discarded"] for r in results], axis=0),
                "cum_turn_deck_reduced": np.cumsum(np.mean([r["turn_deck_reduced"] for r in results], axis=0)),
                "round_avg_added": np.mean([r["round_added"] for r in results], axis=0),
                "round_avg_discarded": np.mean([r["round_discarded" ] for r in results], axis=0),
                "round_avg_net": np.mean([r["round_net"] for r in results], axis=0),
                "results_raw": results,
                "round_maou_pure": round_maou_pure,
                "round_dom_pure": round_dom_pure,
                "turn_maou_pure": turn_maou_pure,
                "turn_dom_pure": turn_dom_pure,
                "round_maou_cum_reset": round_maou_cum_reset,
                "round_dom_cum_reset": round_dom_cum_reset,
            }
            
    st.success("🎉 シミュレーションが完了しました！")

    # --- 簡易サマリー出力 ---
    if show_summary:
        st.subheader("📊 シミュレーション比較簡易サマリー（全15ターン通算 & ラウンド別収支）")
        summary_lines = []
        for p_name, d in comparison_data.items():
            summary_lines.append(f"【{p_name}】")
            summary_lines.append(f"  ・魔王再臨 接触率      : {d['maou_hit_rate']:.1f}% (初回平均 {d['maou_avg_turn']:.2f}T)")
            summary_lines.append(f"  ・ドミニオン 接触率    : {d['dom_hit_rate']:.1f}% (初回平均 {d['dom_avg_turn']:.2f}T)")
            summary_lines.append(f"  ・平均山札掘削枚数     : {d['avg_deck_reduced']:.1f}枚 / 平均リフレッシュ: {d['avg_refresh']:.2f}回")
            for r_i in range(num_rounds):
                summary_lines.append(
                    f"    └ {r_i+1}R平均: 手札増加 +{d['round_avg_added'][r_i]:.1f}枚 / "
                    f"破棄 -{d['round_avg_discarded'][r_i]:.1f}枚 / "
                    f"純増 {d['round_avg_net'][r_i]:+.1f}枚"
                )
            summary_lines.append("=" * 75)
        st.code("\n".join(summary_lines), language="text")

    # --- 詳細統計出力 ---
    if show_detail_stats:
        st.subheader("📋 詳細統計集計")
        detail_lines = []
        for p_name, d in comparison_data.items():
            raw_res = d["results_raw"]
            trials = len(raw_res)
            detail_lines.append(f"### パターン: {p_name} ###")
            detail_lines.append(format_stat_row("魔王再臨 累計接触枚数", [r["touch_maou"] for r in raw_res], trials))
            detail_lines.append(format_stat_row("ドミニオン 累計接触枚数", [r["touch_dom"] for r in raw_res], trials))
            detail_lines.append(format_stat_row("魔王再臨 1枚以上接触率", [r["seen_maou"] for r in raw_res], trials))
            detail_lines.append(format_stat_row("ドミニオン 1枚以上接触率", [r["seen_dom"] for r in raw_res], trials))
            detail_lines.append(format_stat_row("魔王再臨 初接触ターン", [r["first_turn_maou"] for r in raw_res], trials, show_hit_rate=True))
            detail_lines.append(format_stat_row("ドミニオン 初接触ターン", [r["first_turn_dom"] for r in raw_res], trials, show_hit_rate=True))
            detail_lines.append(format_stat_row("デッキリフレッシュ回数", [r["refresh_count"] for r in raw_res], trials))
            detail_lines.append(format_stat_row("試合終了時 手札枚数", [r["final_hand_size"] for r in raw_res], trials))
            detail_lines.append("-" * 65)
        st.code("\n".join(detail_lines), language="text")

    # --- ラウンド別詳細テーブル ---
    if show_round_table:
        st.subheader("⏱️ ラウンドごとの詳細推移 統計テーブル")
        r_lines = []
        for p_name, d in comparison_data.items():
            raw_res = d["results_raw"]
            trials = len(raw_res)
            r_lines.append(f"### パターン: {p_name} ###")
            for r_idx in range(num_rounds):
                r_num = r_idx + 1
                r_lines.append(f"\n--- {r_num}R ---")
                r_lines.append(format_stat_row(f"  {r_num}R 手札に加わった枚数", [r["round_added"][r_idx] for r in raw_res], trials))
                r_lines.append(format_stat_row(f"  {r_num}R 手札から捨てた枚数", [r["round_discarded"][r_idx] for r in raw_res], trials))
                r_lines.append(format_stat_row(f"  {r_num}R 純増減 (加 - 捨)", [r["round_net"][r_idx] for r in raw_res], trials))
                r_lines.append(format_stat_row(f"  {r_num}R 減ったデッキ枚数", [r["round_deck_reduced"][r_idx] for r in raw_res], trials))
                r_lines.append(format_stat_row(f"  {r_num}R 魔王再臨 累計接触数", [r["round_maou_touches"][r_idx] for r in raw_res], trials))
                r_lines.append(format_stat_row(f"  {r_num}R ドミニオン 累計接触数", [r["round_dom_touches"][r_idx] for r in raw_res], trials))
            r_lines.append("-" * 65)
        st.code("\n".join(r_lines), language="text")

    # --- ターン別詳細テーブル ---
    if show_turn_table:
        st.subheader("⏲️ 各ラウンド内 ターンごとの詳細推移 統計テーブル")
        t_lines = []
        for p_name, d in comparison_data.items():
            raw_res = d["results_raw"]
            trials = len(raw_res)
            t_lines.append(f"### パターン: {p_name} ###")
            for r_idx, num_turns in enumerate(TURNS_PER_ROUND):
                r_num = r_idx + 1
                t_lines.append(f"\n--- {r_num}ラウンド内 ターン詳細 ---")
                for t_idx in range(num_turns):
                    global_t = cum_turns[r_idx] + t_idx
                    t_lines.append(f"  <{r_num}R - {t_idx+1}ターン目 (通算 {global_t+1}T)>")
                    t_lines.append(format_stat_row("    手札に加わった枚数", [r["turn_added"][global_t] for r in raw_res], trials))
                    t_lines.append(format_stat_row("    手札から捨てた枚数", [r["turn_discarded"][global_t] for r in raw_res], trials))
                    t_lines.append(format_stat_row("    純増減 (加 - 捨)", [r["turn_net"][global_t] for r in raw_res], trials))
                    t_lines.append(format_stat_row("    減ったデッキ枚数", [r["turn_deck_reduced"][global_t] for r in raw_res], trials))
                    t_lines.append(format_stat_row("    魔王再臨 累計接触数", [r["turn_maou_touches"][global_t] for r in raw_res], trials))
                    t_lines.append(format_stat_row("    ドミニオン 累計接触数", [r["turn_dom_touches"][global_t] for r in raw_res], trials))
            t_lines.append("-" * 65)
        st.code("\n".join(t_lines), language="text")

    # --- グラフ描画設定 ---
    sns.set_theme(style="whitegrid")
    plt.rcParams["font.family"] = "IPAexGothic"
    colors = sns.color_palette("husl", len(patterns_input))

    def plot_keycard_grid(prob_key, count_key, card_label):
        fig, axes = plt.subplots(2, num_rounds, figsize=(18, 10), sharey="row")
        for r_idx, num_turns in enumerate(TURNS_PER_ROUND):
            x_labels = [f"{t+1}T" for t in range(num_turns)]
            
            ax_prob = axes[0, r_idx]
            for p_idx, (p_name, p_data) in enumerate(comparison_data.items()):
                ax_prob.plot(
                    x_labels, p_data[prob_key][r_idx, :num_turns],
                    marker="o", linewidth=2.5, color=colors[p_idx], label=p_name
                )
            ax_prob.set_title(f"{r_idx+1}R {card_label} 累積接触確率 (%)", fontsize=12, fontweight="bold")
            ax_prob.set_ylim(-5, 105)
            if r_idx == 0:
                ax_prob.set_ylabel("累積接触確率 (%)", fontsize=11, fontweight="bold")
            ax_prob.legend(fontsize=8, loc="lower right")
            
            ax_count = axes[1, r_idx]
            width = min(0.5, 0.8 / len(patterns_input))
            x_indices = np.arange(num_turns)
            for p_idx, (p_name, p_data) in enumerate(comparison_data.items()):
                bars = ax_count.bar(
                    x_indices + (p_idx - len(patterns_input) / 2 + 0.5) * width,
                    p_data[count_key][r_idx, :num_turns],
                    width=width, color=colors[p_idx], label=p_name
                )
                for bar in bars:
                    h = bar.get_height()
                    if h > 0:
                        ax_count.text(
                            bar.get_x() + bar.get_width() / 2, h + 0.02,
                            f"{h:.2f}", ha="center", va="bottom", fontsize=7
                        )
            ax_count.set_title(f"{r_idx+1}R {card_label} 平均累積接触枚数", fontsize=12, fontweight="bold")
            ax_count.set_xticks(x_indices)
            ax_count.set_xticklabels(x_labels)
            if r_idx == 0:
                ax_count.set_ylabel("平均接触枚数 (枚)", fontsize=11, fontweight="bold")
            ax_count.legend(fontsize=8, loc="upper left")
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

    if show_keycard_graph:
        st.subheader("📈 キーカード合計 接触グラフ")
        plot_keycard_grid("probs", "counts", "キーカード合計")

    if show_indiv_graph:
        st.subheader("📈 キーカード別 個別接触グラフ")
        plot_keycard_grid("maou_probs", "maou_counts", "【魔王再臨】")
        plot_keycard_grid("dom_probs", "dom_counts", "【アブソリュートドミニオン】")

    if show_draw_graph:
        st.subheader("📈 山札ドロー挙動グラフ")
        fig2, axes2 = plt.subplots(1, 3, figsize=(18, 5))
        turn_labels = [f"{t+1}T" for t in range(total_turns)]
        
        ax_deck = axes2[0]
        for p_idx, (p_name, p_data) in enumerate(comparison_data.items()):
            ax_deck.plot(turn_labels, p_data["cum_turn_deck_reduced"], marker="o", linewidth=2.2, color=colors[p_idx], label=p_name)
        ax_deck.axhline(50, color="gray", linestyle="--", linewidth=1, label="山札1周 (50枚)")
        ax_deck.set_title("通算ターン別 累積山札掘削枚数", fontsize=12, fontweight="bold")
        ax_deck.set_ylabel("累積掘削枚数 (枚)", fontsize=11, fontweight="bold")
        ax_deck.tick_params(axis="x", rotation=45)
        ax_deck.legend(fontsize=8, loc="upper left")
        
        ax_add = axes2[1]
        for p_idx, (p_name, p_data) in enumerate(comparison_data.items()):
            ax_add.plot(turn_labels, p_data["mean_turn_added"], marker="s", linewidth=2, color=colors[p_idx], label=p_name)
        ax_add.set_title("ターン別 平均手札増加枚数", fontsize=12, fontweight="bold")
        ax_add.set_ylabel("増加枚数 (枚/ターン)", fontsize=11, fontweight="bold")
        ax_add.tick_params(axis="x", rotation=45)
        ax_add.legend(fontsize=8, loc="upper right")
        
        ax_disc = axes2[2]
        for p_idx, (p_name, p_data) in enumerate(comparison_data.items()):
            ax_disc.plot(turn_labels, p_data["mean_turn_discarded"], marker="^", linewidth=2, color=colors[p_idx], label=p_name)
        ax_disc.set_title("ターン別 平均ディスカード枚数", fontsize=12, fontweight="bold")
        ax_disc.set_ylabel("破棄枚数 (枚/ターン)", fontsize=11, fontweight="bold")
        ax_disc.tick_params(axis="x", rotation=45)
        ax_disc.legend(fontsize=8, loc="upper right")
        
        plt.tight_layout()
        st.pyplot(fig2)
        plt.close(fig2)

    if show_round_net_graph:
        st.subheader("📈 ラウンド毎リセット 手札純増減グラフ")
        fig_net, axes_net = plt.subplots(1, num_rounds, figsize=(18, 5), sharey=True)
        for r_idx, num_turns in enumerate(TURNS_PER_ROUND):
            x_labels = [f"{t+1}T" for t in range(num_turns)]
            ax = axes_net[r_idx]
            for p_idx, (p_name, p_data) in enumerate(comparison_data.items()):
                vals = p_data["mean_round_net_reset"][r_idx, :num_turns]
                ax.plot(x_labels, vals, marker="o", linewidth=2.3, color=colors[p_idx], label=p_name)
                for t_i, v in enumerate(vals):
                    ax.text(t_i, v + 0.08, f"{v:+.2f}", ha="center", va="bottom", fontsize=7.5)
            ax.axhline(0, color="gray", linestyle="--", linewidth=1)
            ax.set_title(f"{r_idx+1}R ターン別 手札純増減 (加 - 捨)", fontsize=12, fontweight="bold")
            if r_idx == 0:
                ax.set_ylabel("平均手札純増減 (枚/ターン)", fontsize=11, fontweight="bold")
                ax.legend(fontsize=8, loc="upper right")
        plt.tight_layout()
        st.pyplot(fig_net)
        plt.close(fig_net)

    if show_round_deck_graph:
        st.subheader("📈 ラウンド毎リセット 山札掘削グラフ")
        fig_rdeck, axes_rdeck = plt.subplots(1, num_rounds, figsize=(18, 5), sharey=True)
        for r_idx, num_turns in enumerate(TURNS_PER_ROUND):
            x_labels = [f"{t+1}T" for t in range(num_turns)]
            ax = axes_rdeck[r_idx]
            for p_idx, (p_name, p_data) in enumerate(comparison_data.items()):
                vals = p_data["mean_round_deck_reduced_cum_reset"][r_idx, :num_turns]
                ax.plot(x_labels, vals, marker="s", linewidth=2.3, color=colors[p_idx], label=p_name)
                for t_i, v in enumerate(vals):
                    ax.text(t_i, v + 0.4, f"{v:.1f}", ha="center", va="bottom", fontsize=7.5)
            ax.set_title(f"{r_idx+1}R ターン別 累積山札掘削枚数 [R内リセット]", fontsize=12, fontweight="bold")
            if r_idx == 0:
                ax.set_ylabel("R内累積掘削枚数 (枚)", fontsize=11, fontweight="bold")
                ax.legend(fontsize=8, loc="upper left")
        plt.tight_layout()
        st.pyplot(fig_rdeck)
        plt.close(fig_rdeck)

    max_pure_val = 5
    x_vals_pure = np.arange(max_pure_val)

    if show_round_dist:
        st.subheader("📊 ラウンド毎 新規接触分布")
        for p_name, d in comparison_data.items():
            fig_r, axes_r = plt.subplots(num_rounds, 1, figsize=(10, 11), sharex=True)
            trials = len(d["results_raw"])
            for r_idx in range(num_rounds):
                maou_dist = np.bincount(d["round_maou_pure"][:, r_idx], minlength=max_pure_val)[:max_pure_val] / trials * 100
                dom_dist = np.bincount(d["round_dom_pure"][:, r_idx], minlength=max_pure_val)[:max_pure_val] / trials * 100
                axes_r[r_idx].bar(x_vals_pure - 0.2, maou_dist, width=0.4, label="魔王再臨 (新規)", color="crimson", alpha=0.85)
                axes_r[r_idx].bar(x_vals_pure + 0.2, dom_dist, width=0.4, label="ドミニオン (新規)", color="royalblue", alpha=0.85)
                axes_r[r_idx].set_title(f"【{p_name}】{r_idx+1}R単体における新規接触数の分布確率", fontsize=11, fontweight="bold")
                axes_r[r_idx].set_ylabel("確率 (%)", fontsize=9)
                axes_r[r_idx].set_xticks(x_vals_pure)
                axes_r[r_idx].legend(fontsize=8)
            axes_r[num_rounds - 1].set_xlabel("新規接触数", fontsize=10)
            plt.tight_layout()
            st.pyplot(fig_r)
            plt.close(fig_r)

    if show_turn_dist:
        st.subheader("📊 ターン毎 新規接触分布")
        n_cols = 3
        n_rows = int(np.ceil(total_turns / n_cols))
        for p_name, d in comparison_data.items():
            fig_t, axes_t = plt.subplots(n_rows, n_cols, figsize=(18, 3.8 * n_rows), sharex=True, sharey=True)
            axes_t = axes_t.flatten()
            trials = len(d["results_raw"])
            for t_idx in range(total_turns):
                maou_pure_dist_t = np.bincount(d["turn_maou_pure"][:, t_idx], minlength=max_pure_val)[:max_pure_val] / trials * 100
                dom_pure_dist_t = np.bincount(d["turn_dom_pure"].astype(int)[:, t_idx], minlength=max_pure_val)[:max_pure_val] / trials * 100
                
                r_num = 1
                for r_i, limit in enumerate(cum_turns[1:], start=1):
                    if t_idx < limit:
                        r_num = r_i
                        break
                t_num = t_idx - cum_turns[r_num - 1] + 1
                
                axes_t[t_idx].bar(x_vals_pure - 0.2, maou_pure_dist_t, width=0.4, label="魔王再臨 (新規)", color="crimson", alpha=0.85)
                axes_t[t_idx].bar(x_vals_pure + 0.2, dom_pure_dist_t, width=0.4, label="ドミニオン (新規)", color="royalblue", alpha=0.85)
                axes_t[t_idx].set_title(f"{r_num}R-{t_num}T (累計 {t_idx+1}T) 内 新規接触確率分布", fontsize=10, fontweight="bold")
                axes_t[t_idx].set_xticks(x_vals_pure)
                if t_idx % n_cols == 0:
                    axes_t[t_idx].set_ylabel("確率 (%)", fontsize=9)
                if t_idx >= total_turns - n_cols:
                    axes_t[t_idx].set_xlabel("新規接触数", fontsize=10)
                axes_t[t_idx].legend(fontsize=8)
            for idx in range(total_turns, len(axes_t)):
                fig_t.delaxes(axes_t[idx])
            fig_t.suptitle(f"【{p_name}】ターン別 新規接触確率分布", fontsize=14, fontweight="bold", y=1.01)
            plt.tight_layout()
            st.pyplot(fig_t)
            plt.close(fig_t)

    if show_cum_dist:
        st.subheader("📊 ラウンド内累積接触分布")
        max_cum_val = 5
        x_vals_cum = np.arange(max_cum_val)
        for p_name, d in comparison_data.items():
            fig_c, axes_c = plt.subplots(num_rounds, max_turns_in_round, figsize=(20, 11), sharex=True, sharey=True)
            trials = len(d["results_raw"])
            for r_idx in range(num_rounds):
                for t_idx in range(max_turns_in_round):
                    maou_dist = np.bincount(d["round_maou_cum_reset"][:, r_idx, t_idx].astype(int), minlength=max_cum_val)[:max_cum_val] / trials * 100
                    dom_dist = np.bincount(d["round_dom_cum_reset"][:, r_idx, t_idx].astype(int), minlength=max_cum_val)[:max_cum_val] / trials * 100
                    
                    ax = axes_c[r_idx, t_idx]
                    ax.bar(x_vals_cum - 0.2, maou_dist, width=0.4, label="魔王再臨", color="crimson", alpha=0.85)
                    ax.bar(x_vals_cum + 0.2, dom_dist, width=0.4, label="ドミニオン", color="royalblue", alpha=0.85)
                    global_t = r_idx * max_turns_in_round + t_idx + 1
                    ax.set_title(f"{r_idx+1}R-{t_idx+1}T (計{global_t}T)\n[R内累計]", fontsize=9, fontweight="bold")
                    ax.set_xticks(x_vals_cum)
                    if t_idx == 0:
                        ax.set_ylabel(f"{r_idx+1}R 確率 (%)", fontsize=10, fontweight="bold")
                    if r_idx == num_rounds - 1:
                        ax.set_xlabel("R内累計接触数 (枚)", fontsize=9)
                    if r_idx == 0 and t_idx == 0:
                        ax.legend(fontsize=8)
            fig_c.suptitle(f"【{p_name}】ラウンド別 累積接触数分布推移", fontsize=14, fontweight="bold", y=1.01)
            plt.tight_layout()
            st.pyplot(fig_c)
            plt.close(fig_c)
