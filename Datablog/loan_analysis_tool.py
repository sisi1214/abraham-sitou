"""
Global Student Loan Analysis Tool (Gradio)
Loan comparison, payment schedule visualization, and what-if scenario analysis
"""

import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple, Dict, List

# Workaround for numpy.typing compatibility issue with Python 3.9
try:
    import numpy.typing as npt
    if not hasattr(npt, 'NDArray'):
        npt.NDArray = np.ndarray
except (AttributeError, ImportError):
    pass

import gradio as gr


# ─── Load Data ────────────────────────────────────────────────────────────
def load_loan_data():
    """Load tuition and loan rate data from data.json"""
    data_path = Path(__file__).parent / "data.json"
    with open(data_path, "r") as f:
        data = json.load(f)
    return data


# ─── Loan Calculation Functions ────────────────────────────────────────────
def calculate_monthly_payment(principal: float, annual_rate: float, years: int) -> float:
    """Calculate fixed monthly payment (standard amortization)"""
    if annual_rate == 0:
        return principal / (years * 12)
    monthly_rate = annual_rate / 12
    num_payments = years * 12
    if num_payments == 0:
        return 0
    payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / \
              ((1 + monthly_rate) ** num_payments - 1)
    return payment


def generate_payment_schedule(
    principal: float,
    annual_rate: float,
    years: int,
    repayment_type: str = "standard"
) -> pd.DataFrame:
    """Generate detailed payment schedule"""
    monthly_rate = annual_rate / 12
    num_payments = years * 12
    monthly_payment = calculate_monthly_payment(principal, annual_rate, years)
    
    schedule = []
    balance = principal
    total_interest = 0
    
    for month in range(1, num_payments + 1):
        interest_payment = balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        balance = max(0, balance - principal_payment)
        total_interest += interest_payment
        
        schedule.append({
            "Month": month,
            "Payment": monthly_payment,
            "Principal": principal_payment,
            "Interest": interest_payment,
            "Balance": balance,
            "Total Interest Paid": total_interest
        })
        
        if balance <= 0:
            break
    
    return pd.DataFrame(schedule)


def compare_loans(
    loan_amounts: List[float],
    loan_rates: List[float],
    repayment_years: int
) -> Tuple[pd.DataFrame, str]:
    """Compare multiple loan scenarios"""
    comparison_data = []
    
    for i, (amount, rate) in enumerate(zip(loan_amounts, loan_rates)):
        monthly_payment = calculate_monthly_payment(amount, rate, repayment_years)
        total_payments = monthly_payment * repayment_years * 12
        total_interest = total_payments - amount
        
        comparison_data.append({
            "Scenario": f"Loan {i+1}",
            "Principal": f"${amount:,.2f}",
            "Interest Rate": f"{rate:.2%}",
            "Monthly Payment": f"${monthly_payment:,.2f}",
            "Total Interest": f"${total_interest:,.2f}",
            "Total Amount Paid": f"${total_payments:,.2f}",
            "Repayment Period": f"{repayment_years} years"
        })
    
    df = pd.DataFrame(comparison_data)
    
    # Calculate savings
    amounts_numeric = [calculate_monthly_payment(a, r, repayment_years) * repayment_years * 12 
                      for a, r in zip(loan_amounts, loan_rates)]
    max_cost = max(amounts_numeric)
    min_cost = min(amounts_numeric)
    savings = max_cost - min_cost
    
    summary = f"💰 **Comparison Summary**\n\n" \
              f"• Most Expensive: ${max_cost:,.2f}\n" \
              f"• Least Expensive: ${min_cost:,.2f}\n" \
              f"• **Potential Savings: ${savings:,.2f}**"
    
    return df, summary


# ─── Visualization Functions ───────────────────────────────────────────────
def plot_payment_schedule(schedule_df: pd.DataFrame) -> plt.Figure:
    """Visualize payment schedule over time"""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Loan Payment Schedule Analysis", fontsize=14, fontweight="bold")
    
    # Balance over time
    axes[0, 0].plot(schedule_df["Month"], schedule_df["Balance"], linewidth=2, color="#c9a84c")
    axes[0, 0].fill_between(schedule_df["Month"], schedule_df["Balance"], alpha=0.3, color="#c9a84c")
    axes[0, 0].set_xlabel("Month")
    axes[0, 0].set_ylabel("Remaining Balance ($)")
    axes[0, 0].set_title("Loan Balance Over Time")
    axes[0, 0].grid(True, alpha=0.3)
    
    # Principal vs Interest
    axes[0, 1].bar(schedule_df["Month"], schedule_df["Principal"], label="Principal", alpha=0.7, color="#4a8fa8")
    axes[0, 1].bar(schedule_df["Month"], schedule_df["Interest"], bottom=schedule_df["Principal"], 
                   label="Interest", alpha=0.7, color="#c9a84c")
    axes[0, 1].set_xlabel("Month")
    axes[0, 1].set_ylabel("Payment Amount ($)")
    axes[0, 1].set_title("Payment Composition (Principal vs Interest)")
    axes[0, 1].legend()
    axes[0, 1].grid(True, alpha=0.3, axis="y")
    
    # Cumulative interest paid
    axes[1, 0].plot(schedule_df["Month"], schedule_df["Total Interest Paid"], 
                   linewidth=2, color="#c9a84c", marker="o", markersize=3)
    axes[1, 0].fill_between(schedule_df["Month"], schedule_df["Total Interest Paid"], alpha=0.3, color="#c9a84c")
    axes[1, 0].set_xlabel("Month")
    axes[1, 0].set_ylabel("Cumulative Interest ($)")
    axes[1, 0].set_title("Total Interest Paid Over Time")
    axes[1, 0].grid(True, alpha=0.3)
    
    # Payment breakdown (pie chart for final totals)
    total_principal = schedule_df["Principal"].sum()
    total_interest = schedule_df["Interest"].sum()
    axes[1, 1].pie([total_principal, total_interest], 
                   labels=[f"Principal\n${total_principal:,.0f}", 
                          f"Interest\n${total_interest:,.0f}"],
                   autopct="%1.1f%%", colors=["#4a8fa8", "#c9a84c"], startangle=90)
    axes[1, 1].set_title("Total Payment Breakdown")
    
    plt.tight_layout()
    return fig


def plot_comparison(comparison_results: List[Dict]) -> plt.Figure:
    """Visualize loan comparison"""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle("Loan Comparison Analysis", fontsize=14, fontweight="bold")
    
    labels = [f"Loan {i+1}" for i in range(len(comparison_results))]
    monthly_payments = [r["monthly_payment"] for r in comparison_results]
    total_interest = [r["total_interest"] for r in comparison_results]
    
    # Monthly payment comparison
    axes[0].bar(labels, monthly_payments, color="#4a8fa8", alpha=0.7)
    axes[0].set_ylabel("Monthly Payment ($)")
    axes[0].set_title("Monthly Payment Comparison")
    axes[0].grid(True, alpha=0.3, axis="y")
    for i, v in enumerate(monthly_payments):
        axes[0].text(i, v, f"${v:.2f}", ha="center", va="bottom")
    
    # Total interest comparison
    axes[1].bar(labels, total_interest, color="#c9a84c", alpha=0.7)
    axes[1].set_ylabel("Total Interest ($)")
    axes[1].set_title("Total Interest Paid Comparison")
    axes[1].grid(True, alpha=0.3, axis="y")
    for i, v in enumerate(total_interest):
        axes[1].text(i, v, f"${v:.2f}", ha="center", va="bottom")
    
    plt.tight_layout()
    return fig


# ─── Tab 1: Loan Comparison ────────────────────────────────────────────────
def comparison_interface(data: Dict):
    """Create loan comparison interface"""
    country_options = list(data["tuitions_usd"].keys())
    scheme_options = list(data["loan_rates"].keys())
    
    def compare_countries(*args):
        """Compare loans from selected countries"""
        countries = [c for c in args[:len(country_options)] if c]
        years = args[len(country_options)]
        
        if not countries:
            return gr.DataFrame(value=None), "❌ Please select at least one country", None
        
        loan_amounts = []
        loan_rates = []
        
        for country in countries:
            tuition = data["tuitions_usd"].get(country, {})
            usd_amount = tuition.get("usd", 0)
            loan_amounts.append(usd_amount)
            
            # Get the appropriate loan rate for the country
            if country == "UK":
                rate = data["loan_rates"].get("UK_plan5", 0.032)
            elif country == "AU":
                rate = data["loan_rates"].get("AU_cpi", 0.036)
            else:
                rate = data["loan_rates"].get(country, 0)
            loan_rates.append(rate)
        
        comparison_df, summary = compare_loans(loan_amounts, loan_rates, years)
        
        # Generate comparison results for plotting
        comparison_results = []
        for amount, rate in zip(loan_amounts, loan_rates):
            monthly = calculate_monthly_payment(amount, rate, years)
            total_int = (monthly * years * 12) - amount
            comparison_results.append({
                "monthly_payment": monthly,
                "total_interest": total_int
            })
        
        comparison_fig = plot_comparison(comparison_results)
        
        return comparison_df, summary, comparison_fig
    
    with gr.Blocks() as comparison_block:
        gr.Markdown("## 🌍 Global Loan Comparison")
        gr.Markdown("Compare student loan costs across different countries based on current tuition and interest rates.")
        
        with gr.Row():
            with gr.Column(scale=1):
                country_checkboxes = [
                    gr.Checkbox(label=f"🏳️ {country}", value=False) 
                    for country in country_options
                ]
                repayment_years = gr.Slider(
                    minimum=5, maximum=30, value=10, step=1,
                    label="Repayment Period (years)"
                )
            
            with gr.Column(scale=1):
                compare_btn = gr.Button("📊 Compare Loans", variant="primary")
        
        comparison_output = gr.Dataframe(label="Comparison Results")
        comparison_summary = gr.Markdown()
        comparison_plot = gr.Plot(label="Comparison Visualization")
        
        compare_btn.click(
            fn=compare_countries,
            inputs=country_checkboxes + [repayment_years],
            outputs=[comparison_output, comparison_summary, comparison_plot]
        )
    
    return comparison_block


# ─── Tab 2: Payment Schedule ───────────────────────────────────────────────
def schedule_interface(data: Dict):
    """Create payment schedule visualization interface"""
    country_options = list(data["tuitions_usd"].keys())
    
    def generate_schedule(*args):
        """Generate payment schedule for selected parameters"""
        country = args[0]
        rate = args[1]
        years = args[2]
        
        if not country:
            return gr.Dataframe(value=None), None, "❌ Please select a country"
        
        tuition = data["tuitions_usd"].get(country, {})
        principal = tuition.get("usd", 0)
        
        schedule_df = generate_payment_schedule(principal, rate, years)
        
        # Format for display
        display_df = schedule_df.copy()
        display_df["Payment"] = display_df["Payment"].apply(lambda x: f"${x:,.2f}")
        display_df["Principal"] = display_df["Principal"].apply(lambda x: f"${x:,.2f}")
        display_df["Interest"] = display_df["Interest"].apply(lambda x: f"${x:,.2f}")
        display_df["Balance"] = display_df["Balance"].apply(lambda x: f"${x:,.2f}")
        display_df["Total Interest Paid"] = display_df["Total Interest Paid"].apply(lambda x: f"${x:,.2f}")
        
        schedule_fig = plot_payment_schedule(schedule_df)
        
        summary = f"📋 **Payment Schedule Summary**\n\n" \
                  f"• Country: {country}\n" \
                  f"• Principal: ${principal:,.2f}\n" \
                  f"• Interest Rate: {rate:.2%}\n" \
                  f"• Monthly Payment: ${schedule_df.iloc[0]['Payment']:,.2f}\n" \
                  f"• Total Interest: ${schedule_df['Interest'].sum():,.2f}\n" \
                  f"• Repayment Period: {years} years"
        
        return display_df, schedule_fig, summary
    
    with gr.Blocks() as schedule_block:
        gr.Markdown("## 📈 Payment Schedule Visualization")
        gr.Markdown("View detailed amortization schedule and visualize your loan repayment over time.")
        
        with gr.Row():
            with gr.Column(scale=1):
                country_select = gr.Dropdown(
                    choices=country_options,
                    label="🏳️ Select Country",
                    value="US_instate"
                )
                rate_input = gr.Slider(
                    minimum=0, maximum=0.15, value=0.05, step=0.001,
                    label="Interest Rate (%)",
                    info="Annual interest rate"
                )
                years_input = gr.Slider(
                    minimum=5, maximum=30, value=10, step=1,
                    label="Repayment Period (years)"
                )
                generate_btn = gr.Button("📊 Generate Schedule", variant="primary")
        
        schedule_summary = gr.Markdown()
        schedule_plot = gr.Plot(label="Payment Schedule Visualization")
        schedule_table = gr.Dataframe(label="Detailed Amortization Schedule")
        
        generate_btn.click(
            fn=generate_schedule,
            inputs=[country_select, rate_input, years_input],
            outputs=[schedule_table, schedule_plot, schedule_summary]
        )
    
    return schedule_block


# ─── Tab 3: What-If Scenario Analysis ──────────────────────────────────────
def scenario_interface(data: Dict):
    """Create what-if scenario analysis interface"""
    country_options = list(data["tuitions_usd"].keys())
    
    def analyze_scenarios(
        country: str,
        base_rate: float,
        base_years: int,
        alt_rate: float,
        alt_years: int,
        early_payment: float
    ):
        """Analyze different repayment scenarios"""
        if not country:
            return gr.Dataframe(value=None), None, "❌ Please select a country"
        
        tuition = data["tuitions_usd"].get(country, {})
        principal = tuition.get("usd", 0)
        
        # Scenario 1: Base case
        base_schedule = generate_payment_schedule(principal, base_rate, base_years)
        base_total_interest = base_schedule["Interest"].sum()
        base_monthly = base_schedule.iloc[0]["Payment"]
        
        # Scenario 2: Alternative rate/term
        alt_schedule = generate_payment_schedule(principal, alt_rate, alt_years)
        alt_total_interest = alt_schedule["Interest"].sum()
        alt_monthly = alt_schedule.iloc[0]["Payment"]
        
        # Scenario 3: Early payment
        if early_payment > 0:
            early_monthly = base_monthly + early_payment
            early_schedule = generate_payment_schedule(principal, base_rate, base_years)
            
            # Recalculate with higher payments
            balance = principal
            early_months = 0
            early_interest = 0
            monthly_rate = base_rate / 12
            
            while balance > 0 and early_months < base_years * 12:
                interest = balance * monthly_rate
                principal_payment = min(early_monthly - interest, balance)
                balance -= principal_payment
                early_interest += interest
                early_months += 1
            
            early_years = early_months / 12
        else:
            early_monthly = base_monthly
            early_months = base_years * 12
            early_interest = base_total_interest
            early_years = base_years
        
        # Create comparison dataframe
        scenarios_data = [
            {
                "Scenario": "Base Case",
                "Monthly Payment": f"${base_monthly:,.2f}",
                "Interest Rate": f"{base_rate:.2%}",
                "Repayment Period": f"{base_years} years",
                "Total Interest": f"${base_total_interest:,.2f}",
                "Total Paid": f"${principal + base_total_interest:,.2f}"
            },
            {
                "Scenario": "Alternative Rate/Term",
                "Monthly Payment": f"${alt_monthly:,.2f}",
                "Interest Rate": f"{alt_rate:.2%}",
                "Repayment Period": f"{alt_years} years",
                "Total Interest": f"${alt_total_interest:,.2f}",
                "Total Paid": f"${principal + alt_total_interest:,.2f}"
            },
            {
                "Scenario": "Early Payment Strategy",
                "Monthly Payment": f"${early_monthly:,.2f}",
                "Interest Rate": f"{base_rate:.2%}",
                "Repayment Period": f"{early_years:.1f} years",
                "Total Interest": f"${early_interest:,.2f}",
                "Total Paid": f"${principal + early_interest:,.2f}"
            }
        ]
        
        scenarios_df = pd.DataFrame(scenarios_data)
        
        # Calculate savings
        base_total = principal + base_total_interest
        alt_total = principal + alt_total_interest
        early_total = principal + early_interest
        
        best_scenario = min(
            [("Base Case", base_total), ("Alternative", alt_total), ("Early Payment", early_total)],
            key=lambda x: x[1]
        )
        
        max_total = max(base_total, alt_total, early_total)
        min_total = min(base_total, alt_total, early_total)
        
        summary = f"🎯 **What-If Analysis Summary**\n\n" \
                  f"**Principal**: ${principal:,.2f}\n\n" \
                  f"**Best Strategy**: {best_scenario[0]} (${best_scenario[1]:,.2f})\n" \
                  f"**Highest Cost**: ${max_total:,.2f}\n" \
                  f"**Savings Potential**: ${max_total - min_total:,.2f}"
        
        # Create visualization
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        fig.suptitle("What-If Scenario Analysis", fontsize=14, fontweight="bold")
        
        scenario_names = ["Base", "Alternative", "Early Payment"]
        total_costs = [base_total, alt_total, early_total]
        total_interests = [base_total_interest, alt_total_interest, early_interest]
        
        axes[0].bar(scenario_names, total_costs, alpha=0.7, color=["#4a8fa8", "#c9a84c", "#4ca864"])
        axes[0].set_ylabel("Total Amount Paid ($)")
        axes[0].set_title("Total Cost Comparison")
        axes[0].grid(True, alpha=0.3, axis="y")
        for i, v in enumerate(total_costs):
            axes[0].text(i, v, f"${v:,.0f}", ha="center", va="bottom")
        
        axes[1].bar(scenario_names, total_interests, alpha=0.7, color=["#4a8fa8", "#c9a84c", "#4ca864"])
        axes[1].set_ylabel("Total Interest Paid ($)")
        axes[1].set_title("Interest Comparison")
        axes[1].grid(True, alpha=0.3, axis="y")
        for i, v in enumerate(total_interests):
            axes[1].text(i, v, f"${v:,.0f}", ha="center", va="bottom")
        
        plt.tight_layout()
        
        return scenarios_df, fig, summary
    
    with gr.Blocks() as scenario_block:
        gr.Markdown("## 🔮 What-If Scenario Analysis")
        gr.Markdown("Explore different repayment strategies and compare outcomes.")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Base Scenario")
                country_select = gr.Dropdown(
                    choices=country_options,
                    label="🏳️ Select Country",
                    value="US_instate"
                )
                base_rate = gr.Slider(
                    minimum=0, maximum=0.15, value=0.05, step=0.001,
                    label="Base Interest Rate"
                )
                base_years = gr.Slider(
                    minimum=5, maximum=30, value=10, step=1,
                    label="Base Repayment Period (years)"
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### Alternative Scenario")
                alt_rate = gr.Slider(
                    minimum=0, maximum=0.15, value=0.03, step=0.001,
                    label="Alternative Interest Rate"
                )
                alt_years = gr.Slider(
                    minimum=5, maximum=30, value=15, step=1,
                    label="Alternative Repayment Period (years)"
                )
                early_payment = gr.Number(
                    value=0,
                    label="💰 Extra Monthly Payment ($)",
                    info="Additional amount paid monthly"
                )
        
        analyze_btn = gr.Button("🔍 Analyze Scenarios", variant="primary")
        
        scenario_summary = gr.Markdown()
        scenario_plot = gr.Plot(label="Scenario Comparison")
        scenario_table = gr.Dataframe(label="Detailed Scenario Comparison")
        
        analyze_btn.click(
            fn=analyze_scenarios,
            inputs=[country_select, base_rate, base_years, alt_rate, alt_years, early_payment],
            outputs=[scenario_table, scenario_plot, scenario_summary]
        )
    
    return scenario_block


# ─── Main App ──────────────────────────────────────────────────────────────
def main():
    """Build and launch the Gradio app"""
    data = load_loan_data()
    
    with gr.Blocks(title="Global Student Loan Analysis Tool", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            """
            # 🎓 Global Student Loan Analysis Tool
            
            Compare student loan costs across countries, visualize payment schedules, and analyze what-if scenarios.
            Data includes current tuition fees, interest rates, and exchange rates.
            """
        )
        
        with gr.Tabs():
            comparison_interface(data)
            schedule_interface(data)
            scenario_interface(data)
        
        gr.Markdown(
            """
            ---
            **Data Sources:**
            - Exchange Rates: frankfurter.app (ECB reference rates)
            - Tuition Fees: National education ministries and official statistics
            - Loan Rates: Central banks and government loan programs
            
            Last updated: 2026-05-27
            """
        )
    
    demo.launch(server_name="127.0.0.1", server_port=7861, share=False)


if __name__ == "__main__":
    main()
