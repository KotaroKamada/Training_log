import streamlit as st

st.title("全適用ボタンテスト")

idx = 0
actual_sets = 3

st.write("## セッション状態の確認")
st.write(st.session_state)

loads = []
reps = []

for set_num in range(actual_sets):
    st.write(f"--- SET {set_num + 1} ---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        unit_default = 0
        if f"copy_unit_{idx}" in st.session_state and set_num > 0:
            units = ["kg", "%"]
            saved_unit = st.session_state[f"copy_unit_{idx}"]
            if saved_unit in units:
                unit_default = units.index(saved_unit)
        
        unit = st.selectbox(
            "単位",
            ["kg", "%"],
            index=unit_default,
            key=f"unit_{idx}_{set_num}"
        )
    
    with col2:
        load_default = 0.0
        if f"copy_load_{idx}" in st.session_state and set_num > 0:
            load_default = st.session_state[f"copy_load_{idx}"]
        
        load_value = st.number_input(
            "負荷",
            min_value=0.0,
            value=load_default,
            step=0.5,
            key=f"load_{idx}_{set_num}"
        )
    
    with col3:
        rep_default = 1
        if f"copy_rep_{idx}" in st.session_state and set_num > 0:
            rep_default = st.session_state[f"copy_rep_{idx}"]
        
        set_rep = st.number_input(
            "レップ数",
            min_value=0,
            value=rep_default,
            key=f"rep_{idx}_{set_num}"
        )
    
    if set_num == 0:
        if st.button("全適用", key=f"copy_btn_{idx}"):
            st.write("ボタンが押されました！")
            st.session_state[f"copy_unit_{idx}"] = unit
            st.session_state[f"copy_load_{idx}"] = load_value
            st.session_state[f"copy_rep_{idx}"] = set_rep
            st.write(f"保存: unit={unit}, load={load_value}, rep={set_rep}")
            st.rerun()