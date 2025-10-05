import streamlit as st

st.title("全適用ボタンテスト v3 - 確実版")

idx = 0
actual_sets = 3

st.write("## セッション状態")
st.write({k: v for k, v in st.session_state.items() if not k.startswith("FormSubmitter")})

# 全適用が押された直後の処理
apply_key = f"apply_trigger_{idx}"
if apply_key in st.session_state and st.session_state[apply_key]:
    # SET1の値を取得
    set1_unit = st.session_state.get(f"unit_{idx}_0", "kg")
    set1_load = st.session_state.get(f"load_{idx}_0", 0.0)
    set1_rep = st.session_state.get(f"rep_{idx}_0", 1)
    
    # SET2以降のウィジェットに直接値を設定
    for set_num in range(1, actual_sets):
        st.session_state[f"unit_{idx}_{set_num}"] = set1_unit
        st.session_state[f"load_{idx}_{set_num}"] = set1_load
        st.session_state[f"rep_{idx}_{set_num}"] = set1_rep
    
    # トリガーをリセット
    st.session_state[apply_key] = False

for set_num in range(actual_sets):
    st.write(f"--- SET {set_num + 1} ---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        unit = st.selectbox(
            "単位",
            ["kg", "%"],
            key=f"unit_{idx}_{set_num}"
        )
    
    with col2:
        load_value = st.number_input(
            "負荷",
            min_value=0.0,
            step=0.5,
            key=f"load_{idx}_{set_num}"
        )
    
    with col3:
        set_rep = st.number_input(
            "レップ数",
            min_value=0,
            key=f"rep_{idx}_{set_num}"
        )
    
    if set_num == 0:
        if st.button("全適用", key=f"copy_btn_{idx}"):
            st.session_state[apply_key] = True
            st.rerun()