import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="バスケットボール トレーニングシステム", layout="wide")

# Google Sheets認証
@st.cache_resource
def get_gsheet_client():
    try:
        credentials_dict = dict(st.secrets["gcp_service_account"])
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Google Sheets認証エラー: {e}")
        return None

def get_spreadsheet():
    client = get_gsheet_client()
    if client is None:
        return None, None
    try:
        spreadsheet_url = st.secrets["spreadsheet_url"]
        spreadsheet = client.open_by_url(spreadsheet_url)
        return spreadsheet, client
    except Exception as e:
        st.error(f"スプレッドシートオープンエラー: {e}")
        return None, None

# プログラムデータの読み込み
@st.cache_data(ttl=60)
def load_program_file():
    spreadsheet, _ = get_spreadsheet()
    if spreadsheet is None:
        return pd.DataFrame()
    try:
        worksheet = spreadsheet.worksheet("Programs")
        data = worksheet.get_all_values()
        if len(data) > 0:
            df = pd.DataFrame(data[1:], columns=data[0])
            # 列名を入れ替え: Category→Type、Type→Category
            if 'Type' not in df.columns:
                df['Type'] = ''
            if 'Category' not in df.columns:
                df['Category'] = 'U18'  # デフォルト値
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"プログラムデータ読み込みエラー: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=10)
def load_training_log():
    spreadsheet, _ = get_spreadsheet()
    if spreadsheet is None:
        return pd.DataFrame(columns=["日付", "プログラム名", "名前", "体重", "エクササイズ名", "カテゴリー", "set", "負荷", "回数", "総負荷量"])
    try:
        worksheet = spreadsheet.worksheet("TrainingLog")
        data = worksheet.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            if '日付' in df.columns:
                df['日付'] = pd.to_datetime(df['日付'], errors='coerce')
            if '回数' in df.columns:
                df['回数'] = pd.to_numeric(df['回数'], errors='coerce')
            if '総負荷量' in df.columns:
                df['総負荷量'] = pd.to_numeric(df['総負荷量'], errors='coerce')
            return df
        else:
            return pd.DataFrame(columns=["日付", "プログラム名", "名前", "体重", "エクササイズ名", "カテゴリー", "set", "負荷", "回数", "総負荷量"])
    except Exception as e:
        st.error(f"トレーニングログ読み込みエラー: {e}")
        return pd.DataFrame(columns=["日付", "プログラム名", "名前", "体重", "エクササイズ名", "カテゴリー", "set", "負荷", "回数", "総負荷量"])

def get_exercise_history(df, player_name, exercise_name, limit=5):
    if len(df) == 0 or not player_name or not exercise_name:
        return pd.DataFrame()
    filtered_df = df[(df['名前'] == player_name) & (df['エクササイズ名'] == exercise_name)].copy()
    if len(filtered_df) == 0:
        return pd.DataFrame()
    if '日付' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('日付', ascending=False)
    return filtered_df.head(limit)

def get_exercise_stats(history_df):
    if len(history_df) == 0:
        return None
    latest = history_df.iloc[0]
    stats = {
        'latest_date': latest.get('日付'),
        'latest_load': latest.get('負荷'),
        'latest_reps': latest.get('回数'),
        'latest_total_load': latest.get('総負荷量', 0),
        'avg_reps': history_df['回数'].mean() if '回数' in history_df.columns else 0,
        'max_load': history_df['総負荷量'].max() if '総負荷量' in history_df.columns else 0,
        'total_sessions': len(history_df['日付'].dt.date.unique()) if '日付' in history_df.columns else len(history_df),
        'total_sets': len(history_df)
    }
    return stats

def save_training_log_formatted(player_name, program_name, exercise_name, exercise_category, sets_data, body_weight=None, date=None):
    if date is None:
        date = datetime.today().date()
    spreadsheet, _ = get_spreadsheet()
    if spreadsheet is None:
        st.error("Google Sheetsに接続できません")
        return 0
    try:
        worksheet = spreadsheet.worksheet("TrainingLog")
    except:
        worksheet = spreadsheet.add_worksheet(title="TrainingLog", rows="1000", cols="10")
        worksheet.append_row(["日付", "プログラム名", "名前", "体重", "エクササイズ名", "カテゴリー", "set", "負荷", "回数", "総負荷量"])
    
    new_rows = []
    for set_data in sets_data:
        load_value = set_data['load']
        reps = set_data['reps']
        load_numeric = 0
        if isinstance(load_value, str):
            if 'kg' in load_value:
                try:
                    load_numeric = float(load_value.replace('kg', ''))
                except:
                    load_numeric = 0
            elif load_value == "体重":
                load_numeric = body_weight if body_weight else 0
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
        total_load = load_numeric * reps
        new_row = [str(date), program_name, player_name, str(body_weight) if body_weight else '', exercise_name, exercise_category, str(set_data['set_number']), str(load_value), str(reps), str(total_load)]
        new_rows.append(new_row)
    try:
        worksheet.append_rows(new_rows)
        st.cache_data.clear()
        return len(new_rows)
    except Exception as e:
        st.error(f"保存エラー: {e}")
        return 0

def get_category_display(category):
    if not category or category == '' or pd.isna(category):
        return ""
    category_colors = {
        'Upper': {'color': '#e74c3c', 'icon': '💪'},
        'Lower': {'color': '#3498db', 'icon': '🦵'},
        'Power': {'color': '#f39c12', 'icon': '⚡'},
        'Core': {'color': '#27ae60', 'icon': '🎯'}
    }
    if category in category_colors:
        color = category_colors[category]['color']
        icon = category_colors[category]['icon']
        return f'<span style="color: {color}; font-weight: 600;">{icon} {category}</span>'
    else:
        return f'<span style="color: #7f8c8d;">{category}</span>'

# Type選択をセッション状態で管理
if 'selected_type' not in st.session_state:
    st.session_state.selected_type = None

# サイドバーでページ選択
st.sidebar.title("メニュー")

# Type選択がまだの場合は選択画面を表示
if st.session_state.selected_type is None:
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%);
        padding: 20px;
        border-radius: 12px;
        margin: 30px 0;
        text-align: center;
        box-shadow: 0 6px 20px rgba(44, 62, 80, 0.25);
    ">
        <h1 style="
            color: #ECF0F1;
            margin: 0;
            font-size: 32px;
            font-weight: 600;
            letter-spacing: 1px;
        ">Basketball Training System</h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
    
    # 縦に並べる（色を変更）
    st.markdown("""
    <style>
    div.stButton > button {
        background-color: #2C3E50;
        color: white;
        border: none;
        padding: 15px;
        font-size: 18px;
        font-weight: 600;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #34495E;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(44, 62, 80, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("U18", use_container_width=True, key="btn_u18"):
        st.session_state.selected_type = "U18"
        st.rerun()
    
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    if st.button("U15", use_container_width=True, key="btn_u15"):
        st.session_state.selected_type = "U15"
        st.rerun()
    
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    if st.button("Personal", use_container_width=True, key="btn_personal"):
        st.session_state.selected_type = "Personal"
        st.rerun()
    
    st.stop()

# Type選択済みの場合、サイドバーに表示とリセットボタン
st.sidebar.markdown(f"### 選択中: **{st.session_state.selected_type}**")
if st.sidebar.button("タイプ変更"):
    st.session_state.selected_type = None
    st.rerun()

page = st.sidebar.selectbox("ページを選択", ["プログラム一覧", "Training Log 入力", "データ管理"])

if page == "Training Log 入力":
    st.title("Training Log 入力")
    program_df = load_program_file()
    if len(program_df) == 0:
        st.error("プログラムデータを読み込めませんでした。")
        st.stop()
    
    # 選択されたCategoryでフィルタリング
    program_df = program_df[program_df['Category'] == st.session_state.selected_type]
    if len(program_df) == 0:
        st.warning(f"{st.session_state.selected_type}のプログラムが見つかりません。")
        st.stop()
    
    st.markdown(f"""<div style="background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%); padding: 15px 20px; border-radius: 12px; margin: 15px 0; text-align: center; box-shadow: 0 6px 20px rgba(44, 62, 80, 0.25);"><h2 style="color: #ECF0F1; margin: 0; font-size: 24px; font-weight: 600;">TRAINING LOG INPUT</h2><p style="color: #BDC3C7; margin: 8px 0 0 0; font-size: 14px;">トレーニング記録を入力 - {st.session_state.selected_type}</p></div>""", unsafe_allow_html=True)
    
    player_name = st.text_input("選手名", key="player_name", placeholder="例: 田中太郎")
    body_weight = st.number_input("体重 (kg)", min_value=30.0, max_value=200.0, value=70.0, step=0.1, key="body_weight")
    
    available_programs = program_df['Program'].unique()
    st.markdown("### プログラム選択")
    selected_program = st.selectbox("実行するプログラム", available_programs, help="エクセルで設定されたトレーニングプログラムから選択")
    
    if selected_program:
        program_exercises = program_df[program_df['Program'] == selected_program].reset_index(drop=True)
        main_exercises = program_exercises[~program_exercises['No'].isin(['WU', 'ST', 'PL'])] if 'No' in program_exercises.columns else program_exercises
        
        grouped_exercises = []
        seen_exercises = set()
        for _, exercise in main_exercises.iterrows():
            exercise_name = exercise['Exercise']
            if exercise_name not in seen_exercises:
                same_exercises = main_exercises[main_exercises['Exercise'] == exercise_name]
                grouped_exercise = {
                    'Exercise': exercise_name,
                    'No': same_exercises['No'].iloc[0] if 'No' in same_exercises.columns else '',
                    'set': '・'.join(map(str, same_exercises['set'])),
                    'load': '・'.join(map(str, same_exercises['load'])),
                    'rep': '・'.join(map(str, same_exercises['rep'])),
                    'Type': same_exercises['Type'].iloc[0] if 'Type' in same_exercises.columns else ''
                }
                if 'Point' in same_exercises.columns:
                    grouped_exercise['Point'] = same_exercises['Point'].iloc[0]
                grouped_exercises.append(grouped_exercise)
                seen_exercises.add(exercise_name)
        
        st.markdown(f"### プログラム {selected_program}")
        
        warmup_exercises = program_exercises[program_exercises['No'].isin(['WU', 'ST', 'PL'])] if 'No' in program_exercises.columns else pd.DataFrame()
        if len(warmup_exercises) > 0:
            st.markdown("#### ウォーミングアップ・補助種目")
            for _, warmup in warmup_exercises.iterrows():
                exercise_type = "WU " if warmup['No'] == 'WU' else "ST " if warmup['No'] == 'ST' else "PL "
                warmup_details = []
                if pd.notna(warmup['set']) and warmup['set'] != '-':
                    warmup_details.append(f"{warmup['set']}セット")
                if pd.notna(warmup['rep']) and warmup['rep'] != '-':
                    warmup_details.append(f"{warmup['rep']}レップ")
                if pd.notna(warmup['load']) and warmup['load'] != '-':
                    load_display = warmup['load']
                    if str(load_display).replace('.', '').isdigit() and float(load_display) <= 1.0:
                        load_display = f"{float(load_display)*100:.0f}%"
                    warmup_details.append(f"{load_display}")
                detail_text = " / ".join(warmup_details) if warmup_details else ""
                type_display = ""
                if 'Type' in warmup.index and pd.notna(warmup['Type']) and warmup['Type'] != '':
                    type_display = f" {get_category_display(warmup['Type'])}"
                if detail_text:
                    st.markdown(f"• {exercise_type}**{warmup['Exercise']}**{type_display} - {detail_text}", unsafe_allow_html=True)
                else:
                    st.markdown(f"• {exercise_type}**{warmup['Exercise']}**{type_display}", unsafe_allow_html=True)
                if 'Point' in warmup and pd.notna(warmup['Point']) and warmup['Point'] != '':
                    st.markdown(f"  POINT: {warmup['Point']}")
            st.markdown("---")
        
        st.markdown("""<div style="margin: 20px 0 15px 0; padding: 12px 0; border-bottom: 2px solid #34495E;"><h4 style="color: #2C3E50; margin: 0; font-size: 18px; font-weight: 600;">EXERCISES</h4></div>""", unsafe_allow_html=True)
        
        if 'selected_exercise_idx' not in st.session_state:
            st.session_state.selected_exercise_idx = None
        
        st.markdown("""<div style="background: rgba(44, 62, 80, 0.03); padding: 15px; border-radius: 10px; margin: 15px 0;"><p style="color: #34495E; margin: 0; font-size: 14px; font-weight: 500; text-align: center;">実施する種目を選択してください</p></div>""", unsafe_allow_html=True)
        
        for idx, exercise in enumerate(grouped_exercises):
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
            
            is_selected = st.session_state.selected_exercise_idx == idx
            button_type = "primary" if is_selected else "secondary"
            type_display = ""
            if exercise.get('Type') and exercise['Type'] != '':
                type_display = f" | {exercise['Type']}"
            exercise_name = f"{exercise.get('No', '')} {exercise['Exercise']}{type_display}"
            exercise_details = f"{exercise['set']}set | {load_display} | {exercise['rep']}rep"
            button_text = f"**{exercise_name}**\n{exercise_details}"
            
            if st.button(button_text, key=f"exercise_select_{idx}", use_container_width=True, type=button_type):
                if st.session_state.selected_exercise_idx == idx:
                    st.session_state.selected_exercise_idx = None
                else:
                    st.session_state.selected_exercise_idx = idx
                st.rerun()
            
            if st.session_state.selected_exercise_idx == idx:
                exercise_title = f"{exercise.get('No', '')} {exercise['Exercise']}"
                with st.expander(f"記録入力: {exercise_title}", expanded=True):
                    if exercise.get('Type') and exercise['Type'] != '':
                        st.markdown(f"""<div style="background: linear-gradient(135deg, rgba(108, 117, 125, 0.1) 0%, rgba(73, 80, 87, 0.1) 100%); border-left: 4px solid #6c757d; padding: 8px 12px; margin: 8px 0; border-radius: 6px; text-align: center;"><div style="color: #495057; font-weight: 600; font-size: 14px;">Type: {get_category_display(exercise['Type'])}</div></div>""", unsafe_allow_html=True)
                    
                    log_df = load_training_log()
                    if len(log_df) > 0 and player_name:
                        exercise_history = get_exercise_history(log_df, player_name, exercise['Exercise'], limit=5)
                        if len(exercise_history) > 0:
                            stats = get_exercise_stats(exercise_history)
                            if stats:
                                latest_date_str = pd.to_datetime(stats['latest_date']).strftime('%m/%d') if pd.notna(stats['latest_date']) else '-'
                                st.markdown(f"""<div style="background: linear-gradient(135deg, rgba(25, 118, 210, 0.1) 0%, rgba(21, 101, 192, 0.1) 100%); border: 2px solid rgba(25, 118, 210, 0.3); border-radius: 12px; padding: 16px; margin: 12px 0;"><h5 style="color: #1976d2; margin: 0; font-size: 16px; font-weight: 700;">📈 前回のトレーニング ({latest_date_str})</h5></div>""", unsafe_allow_html=True)
                        else:
                            st.markdown("""<div style="background: linear-gradient(135deg, rgba(96, 125, 139, 0.1) 0%, rgba(120, 144, 156, 0.1) 100%); border: 2px dashed rgba(96, 125, 139, 0.3); border-radius: 8px; padding: 16px; margin: 12px 0; text-align: center;"><div style="color: #607d8b; font-size: 16px; font-weight: 600;">🌟 初回トレーニング</div></div>""", unsafe_allow_html=True)
                    elif not player_name:
                        st.markdown("""<div style="background: rgba(255, 193, 7, 0.1); border: 2px solid rgba(255, 193, 7, 0.3); border-radius: 8px; padding: 12px; margin: 12px 0; text-align: center;"><div style="color: #f57c00; font-size: 14px; font-weight: 600;">⚠️ 選手名を入力すると前回のデータが表示されます</div></div>""", unsafe_allow_html=True)
                    
                    if 'Point' in exercise and exercise['Point'] and pd.notna(exercise['Point']) and exercise['Point'] != '':
                        st.markdown(f"""<div style="background: linear-gradient(135deg, rgba(108, 117, 125, 0.1) 0%, rgba(73, 80, 87, 0.1) 100%); border-left: 4px solid #6c757d; padding: 10px 15px; margin: 10px 0 15px 0; border-radius: 6px;"><p style="margin: 0; color: #495057; font-weight: 600; font-size: 13px;"><span style="color: #6c757d; font-weight: 700;">POINT:</span> {exercise['Point']}</p></div>""", unsafe_allow_html=True)
                    
                    total_sets = sum([int(s) for s in exercise['set'].split('・')])
                    actual_sets = st.number_input("実施セット数", min_value=1, value=total_sets, key=f"sets_{idx}", help=f"予定: {exercise['set']}")
                    
                    st.markdown("**記録入力:**")
                    
                    # 全適用トリガーの処理（ウィジェット作成前に実行）
                    apply_trigger_key = f"apply_trigger_{idx}"
                    if apply_trigger_key in st.session_state and st.session_state[apply_trigger_key]:
                        # SET1の値を取得
                        set1_unit = st.session_state.get(f"unit_{idx}_0", "kg")
                        set1_rep = st.session_state.get(f"rep_{idx}_0", 1)
                        
                        # 負荷の値を取得（単位によって異なるキーを使用）
                        if set1_unit == "その他":
                            set1_load_text = st.session_state.get(f"load_{idx}_0", "")
                        elif set1_unit == "体重":
                            set1_load_text = "体重"
                        else:
                            set1_load_val = st.session_state.get(f"load_val_{idx}_0", 0.0)
                        
                        # SET2以降に値を設定
                        for set_num in range(1, actual_sets):
                            st.session_state[f"unit_{idx}_{set_num}"] = set1_unit
                            st.session_state[f"rep_{idx}_{set_num}"] = set1_rep
                            
                            if set1_unit == "その他":
                                st.session_state[f"load_{idx}_{set_num}"] = set1_load_text
                            elif set1_unit != "体重":
                                st.session_state[f"load_val_{idx}_{set_num}"] = set1_load_val
                        
                        # トリガーをリセット
                        st.session_state[apply_trigger_key] = False
                    
                    loads = []
                    reps = []
                    
                    for set_num in range(actual_sets):
                        st.markdown(f"""<div style="background: linear-gradient(135deg, rgba(52, 73, 94, 0.1) 0%, rgba(44, 62, 80, 0.1) 100%); border-left: 3px solid #34495e; padding: 6px 10px; margin: 8px 0 4px 0; border-radius: 4px;"><span style="color: #2c3e50; font-weight: 600; font-size: 13px;">SET {set_num + 1}</span></div>""", unsafe_allow_html=True)
                        
                        col1, col2, col3, col4 = st.columns([1, 1, 1, 0.7])
                        
                        with col1:
                            unit = st.selectbox(
                                "単位",
                                ["kg", "%", "体重", "その他"],
                                key=f"unit_{idx}_{set_num}",
                                label_visibility="collapsed"
                            )
                        
                        with col2:
                            if unit == "その他":
                                set_load = st.text_input(
                                    "負荷",
                                    key=f"load_{idx}_{set_num}",
                                    placeholder="負荷",
                                    label_visibility="collapsed"
                                )
                            elif unit == "体重":
                                set_load = "体重"
                                st.text_input("負荷", value="体重", disabled=True, key=f"load_disabled_{idx}_{set_num}", label_visibility="collapsed")
                            else:
                                load_value = st.number_input(
                                    "値",
                                    min_value=0.0,
                                    step=0.1 if unit == "%" else 0.5,
                                    key=f"load_val_{idx}_{set_num}",
                                    label_visibility="collapsed"
                                )
                                set_load = f"{load_value}{unit}"
                            
                            loads.append(set_load)
                        
                        with col3:
                            set_rep = st.number_input(
                                "レップ数",
                                min_value=0,
                                key=f"rep_{idx}_{set_num}",
                                label_visibility="collapsed"
                            )
                            reps.append(set_rep)
                        
                        with col4:
                            if set_num == 0 and actual_sets > 1:
                                if st.button("全適用", key=f"copy_all_{idx}", help="この設定を全セットに適用"):
                                    st.session_state[apply_trigger_key] = True
                                    st.rerun()
                            else:
                                st.write("")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(f"{exercise['Exercise']} 完了", key=f"complete_{idx}", type="primary", use_container_width=True):
                            if not player_name:
                                st.error("選手名を入力してください")
                            else:
                                sets_data = []
                                for set_num in range(actual_sets):
                                    sets_data.append({'set_number': set_num + 1, 'load': loads[set_num], 'reps': reps[set_num]})
                                exercise_type = exercise.get('Type', '')
                                with st.spinner('保存中...'):
                                    saved_sets = save_training_log_formatted(player_name=player_name, program_name=selected_program, exercise_name=exercise['Exercise'], exercise_category=exercise_type, sets_data=sets_data, body_weight=body_weight)
                                if saved_sets > 0:
                                    st.success(f"✅ {exercise['Exercise']} 完了！{saved_sets}セットのデータを保存しました。")
                                    # セッション状態のクリーンアップ
                                    if apply_trigger_key in st.session_state:
                                        del st.session_state[apply_trigger_key]
                                    st.session_state.selected_exercise_idx = None
                                    st.rerun()
                    with col_btn2:
                        if st.button("種目選択に戻る", key=f"back_{idx}", use_container_width=True):
                            # セッション状態のクリーンアップ
                            if apply_trigger_key in st.session_state:
                                del st.session_state[apply_trigger_key]
                            st.session_state.selected_exercise_idx = None
                            st.rerun()
        
        if st.session_state.selected_exercise_idx is None:
            st.markdown("---")
            if 'program_completed' not in st.session_state:
                st.session_state.program_completed = False
            if st.button("全プログラム完了", type="primary", use_container_width=True):
                st.session_state.program_completed = True
                # セッション状態をクリア
                for key in list(st.session_state.keys()):
                    if key.startswith(('copy_', 'sets_', 'unit_', 'load_', 'rep_', 'comment_')):
                        del st.session_state[key]
                st.rerun()
            if st.session_state.program_completed:
                st.markdown("---")
                st.success("🎉 お疲れ様でした！全プログラムが完了しました！")
                if st.button("新しいトレーニングを開始", type="secondary", use_container_width=True):
                    st.session_state.program_completed = False
                    st.rerun()

elif page == "データ管理":
    st.title("データ管理")
    st.markdown("### Google Sheets連携状態")
    
    spreadsheet, client = get_spreadsheet()
    if spreadsheet:
        st.success(f"✅ 接続成功: {spreadsheet.title}")
        
        st.markdown("### データダウンロード")
        log_df = load_training_log()
        if len(log_df) > 0:
            csv = log_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("📥 トレーニングログをCSVダウンロード", csv, f"training_log_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv")
        else:
            st.info("ダウンロード可能なデータがありません")
        
        st.markdown("---")
        st.markdown("### データ統計")
        if len(log_df) > 0:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("総ログ数", len(log_df))
            with col2:
                unique_players = log_df['名前'].nunique() if '名前' in log_df.columns else 0
                st.metric("登録選手数", unique_players)
            with col3:
                if '日付' in log_df.columns:
                    log_df['日付'] = pd.to_datetime(log_df['日付'])
                    latest_date = log_df['日付'].max().strftime('%Y/%m/%d')
                    st.metric("最新記録日", latest_date)
            with col4:
                if 'カテゴリー' in log_df.columns:
                    unique_categories = len([cat for cat in log_df['カテゴリー'].unique() if cat != '' and pd.notna(cat)])
                    st.metric("カテゴリー数", unique_categories)
            
            if '名前' in log_df.columns:
                st.markdown("#### 選手別ログ数")
                player_counts = log_df['名前'].value_counts()
                st.bar_chart(player_counts)
            
            if 'カテゴリー' in log_df.columns:
                st.markdown("#### カテゴリー別ログ数")
                category_counts = log_df[log_df['カテゴリー'] != '']['カテゴリー'].value_counts()
                if len(category_counts) > 0:
                    st.bar_chart(category_counts)
        
        st.markdown("---")
        st.markdown("### Google Sheetsリンク")
        if st.button("📊 Google Sheetsを開く"):
            st.markdown(f"[Google Sheetsで開く]({st.secrets['spreadsheet_url']})")
    else:
        st.error("❌ Google Sheetsに接続できません。設定を確認してください。")
    
    st.markdown("---")
    st.markdown("### システム情報")
    st.info("""**バスケットボール トレーニングシステム v2.1 (Type選択機能付き)**
    
- ☁️ Google Sheets連携でデータ永続化
- 🎯 Type選択機能 (U18/U15/Personal)
- 📊 リアルタイムデータ同期
- 🏷️ カテゴリー機能 (Upper/Lower/Power/Core)
- ⚖️ 体重データ記録・管理
- 📥 CSVダウンロード機能
- 👥 複数人同時使用対応

**注意事項:**
- データはGoogle Sheetsに保存されます
- 再起動してもデータは保持されます
- 複数人が同時に使用できます""")

elif page == "プログラム一覧":
    st.title("プログラム一覧")
    program_df = load_program_file()
    if len(program_df) == 0:
        st.error("プログラムデータを読み込めませんでした。")
        st.stop()
    
    # 選択されたCategoryでフィルタリング
    program_df = program_df[program_df['Category'] == st.session_state.selected_type]
    
    st.markdown(f"### {st.session_state.selected_type} プログラム一覧")
    
    available_programs = program_df['Program'].unique()
    st.markdown("### プログラム検索")
    col_search1, col_search2, col_search3 = st.columns(3)
    with col_search1:
        selected_programs = st.multiselect("プログラムを選択", ["すべて"] + list(available_programs), default=["すべて"], help="複数選択可能")
    with col_search2:
        exercise_search = st.text_input("エクササイズ名で検索", placeholder="例: Squat, Bench")
    with col_search3:
        available_types = ["すべて"] + [cat for cat in program_df['Type'].unique() if cat != '' and pd.notna(cat)]
        selected_type_filter = st.selectbox("Typeで絞り込み", available_types)
    
    if "すべて" not in selected_programs and selected_programs:
        filtered_programs = selected_programs
    else:
        filtered_programs = list(available_programs)
    if exercise_search:
        exercise_matches = program_df[program_df['Exercise'].str.contains(exercise_search, case=False, na=False)]['Program'].unique()
        filtered_programs = [prog for prog in filtered_programs if prog in exercise_matches]
    if selected_type_filter != "すべて":
        type_matches = program_df[program_df['Type'] == selected_type_filter]['Program'].unique()
        filtered_programs = [prog for prog in filtered_programs if prog in type_matches]
    
    if len(selected_programs) > 1 or (len(selected_programs) == 1 and "すべて" not in selected_programs) or exercise_search or selected_type_filter != "すべて":
        st.markdown(f"**検索結果: {len(filtered_programs)}件**")
    
    for program in filtered_programs:
        with st.expander(f"{program}", expanded=len(filtered_programs) <= 3):
            program_exercises = program_df[program_df['Program'] == program]
            warmup_exercises = program_exercises[program_exercises['No'].isin(['WU', 'ST', 'PL'])] if 'No' in program_exercises.columns else pd.DataFrame()
            if len(warmup_exercises) > 0:
                st.markdown("""<div style="background: rgba(108, 117, 125, 0.08); border-left: 3px solid #6c757d; padding: 8px 12px; margin: 10px 0; border-radius: 6px;"><h4 style="color: #495057; margin: 0; font-size: 14px; font-weight: 600;">WARM UP & AUXILIARY</h4></div>""", unsafe_allow_html=True)
                for _, warmup in warmup_exercises.iterrows():
                    exercise_type = "WU " if warmup['No'] == 'WU' else "ST " if warmup['No'] == 'ST' else "PL "
                    st.markdown(f"• {exercise_type}**{warmup['Exercise']}**")
                st.markdown("---")
            
            main_exercises = program_exercises[~program_exercises['No'].isin(['WU', 'ST', 'PL'])] if 'No' in program_exercises.columns else program_exercises
            if len(main_exercises) > 0:
                st.markdown("""<div style="background: rgba(73, 80, 87, 0.08); border-left: 3px solid #495057; padding: 8px 12px; margin: 10px 0; border-radius: 6px;"><h4 style="color: #495057; margin: 0; font-size: 14px; font-weight: 600;">MAIN EXERCISES</h4></div>""", unsafe_allow_html=True)
                display_df = main_exercises[['No', 'Exercise', 'Type', 'set', 'load', 'rep']].copy()
                display_df.columns = ['No.', 'エクササイズ', 'Type', 'セット数', '負荷', 'レップ数']
                for col in display_df.columns:
                    display_df[col] = display_df[col].astype(str)
                display_df.index = range(1, len(display_df) + 1)
                st.dataframe(display_df, use_container_width=True)

else:
    st.error("無効なページが選択されました。")