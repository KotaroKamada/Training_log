import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="バスケットボール トレーニングシステム", layout="wide")

# サイドバーでページ選択
st.sidebar.title("メニュー")
page = st.sidebar.selectbox("ページを選択", ["プログラム一覧", "Training Log 入力", "過去ログ検索", "データ管理"])

# エクセルファイルのパス
LOG_FILE = "training_log.xlsx"
PROGRAM_FILE = "training_program.xlsx"

# プログラムファイルの読み込み
def load_program_file():
    try:
        if os.path.exists(PROGRAM_FILE):
            # エクセルファイルを読み込み（ヘッダーは1行目）
            df = pd.read_excel(PROGRAM_FILE)
            
            # 列名を統一（スペースなど除去）
            df.columns = df.columns.str.strip()
            
            # 必要な列名にリネーム
            expected_columns = ['Program', 'No', 'Exercise', 'set', 'load', 'rep', 'Point']
            if len(df.columns) >= 6:
                df.columns = expected_columns[:len(df.columns)]
            
            return df
        else:
            # サンプルファイルを作成
            sample_df = pd.DataFrame({
                'Program': ['①', '①', '①', '②', '②', '③'],
                'No': ['WU', 1, 2, 'WU', 1, 1],
                'Exercise': ['Dynamic Stretch', 'Back Squat', 'Bench Press', 'Light Jog', 'Sprint 20m', 'Vertical Jump'],
                'set': [1, 4, 3, 1, 5, 3],
                'load': ['-', 0.8, 0.75, '-', '-', '-'],
                'rep': [10, 8, 10, 5, 1, 10],
                'Point': ['全身をほぐす', '膝をつま先の方向に', 'バーパスに注意', '軽く温める', '全力疾走', '着地を意識']
            })
            sample_df.to_excel(PROGRAM_FILE, index=False)
            return sample_df
    except Exception as e:
        st.error(f"プログラムファイルの読み込みエラー: {e}")
        return pd.DataFrame()

# ログファイルの読み込み
def load_training_log():
    if os.path.exists(LOG_FILE):
        return pd.read_excel(LOG_FILE)
    else:
        return pd.DataFrame(columns=["名前", "体重", "日付", "プログラム", "エクササイズ", "予定セット", "予定負荷", "予定レップ", "実施セット", "実施負荷", "実施レップ", "コメント", "ポイント"])

# ログの保存
def save_training_log(new_data, existing_data):
    updated_data = pd.concat([existing_data, new_data], ignore_index=True)
    updated_data.to_excel(LOG_FILE, index=False)

# 新しいログ保存関数（指定形式）
def save_training_log_formatted(player_name, program_name, exercise_name, sets_data, date=None):
    if date is None:
        date = datetime.today().date()
    
    # 既存のファイルを読み込み、なければ新規作成
    if os.path.exists(LOG_FILE):
        try:
            existing_df = pd.read_excel(LOG_FILE)
        except:
            existing_df = pd.DataFrame()
    else:
        existing_df = pd.DataFrame()
    
    # 新しいデータを作成
    new_rows = []
    for set_data in sets_data:
        load_value = set_data['load']
        reps = set_data['reps']
        
        # 負荷値から数値を抽出（重量の場合）
        load_numeric = 0
        if isinstance(load_value, str):
            if 'kg' in load_value:
                try:
                    load_numeric = float(load_value.replace('kg', ''))
                except:
                    load_numeric = 0
            elif load_value == "体重":
                load_numeric = 0  # 体重の場合は0として扱う
            else:
                try:
                    load_numeric = float(load_value)
                except:
                    load_numeric = 0
        else:
            try:
                load_numeric = float(load_value)
            except:
                load_numeric = 0
        
        # 総負荷量を計算
        total_load = load_numeric * reps
        
        new_row = {
            '日付': date,
            'プログラム名': program_name,
            '名前': player_name,
            'エクササイズ名': exercise_name,
            'set': set_data['set_number'],
            '負荷': load_value,
            '回数': reps,
            '総負荷量': total_load
        }
        new_rows.append(new_row)
    
    # 新しいデータをDataFrameに変換
    new_df = pd.DataFrame(new_rows)
    
    # 既存データと結合
    if len(existing_df) > 0:
        # 列名を統一
        expected_columns = ['日付', 'プログラム名', '名前', 'エクササイズ名', 'set', '負荷', '回数', '総負荷量']
        if list(existing_df.columns) != expected_columns:
            existing_df = pd.DataFrame(columns=expected_columns)
        
        updated_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        updated_df = new_df
    
    # Excelファイルに保存
    updated_df.to_excel(LOG_FILE, index=False)
    
    return len(new_rows)

# ページ別処理
if page == "Training Log 入力":
    st.title("Training Log 入力")
    
    # プログラムファイルを読み込み
    program_df = load_program_file()
    
    if len(program_df) == 0:
        st.error("プログラムデータを読み込めませんでした。")
        st.stop()
    
    # 選手名入力をスタイリッシュに
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%);
        padding: 15px 20px;
        border-radius: 12px;
        margin: 15px 0;
        text-align: center;
        box-shadow: 0 6px 20px rgba(44, 62, 80, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.1);
    ">
        <h2 style="
            color: #ECF0F1; 
            margin: 0; 
            font-size: 24px;
            font-weight: 600;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            letter-spacing: 0.8px;
        ">
            TRAINING LOG INPUT
        </h2>
        <p style="
            color: #BDC3C7; 
            margin: 8px 0 0 0; 
            font-size: 14px;
            font-weight: 300;
        ">
            トレーニング記録を入力
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    player_name = st.text_input("選手名", key="player_name", placeholder="例: 田中太郎")
    
    # 体重入力
    body_weight = st.number_input("体重 (kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.1, key="body_weight")
    
    # 利用可能なプログラム一覧を表示
    available_programs = program_df['Program'].unique()
    
    st.markdown("### プログラム選択")
    selected_program = st.selectbox(
        "実行するプログラム", 
        available_programs,
        help="エクセルで設定されたトレーニングプログラムから選択"
    )
    
    if selected_program:
        # 選択されたプログラムのエクササイズを表示（エクセルの順序を保持）
        program_exercises = program_df[program_df['Program'] == selected_program].reset_index(drop=True)
        
        # ウォーミングアップ種目を除外（番号のみがログ対象）
        main_exercises = program_exercises[
            ~program_exercises['No'].isin(['WU', 'ST', 'PL'])
        ] if 'No' in program_exercises.columns else program_exercises
        
        # 同じエクササイズをグループ化（順序を保持）
        grouped_exercises = []
        seen_exercises = set()
        
        for _, exercise in main_exercises.iterrows():
            exercise_name = exercise['Exercise']
            if exercise_name not in seen_exercises:
                # 同じエクササイズのすべての行を取得
                same_exercises = main_exercises[main_exercises['Exercise'] == exercise_name]
                
                # データを統合
                grouped_exercise = {
                    'Exercise': exercise_name,
                    'No': same_exercises['No'].iloc[0] if 'No' in same_exercises.columns else '',
                    'set': '・'.join(map(str, same_exercises['set'])),
                    'load': '・'.join(map(str, same_exercises['load'])),
                    'rep': '・'.join(map(str, same_exercises['rep']))
                }
                
                # Point列が存在する場合は追加
                if 'Point' in same_exercises.columns:
                    grouped_exercise['Point'] = same_exercises['Point'].iloc[0]
                
                grouped_exercises.append(grouped_exercise)
                seen_exercises.add(exercise_name)
        
        st.markdown(f"### プログラム {selected_program}")
        
        # ウォーミングアップの表示（WU、ST、PLを含む）
        warmup_exercises = program_exercises[
            program_exercises['No'].isin(['WU', 'ST', 'PL'])
        ] if 'No' in program_exercises.columns else pd.DataFrame()
        
        if len(warmup_exercises) > 0:
            st.markdown("#### ウォーミングアップ・補助種目")
            for _, warmup in warmup_exercises.iterrows():
                # 種目タイプの表示
                exercise_type = ""
                if warmup['No'] == 'WU':
                    exercise_type = "WU "
                elif warmup['No'] == 'ST':
                    exercise_type = "ST "  # Stability
                elif warmup['No'] == 'PL':
                    exercise_type = "PL "  # Plyometrics
                
                # ウォーミングアップの詳細情報
                warmup_details = []
                if pd.notna(warmup['set']) and warmup['set'] != '-':
                    warmup_details.append(f"{warmup['set']}セット")
                if pd.notna(warmup['rep']) and warmup['rep'] != '-':
                    warmup_details.append(f"{warmup['rep']}レップ")
                if pd.notna(warmup['load']) and warmup['load'] != '-':
                    # 負荷の%表記変換
                    load_display = warmup['load']
                    if str(load_display).replace('.', '').isdigit() and float(load_display) <= 1.0:
                        load_display = f"{float(load_display)*100:.0f}%"
                    warmup_details.append(f"{load_display}")
                
                detail_text = " / ".join(warmup_details) if warmup_details else ""
                
                if detail_text:
                    st.markdown(f"• {exercise_type}**{warmup['Exercise']}** - {detail_text}")
                else:
                    st.markdown(f"• {exercise_type}**{warmup['Exercise']}**")
                
                # ポイントがあれば表示
                if 'Point' in warmup and pd.notna(warmup['Point']) and warmup['Point'] != '':
                    st.markdown(f"  POINT: {warmup['Point']}")
            
            st.markdown("---")
        
        st.markdown("""
        <div style="
            margin: 20px 0 15px 0;
            padding: 12px 0;
            border-bottom: 2px solid #34495E;
        ">
            <h4 style="
                color: #2C3E50;
                margin: 0;
                font-size: 18px;
                font-weight: 600;
                letter-spacing: 1px;
            ">EXERCISES</h4>
        </div>
        """, unsafe_allow_html=True)
        
        # 種目選択のセッション状態を初期化
        if 'selected_exercise_idx' not in st.session_state:
            st.session_state.selected_exercise_idx = None
        
        # 種目一覧を表示（選択式）
        st.markdown("""
        <div style="
            background: rgba(44, 62, 80, 0.03);
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            border: 1px solid rgba(44, 62, 80, 0.1);
        ">
            <p style="
                color: #34495E;
                margin: 0;
                font-size: 14px;
                font-weight: 500;
                text-align: center;
            ">実施する種目を選択してください</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 種目一覧をコンパクトなボタンで表示（1列レイアウト）
        for idx, exercise in enumerate(grouped_exercises):
            # %表記の処理
            load_display = exercise['load']
            if '・' in str(load_display):
                loads = str(load_display).split('・')
                formatted_loads = []
                for load in loads:
                    if load.replace('.', '').isdigit() and float(load) <= 1.0:
                        formatted_loads.append(f"{float(load)*100:.0f}%")
                    else:
                        formatted_loads.append(load)
                load_display = '・'.join(formatted_loads)
            else:
                if str(load_display).replace('.', '').isdigit() and float(load_display) <= 1.0:
                    load_display = f"{float(load_display)*100:.0f}%"
            
            # 選択状態によるボタンスタイル
            is_selected = st.session_state.selected_exercise_idx == idx
            button_type = "primary" if is_selected else "secondary"
            
            # スタイリッシュなボタンテキストを構築
            exercise_name = f"{exercise.get('No', '')} {exercise['Exercise']}"
            exercise_details = f"{exercise['set']}set | {load_display} | {exercise['rep']}rep"
            
            # カスタムスタイルのボタン（改良版）
            button_style = """
            <style>
            div[data-testid="column"] > div > div > div > button {
                width: 100% !important;
                height: auto !important;
                min-height: 70px !important;
                padding: 12px 16px !important;
                border-radius: 12px !important;
                font-weight: 600 !important;
                line-height: 1.3 !important;
                white-space: pre-line !important;
                box-shadow: 0 4px 12px rgba(44, 62, 80, 0.15) !important;
                transition: all 0.2s ease !important;
                margin-bottom: 10px !important;
            }
            div[data-testid="column"] > div > div > div > button:hover {
                transform: translateY(-1px) !important;
                box-shadow: 0 6px 16px rgba(44, 62, 80, 0.25) !important;
            }
            </style>
            """
            st.markdown(button_style, unsafe_allow_html=True)
            
            # ボタンのテキストを2行に分ける
            button_text = f"""**{exercise_name}**
{exercise_details}"""
            
            if st.button(
                button_text,
                key=f"exercise_select_{idx}",
                use_container_width=True,
                type=button_type
            ):
                # 同じ種目をクリックした場合は閉じる、違う種目なら切り替え
                if st.session_state.selected_exercise_idx == idx:
                    st.session_state.selected_exercise_idx = None
                else:
                    st.session_state.selected_exercise_idx = idx
                st.rerun()
            
            # このエクササイズが選択されている場合、直下にアコーディオン入力画面を表示
            if st.session_state.selected_exercise_idx == idx:
                # エクササイズタイトルとアコーディオン
                exercise_title = f"{exercise.get('No', '')} {exercise['Exercise']}"
                
                with st.expander(f"記録入力: {exercise_title}", expanded=True):
                    # 前回のトレーニングログを表示
                    log_df = load_training_log()
                    if len(log_df) > 0 and 'エクササイズ名' in log_df.columns and '名前' in log_df.columns:
                        # 現在の選手の同じエクササイズの履歴を取得
                        player_exercise_logs = log_df[
                            (log_df['エクササイズ名'] == exercise['Exercise']) & 
                            (log_df['名前'] == player_name)
                        ].sort_values('日付', ascending=False) if player_name else pd.DataFrame()
                        
                        if len(player_exercise_logs) > 0:
                            latest_log = player_exercise_logs.iloc[0]
                            st.markdown(f"""
                            <div style="
                                background: linear-gradient(135deg, rgba(108, 117, 125, 0.05) 0%, rgba(73, 80, 87, 0.05) 100%);
                                border: 1px solid rgba(108, 117, 125, 0.2);
                                border-radius: 8px;
                                padding: 12px 15px;
                                margin: 10px 0 15px 0;
                            ">
                                <h5 style="
                                    color: #495057;
                                    margin: 0 0 8px 0;
                                    font-size: 14px;
                                    font-weight: 600;
                                ">前回のトレーニング</h5>
                                <div style="
                                    display: grid;
                                    grid-template-columns: 1fr 1fr 1fr 1fr;
                                    gap: 8px;
                                    font-size: 12px;
                                    color: #6c757d;
                                ">
                                    <div><strong>日付:</strong><br>{pd.to_datetime(latest_log['日付']).strftime('%m/%d') if '日付' in latest_log else '-'}</div>
                                    <div><strong>セット:</strong><br>{latest_log.get('set', '-')}</div>
                                    <div><strong>負荷:</strong><br>{latest_log.get('負荷', '-')}</div>
                                    <div><strong>回数:</strong><br>{latest_log.get('回数', '-')}</div>
                                </div>
                                {f'<div style="margin-top: 8px; font-size: 12px; color: #6c757d;"><strong>総負荷量:</strong> {latest_log.get("総負荷量", 0):.1f}kg</div>' if '総負荷量' in latest_log else ''}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # 過去3回の履歴サマリー
                            if len(player_exercise_logs) > 1:
                                recent_logs = player_exercise_logs.head(3)
                                st.markdown("""
                                <div style="
                                    background: rgba(248, 249, 250, 0.7);
                                    border-radius: 6px;
                                    padding: 10px;
                                    margin: 10px 0;
                                ">
                                    <h6 style="
                                        color: #6c757d;
                                        margin: 0 0 6px 0;
                                        font-size: 12px;
                                        font-weight: 600;
                                    ">履歴サマリー (直近3回)</h6>
                                </div>
                                """, unsafe_allow_html=True)
                                
                                for i, (_, log) in enumerate(recent_logs.iterrows()):
                                    if i < 3:  # 最大3件
                                        date_str = pd.to_datetime(log['日付']).strftime('%m/%d') if '日付' in log else '-'
                                        st.markdown(f"""
                                        <div style="
                                            font-size: 11px;
                                            color: #8a9298;
                                            padding: 2px 10px;
                                            display: flex;
                                            justify-content: space-between;
                                        ">
                                            <span>{date_str}</span>
                                            <span>{log.get('負荷', '-')} × {log.get('回数', '-')} ({log.get('総負荷量', 0):.0f}kg)</span>
                                        </div>
                                        """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div style="
                                background: rgba(248, 249, 250, 0.7);
                                border: 1px dashed rgba(108, 117, 125, 0.3);
                                border-radius: 6px;
                                padding: 10px;
                                margin: 10px 0 15px 0;
                                text-align: center;
                            ">
                                <span style="color: #8a9298; font-size: 12px;">初回トレーニングです</span>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Point表示（改善されたデザイン）
                    if 'Point' in exercise and exercise['Point'] and pd.notna(exercise['Point']) and exercise['Point'] != '':
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, rgba(108, 117, 125, 0.1) 0%, rgba(73, 80, 87, 0.1) 100%);
                            border-left: 4px solid #6c757d;
                            padding: 10px 15px;
                            margin: 10px 0 15px 0;
                            border-radius: 6px;
                        ">
                            <p style="
                                margin: 0;
                                color: #495057;
                                font-weight: 600;
                                font-size: 13px;
                                line-height: 1.4;
                            ">
                                <span style="color: #6c757d; font-weight: 700;">POINT:</span> {exercise['Point']}
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # プログラム情報をコンパクトに
                    st.markdown(f"""
                    <div style="
                        background: rgba(248, 249, 250, 0.8);
                        padding: 12px;
                        border-radius: 8px;
                        margin: 10px 0;
                        display: grid;
                        grid-template-columns: 1fr 1fr 1fr;
                        gap: 10px;
                        text-align: center;
                        border: 1px solid rgba(108, 117, 125, 0.2);
                    ">
                        <div style="
                            background: rgba(255, 255, 255, 0.8);
                            padding: 8px;
                            border-radius: 6px;
                        ">
                            <div style="color: #6c757d; font-size: 10px; font-weight: 700; margin-bottom: 4px;">SETS</div>
                            <div style="color: #495057; font-size: 16px; font-weight: 700;">{exercise['set']}</div>
                        </div>
                        <div style="
                            background: rgba(255, 255, 255, 0.8);
                            padding: 8px;
                            border-radius: 6px;
                        ">
                            <div style="color: #6c757d; font-size: 10px; font-weight: 700; margin-bottom: 4px;">LOAD</div>
                            <div style="color: #495057; font-size: 16px; font-weight: 700;">{load_display}</div>
                        </div>
                        <div style="
                            background: rgba(255, 255, 255, 0.8);
                            padding: 8px;
                            border-radius: 6px;
                        ">
                            <div style="color: #6c757d; font-size: 10px; font-weight: 700; margin-bottom: 4px;">REPS</div>
                            <div style="color: #495057; font-size: 16px; font-weight: 700;">{exercise['rep']}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # セット数の計算
                    total_sets = sum([int(s) for s in exercise['set'].split('・')])
                    
                    # セット数入力（コンパクト）
                    actual_sets = st.number_input(
                        "実施セット数", 
                        min_value=1, 
                        value=total_sets, 
                        key=f"sets_{idx}",
                        help=f"予定: {exercise['set']}"
                    )
                    
                    # モバイル対応の横並び入力
                    st.markdown("**記録入力:**")
                    
                    loads = []
                    reps = []
                    
                    for set_num in range(actual_sets):
                        # モバイルで使いやすい横並びレイアウト
                        col1, col2, col3, col4 = st.columns([1, 1, 1, 0.7])
                        
                        with col1:
                            unit_default = 0
                            if f"copy_unit_{idx}" in st.session_state and set_num > 0:
                                units = ["kg", "%", "体重", "その他"]
                                saved_unit = st.session_state[f"copy_unit_{idx}"]
                                if saved_unit in units:
                                    unit_default = units.index(saved_unit)
                            
                            unit = st.selectbox(
                                "単位",
                                ["kg", "%", "体重", "その他"],
                                index=unit_default,
                                key=f"unit_{idx}_{set_num}",
                                label_visibility="collapsed"
                            )
                        
                        with col2:
                            if unit == "その他":
                                load_default = ""
                                if f"copy_load_text_{idx}" in st.session_state and set_num > 0:
                                    load_default = st.session_state[f"copy_load_text_{idx}"]
                                
                                set_load = st.text_input(
                                    "負荷", 
                                    value=load_default,
                                    key=f"load_{idx}_{set_num}",
                                    placeholder="負荷",
                                    label_visibility="collapsed"
                                )
                            elif unit == "体重":
                                set_load = "体重"
                                st.text_input("負荷", value="体重", disabled=True, key=f"load_disabled_{idx}_{set_num}", label_visibility="collapsed")
                            else:
                                load_default = 0.0
                                if f"copy_load_val_{idx}" in st.session_state and set_num > 0:
                                    load_default = st.session_state[f"copy_load_val_{idx}"]
                                
                                load_value = st.number_input(
                                    "値",
                                    min_value=0.0,
                                    value=load_default,
                                    step=0.1 if unit == "%" else 0.5,
                                    key=f"load_val_{idx}_{set_num}",
                                    label_visibility="collapsed"
                                )
                                set_load = f"{load_value}{unit}"
                            
                            loads.append(set_load)
                        
                        with col3:
                            rep_default = 1
                            if f"copy_rep_{idx}" in st.session_state and set_num > 0:
                                rep_default = st.session_state[f"copy_rep_{idx}"]
                            
                            set_rep = st.number_input(
                                "レップ数", 
                                min_value=0, 
                                value=rep_default, 
                                key=f"rep_{idx}_{set_num}",
                                label_visibility="collapsed"
                            )
                            reps.append(set_rep)
                        
                        with col4:
                            if set_num == 0 and actual_sets > 1:
                                if st.button("全適用", key=f"copy_all_{idx}", help="この設定を全セットに適用"):
                                    st.session_state[f"copy_unit_{idx}"] = unit
                                    st.session_state[f"copy_rep_{idx}"] = set_rep
                                    
                                    if unit == "その他":
                                        st.session_state[f"copy_load_text_{idx}"] = set_load
                                    elif unit != "体重":
                                        st.session_state[f"copy_load_val_{idx}"] = load_value
                                    
                                    st.rerun()
                            else:
                                st.write("")
                    
                    # コメント入力（コンパクト）
                    exercise_comment = st.text_input(
                        "コメント", 
                        key=f"comment_{idx}",
                        placeholder="調子、フォームなど"
                    )
                    
                    # ボタン群（横並び）
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        # 完了ボタン（モバイル対応）
                        if st.button(f"{exercise['Exercise']} 完了", key=f"complete_{idx}", type="primary", use_container_width=True):
                            if not player_name:
                                st.error("選手名を入力してください")
                            else:
                                # セットデータを準備
                                sets_data = []
                                for set_num in range(actual_sets):
                                    sets_data.append({
                                        'set_number': set_num + 1,
                                        'load': loads[set_num],
                                        'reps': reps[set_num]
                                    })
                                
                                # 新しい形式で保存
                                saved_sets = save_training_log_formatted(
                                    player_name=player_name,
                                    program_name=selected_program,
                                    exercise_name=exercise['Exercise'],
                                    sets_data=sets_data
                                )
                                
                                st.success(f"{exercise['Exercise']} 完了！{saved_sets}セットのデータを保存しました。")
                                st.balloons()
                                
                                # 種目選択をリセット
                                st.session_state.selected_exercise_idx = None
                                st.rerun()
                    
                    with col_btn2:
                        # 戻るボタン
                        if st.button("種目選択に戻る", key=f"back_{idx}", use_container_width=True):
                            st.session_state.selected_exercise_idx = None
                            st.rerun()
        
        # 全種目完了ボタン（全ての種目を完了した場合に表示）
        if st.session_state.selected_exercise_idx is None:
            st.markdown("---")
            if st.button("全プログラム完了", type="primary", use_container_width=True):
                st.success("お疲れ様でした！全プログラムが完了しました！")
                st.balloons()
                # セッション状態をクリア
                for key in list(st.session_state.keys()):
                    if key.startswith(('copy_', 'sets_', 'unit_', 'load_', 'rep_', 'comment_')):
                        del st.session_state[key]
                st.rerun()

elif page == "プログラム一覧":
    st.title("プログラム一覧")
    
    # プログラムファイルを読み込み
    program_df = load_program_file()
    
    if len(program_df) == 0:
        st.error("プログラムデータを読み込めませんでした。")
        st.stop()
    
    # プログラム検索機能
    available_programs = program_df['Program'].unique()
    
    # 検索バー
    st.markdown("### プログラム検索")
    
    # プログラム選択式
    col_search1, col_search2 = st.columns(2)
    
    with col_search1:
        selected_programs = st.multiselect(
            "プログラムを選択", 
            ["すべて"] + list(available_programs),
            default=["すべて"],
            help="複数選択可能"
        )
    
    with col_search2:
        # エクササイズ名での検索も可能
        exercise_search = st.text_input("エクササイズ名で検索", placeholder="例: Squat, Bench")
    
    # 検索結果のフィルタリング
    if "すべて" not in selected_programs and selected_programs:
        filtered_programs = selected_programs
    else:
        filtered_programs = list(available_programs)
    
    # エクササイズ名での追加フィルタリング
    if exercise_search:
        exercise_matches = program_df[program_df['Exercise'].str.contains(exercise_search, case=False, na=False)]['Program'].unique()
        filtered_programs = [prog for prog in filtered_programs if prog in exercise_matches]
    
    # 検索結果の表示
    if len(selected_programs) > 1 or (len(selected_programs) == 1 and "すべて" not in selected_programs) or exercise_search:
        st.markdown(f"**検索結果: {len(filtered_programs)}件**")
    
    # 検索結果に基づいてプログラムを表示
    for program in filtered_programs:
        with st.expander(f"PROGRAM {program}", expanded=len(filtered_programs) <= 3):
            program_exercises = program_df[program_df['Program'] == program]
            
            # ウォーミングアップ・補助種目の表示（WU、ST、PLを含む）
            warmup_exercises = program_exercises[
                program_exercises['No'].isin(['WU', 'ST', 'PL'])
            ] if 'No' in program_exercises.columns else pd.DataFrame()
            
            if len(warmup_exercises) > 0:
                st.markdown("""
                <div style="
                    background: rgba(108, 117, 125, 0.08);
                    border-left: 3px solid #6c757d;
                    padding: 8px 12px;
                    margin: 10px 0;
                    border-radius: 6px;
                ">
                    <h4 style="
                        color: #495057;
                        margin: 0;
                        font-size: 14px;
                        font-weight: 600;
                        letter-spacing: 0.5px;
                    ">WARM UP & AUXILIARY</h4>
                </div>
                """, unsafe_allow_html=True)
                
                for _, warmup in warmup_exercises.iterrows():
                    # 種目タイプの表示
                    exercise_type = ""
                    type_name = ""
                    if warmup['No'] == 'WU':
                        exercise_type = "WU "
                        type_name = "Warm Up"
                    elif warmup['No'] == 'ST':
                        exercise_type = "ST "
                        type_name = "Stability"
                    elif warmup['No'] == 'PL':
                        exercise_type = "PL "
                        type_name = "Plyometrics"
                    
                    # ウォーミングアップの詳細情報
                    warmup_details = []
                    if pd.notna(warmup['set']) and warmup['set'] != '-':
                        warmup_details.append(f"{warmup['set']}set")
                    if pd.notna(warmup['rep']) and warmup['rep'] != '-':
                        warmup_details.append(f"{warmup['rep']}rep")
                    if pd.notna(warmup['load']) and warmup['load'] != '-':
                        # 負荷の%表記変換
                        load_display = warmup['load']
                        if str(load_display).replace('.', '').isdigit() and float(load_display) <= 1.0:
                            load_display = f"{float(load_display)*100:.0f}%"
                        warmup_details.append(f"{load_display}")
                    
                    detail_text = " | ".join(warmup_details) if warmup_details else ""
                    
                    if detail_text:
                        st.markdown(f"• {exercise_type}**{warmup['Exercise']}** ({type_name}) - {detail_text}")
                    else:
                        st.markdown(f"• {exercise_type}**{warmup['Exercise']}** ({type_name})")
                    
                    # ポイントがあれば表示
                    if 'Point' in warmup and pd.notna(warmup['Point']) and warmup['Point'] != '':
                        st.markdown(f"  POINT: {warmup['Point']}")
                
                st.markdown("---")
            
            # メイン種目の表示（番号のみ）
            main_exercises = program_exercises[
                ~program_exercises['No'].isin(['WU', 'ST', 'PL'])
            ] if 'No' in program_exercises.columns else program_exercises
            
            if len(main_exercises) > 0:
                st.markdown("""
                <div style="
                    background: rgba(73, 80, 87, 0.08);
                    border-left: 3px solid #495057;
                    padding: 8px 12px;
                    margin: 10px 0;
                    border-radius: 6px;
                ">
                    <h4 style="
                        color: #495057;
                        margin: 0;
                        font-size: 14px;
                        font-weight: 600;
                        letter-spacing: 0.5px;
                    ">MAIN EXERCISES</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # エクササイズ一覧を表形式で表示
                st.write("**エクササイズ詳細:**")
                
                # 表示用にデータを整形
                if 'Point' in main_exercises.columns:
                    display_df = main_exercises[['No', 'Exercise', 'set', 'load', 'rep', 'Point']].copy()
                    display_df.columns = ['No.', 'エクササイズ', 'セット数', '負荷', 'レップ数', 'ポイント']
                else:
                    display_df = main_exercises[['No', 'Exercise', 'set', 'load', 'rep']].copy() if 'No' in main_exercises.columns else main_exercises[['Exercise', 'set', 'load', 'rep']].copy()
                    if 'No' in main_exercises.columns:
                        display_df.columns = ['No.', 'エクササイズ', 'セット数', '負荷', 'レップ数']
                    else:
                        display_df.columns = ['エクササイズ', 'セット数', '負荷', 'レップ数']
                
                # 負荷の%表記変換
                def format_load(load):
                    if str(load).replace('.', '').isdigit() and float(load) <= 1.0:
                        return f"{float(load)*100:.0f}%"
                    else:
                        return str(load)
                
                display_df['負荷'] = display_df['負荷'].apply(format_load)
                
                # エクササイズ名を太文字にする
                display_df['エクササイズ'] = display_df['エクササイズ'].apply(lambda x: f"**{x}**")
                
                # インデックスを1から始まる連番に変更
                display_df.index = range(1, len(display_df) + 1)
                
                st.dataframe(display_df, use_container_width=True)
            else:
                st.info("このプログラムにはメイン種目が設定されていません。")

elif page == "過去ログ検索":
    st.title("過去ログ検索")
    
    # ログファイルを読み込み
    log_df = load_training_log()
    
    if len(log_df) == 0:
        st.info("まだログデータがありません。")
        st.stop()
    
    # 検索条件入力
    st.markdown("### 検索条件")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 選手名選択
        if '名前' in log_df.columns:
            available_names = ["すべて"] + sorted(log_df['名前'].unique().tolist())
            selected_name = st.selectbox("選手名", available_names)
        else:
            selected_name = "すべて"
            st.selectbox("選手名", ["すべて"], disabled=True)
    
    with col2:
        # プログラム選択
        if 'プログラム名' in log_df.columns:
            available_programs = ["すべて"] + sorted(log_df['プログラム名'].unique().tolist())
            selected_program = st.selectbox("プログラム", available_programs)
        else:
            selected_program = "すべて"
            st.selectbox("プログラム", ["すべて"], disabled=True)
    
    with col3:
        # 日付範囲選択
        date_option = st.selectbox("期間", ["すべて", "今日", "今週", "今月", "カスタム"])
    
    # カスタム日付範囲
    if date_option == "カスタム":
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            start_date = st.date_input("開始日", value=datetime.today() - timedelta(days=7))
        with col_date2:
            end_date = st.date_input("終了日", value=datetime.today())
    
    # フィルタリング処理
    filtered_df = log_df.copy()
    
    # 名前でフィルタ
    if selected_name != "すべて" and '名前' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['名前'] == selected_name]
    
    # プログラムでフィルタ
    if selected_program != "すべて" and 'プログラム名' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['プログラム名'] == selected_program]
    
    # 日付でフィルタ
    if '日付' in filtered_df.columns:
        filtered_df['日付'] = pd.to_datetime(filtered_df['日付'])
        today = datetime.today()
        
        if date_option == "今日":
            filtered_df = filtered_df[filtered_df['日付'].dt.date == today.date()]
        elif date_option == "今週":
            start_week = today - timedelta(days=today.weekday())
            filtered_df = filtered_df[filtered_df['日付'] >= start_week]
        elif date_option == "今月":
            start_month = today.replace(day=1)
            filtered_df = filtered_df[filtered_df['日付'] >= start_month]
        elif date_option == "カスタム":
            filtered_df = filtered_df[
                (filtered_df['日付'].dt.date >= start_date) & 
                (filtered_df['日付'].dt.date <= end_date)
            ]
    
    # 検索結果表示
    st.markdown(f"### 検索結果: {len(filtered_df)}件")
    
    if len(filtered_df) > 0:
        # データテーブルで表示
        display_columns = ['日付', 'プログラム名', '名前', 'エクササイズ名', 'set', '負荷', '回数', '総負荷量']
        available_columns = [col for col in display_columns if col in filtered_df.columns]
        display_df = filtered_df[available_columns].copy()
        
        # 日付フォーマットを調整
        if '日付' in display_df.columns:
            display_df['日付'] = pd.to_datetime(display_df['日付']).dt.strftime('%Y/%m/%d')
        
        st.dataframe(display_df, use_container_width=True)
        
        # 統計情報
        if len(filtered_df) > 0:
            st.markdown("### 統計情報")
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                total_sets = len(filtered_df)
                st.metric("総セット数", total_sets)
            
            with col_stat2:
                if '総負荷量' in filtered_df.columns:
                    total_volume = filtered_df['総負荷量'].sum()
                    st.metric("総負荷量", f"{total_volume:.1f}kg")
            
            with col_stat3:
                if 'エクササイズ名' in filtered_df.columns:
                    unique_exercises = filtered_df['エクササイズ名'].nunique()
                    st.metric("実施種目数", unique_exercises)
            
            with col_stat4:
                if 'プログラム名' in filtered_df.columns:
                    unique_programs = filtered_df['プログラム名'].nunique()
                    st.metric("実施プログラム数", unique_programs)
        
        # データのエクスポート機能
        st.markdown("### データエクスポート")
        if st.button("CSVダウンロード"):
            csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="CSVファイルをダウンロード",
                data=csv,
                file_name=f"training_log_{datetime.today().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("条件に一致するデータが見つかりませんでした。")

elif page == "データ管理":
    st.title("データ管理")
    
    st.markdown("### ファイル管理")
    
    # 現在のファイル状況
    col_file1, col_file2 = st.columns(2)
    
    with col_file1:
        st.markdown("#### トレーニングログ")
        if os.path.exists(LOG_FILE):
            log_df = load_training_log()
            st.success(f"ファイル存在 ({len(log_df)}件のログ)")
            
            if st.button("ログファイルを削除", type="secondary"):
                os.remove(LOG_FILE)
                st.success("ログファイルを削除しました")
                st.rerun()
        else:
            st.info("ログファイルなし")
    
    with col_file2:
        st.markdown("#### プログラムファイル")
        if os.path.exists(PROGRAM_FILE):
            program_df = load_program_file()
            st.success(f"ファイル存在 ({len(program_df)}件のプログラム)")
            
            if st.button("プログラムファイルを削除", type="secondary"):
                os.remove(PROGRAM_FILE)
                st.success("プログラムファイルを削除しました")
                st.rerun()
        else:
            st.info("プログラムファイルなし")
    
    st.markdown("---")
    
    # ファイルアップロード機能
    st.markdown("### ファイルアップロード")
    
    col_upload1, col_upload2 = st.columns(2)
    
    with col_upload1:
        st.markdown("#### プログラムファイルアップロード")
        uploaded_program = st.file_uploader(
            "プログラム用Excelファイル", 
            type=['xlsx', 'xls'],
            key="program_upload"
        )
        
        if uploaded_program:
            try:
                # アップロードされたファイルを保存
                with open(PROGRAM_FILE, "wb") as f:
                    f.write(uploaded_program.getbuffer())
                st.success("プログラムファイルをアップロードしました")
                st.rerun()
            except Exception as e:
                st.error(f"アップロードエラー: {e}")
    
    with col_upload2:
        st.markdown("#### ログファイルアップロード")
        uploaded_log = st.file_uploader(
            "ログ用Excelファイル", 
            type=['xlsx', 'xls'],
            key="log_upload"
        )
        
        if uploaded_log:
            try:
                # アップロードされたファイルを保存
                with open(LOG_FILE, "wb") as f:
                    f.write(uploaded_log.getbuffer())
                st.success("ログファイルをアップロードしました")
                st.rerun()
            except Exception as e:
                st.error(f"アップロードエラー: {e}")
    
    st.markdown("---")
    
    # サンプルファイル作成
    st.markdown("### サンプルファイル作成")
    
    col_sample1, col_sample2 = st.columns(2)
    
    with col_sample1:
        if st.button("サンプルプログラムファイル作成"):
            sample_program_df = pd.DataFrame({
                'Program': ['①', '①', '①', '②', '②', '③'],
                'No': ['WU', 1, 2, 'WU', 1, 1],
                'Exercise': ['Dynamic Stretch', 'Back Squat', 'Bench Press', 'Light Jog', 'Sprint 20m', 'Vertical Jump'],
                'set': [1, 4, 3, 1, 5, 3],
                'load': ['-', 0.8, 0.75, '-', '-', '-'],
                'rep': [10, 8, 10, 5, 1, 10],
                'Point': ['全身をほぐす', '膝をつま先の方向に', 'バーパスに注意', '軽く温める', '全力疾走', '着地を意識']
            })
            sample_program_df.to_excel(PROGRAM_FILE, index=False)
            st.success("サンプルプログラムファイルを作成しました")
            st.rerun()
    
    with col_sample2:
        if st.button("空のログファイル作成"):
            empty_log_df = pd.DataFrame(columns=[
                "日付", "プログラム名", "名前", "エクササイズ名", 
                "set", "負荷", "回数", "総負荷量"
            ])
            empty_log_df.to_excel(LOG_FILE, index=False)
            st.success("空のログファイルを作成しました")
            st.rerun()
    
    st.markdown("---")
    
    # データ統計
    st.markdown("### データ統計")
    
    if os.path.exists(LOG_FILE):
        log_df = load_training_log()
        if len(log_df) > 0:
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            with col_stat1:
                st.metric("総ログ数", len(log_df))
            
            with col_stat2:
                unique_players = log_df['名前'].nunique() if '名前' in log_df.columns else 0
                st.metric("登録選手数", unique_players)
            
            with col_stat3:
                if '日付' in log_df.columns:
                    log_df['日付'] = pd.to_datetime(log_df['日付'])
                    latest_date = log_df['日付'].max().strftime('%Y/%m/%d')
                    st.metric("最新記録日", latest_date)
            
            # 選手別統計
            if '名前' in log_df.columns and len(log_df) > 0:
                st.markdown("#### 選手別ログ数")
                player_counts = log_df['名前'].value_counts()
                st.bar_chart(player_counts)
    
    st.markdown("---")
    
    # システム情報
    st.markdown("### システム情報")
    st.info("""
    **バスケットボール トレーニングシステム v1.0**
    
    - トレーニングプログラムの管理
    - 個別ログの記録
    - 過去データの検索・分析
    - データのインポート・エクスポート
    
    **サポートファイル形式:** Excel (.xlsx, .xls), CSV
    """)

else:
    st.error("無効なページが選択されました。")