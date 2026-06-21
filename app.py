import streamlit as st
import pandas as pd

# Set up page configuration for a modern, wide layout
st.set_page_config(page_title="Blast Furnace Slag App V2.0", layout="wide")

st.title("Blast Furnace Slag Prediction Application (V2.0)")
st.markdown("Enter your raw input data below. Calculations update automatically based on your new Pig Iron inputs.")

# ==========================================
# 1. USER INPUTS
# ==========================================
st.header("📋 Input Data")

# Create layout columns for the main parameters
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Ferrous Material Burden (%)")
    pellet_pct = st.number_input("Pellet (%) [G2]", min_value=0.0, max_value=100.0, value=50.0)
    sinter_pct = st.number_input("Sinter (%) [G3]", min_value=0.0, max_value=100.0, value=30.0)
    ore_pct = st.number_input("Iron Ore (%) [G4]", min_value=0.0, max_value=100.0, value=20.0)

with right_col:
    st.subheader("Process Parameters")
    coke_rate = st.number_input("Coke consumption rate (kg/tHM) [S1]", value=400.0)
    coke_ash_content = st.number_input("Coke ash content (%) [S2]", value=10.0)
    iron_recovery = st.number_input("Iron recovery (%) [L2]", value=99.0)
    fe_in_pig_iron = st.number_input("Percentage of iron in pig iron (%) [L3]", value=94.0)
    target_basicity = st.number_input("Target Basicity (B.I. need) [L4]", value=1.20)

st.write("---")
st.subheader("Composition Matrix Inputs")
col_tbl1, col_tbl2, col_tbl3 = st.columns(3)

# --- Table 1: Ferrous Material Compositions ---
# Maintained full table for background weighted average calculations
ferrous_elements = ["Fe", "FeO", "SiO₂", "CaO", "MgO", "Al₂O₃", "MnO", "TiO₂", "P", "S", "K₂O", "Na₂O"]
default_ferrous_data = {
    "Pellet (B)": [63.0, 1.0, 5.0, 1.2, 0.4, 1.5, 0.05, 0.1, 0.03, 0.01, 0.04, 0.02],
    "Sinter (C)": [56.0, 8.5, 5.5, 10.2, 2.5, 1.8, 0.20, 0.15, 0.05, 0.02, 0.06, 0.03],
    "Iron Ore (D)": [62.0, 0.0, 4.5, 0.5, 0.2, 2.0, 0.08, 0.08, 0.04, 0.01, 0.05, 0.02]
}
df_ferrous_input = pd.DataFrame(default_ferrous_data, index=ferrous_elements)

with col_tbl1:
    st.write("**Ferrous Material Analysis (%)**")
    edited_ferrous = st.data_editor(df_ferrous_input, use_container_width=True)

# --- Table 2: Coke Ash Compositions ---
coke_elements = ["SiO₂", "CaO", "MgO", "Al₂O₃", "Fe₂O₃", "MnO", "TiO₂", "P", "S", "K₂O", "Na₂O"]
default_coke_data = {
    "Ash % [P]": [52.0, 4.0, 2.0, 28.0, 8.0, 0.1, 1.2, 0.2, 0.6, 2.1, 0.8]
}
df_coke_input = pd.DataFrame(default_coke_data, index=coke_elements)

with col_tbl2:
    st.write("**Coke Ash Analysis (%)**")
    edited_coke = st.data_editor(df_coke_input, use_container_width=True)

# --- Table 3: NEW Pig Iron Analysis ---
pig_iron_elements = ["Fe", "Si", "Mn", "S", "P", "Ti", "Al"]
default_pig_iron_data = {
    "Pig Iron % [V]": [94.0, 0.50, 0.20, 0.03, 0.05, 0.02, 0.10]
}
df_pig_iron_input = pd.DataFrame(default_pig_iron_data, index=pig_iron_elements)

with col_tbl3:
    st.write("**Analysis of Pig Iron (%)**")
    edited_pig_iron = st.data_editor(df_pig_iron_input, use_container_width=True)


# ==========================================
# 2. CALCULATION ENGINE (V2.0 Core Logic)
# ==========================================

# --- Source 1: Weighted average of each compound in the ferrous burden ---
weighted_avg = {}
for elem in ferrous_elements:
    p_val = edited_ferrous.loc[elem, "Pellet (B)"]
    s_val = edited_ferrous.loc[elem, "Sinter (C)"]
    o_val = edited_ferrous.loc[elem, "Iron Ore (D)"]
    weighted_avg[elem] = (p_val * (pellet_pct / 100)) + (s_val * (sinter_pct / 100)) + (o_val * (ore_pct / 100))

b3_weighted_fe = weighted_avg["Fe"]

# --- Sinter Basicity Constants ---
sinter_cao = edited_ferrous.loc["CaO", "Sinter (C)"]
sinter_sio2 = edited_ferrous.loc["SiO₂", "Sinter (C)"]
sinter_mgo = edited_ferrous.loc["MgO", "Sinter (C)"]
sinter_al2o3 = edited_ferrous.loc["Al₂O₃", "Sinter (C)"]

sinter_bi2 = sinter_cao / sinter_sio2 if sinter_sio2 != 0 else 0.0
sinter_bi4 = (sinter_cao + sinter_mgo) / (sinter_sio2 + sinter_al2o3) if (sinter_sio2 + sinter_al2o3) != 0 else 0.0

# --- Source 2: Prediction of iron reducibility and efficiency ---
e2_fe_1000kg = b3_weighted_fe * 1000 / 100
e3_fe_available = e2_fe_1000kg * (iron_recovery / 100)
e4_tonnage_cast_iron = fe_in_pig_iron * 1000 / 100

denominator = (iron_recovery / 100) * (b3_weighted_fe / 100)
e5_iron_burden_req = e4_tonnage_cast_iron / denominator if denominator != 0 else 0.0

# --- Source 4 & 6: Main 4 Oxides from Ferrous and Coke ---
target_oxides = ["SiO₂", "CaO", "MgO", "Al₂O₃"]
ferrous_oxides_kg = {}
coke_oxides_kg = {}

n1_coke_ash_content = (coke_rate * coke_ash_content) / 100

for ox in target_oxides:
    ferrous_oxides_kg[ox] = (weighted_avg[ox] / 100) * e5_iron_burden_req
    coke_oxides_kg[ox] = (n1_coke_ash_content * edited_coke.loc[ox, "Ash % [P]"]) / 100

# --- Source 7: Blast furnace slag prediction analysis (With Pig Iron Corrections) ---
total_input = {}

# SiO2: Sum of inputs MINUS Si absorbed into Pig Iron
pig_iron_si = edited_pig_iron.loc["Si", "Pig Iron % [V]"]
si_correction = 1000 * ((pig_iron_si / 100) / 0.4674)
total_input["SiO₂"] = coke_oxides_kg["SiO₂"] + ferrous_oxides_kg["SiO₂"] - si_correction

# CaO and MgO (No corrections needed)
total_input["CaO"] = coke_oxides_kg["CaO"] + ferrous_oxides_kg["CaO"]
total_input["MgO"] = coke_oxides_kg["MgO"] + ferrous_oxides_kg["MgO"]

# Al2O3: Sum of inputs MINUS Al absorbed into Pig Iron
pig_iron_al = edited_pig_iron.loc["Al", "Pig Iron % [V]"]
al_correction = 1000 * ((pig_iron_al / 100) / 0.5293)
total_input["Al₂O₃"] = coke_oxides_kg["Al₂O₃"] + ferrous_oxides_kg["Al₂O₃"] - al_correction

# --- Source 8: Targets and Totals ---
# X3: Total Slag (Sum of T3:T6)
x3_total_slag = sum(total_input.values())

# X1 & X2: Basicity Target adjustments
x1_cao_target = total_input["SiO₂"] * target_basicity
x2_cao_required = x1_cao_target - total_input["CaO"]

# X4: Total Slag after correction
x4_total_slag_corrected = x3_total_slag + x2_cao_required

# Real Basicities
bi2_real = total_input["CaO"] / total_input["SiO₂"] if total_input["SiO₂"] != 0 else 0.0
bi4_real = (total_input["CaO"] + total_input["MgO"]) / (total_input["SiO₂"] + total_input["Al₂O₃"]) if (total_input["SiO₂"] + total_input["Al₂O₃"]) != 0 else 0.0


# ==========================================
# 3. RESULTS DISPLAY
# ==========================================
st.write("---")
st.header("📊 V2.0 Calculation Results")

# Display key efficiency stats metrics
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
m_col1.metric("Fe in 1000kg Burden", f"{round(e2_fe_1000kg, 2)} kg")
m_col2.metric("Fe After Recovery", f"{round(e3_fe_available, 2)} kg")
m_col3.metric("Fe in 1000kg Hot Metal", f"{round(e4_tonnage_cast_iron, 2)} kg")
m_col4.metric("Iron Burden Required", f"{round(e5_iron_burden_req, 2)} kg/tHM")

st.markdown("#### Basicity Verifications")
b_col1, b_col2, b_col3, b_col4 = st.columns(4)
b_col1.metric("Sinter B.I. 2", f"{round(sinter_bi2, 3)}")
b_col2.metric("Sinter B.I. 4", f"{round(sinter_bi4, 3)}")
b_col3.metric("Real Slag B.I. 2", f"{round(bi2_real, 3)}")
b_col4.metric("Real Slag B.I. 4", f"{round(bi4_real, 3)}")

# Generate Output Slag Dataframe (V2.0 - 4 Primary Oxides Only)
slag_table_rows = []
for oxide, total_wt in total_input.items():
    contribution_pct = (total_wt / x3_total_slag) * 100 if x3_total_slag != 0 else 0.0
    slag_table_rows.append({
        "Oxide": oxide,
        "Total Input (kg)": round(total_wt, 2),
        "Contribution to final slag weight (%)": round(contribution_pct, 2)
    })

df_final_slag = pd.DataFrame(slag_table_rows)

st.markdown("#### Blast Furnace Slag Prediction Analysis Table")
st.dataframe(df_final_slag, use_container_width=True, hide_index=True)

# Target adjustments metrics block
st.markdown("#### Target Basicity Balance Adjustments")
adj_col1, adj_col2, adj_col3, adj_col4 = st.columns(4)
adj_col1.metric("CaO Target to Basicity [X1]", f"{round(x1_cao_target, 2)} kg")
adj_col2.metric("CaO Required Correction [X2]", f"{round(x2_cao_required, 2)} kg")
adj_col3.metric("Total Slag (kg/tHM) [X3]", f"{round(x3_total_slag, 2)} kg")
adj_col4.metric("Slag After Correction (kg/tHM) [X4]", f"{round(x4_total_slag_corrected, 2)} kg")
