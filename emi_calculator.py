import streamlit as st
from streamlit_option_menu import option_menu
import numpy as np
import pandas as pd
import plotly.express as px
import inflect

# Set Page Config
st.set_page_config(page_title="Loan EMI Calculator", layout="wide", page_icon="Assets\logo.png")

def number_to_words_indian(n):
    p = inflect.engine()
    if n < 100000:
        return p.number_to_words(n, andword="").replace(",", "").capitalize()
    crore, lakh, thousand, remainder = n // 10000000, (n % 10000000) // 100000, (n % 100000) // 1000, n % 1000
    words = [
        f"{p.number_to_words(crore)} crore" if crore else "",
        f"{p.number_to_words(lakh)} lakh" if lakh else "",
        f"{p.number_to_words(thousand)} thousand" if thousand else "",
        p.number_to_words(remainder) if remainder else ""
    ]
    return " ".join(filter(None, words)).replace(",", "").capitalize()

# Sidebar Navigation
with st.sidebar:
    selected = option_menu(
        menu_title="Loan Calculator",
        options=["EMI Calculator", "Compare Loans", "Graphs", "Prepayment Simulation"],
        icons=["calculator", "bar-chart", "graph-up", "cash"],
        menu_icon="cast",
        default_index=0
    )

def calculate_emi(P, r, n):
    r = r / 100 / 12  # Monthly interest rate
    n = n * 12  # Convert years to months
    emi = (P * r * (1 + r) ** n) / ((1 + r) ** n - 1)
    total_payment = emi * n
    total_interest = total_payment - P
    return emi, total_payment, total_interest

def generate_amortization_schedule(P, r, n):
    r = r / 100 / 12
    n = n * 12
    emi, _, _ = calculate_emi(P, r * 100 * 12, n // 12)
    schedule, balance = [], P
    for i in range(1, n + 1):
        interest, principal = balance * r, emi - balance * r
        balance -= principal
        schedule.append([i, emi, principal, interest, max(0, balance)])
    return pd.DataFrame(schedule, columns=["Month", "EMI", "Principal Paid", "Interest Paid", "Remaining Balance"])

if selected == "EMI Calculator":
    st.title("🏦 Loan EMI Calculator")
    loan_amount = st.number_input("Loan Amount (₹)", min_value=1000, value=500000, step=1000)
    st.caption(f"**{number_to_words_indian(loan_amount)} rupees**")
    interest_rate, loan_tenure = st.number_input("Annual Interest Rate (%)", 0.1, 20.0, 8.5, 0.1), st.slider("Loan Tenure (Years)", 1, 30, 10)
    if st.button("Calculate EMI"):
        emi, total_payment, total_interest = calculate_emi(loan_amount, interest_rate, loan_tenure)
        col1, col2, col3 = st.columns(3)
        with col1: st.success(f"📌 EMI per Month: ₹{emi:.2f}")
        with col2: st.info(f"💰 Total Payment: ₹{total_payment:.2f}")
        with col3: st.warning(f"📊 Total Interest Payable: ₹{total_interest:.2f}")
        fig = px.pie(names=["Principal", "Interest"], values=[loan_amount, total_interest], title="Loan Breakdown", hole=0.3)
        st.plotly_chart(fig)
        df = generate_amortization_schedule(loan_amount, interest_rate, loan_tenure)
        st.subheader("📅 Loan Amortization Schedule")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Schedule", data=csv, file_name="loan_amortization.csv", mime="text/csv")

elif selected == "Compare Loans":
    st.title("📊 Compare Loan Plans")
    num_loans, data = st.slider("Number of Loans", 2, 3, 2), []
    cols = st.columns(num_loans)
    for i, col in enumerate(cols):
        with col:
            st.subheader(f"Loan {i+1}")
            amount = st.number_input(f"Amount ₹ - {i+1}", 1000, 10000000, 500000, 1000)
            st.caption(f"**{number_to_words_indian(amount)} rupees**")
            rate = st.number_input(f"Rate % - {i+1}", 0.1, 20.0, 8.5, 0.1)
            tenure = st.slider(f"Years - {i+1}", 1, 30, 10)
            
            emi, total_payment, total_interest = calculate_emi(amount, rate, tenure)
            data.append({"Loan": f"Loan {i+1}", "EMI": emi, "Total Payment": total_payment, "Total Interest": total_interest})
    df = pd.DataFrame(data)
    st.dataframe(df)
    best_loan = df.loc[df["Total Interest"].idxmin(), "Loan"]
    st.success(f"✅ Best Loan Choice: **{best_loan}**")
    fig = px.bar(df, x="Loan", y="Total Payment", title="Loan Comparison", color="Loan")
    st.plotly_chart(fig)

elif selected == "Graphs":
    st.title("📈 Loan Repayment Graphs")
    amount, rate, tenure = st.number_input("Loan Amount (₹)", 1000, 10000000, 500000, 1000), st.number_input("Rate (%)", 0.1, 20.0, 8.5, 0.1), st.slider("Years", 1, 30, 10)
    st.caption(f"**{number_to_words_indian(amount)} rupees**")
    df = generate_amortization_schedule(amount, rate, tenure)
    fig = px.line(df, x="Month", y=["Principal Paid", "Interest Paid"], title="Principal vs Interest Paid Over Time")
    st.plotly_chart(fig)
    fig2 = px.line(df, x="Month", y="Remaining Balance", title="Loan Balance Over Time")
    st.plotly_chart(fig2)

elif selected == "Prepayment Simulation":
    st.title("💰 Prepayment Impact on Loan")
    amount = st.number_input("Loan Amount (₹)", 1000, 10000000, 500000, 1000)
    st.caption(f"**{number_to_words_indian(amount)} rupees**")
    rate = st.number_input("Rate (%)", 0.1, 20.0, 8.5, 0.1)
    tenure = st.slider("Years", 1, 30, 10)
    prepay_amount = st.number_input("Prepayment Amount (₹)", 0, 1000000, 50000, 1000)
    
    new_amount = amount - prepay_amount
    emi, total_payment, total_interest = calculate_emi(new_amount, rate, tenure)
    st.success(f"New EMI: ₹{emi:.2f}, Total Payment: ₹{total_payment:.2f}, Interest: ₹{total_interest:.2f}")
