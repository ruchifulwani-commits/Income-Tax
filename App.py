import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# ---------------- SESSION INIT ---------------- #
if "last_result" not in st.session_state:
    st.session_state.last_result = {}

# ---------------- TAX LOGIC ---------------- #

def new_tax(income):
    slabs = [
        (400000, 0.00),
        (800000, 0.05),
        (1200000, 0.10),
        (1600000, 0.15),
        (2000000, 0.20),
        (2400000, 0.25),
        (float("inf"), 0.30)
    ]

    tax = 0
    prev = 0
    breakdown = []

    for limit, rate in slabs:
        if income > prev:
            taxable = min(income, limit) - prev
            t = taxable * rate
            tax += t
            breakdown.append({"Slab": f"{prev}-{limit}", "Tax": t})
            prev = limit
        else:
            break

    return tax, breakdown


def old_tax(income):
    slabs = [
        (250000, 0.00),
        (500000, 0.05),
        (1000000, 0.20),
        (float("inf"), 0.30)
    ]

    tax = 0
    prev = 0
    breakdown = []

    for limit, rate in slabs:
        if income > prev:
            taxable = min(income, limit) - prev
            t = taxable * rate
            tax += t
            breakdown.append({"Slab": f"{prev}-{limit}", "Tax": t})
            prev = limit
        else:
            break

    return tax, breakdown


def surcharge(income, tax):
    if income > 50000000:
        return tax * 0.37
    elif income > 20000000:
        return tax * 0.25
    elif income > 10000000:
        return tax * 0.15
    elif income > 5000000:
        return tax * 0.10
    return 0


def cess(amount):
    return amount * 0.04


# ---------------- UI SIDEBAR ---------------- #

st.sidebar.title("⚙️ Controls")

income = st.sidebar.number_input("Income", min_value=0.0, step=50000.0)
regime = st.sidebar.radio("Regime", ["Old", "New"])
year = st.sidebar.selectbox("Assessment Year", ["2024-25", "2025-26", "2026-27"])
currency = st.sidebar.selectbox("Currency", ["₹", "$", "€"])

# ---------------- LEAD FORM ---------------- #

st.sidebar.markdown("---")
st.sidebar.subheader("📩 Lead Form")

with st.sidebar.form("lead_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    interest = st.selectbox("Interest", ["Tax Planning", "Investment", "Consultation"])
    submit = st.form_submit_button("Submit")

    if submit:
        if name and email:
            lead = pd.DataFrame([{
                "Name": name,
                "Email": email,
                "Phone": phone,
                "Interest": interest,
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])

            file = "leads.xlsx"

            if os.path.exists(file):
                old = pd.read_excel(file, engine="openpyxl")
                final = pd.concat([old, lead], ignore_index=True)
            else:
                final = lead

            final.to_excel(file, index=False, engine="openpyxl")
            st.sidebar.success("Lead Saved ✅")
        else:
            st.sidebar.error("Fill required fields")

# ---------------- MAIN ---------------- #

st.title("💰 Advanced Income Tax Dashboard")

if st.button("Calculate"):

    if income < 0:
        st.error("Income cannot be negative")
        st.stop()

    if regime == "New":
        base_tax, breakdown = new_tax(income)
    else:
        base_tax, breakdown = old_tax(income)

    sur = surcharge(income, base_tax)
    total_before_cess = base_tax + sur
    c = cess(total_before_cess)
    total_tax = total_before_cess + c
    net_income = income - total_tax

    st.session_state.last_result = {
        "income": income,
        "tax": total_tax,
        "net": net_income
    }

    # ---------------- METRICS ---------------- #
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tax", f"{currency}{total_tax:,.2f}")
    col2.metric("Cess", f"{currency}{c:,.2f}")
    col3.metric("Net Income", f"{currency}{net_income:,.2f}")

    # ---------------- CHART 1: SLAB ---------------- #
    df = pd.DataFrame(breakdown)

    fig1 = px.bar(
        df,
        x="Tax",
        y="Slab",
        orientation="h",
        title="Slab-wise Tax Distribution"
    )
    st.plotly_chart(fig1, use_container_width=True)

    # ---------------- CHART 2: COMPARISON ---------------- #
    old_tax_val, _ = old_tax(income)
    new_tax_val, _ = new_tax(income)

    comp = pd.DataFrame({
        "Regime": ["Old", "New"],
        "Tax": [old_tax_val, new_tax_val]
    })

    fig2 = px.bar(comp, x="Regime", y="Tax", text="Tax", title="Old vs New Comparison")
    st.plotly_chart(fig2, use_container_width=True)

# ---------------- DOWNLOAD REPORT ---------------- #

if st.session_state.last_result:
    df_report = pd.DataFrame([st.session_state.last_result])

    st.download_button(
        "📥 Download Report",
        df_report.to_csv(index=False),
        "tax_report.csv",
        "text/csv"
    )