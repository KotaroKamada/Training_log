import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

st.set_page_config(page_title="バスケットボール トレーニングシステム", layout="wide")

# Google Sheets認証
@st.cache_resource
def get_gsheet_client():
    try:
        # Streamlit Secretsから認証情報を取得
        credentials_dict = dict(st.secrets["gcp_service_account"])
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"Google Sheets認証エラー: {e}")
        return None

# スプレッドシートを開く
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
            if 'Category' not in df.columns:
                df['Category'] = ''
            return df
        else:
            return pd.DataFrame()
    except Exception as e:
        st.error(f"プログラムデータ読み込みエラー: {e}")
        return pd.DataFrame()

# トレーニングログの読み込み
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
            # データ型変換
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

# Google Sheetsへの保存
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
        # TrainingLogシートが存在しない場合は作成
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
        
        new_row = [
            str(date),
            program_name,
            player_name,
            str(body_weight) if body_weight else '',
            exercise_name,
            exercise_category,
            str(set_data['set_number']),
            str(load_value),
            str(reps),
            str(total_load)
        ]
        new_rows.append(new_row)
    
    try:
        worksheet.append_rows(new_rows)
        st.cache_data.clear()  # キャッシュをクリア
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

# サイドバーでページ選択
st.sidebar.title("メニュー")
page = st.sidebar.selectbox("ページを選択", ["プログラム一覧", "Training Log 入力", "データ管理"])

if page == "Training Log 入力":
    st.title("Training Log 入力")
    program_df = load_program_file()
    if len(program_df) == 0:
        st.error("プログラムデータを読み込めませんでした。")
        st.stop()
    
    st.markdown("""<div style="background: linear-gradient(135deg, #2C3E50 0%, #34495E 100%); padding: 15px 20px; border-radius: 12px; margin: 15px 0; text-align: center; box-shadow: 0 6px 20px rgba(44, 62, 80, 0.25); border: 1px solid rgba(255, 255, 255, 0.1);"><h2 style="color: #ECF0F1; margin: 0; font-size: 24px; font-weight: 600; text-shadow: 0 2px 4px rgba(0,0,0,0.3); letter-spacing: 0.8px;">TRAINING LOG INPUT</h2><p style="color: #BDC3C7; margin: 8px 0 0 0; font-size: 14px; font-weight: 300;">トレーニング記録を入力</p></div>""", unsafe_allow_html=True)
    
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
                    'Category': same_exercises['Category'].iloc[0] if 'Category' in same_exercises.columns else ''
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
                category_display = ""
                if 'Category' in warmup.index and pd.notna(warmup['Category']) and warmup['Category'] != '':
                    category_display = f" {get_category_display(warmup['Category'])}"
                if detail_text:
                    st.markdown(f"• {exercise_type}**{warmup['Exercise']}**{category_display} - {detail_text}", unsafe_allow_html=True)
                else:
                    st.markdown(f"• {exercise_type}**{warmup['Exercise']}**{category_display}", unsafe_allow_html=True)
                if 'Point' in warmup and pd.notna(warmup['Point']) and warmup['Point'] != '':
                    st.markdown(f"  POINT: {warmup['Point']}")
            st.markdown("---")
        
        st.markdown("""<div style="margin: 20px 0 15px 0; padding: 12px 0; border-bottom: 2px solid #34495E;"><h4 style="color: #2C3E50; margin: 0; font-size: 18px; font-weight: 600; letter-spacing: 1px;">EXERCISES</h4></div>""", unsafe_allow_html=True)
        
        if 'selected_exercise_idx' not in st.session_state:
            st.session_state.selected_exercise_idx = None
        
        st.markdown("""<div style="background: rgba(44, 62, 80, 0.03); padding: 15px; border-radius: 10px; margin: 15px 0; border: 1px solid rgba(44, 62, 80, 0.1);"><p style="color: #34495E; margin: 0; font-size: 14px; font-weight: 500; text-align: center;">実施する種目を選択してください</p></div>""", unsafe_allow_html=True)
        
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
            category_display = ""
            if exercise.get('Category') and exercise['Category'] != '':
                category_display = f" | {exercise['Category']}"
            exercise_name = f"{exercise.get('No', '')} {exercise['Exercise']}{category_display}"
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
                    if exercise.get('Category') and exercise['Category'] != '':
                        st.markdown(f"""<div style="background: linear-gradient(135deg, rgba(108, 117, 125, 0.1) 0%, rgba(73, 80, 87, 0.1) 100%); border-left: 4px solid #6c757d; padding: 8px 12px; margin: 8px 0; border-radius: 6px; text-align: center;"><div style="color: #495057; font-weight: 600; font-size: 14px;">Category: {get_category_display(exercise['Category'])}</div></div>""", unsafe_allow_html=True)
                    
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
                    loads = []
                    reps = []
                    
                    for set_num in range(actual_sets):
                        st.markdown(f"""<div style="background: linear-gradient(135deg, rgba(52, 73, 94, 0.1) 0%, rgba(44, 62, 80, 0.1) 100%); border-left: 3px solid #34495e; padding: 6px 10px; margin: 8px 0 4px 0; border-radius: 4px;"><span style="color: #2c3e50; font-weight: 600; font-size: 13px;">SET {set_num + 1}</span></div>""", unsafe_allow_html=True)
                        
                        col1, col2, col3, col4 = st.columns([1, 1, 1, 0.7])
                        
                        with col1:
                            unit_default = 0
                            if set_num > 0 and f"copy_unit_{idx}" in st.session_state:
                                units = ["kg", "%", "体重", "その他"]
                                saved_unit = st.session_state[f"copy_unit_{idx}"]
                                if saved_unit in units:
                                    unit_default = units.index(saved_unit)
                            unit = st.selectbox("単位", ["kg", "%", "体重", "その他"], index=unit_default, key=f"unit_{idx}_{set_num}", label_visibility="collapsed")
                        
                        with col2:
                            if unit == "その他":
                                load_default = ""
                                if set_num > 0 and f"copy_load_text_{idx}" in st.session_state:
                                    load_default = st.session_state[f"copy_load_text_{idx}"]
                                set_load = st.text_input("負荷", value=load_default, key=f"load_{idx}_{set_num}", placeholder="負荷", label_visibility="collapsed")
                            elif unit == "体重":
                                set_load = "体重"
                                st.text_input("負荷", value="体重", disabled=True, key=f"load_disabled_{idx}_{set_num}", label_visibility="collapsed")
                            else:
                                load_default = 0.0
                                if set_num > 0 and f"copy_load_val_{idx}" in st.session_state:
                                    load_default = st.session_state[f"copy_load_val_{idx}"]
                                load_value = st.number_input("値", min_value=0.0, value=load_default, step=0.1 if unit == "%" else 0.5, key=f"load_val_{idx}_{set_num}", label_visibility="collapsed")
                                set_load = f"{load_value}{unit}"
                            loads.append(set_load)
                        
                        with col3:
                            rep_default = 1
                            if set_num > 0 and f"copy_rep_{idx}" in st.session_state:
                                rep_default = st.session_state[f"copy_rep_{idx}"]
                            set_rep = st.number_input("レップ数", min_value=0, value=rep_default, key=f"rep_{idx}_{set_num}", label_visibility="collapsed")
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
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button(f"{exercise['Exercise']} 完了", key=f"complete_{idx}", type="primary", use_container_width=True):
                            if not player_name:
                                st.error("選手名を入力してください")
                            else:
                                sets_data = []
                                for set_num in range(actual_sets):
                                    sets_data.append({'set_number': set_num + 1, 'load': loads[set_num], 'reps': reps[set_num]})
                                exercise_category = exercise.get('Category', '')
                                with st.spinner('保存中...'):
                                    saved_sets = save_training_log_formatted(player_name=player_name, program_name=selected_program, exercise_name=exercise['Exercise'], exercise_category=exercise_category, sets_data=sets_data, body_weight=body_weight)
                                if saved_sets > 0:
                                    st.success(f"✅ {exercise['Exercise']} 完了！{saved_sets}セットのデータを保存しました。")
                                    for key in [f"copy_unit_{idx}", f"copy_rep_{idx}", f"copy_load_text_{idx}", f"copy_load_val_{idx}"]:
                                        if key in st.session_state:
                                            del st.session_state[key]
                                    st.session_state.selected_exercise_idx = None
                                    st.rerun()
                    with col_btn2:
                        if st.button("種目選択に戻る", key=f"back_{idx}", use_container_width=True):
                            for key in [f"copy_unit_{idx}", f"copy_rep_{idx}", f"copy_load_text_{idx}", f"copy_load_val_{idx}"]:
                                if key in st.session_state:
                                    del st.session_state[key]
                            st.session_state.selected_exercise_idx = None
                            st.rerun()
        
        if st.session_state.selected_exercise_idx is None:
            st.markdown("---")
            if 'program_completed' not in st.session_state:
                st.session_state.program_completed = False
            if st.button("全プログラム完了", type="primary", use_container_width=True):
                st.session_state.program_completed = True
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
    st.info("""**バスケットボール トレーニングシステム v2.0 (Google Sheets連携版)**
    
- ☁️ Google Sheets連携でデータ永続化
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
    
    available_programs = program_df['Program'].unique()
    st.markdown("### プログラム検索")
    col_search1, col_search2, col_search3 = st.columns(3)
    with col_search1:
        selected_programs = st.multiselect("プログラムを選択", ["すべて"] + list(available_programs), default=["すべて"], help="複数選択可能")
    with col_search2:
        exercise_search = st.text_input("エクササイズ名で検索", placeholder="例: Squat, Bench")
    with col_search3:
        available_categories = ["すべて"] + [cat for cat in program_df['Category'].unique() if cat != '' and pd.notna(cat)]
        selected_category = st.selectbox("カテゴリーで絞り込み", available_categories)
    
    if "すべて" not in selected_programs and selected_programs:
        filtered_programs = selected_programs
    else:
        filtered_programs = list(available_programs)
    if exercise_search:
        exercise_matches = program_df[program_df['Exercise'].str.contains(exercise_search, case=False, na=False)]['Program'].unique()
        filtered_programs = [prog for prog in filtered_programs if prog in exercise_matches]
    if selected_category != "すべて":
        category_matches = program_df[program_df['Category'] == selected_category]['Program'].unique()
        filtered_programs = [prog for prog in filtered_programs if prog in category_matches]
    
    if len(selected_programs) > 1 or (len(selected_programs) == 1 and "すべて" not in selected_programs) or exercise_search or selected_category != "すべて":
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
                display_df = main_exercises[['No', 'Exercise', 'Category', 'set', 'load', 'rep']].copy()
                display_df.columns = ['No.', 'エクササイズ', 'カテゴリー', 'セット数', '負荷', 'レップ数']
                for col in display_df.columns:
                    display_df[col] = display_df[col].astype(str)
                display_df.index = range(1, len(display_df) + 1)
                st.dataframe(display_df, use_container_width=True)

else:
    st.error("無効なページが選択されました。")