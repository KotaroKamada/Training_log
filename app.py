import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="🏀 バスケットボール トレーニングシステム", layout="wide")

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
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        text-align: center;
        box-shadow: 0 10px 30px rgba(44, 62, 80, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
    ">
        <h1 style="
            color: #ECF0F1; 
            margin: 0; 
            font-size: 32px;
            font-weight: 700;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
            letter-spacing: 1px;
        ">
            TRAINING LOG INPUT
        </h1>
        <p style="
            color: #BDC3C7; 
            margin: 12px 0 0 0; 
            font-size: 16px;
            font-weight: 300;
            letter-spacing: 0.5px;
        ">
            本日のトレーニング記録を入力してください
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
        # 選択されたプログラムのエクササイズを表示
        program_exercises = program_df[program_df['Program'] == selected_program]
        
        # 選択されたプログラムのエクササイズを表示（エクセルの順序を保持）
        program_exercises = program_df[program_df['Program'] == selected_program].reset_index(drop=True)
        
        # ウォーミングアップ種目を除外（WU以外のみ）
        main_exercises = program_exercises[program_exercises['No'] != 'WU'] if 'No' in program_exercises.columns else program_exercises
        
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
        
        # ウォーミングアップの表示
        warmup_exercises = program_exercises[program_exercises['No'] == 'WU'] if 'No' in program_exercises.columns else pd.DataFrame()
        
        if len(warmup_exercises) > 0:
            st.markdown("#### ウォーミングアップ")
            for _, warmup in warmup_exercises.iterrows():
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
                    st.markdown(f"• **{warmup['Exercise']}** - {detail_text}")
                else:
                    st.markdown(f"• **{warmup['Exercise']}**")
                
                # ポイントがあれば表示
                if 'Point' in warmup and pd.notna(warmup['Point']) and warmup['Point'] != '':
                    st.markdown(f"  💡 {warmup['Point']}")
            
            st.markdown("---")
            st.markdown("#### メイン種目")
        
        st.markdown("---")
        
        for idx, exercise in enumerate(grouped_exercises):
            # スタイリッシュなカード風デザイン
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%);
                padding: 20px 30px;
                border-radius: 15px;
                margin: 25px 0 20px 0;
                box-shadow: 0 8px 25px rgba(44, 62, 80, 0.25);
                border: 1px solid rgba(255, 255, 255, 0.1);
            ">
                <h2 style="
                    color: #ECF0F1;
                    margin: 0;
                    font-size: 24px;
                    font-weight: 600;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    letter-spacing: 0.8px;
                    text-align: center;
                ">{exercise.get('No', '')} {exercise['Exercise']}</h2>
            </div>
            """, unsafe_allow_html=True)
            
            # Point表示（F列）
            if 'Point' in exercise and exercise['Point'] and pd.notna(exercise['Point']) and exercise['Point'] != '':
                st.markdown(f"""
                <div style="
                    background: rgba(52, 73, 94, 0.08);
                    border-left: 4px solid #34495E;
                    padding: 12px 18px;
                    margin: 10px 0 20px 0;
                    border-radius: 8px;
                ">
                    <p style="
                        margin: 0; 
                        color: #2C3E50; 
                        font-weight: 500; 
                        font-size: 14px;
                        line-height: 1.4;
                    ">
                        <strong>TECHNICAL POINT:</strong> {exercise['Point']}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            # プログラム情報をカード風に表示
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"""
                <div style="
                    background: rgba(52, 73, 94, 0.08);
                    padding: 15px 12px;
                    border-radius: 10px;
                    text-align: center;
                    border: 1px solid rgba(52, 73, 94, 0.15);
                    margin: 0 5px;
                ">
                    <h4 style="
                        margin: 0 0 8px 0; 
                        color: #2C3E50; 
                        font-weight: 600; 
                        font-size: 13px;
                        letter-spacing: 0.5px;
                    ">SETS</h4>
                    <p style="
                        margin: 0; 
                        font-size: 22px; 
                        font-weight: 700; 
                        color: #2C3E50;
                        line-height: 1.2;
                    ">{exercise['set']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                # %表記の処理
                load_display = exercise['load']
                if '・' in str(load_display):
                    # 複数の値がある場合
                    loads = str(load_display).split('・')
                    formatted_loads = []
                    for load in loads:
                        if load.replace('.', '').isdigit() and float(load) <= 1.0:
                            formatted_loads.append(f"{float(load)*100:.0f}%")
                        else:
                            formatted_loads.append(load)
                    load_display = '・'.join(formatted_loads)
                else:
                    # 単一の値の場合
                    if str(load_display).replace('.', '').isdigit() and float(load_display) <= 1.0:
                        load_display = f"{float(load_display)*100:.0f}%"
                
                st.markdown(f"""
                <div style="
                    background: rgba(52, 73, 94, 0.08);
                    padding: 15px 12px;
                    border-radius: 10px;
                    text-align: center;
                    border: 1px solid rgba(52, 73, 94, 0.15);
                    margin: 0 5px;
                ">
                    <h4 style="
                        margin: 0 0 8px 0; 
                        color: #2C3E50; 
                        font-weight: 600; 
                        font-size: 13px;
                        letter-spacing: 0.5px;
                    ">LOAD</h4>
                    <p style="
                        margin: 0; 
                        font-size: 22px; 
                        font-weight: 700; 
                        color: #2C3E50;
                        line-height: 1.2;
                    ">{load_display}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div style="
                    background: rgba(52, 73, 94, 0.08);
                    padding: 15px 12px;
                    border-radius: 10px;
                    text-align: center;
                    border: 1px solid rgba(52, 73, 94, 0.15);
                    margin: 0 5px;
                ">
                    <h4 style="
                        margin: 0 0 8px 0; 
                        color: #2C3E50; 
                        font-weight: 600; 
                        font-size: 13px;
                        letter-spacing: 0.5px;
                    ">REPS</h4>
                    <p style="
                        margin: 0; 
                        font-size: 22px; 
                        font-weight: 700; 
                        color: #2C3E50;
                        line-height: 1.2;
                    ">{exercise['rep']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # セット数の計算（複数セットの場合は合計）
            total_sets = sum([int(s) for s in exercise['set'].split('・')])
            
            # セット数入力
            st.markdown("<br>", unsafe_allow_html=True)
            actual_sets = st.number_input(
                "実施セット数", 
                min_value=1, 
                value=total_sets, 
                key=f"sets_{idx}",
                help=f"予定: {exercise['set']} セット"
            )
            
            # 各セットの負荷とレップ入力
            loads = []
            reps = []
            
            for set_num in range(actual_sets):
                col_load_unit, col_load_val, col_rep, col_btn = st.columns([1.2, 1.2, 1.2, 0.8])
                
                with col_load_unit:
                    # 全適用された値をチェック
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
                        key=f"unit_{idx}_{set_num}"
                    )
                
                with col_load_val:
                    if unit == "その他":
                        load_default = ""
                        if f"copy_load_text_{idx}" in st.session_state and set_num > 0:
                            load_default = st.session_state[f"copy_load_text_{idx}"]
                        
                        set_load = st.text_input(
                            "負荷", 
                            value=load_default,
                            key=f"load_{idx}_{set_num}",
                            placeholder="自由入力"
                        )
                    elif unit == "体重":
                        set_load = "体重"
                        st.text_input("負荷", value="体重", disabled=True, key=f"load_disabled_{idx}_{set_num}")
                    else:
                        load_default = 0.0
                        if f"copy_load_val_{idx}" in st.session_state and set_num > 0:
                            load_default = st.session_state[f"copy_load_val_{idx}"]
                        
                        load_value = st.number_input(
                            "値",
                            min_value=0.0,
                            value=load_default,
                            step=0.1 if unit == "%" else 0.5,
                            key=f"load_val_{idx}_{set_num}"
                        )
                        set_load = f"{load_value}{unit}"
                    
                    loads.append(set_load)
                
                with col_rep:
                    rep_default = 1
                    if f"copy_rep_{idx}" in st.session_state and set_num > 0:
                        rep_default = st.session_state[f"copy_rep_{idx}"]
                    
                    set_rep = st.number_input(
                        "レップ数", 
                        min_value=0, 
                        value=rep_default, 
                        key=f"rep_{idx}_{set_num}"
                    )
                    reps.append(set_rep)
                
                with col_btn:
                    # 1セット目のみ全適用ボタン
                    if set_num == 0 and actual_sets > 1:
                        if st.button("全適用", key=f"copy_all_{idx}", help="1セット目の設定を全セットに適用", type="secondary"):
                            # 現在の値をセッションステートに保存
                            st.session_state[f"copy_unit_{idx}"] = unit
                            st.session_state[f"copy_rep_{idx}"] = set_rep
                            
                            if unit == "その他":
                                st.session_state[f"copy_load_text_{idx}"] = set_load
                            elif unit != "体重":
                                st.session_state[f"copy_load_val_{idx}"] = load_value
                            
                            st.rerun()
                    else:
                        st.write("")  # 空白
            
            # コメント入力
            st.markdown("<br>", unsafe_allow_html=True)
            exercise_comment = st.text_input(
                "コメント", 
                key=f"comment_{idx}",
                placeholder="フォーム、調子、注意点など"
            )
            
            # 完了ボタン
            st.markdown("<br>", unsafe_allow_html=True)
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                if st.button(f"{exercise['Exercise']} 完了", key=f"complete_{idx}", type="primary", use_container_width=True):
                    if not player_name:
                        st.error("選手名を入力してください")
                    else:
                        # 負荷とレップをカンマ区切りの文字列に変換
                        loads_str = ", ".join([str(load) for load in loads])
                        reps_str = ", ".join([str(rep) for rep in reps])
                        
                        # ログに保存
                        log_data = pd.DataFrame({
                            "名前": [player_name],
                            "体重": [body_weight],
                            "日付": [datetime.today().date()],
                            "プログラム": [selected_program],
                            "エクササイズ": [exercise['Exercise']],
                            "予定セット": [exercise['set']],
                            "予定負荷": [exercise['load']],
                            "予定レップ": [exercise['rep']],
                            "実施セット": [actual_sets],
                            "実施負荷": [loads_str],
                            "実施レップ": [reps_str],
                            "コメント": [exercise_comment],
                            "ポイント": [exercise.get('Point', '') if 'Point' in exercise else '']
                        })
                        existing_log = load_training_log()
                        save_training_log(log_data, existing_log)
                        
                        st.success(f"{exercise['Exercise']} 完了！")
                        st.balloons()
                        st.rerun()
            
            # セパレーター
            st.markdown("""
            <div style="
                height: 1px;
                background: linear-gradient(90deg, transparent 0%, #34495E 50%, transparent 100%);
                margin: 35px 0;
            "></div>
            """, unsafe_allow_html=True)

elif page == "プログラム一覧":
    st.title("プログラム一覧")
    
    # プログラムファイルを読み込み
    program_df = load_program_file()
    
    if len(program_df) == 0:
        st.error("プログラムデータを読み込めませんでした。")
        st.stop()
    
    # 利用可能なプログラム一覧を表示
    available_programs = program_df['Program'].unique()
    
    # プログラム選択用のタブを作成
    tabs = st.tabs([f"{prog}" for prog in available_programs])
    
    for i, program in enumerate(available_programs):
        with tabs[i]:
            program_exercises = program_df[program_df['Program'] == program]
            
            st.subheader(f"{program} の構成")
            
            # ウォーミングアップ種目の表示
            warmup_exercises = program_exercises[program_exercises['No'] == 'WU'] if 'No' in program_exercises.columns else pd.DataFrame()
            
            if len(warmup_exercises) > 0:
                st.markdown("#### ウォーミングアップ")
                for _, warmup in warmup_exercises.iterrows():
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
                        st.markdown(f"• **{warmup['Exercise']}** - {detail_text}")
                    else:
                        st.markdown(f"• **{warmup['Exercise']}**")
                    
                    # ポイントがあれば表示
                    if 'Point' in warmup and pd.notna(warmup['Point']) and warmup['Point'] != '':
                        st.markdown(f"  💡 {warmup['Point']}")
                
                st.markdown("---")
            
            # メイン種目の表示（WU以外）
            main_exercises = program_exercises[program_exercises['No'] != 'WU'] if 'No' in program_exercises.columns else program_exercises
            
            if len(main_exercises) > 0:
                st.markdown("#### メイン種目")
                
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
                
                # インデックスを1から始まる連番に変更
                display_df.index = range(1, len(display_df) + 1)
                
                st.dataframe(display_df, use_container_width=True)
                
                # 各エクササイズの詳細表示（折りたたみ式）
                st.write("**詳細設定:**")
                for idx, exercise in main_exercises.iterrows():
                    exercise_title = f"{exercise.get('No', '')} {exercise['Exercise']}" if 'No' in exercise and pd.notna(exercise['No']) else exercise['Exercise']
                    
                    with st.expander(exercise_title):
                        col_ex1, col_ex2 = st.columns(2)
                        
                        with col_ex1:
                            # 負荷の%表記変換
                            load_display = exercise['load']
                            if str(load_display).replace('.', '').isdigit() and float(load_display) <= 1.0:
                                load_display = f"{float(load_display)*100:.0f}%"
                            
                            if 'No' in exercise and pd.notna(exercise['No']):
                                st.write(f"**No.:** {exercise['No']}")
                            st.write(f"**セット数:** {exercise['set']}")
                            st.write(f"**負荷:** {load_display}")
                            st.write(f"**レップ数:** {exercise['rep']}")
                            
                            # Pointがあれば表示
                            if 'Point' in exercise and pd.notna(exercise['Point']) and exercise['Point'] != '':
                                st.info(f"**ポイント:** {exercise['Point']}")
                        
                        with col_ex2:
                            # メモ機能
                            memo = st.text_area(
                                "メモ",
                                placeholder="フォーム、注意点など",
                                key=f"memo_{program}_{idx}",
                                height=68
                            )
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
        available_names = ["すべて"] + sorted(log_df['名前'].unique().tolist())
        selected_name = st.selectbox("選手名", available_names)
    
    with col2:
        # プログラム選択
        if 'プログラム' in log_df.columns:
            available_programs = ["すべて"] + sorted(log_df['プログラム'].unique().tolist())
            selected_program_search = st.selectbox("プログラム", available_programs)
        else:
            st.selectbox("プログラム", ["すべて"], disabled=True)
            selected_program_search = "すべて"
    
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
    if selected_name != "すべて":
        filtered_df = filtered_df[filtered_df['名前'] == selected_name]
    
    # プログラムでフィルタ
    if selected_program_search != "すべて" and 'プログラム' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['プログラム'] == selected_program_search]
    
    # 日付でフィルタ
    if 'カスタム' != date_option:
        today = datetime.today().date()
        if date_option == "今日":
            filtered_df = filtered_df[pd.to_datetime(filtered_df['日付']).dt.date == today]
        elif date_option == "今週":
            week_start = today - timedelta(days=today.weekday())
            filtered_df = filtered_df[pd.to_datetime(filtered_df['日付']).dt.date >= week_start]
        elif date_option == "今月":
            month_start = today.replace(day=1)
            filtered_df = filtered_df[pd.to_datetime(filtered_df['日付']).dt.date >= month_start]
    else:
        # カスタム範囲
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df['日付']).dt.date >= start_date) &
            (pd.to_datetime(filtered_df['日付']).dt.date <= end_date)
        ]
    
    # 検索結果表示
    st.markdown("---")
    st.markdown(f"### 検索結果 ({len(filtered_df)}件)")
    
    if len(filtered_df) > 0:
        # サマリー情報
        col_summary1, col_summary2, col_summary3, col_summary4 = st.columns(4)
        
        with col_summary1:
            unique_dates = filtered_df['日付'].nunique()
            st.metric("トレーニング日数", f"{unique_dates}日")
        
        with col_summary2:
            total_sets = filtered_df['実施セット'].sum() if '実施セット' in filtered_df.columns else 0
            st.metric("総セット数", f"{total_sets}セット")
        
        with col_summary3:
            if 'エクササイズ' in filtered_df.columns:
                unique_exercises = filtered_df['エクササイズ'].nunique()
                st.metric("エクササイズ種類", f"{unique_exercises}種目")
            else:
                st.metric("エクササイズ種類", "データなし")
        
        with col_summary4:
            if '体重' in filtered_df.columns and filtered_df['体重'].notna().any():
                avg_weight = filtered_df['体重'].mean()
                st.metric("平均体重", f"{avg_weight:.1f}kg")
            else:
                st.metric("平均体重", "データなし")
        
        # 詳細データ表示
        st.markdown("### 詳細データ")
        
        # 表示列の選択
        display_columns = ["日付", "名前"]
        if '体重' in filtered_df.columns:
            display_columns.append("体重")
        if 'プログラム' in filtered_df.columns:
            display_columns.append("プログラム")
        if 'エクササイズ' in filtered_df.columns:
            display_columns.append("エクササイズ")
        
        # 他の列も条件付きで追加
        for col in ["実施セット", "実施負荷", "実施レップ", "コメント"]:
            if col in filtered_df.columns:
                display_columns.append(col)
        
        # 利用可能な列のみ表示
        available_display_cols = [col for col in display_columns if col in filtered_df.columns]
        
        # 日付でソート（最新順）
        filtered_df_sorted = filtered_df.sort_values('日付', ascending=False)
        
        st.dataframe(filtered_df_sorted[available_display_cols], use_container_width=True)
        
        # エクササイズ別の詳細分析
        if st.checkbox("エクササイズ別詳細分析を表示") and 'エクササイズ' in filtered_df.columns:
            st.markdown("### エクササイズ別分析")
            
            for exercise_name in filtered_df['エクササイズ'].unique():
                exercise_data = filtered_df[filtered_df['エクササイズ'] == exercise_name]
                
                with st.expander(f"{exercise_name} ({len(exercise_data)}回実施)"):
                    col_ex1, col_ex2 = st.columns(2)
                    
                    with col_ex1:
                        # 統計情報
                        if '実施セット' in exercise_data.columns:
                            avg_sets = exercise_data['実施セット'].mean()
                            st.write(f"**平均セット数:** {avg_sets:.1f}")
                        
                        if 'コメント' in exercise_data.columns:
                            comments = exercise_data['コメント'].dropna()
                            if len(comments) > 0:
                                st.write("**最新コメント:**")
                                for comment in comments.tail(3):
                                    if comment:
                                        st.write(f"• {comment}")
                    
                    with col_ex2:
                        # 実施履歴
                        st.write("**実施履歴:**")
                        history_cols = ['日付']
                        for col in ['実施セット', '実施負荷', '実施レップ']:
                            if col in exercise_data.columns:
                                history_cols.append(col)
                        
                        recent_sessions = exercise_data[history_cols].tail(5)
                        st.dataframe(recent_sessions, use_container_width=True)
        elif 'エクササイズ' not in filtered_df.columns:
            st.info("エクササイズデータがないため、詳細分析は利用できません。")
        
        # CSV出力
        st.markdown("---")
        if st.button("📥 検索結果をCSVでダウンロード"):
            csv = filtered_df_sorted[available_display_cols].to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="CSVファイルをダウンロード",
                data=csv,
                file_name=f"training_log_search_{datetime.today().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    else:
        st.info("検索条件に一致するデータがありません。")
        st.write("**検索のヒント:**")
        st.write("• 検索条件を緩くしてみてください")
        st.write("• 期間を広げてみてください")
        st.write("• 「すべて」を選択して全データを確認してください")

elif page == "データ管理":
    st.title("データ管理")
    
    tab1, tab2 = st.tabs(["📋 プログラム管理", "📈 ログ分析"])
    
    with tab1:
        st.subheader("トレーニングプログラム管理")
        
        # 現在のプログラム表示
        program_df = load_program_file()
        
        if len(program_df) > 0:
            st.write("**現在のプログラム:**")
            st.dataframe(program_df, use_container_width=True)
            
            # プログラム別サマリー
            st.write("**プログラム別サマリー:**")
            program_summary = program_df.groupby('Program').agg({
                'Exercise': 'count',
                'set': 'sum'
            }).rename(columns={'Exercise': 'エクササイズ数', 'set': '総セット数'})
            st.dataframe(program_summary, use_container_width=True)
        else:
            st.warning("プログラムデータがありません。")
        
        st.write("---")
        st.write("**新しいエクササイズを追加:**")
        
        col1, col2 = st.columns(2)
        with col1:
            new_program = st.text_input("プログラム名", placeholder="例: ①")
            new_exercise = st.text_input("エクササイズ名", placeholder="例: Back Squat")
            new_sets = st.number_input("セット数", min_value=1, value=3)
        
        with col2:
            new_load = st.text_input("負荷", placeholder="例: 0.8, 60kg, -")
            new_reps = st.number_input("レップ数", min_value=1, value=8)
            new_point = st.text_input("ポイント", placeholder="例: 膝をつま先の方向に")
            new_no = st.number_input("No.", min_value=1, value=1)
        
        if st.button("エクササイズを追加"):
            if new_program and new_exercise:
                new_row = pd.DataFrame({
                    'Program': [new_program],
                    'No': [new_no],
                    'Exercise': [new_exercise],
                    'set': [new_sets],
                    'load': [new_load],
                    'rep': [new_reps],
                    'Point': [new_point]
                })
                
                updated_program = pd.concat([program_df, new_row], ignore_index=True)
                updated_program.to_excel(PROGRAM_FILE, index=False)
                st.success("エクササイズが追加されました！")
                st.rerun()
            else:
                st.error("プログラム名とエクササイズ名を入力してください。")
    
    with tab2:
        st.subheader("トレーニングログ分析")
        
        log_df = load_training_log()
        
        if len(log_df) > 0:
            # 基本統計
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("総セッション数", len(log_df))
            with col2:
                if '実施セット' in log_df.columns:
                    avg_sets = log_df['実施セット'].mean()
                    st.metric("平均実施セット", f"{avg_sets:.1f}")
                else:
                    st.metric("平均実施セット", "データなし")
            with col3:
                unique_players = log_df['名前'].nunique()
                st.metric("登録選手数", unique_players)
            with col4:
                if 'エクササイズ' in log_df.columns:
                    unique_exercises = log_df['エクササイズ'].nunique()
                    st.metric("エクササイズ種類", unique_exercises)
                else:
                    st.metric("エクササイズ種類", "データなし")
            
            # エクササイズ別分析
            st.subheader("エクササイズ別分析")
            if 'エクササイズ' in log_df.columns and len(log_df) > 0:
                exercise_analysis = log_df.groupby('エクササイズ').agg({
                    '実施セット': ['count', 'mean'] if '実施セット' in log_df.columns else 'count',
                    '名前': 'nunique'
                })
                
                if '実施セット' in log_df.columns:
                    exercise_analysis.columns = ['実施回数', '平均セット数', '実施選手数']
                else:
                    exercise_analysis.columns = ['実施回数', '実施選手数']
                
                exercise_analysis = exercise_analysis.round(1)
                st.dataframe(exercise_analysis, use_container_width=True)
            else:
                st.info("エクササイズデータがありません。")
            
            # プログラム別分析
            if 'プログラム' in log_df.columns and len(log_df) > 0:
                st.subheader("プログラム別分析")
                program_analysis = log_df.groupby('プログラム').agg({
                    '実施セット': ['count', 'mean'] if '実施セット' in log_df.columns else 'count',
                    '名前': 'nunique'
                })
                
                if '実施セット' in log_df.columns:
                    program_analysis.columns = ['実施回数', '平均セット数', '実施選手数']
                else:
                    program_analysis.columns = ['実施回数', '実施選手数']
                
                program_analysis = program_analysis.round(1)
                st.dataframe(program_analysis, use_container_width=True)
            
            # 最新10件の詳細ログ
            st.subheader("最新ログ詳細")
            if len(log_df) > 0:
                latest_logs = log_df.tail(10)
                # 表示用に列を選択
                display_cols = ["名前", "日付", "エクササイズ", "予定セット", "実施セット", "実施負荷", "実施レップ"]
                available_cols = [col for col in display_cols if col in latest_logs.columns]
                st.dataframe(latest_logs[available_cols], use_container_width=True)
            
        else:
            st.info("分析するログデータがありません。")

# ファイル管理機能
st.sidebar.write("---")
st.sidebar.subheader("📁 ファイル管理")

col_sidebar1, col_sidebar2 = st.sidebar.columns(2)

with col_sidebar1:
    if st.button("💾 ログDL"):
        log_df = load_training_log()
        if len(log_df) > 0:
            csv = log_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="CSV形式",
                data=csv,
                file_name=f"training_log_{datetime.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_log"
            )
        else:
            st.info("データなし")

with col_sidebar2:
    if st.button("📋 プログラムDL"):
        program_df = load_program_file()
        if len(program_df) > 0:
            csv = program_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="CSV形式", 
                data=csv,
                file_name=f"training_program_{datetime.today().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="download_program"
            )

# ファイル構造の説明
with st.sidebar.expander("📋 エクセル形式"):
    st.write("**training_program.xlsx:**")
    st.code("""
Program | No. | Exercise       | set | load | rep | Point
①      | WU  | Dynamic Stretch| 1   | -    | 10  | 全身をほぐす
①      | 1   | Back Squat     | 4   | 0.8  | 8   | 膝をつま先の方向に
①      | 2   | Bench Press    | 3   | 0.75 | 10  | バーパスに注意  
②      | WU  | Light Jog      | 1   | -    | 5   | 軽く温める
②      | 1   | Sprint 20m     | 5   | -    | 1   | 全力疾走
    """)
    
    st.write("- **Program**: プログラム名（①、②など）")
    st.write("- **No.**: エクササイズ番号（WU=ウォーミングアップ、1,2,3...=メイン種目）")
    st.write("- **Exercise**: エクササイズ名")
    st.write("- **set**: セット数")
    st.write("- **load**: 負荷（重量比率、重量、体重など）")
    st.write("- **rep**: レップ数")
    st.write("- **Point**: 技術ポイント（G列）")

# 使用方法の説明
with st.sidebar.expander("ℹ️ 使用方法"):
    st.write("""
    **1. プログラム一覧**
    - 全プログラムの構成を確認
    - 各エクササイズの詳細設定
    - メモ機能
    
    **2. Training Log 入力**
    - エクセルで設定したプログラムを選択
    - セットごとに実施負荷・レップ数を入力
    - 単位選択機能（kg, %, 体重）
    
    **3. 過去ログ検索**
    - 名前・プログラム・日付で検索
    - エクササイズ別詳細分析
    - CSV出力機能
    
    **4. データ管理**
    - プログラムの追加・確認
    - セット数、負荷の統計分析
    """)