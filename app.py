import streamlit as st
import pandas as pd
from openpyxl import load_workbook
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="バスケットボール トレーニングシステム", layout="wide")

# サイドバーでページ選択
st.sidebar.title("メニュー")
page = st.sidebar.selectbox("ページを選択", ["プログラム一覧", "Training Log 入力", "データ管理"])

# エクセルファイルのパス
LOG_FILE = "training_log.xlsx"
PROGRAM_FILE = "training_program.xlsx"

# プログラムファイルの読み込み
def load_program_file():
    try:
        if os.path.exists(PROGRAM_FILE):
            df = pd.read_excel(PROGRAM_FILE)
            df.columns = df.columns.str.strip()
            expected_columns = ['Program', 'No', 'Exercise', 'set', 'load', 'rep', 'Point', 'Category']
            if len(df.columns) >= 7:
                df.columns = expected_columns[:len(df.columns)]
            if 'Category' not in df.columns:
                df['Category'] = ''
            return df
        else:
            sample_df = pd.DataFrame({
                'Program': ['①', '①', '①', '②', '②', '③'],
                'No': ['WU', 1, 2, 'WU', 1, 1],
                'Exercise': ['Dynamic Stretch', 'Back Squat', 'Bench Press', 'Light Jog', 'Sprint 20m', 'Vertical Jump'],
                'set': [1, 4, 3, 1, 5, 3],
                'load': ['-', 0.8, 0.75, '-', '-', '-'],
                'rep': [10, 8, 10, 5, 1, 10],
                'Point': ['全身をほぐす', '膝をつま先の方向に', 'バーパスに注意', '軽く温める', '全力疾走', '着地を意識'],
                'Category': ['', 'Lower', 'Upper', '', 'Power', 'Power']
            })
            sample_df.to_excel(PROGRAM_FILE, index=False)
            return sample_df
    except Exception as e:
        st.error(f"プログラムファイルの読み込みエラー: {e}")
        return pd.DataFrame()

# ログファイルの読み込み（体重列追加）
def load_training_log():
    if os.path.exists(LOG_FILE):
        try:
            df = pd.read_excel(LOG_FILE)
            if '体重' not in df.columns:
                df['体重'] = ''
            if 'カテゴリー' not in df.columns:
                df['カテゴリー'] = ''
            return df
        except Exception as e:
            return pd.DataFrame(columns=["日付", "プログラム名", "名前", "体重", "エクササイズ名", "カテゴリー", "set", "負荷", "回数", "総負荷量"])
    else:
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

# ログ保存関数（体重パラメータ追加）
def save_training_log_formatted(player_name, program_name, exercise_name, exercise_category, sets_data, body_weight=None, date=None):
    if date is None:
        date = datetime.today().date()
    
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
        
        new_row = {
            '日付': date,
            'プログラム名': program_name,
            '名前': player_name,
            '体重': body_weight if body_weight else '',
            'エクササイズ名': exercise_name,
            'カテゴリー': exercise_category,
            'set': set_data['set_number'],
            '負荷': load_value,
            '回数': reps,
            '総負荷量': total_load
        }
        new_rows.append(new_row)
    
    new_df = pd.DataFrame(new_rows)
    
    try:
        if os.path.exists(LOG_FILE):
            try:
                existing_df = pd.read_excel(LOG_FILE)
            except Exception as e:
                st.error(f"既存ファイル読み込みエラー: {e}")
                existing_df = pd.DataFrame()
        else:
            existing_df = pd.DataFrame()
        
        if len(existing_df) > 0:
            expected_columns = ['日付', 'プログラム名', '名前', '体重', 'エクササイズ名', 'カテゴリー', 'set', '負荷', '回数', '総負荷量']
            if '体重' not in existing_df.columns:
                existing_df['体重'] = ''
            if 'カテゴリー' not in existing_df.columns:
                existing_df['カテゴリー'] = ''
            for col in expected_columns:
                if col not in existing_df.columns:
                    existing_df[col] = ''
            existing_df = existing_df[expected_columns]
            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        else:
            updated_df = new_df
        
        updated_df.to_excel(LOG_FILE, index=False)
        st.sidebar.success(f"✅ ローカル保存成功: {len(new_rows)}件")
        return len(new_rows)
    except Exception as e:
        st.error(f"❌ 保存失敗: {e}")
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
                exercise_type = ""
                if warmup['No'] == 'WU':
                    exercise_type = "WU "
                elif warmup['No'] == 'ST':
                    exercise_type = "ST "
                elif warmup['No'] == 'PL':
                    exercise_type = "PL "
                
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
                                st.markdown(f"""<div style="background: linear-gradient(135deg, rgba(25, 118, 210, 0.1) 0%, rgba(21, 101, 192, 0.1) 100%); border: 2px solid rgba(25, 118, 210, 0.3); border-radius: 12px; padding: 16px; margin: 12px 0; box-shadow: 0 4px 12px rgba(25, 118, 210, 0.15);"><h5 style="color: #1976d2; margin: 0 0 12px 0; font-size: 16px; font-weight: 700;">📈 前回のトレーニング ({latest_date_str})</h5></div>""", unsafe_allow_html=True)
                        else:
                            st.markdown("""<div style="background: linear-gradient(135deg, rgba(96, 125, 139, 0.1) 0%, rgba(120, 144, 156, 0.1) 100%); border: 2px dashed rgba(96, 125, 139, 0.3); border-radius: 8px; padding: 16px; margin: 12px 0; text-align: center;"><div style="color: #607d8b; font-size: 16px; font-weight: 600; margin-bottom: 4px;">🌟 初回トレーニング</div></div>""", unsafe_allow_html=True)
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
                                saved_sets = save_training_log_formatted(player_name=player_name, program_name=selected_program, exercise_name=exercise['Exercise'], exercise_category=exercise_category, sets_data=sets_data, body_weight=body_weight)
                                if saved_sets > 0:
                                    st.success(f"✅ {exercise['Exercise']} 完了！{saved_sets}セットのデータを保存しました。")
                                    st.balloons()
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
                st.balloons()
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
    st.markdown("### ファイル管理")
    col_file1, col_file2 = st.columns(2)
    with col_file1:
        st.markdown("#### トレーニングログ")
        if os.path.exists(LOG_FILE):
            log_df = load_training_log()
            st.success(f"ローカルファイル: {len(log_df)}件のログ")
            if len(log_df) > 0:
                csv = log_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button("📥 ログデータをダウンロード", csv, f"training_log_backup_{datetime.today().strftime('%Y%m%d')}.csv", "text/csv")
            if st.button("ローカルログファイルを削除", type="secondary"):
                os.remove(LOG_FILE)
                st.success("ローカルログファイルを削除しました")
                st.rerun()
        else:
            st.info("ローカルログファイルなし")
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
    st.markdown("### ファイルアップロード")
    col_upload1, col_upload2 = st.columns(2)
    with col_upload1:
        st.markdown("#### プログラムファイルアップロード")
        uploaded_program = st.file_uploader("プログラム用Excelファイル", type=['xlsx', 'xls'], key="program_upload")
        if uploaded_program:
            try:
                with open(PROGRAM_FILE, "wb") as f:
                    f.write(uploaded_program.getbuffer())
                st.success("プログラムファイルをアップロードしました")
                st.rerun()
            except Exception as e:
                st.error(f"アップロードエラー: {e}")
    with col_upload2:
        st.markdown("#### ログファイルアップロード")
        uploaded_log = st.file_uploader("ログ用Excelファイル", type=['xlsx', 'xls'], key="log_upload")
        if uploaded_log:
            try:
                with open(LOG_FILE, "wb") as f:
                    f.write(uploaded_log.getbuffer())
                st.success("ログファイルをアップロードしました")
                st.rerun()
            except Exception as e:
                st.error(f"アップロードエラー: {e}")
    
    st.markdown("---")
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
                'Point': ['全身をほぐす', '膝をつま先の方向に', 'バーパスに注意', '軽く温める', '全力疾走', '着地を意識'],
                'Category': ['', 'Lower', 'Upper', '', 'Power', 'Power']
            })
            sample_program_df.to_excel(PROGRAM_FILE, index=False)
            st.success("サンプルプログラムファイルを作成しました")
            st.rerun()
    with col_sample2:
        if st.button("空のログファイル作成"):
            empty_log_df = pd.DataFrame(columns=["日付", "プログラム名", "名前", "体重", "エクササイズ名", "カテゴリー", "set", "負荷", "回数", "総負荷量"])
            empty_log_df.to_excel(LOG_FILE, index=False)
            st.success("空のログファイルを作成しました")
            st.rerun()
    
    st.markdown("---")
    st.markdown("### データ統計")
    log_df = load_training_log()
    if len(log_df) > 0:
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
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
        with col_stat4:
            if 'カテゴリー' in log_df.columns:
                unique_categories = len([cat for cat in log_df['カテゴリー'].unique() if cat != '' and pd.notna(cat)])
                st.metric("カテゴリー数", unique_categories)
        
        if '名前' in log_df.columns and len(log_df) > 0:
            st.markdown("#### 選手別ログ数")
            player_counts = log_df['名前'].value_counts()
            st.bar_chart(player_counts)
        
        if 'カテゴリー' in log_df.columns and len(log_df) > 0:
            st.markdown("#### カテゴリー別ログ数")
            category_counts = log_df[log_df['カテゴリー'] != '']['カテゴリー'].value_counts()
            if len(category_counts) > 0:
                st.bar_chart(category_counts)
    
    st.markdown("---")
    st.markdown("### システム情報")
    st.info("""**バスケットボール トレーニングシステム v1.2 (体重データ対応版)**
    
- 💾 ローカルExcelファイル保存
- 📊 セッション内データ分析
- 🏷️ カテゴリー機能 (Upper/Lower/Power/Core)
- ⚖️ 体重データ記録・管理
- 📥 データダウンロード機能

**サポートファイル形式:** Excel (.xlsx, .xls), CSV

**注意:** Streamlit Cloudでは、ページをリロードするとデータが失われます。
重要なデータは定期的にダウンロードしてバックアップしてください。""")

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