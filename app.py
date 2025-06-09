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
        
        # 種目一覧をコンパクトなボタンで表示（2列レイアウト）
        cols = st.columns(2)
        for idx, exercise in enumerate(grouped_exercises):
            col_idx = idx % 2
            with cols[col_idx]:
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
                    min-height: 80px !important;
                    padding: 12px 16px !important;
                    border-radius: 12px !important;
                    font-weight: 600 !important;
                    line-height: 1.3 !important;
                    white-space: pre-line !important;
                    box-shadow: 0 4px 12px rgba(44, 62, 80, 0.15) !important;
                    transition: all 0.2s ease !important;
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
                    st.session_state.selected_exercise_idx = idx
                    st.rerun()
        
        # 選択された種目の詳細入力画面
        if st.session_state.selected_exercise_idx is not None:
            exercise = grouped_exercises[st.session_state.selected_exercise_idx]
            idx = st.session_state.selected_exercise_idx
            
            st.markdown("---")
            
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
            
            # 選択された種目のタイトル
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #1a252f 0%, #2c3e50 50%, #34495e 100%);
                padding: 25px 20px;
                border-radius: 15px;
                margin: 25px 0 20px 0;
                box-shadow: 0 10px 30px rgba(44, 62, 80, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.1);
                position: relative;
                overflow: hidden;
            ">
                <div style="
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 3px;
                    background: linear-gradient(90deg, #3498db, #e74c3c, #f39c12);
                "></div>
                <h2 style="
                    color: #ECF0F1;
                    margin: 0;
                    font-size: 24px;
                    font-weight: 700;
                    text-align: center;
                    letter-spacing: 1px;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
                ">{exercise.get('No', '')} {exercise['Exercise']}</h2>
                <div style="
                    width: 50px;
                    height: 2px;
                    background: #ECF0F1;
                    margin: 15px auto 0 auto;
                    border-radius: 1px;
                "></div>
            </div>
            """, unsafe_allow_html=True)
            
            # Point表示（改善されたデザイン）
            if 'Point' in exercise and exercise['Point'] and pd.notna(exercise['Point']) and exercise['Point'] != '':
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, rgba(52, 152, 219, 0.1) 0%, rgba(155, 89, 182, 0.1) 100%);
                    border-left: 4px solid #3498db;
                    padding: 15px 20px;
                    margin: 15px 0 20px 0;
                    border-radius: 8px;
                    box-shadow: 0 4px 15px rgba(52, 152, 219, 0.1);
                ">
                    <div style="
                        display: flex;
                        align-items: center;
                        gap: 10px;
                    ">
                        <div>
                            <p style="
                                margin: 0;
                                color: #2C3E50;
                                font-weight: 600;
                                font-size: 14px;
                                line-height: 1.4;
                            ">
                                <span style="color: #3498db; font-weight: 700;">POINT:</span> {exercise['Point']}
                            </p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # プログラム情報を洗練されたデザインに
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, rgba(236, 240, 241, 0.8) 0%, rgba(189, 195, 199, 0.8) 100%);
                padding: 20px;
                border-radius: 12px;
                margin: 20px 0;
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 15px;
                text-align: center;
                box-shadow: 0 6px 20px rgba(44, 62, 80, 0.1);
                border: 1px solid rgba(44, 62, 80, 0.1);
            ">
                <div style="
                    background: rgba(255, 255, 255, 0.7);
                    padding: 15px 10px;
                    border-radius: 10px;
                    box-shadow: 0 2px 8px rgba(44, 62, 80, 0.1);
                ">
                    <div style="color: #7f8c8d; font-size: 11px; font-weight: 700; margin-bottom: 8px; letter-spacing: 1px;">SETS</div>
                    <div style="color: #2c3e50; font-size: 20px; font-weight: 800;">{exercise['set']}</div>
                </div>
                <div style="
                    background: rgba(255, 255, 255, 0.7);
                    padding: 15px 10px;
                    border-radius: 10px;
                    box-shadow: 0 2px 8px rgba(44, 62, 80, 0.1);
                ">
                    <div style="color: #7f8c8d; font-size: 11px; font-weight: 700; margin-bottom: 8px; letter-spacing: 1px;">LOAD</div>
                    <div style="color: #2c3e50; font-size: 20px; font-weight: 800;">{load_display}</div>
                </div>
                <div style="
                    background: rgba(255, 255, 255, 0.7);
                    padding: 15px 10px;
                    border-radius: 10px;
                    box-shadow: 0 2px 8px rgba(44, 62, 80, 0.1);
                ">
                    <div style="color: #7f8c8d; font-size: 11px; font-weight: 700; margin-bottom: 8px; letter-spacing: 1px;">REPS</div>
                    <div style="color: #2c3e50; font-size: 20px; font-weight: 800;">{exercise['rep']}</div>
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
        
        if not filtered_programs:
            st.warning(f"「{exercise_search}」に一致するエクササイズが見つかりません。")
            filtered_programs = list(available_programs) if "すべて" in selected_programs else selected_programs
    
    # 検索結果の表示
    if len(selected_programs) > 1 or (len(selected_programs) == 1 and "すべて" not in selected_programs) or exercise_search:
        st.markdown(f"**検索結果: {len(filtered_programs)}件**")
    
    # 検索結果に基づいてプログラムを表示
    for program in filtered_programs:
        with st.expander(f"PROGRAM {program}", expanded=len(filtered_programs) <= 3):
            program_exercises = program_df[program_df['Program'] == program]
            
            # ウォーミングアップ種目の表示
            warmup_exercises = program_exercises[program_exercises['No'] == 'WU'] if 'No' in program_exercises.columns else pd.DataFrame()
            
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
                    ">WARM UP</h4>
                </div>
                """, unsafe_allow_html=True)
                
                for _, warmup in warmup_exercises.iterrows():
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
                        st.markdown(f"• **{warmup['Exercise']}** - {detail_text}")
                    else:
                        st.markdown(f"• **{warmup['Exercise']}**")
                    
                    # ポイントがあれば表示
                    if 'Point' in warmup and pd.notna(warmup['Point']) and warmup['Point'] != '':
                        st.markdown(f"  POINT: {warmup['Point']}")
                
                st.markdown("---")
            
            # メイン種目の表示（WU以外）
            main_exercises = program_exercises[program_exercises['No'] != 'WU'] if 'No' in program_exercises.columns else program_exercises
            
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
        # エクササイズ別の詳細表示
        if 'エクササイズ' in filtered_df.columns:
            exercises = filtered_df['エクササイズ'].unique()
            
            for exercise in exercises:
                exercise_data = filtered_df[filtered_df['エクササイズ'] == exercise].sort_values('日付', ascending=False)
                
                # エクササイズ見出し
                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%);
                    color: white;
                    padding: 10px 15px;
                    border-radius: 8px;
                    margin: 15px 0 10px 0;
                ">
                    <h4 style="margin: 0; color: white;">{exercise} ({len(exercise_data)}回実施)</h4>
                </div>
                """, unsafe_allow_html=True)
                
                # 詳細データを表示（expanderは使わない）
                for idx, row in exercise_data.iterrows():
                    # 各記録の詳細
                    st.markdown(f"**{row['日付'].strftime('%Y/%m/%d')}** - {row['名前']}")
                    
                    col_log1, col_log2 = st.columns(2)
                    
                    with col_log1:
                        st.write(f"プログラム: {row.get('プログラム', '-')}")
                        st.write(f"実施セット: {row.get('実施セット', '-')}")
                        st.write(f"実施負荷: {row.get('実施負荷', '-')}")
                        st.write(f"実施レップ: {row.get('実施レップ', '-')}")
                    
                    with col_log2:
                        st.write(f"予定セット: {row.get('予定セット', '-')}")
                        st.write(f"予定負荷: {row.get('予定負荷', '-')}")
                        st.write(f"予定レップ: {row.get('予定レップ', '-')}")
                        if row.get('コメント', ''):
                            st.write(f"コメント: {row['コメント']}")
                    
                    st.markdown("---")
        
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
            st.success(f"✅ ファイル存在 ({len(log_df)}件のログ)")
            
            if st.button("ログファイルを削除", type="secondary"):
                os.remove(LOG_FILE)
                st.success("ログファイルを削除しました")
                st.rerun()
        else:
            st.info("📁 ログファイルなし")
    
    with col_file2:
        st.markdown("#### プログラムファイル")
        if os.path.exists(PROGRAM_FILE):
            program_df = load_program_file()
            st.success(f"✅ ファイル存在 ({len(program_df)}件のプログラム)")
            
            if st.button("プログラムファイルを削除", type="secondary"):
                os.remove(PROGRAM_FILE)
                st.success("プログラムファイルを削除しました")
                st.rerun()
        else:
            st.info("📁 プログラムファイルなし")
    
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
                "名前", "体重", "日付", "プログラム", "エクササイズ", 
                "予定セット", "予定負荷", "予定レップ", "実施セット", 
                "実施負荷", "実施レップ", "コメント", "ポイント"
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