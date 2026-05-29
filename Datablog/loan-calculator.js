/**
 * loan-calculator.js — Interactive loan analysis tool
 * Integrates with data.json for live tuition & rate data
 * Provides: payment schedule, scenario comparison, and cost analysis
 */

let loanData = null;
let currentCharts = {};

async function initLoanCalculator() {
  try {
    const resp = await fetch("./data.json", { cache: "no-store" });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    loanData = await resp.json();
  } catch (err) {
    console.error("[loan-calculator] Failed to load data.json", err);
    return;
  }

  // Wire up tabs
  setupLoanTabs();
  
  // Initialize first tab
  showLoanTab("schedule");
}

// ─── Helpers ──────────────────────────────────────────────────────────
function formatCurrency(n) {
  return "$" + Math.round(n).toLocaleString("en-US");
}

function formatPercent(n) {
  return (n * 100).toFixed(2) + "%";
}

function calculateMonthlyPayment(principal, annualRate, years) {
  if (annualRate === 0) {
    return principal / (years * 12);
  }
  const monthlyRate = annualRate / 12;
  const numPayments = years * 12;
  const payment =
    (principal * (monthlyRate * Math.pow(1 + monthlyRate, numPayments))) /
    (Math.pow(1 + monthlyRate, numPayments) - 1);
  return payment;
}

function generatePaymentSchedule(principal, annualRate, years) {
  const monthlyRate = annualRate / 12;
  const numPayments = years * 12;
  const monthlyPayment = calculateMonthlyPayment(principal, annualRate, years);
  
  const schedule = [];
  let balance = principal;
  let totalInterest = 0;
  
  for (let month = 1; month <= numPayments; month++) {
    const interestPayment = balance * monthlyRate;
    const principalPayment = monthlyPayment - interestPayment;
    balance = Math.max(0, balance - principalPayment);
    totalInterest += interestPayment;
    
    schedule.push({
      month,
      payment: monthlyPayment,
      principal: principalPayment,
      interest: interestPayment,
      balance,
      totalInterest
    });
    
    if (balance <= 0) break;
  }
  
  return schedule;
}

function getTuitionAndRate(country) {
  const tuition = loanData?.tuitions_usd?.[country];
  let rate = 0;
  
  if (country === "UK") {
    rate = loanData?.loan_rates?.["UK_plan5"] || 0.032;
  } else if (country === "AU") {
    rate = loanData?.loan_rates?.["AU_cpi"] || 0.036;
  } else if (country === "US_instate" || country === "US_private") {
    rate = loanData?.loan_rates?.["US"] || 0.0639;
  } else {
    rate = loanData?.loan_rates?.[country] || 0;
  }
  
  // Multiply by 4 for full 4-year degree
  const totalTuition = (tuition?.usd || 0) * 4;
  
  return { tuition: totalTuition, rate };
}

// ─── Tab Management ───────────────────────────────────────────────────
function setupLoanTabs() {
  const tabButtons = document.querySelectorAll(".loan-tab-btn");
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const tabName = btn.dataset.loanTab;
      showLoanTab(tabName);
      
      tabButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
    });
  });
}

function showLoanTab(tabName) {
  const panels = document.querySelectorAll(".loan-tab-panel");
  panels.forEach(p => p.classList.remove("active"));
  
  const panel = document.getElementById(`loan-tab-${tabName}`);
  if (panel) panel.classList.add("active");
  
  // Initialize tab-specific content
  if (tabName === "schedule") {
    initScheduleTab();
  } else if (tabName === "comparison") {
    initComparisonTab();
  } else if (tabName === "scenario") {
    initScenarioTab();
  }
}

// ─── Tab 1: Payment Schedule ──────────────────────────────────────────
function initScheduleTab() {
  const countrySelect = document.getElementById("scheduleCountry");
  const rateInput = document.getElementById("scheduleRate");
  const yearsInput = document.getElementById("scheduleYears");
  const generateBtn = document.getElementById("scheduleGenBtn");
  
  if (!generateBtn) return;
  
  generateBtn.addEventListener("click", () => {
    const country = countrySelect.value;
    const rate = (parseFloat(rateInput.value) || 0) / 100;  // Convert % to decimal
    const years = parseInt(yearsInput.value) || 10;
    
    const { tuition } = getTuitionAndRate(country);
    if (!tuition) {
      alert("Please select a valid country");
      return;
    }
    
    const schedule = generatePaymentSchedule(tuition, rate, years);
    const monthlyPayment = schedule[0]?.payment || 0;
    const totalInterest = schedule[schedule.length - 1]?.totalInterest || 0;
    
    // Update summary
    const summary = document.getElementById("scheduleSummary");
    if (summary) {
      summary.innerHTML = `
        <div class="loan-summary-grid">
          <div class="loan-summary-item">
            <span class="loan-summary-label">Principal (4-year)</span>
            <span class="loan-summary-value">${formatCurrency(tuition)}</span>
          </div>
          <div class="loan-summary-item">
            <span class="loan-summary-label">Interest Rate</span>
            <span class="loan-summary-value">${formatPercent(rate)}</span>
          </div>
          <div class="loan-summary-item">
            <span class="loan-summary-label">Monthly Payment</span>
            <span class="loan-summary-value">${formatCurrency(monthlyPayment)}</span>
          </div>
          <div class="loan-summary-item">
            <span class="loan-summary-label">Total Interest</span>
            <span class="loan-summary-value">${formatCurrency(totalInterest)}</span>
          </div>
          <div class="loan-summary-item">
            <span class="loan-summary-label">Total Paid</span>
            <span class="loan-summary-value">${formatCurrency(tuition + totalInterest)}</span>
          </div>
          <div class="loan-summary-item">
            <span class="loan-summary-label">Repayment Period</span>
            <span class="loan-summary-value">${years} years</span>
          </div>
        </div>
      `;
    }
    
    // Update table (first 12 months + annual milestones)
    const table = document.getElementById("scheduleTable");
    if (table) {
      let rows = "";
      const step = Math.max(1, Math.floor(schedule.length / 20)); // Show ~20 rows
      
      for (let i = 0; i < schedule.length; i += step) {
        const row = schedule[i];
        rows += `
          <tr>
            <td>${row.month}</td>
            <td>${formatCurrency(row.payment)}</td>
            <td>${formatCurrency(row.principal)}</td>
            <td>${formatCurrency(row.interest)}</td>
            <td>${formatCurrency(row.balance)}</td>
          </tr>
        `;
      }
      // Always include final row
      if (schedule.length > 1 && step > 1) {
        const lastRow = schedule[schedule.length - 1];
        rows += `
          <tr>
            <td>${lastRow.month}</td>
            <td>${formatCurrency(lastRow.payment)}</td>
            <td>${formatCurrency(lastRow.principal)}</td>
            <td>${formatCurrency(lastRow.interest)}</td>
            <td>${formatCurrency(lastRow.balance)}</td>
          </tr>
        `;
      }
      table.innerHTML = rows;
    }
    
    // Draw charts
    drawScheduleCharts(schedule, tuition, rate);
  });
}

function drawScheduleCharts(schedule, principal, rate) {
  // Balance chart
  const balanceCtx = document.getElementById("scheduleBalanceChart");
  if (balanceCtx) {
    if (currentCharts.balance) currentCharts.balance.destroy();
    
    currentCharts.balance = new Chart(balanceCtx, {
      type: "line",
      data: {
        labels: schedule.map(s => `M${s.month}`),
        datasets: [{
          label: "Remaining Balance",
          data: schedule.map(s => s.balance),
          borderColor: "#185FA5",
          backgroundColor: "rgba(24, 95, 165, 0.05)",
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { callback: v => "$" + (v / 1000).toFixed(0) + "k" }
          }
        }
      }
    });
  }
  
  // Interest vs Principal breakdown
  const compCtx = document.getElementById("scheduleCompChart");
  if (compCtx) {
    if (currentCharts.comp) currentCharts.comp.destroy();
    
    const totalPrincipal = schedule.reduce((s, r) => s + r.principal, 0);
    const totalInterest = schedule.reduce((s, r) => s + r.interest, 0);
    
    currentCharts.comp = new Chart(compCtx, {
      type: "doughnut",
      data: {
        labels: ["Principal", "Interest"],
        datasets: [{
          data: [totalPrincipal, totalInterest],
          backgroundColor: ["#185FA5", "#C93A39"],
          borderColor: "var(--surface)"
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom" },
          tooltip: {
            callbacks: {
              label: ctx => formatCurrency(ctx.parsed)
            }
          }
        }
      }
    });
  }
}

// ─── Tab 2: Loan Comparison ───────────────────────────────────────────
function initComparisonTab() {
  const countrySelects = document.querySelectorAll(".comparison-country");
  const yearsInput = document.getElementById("comparisonYears");
  const compareBtn = document.getElementById("comparisonBtn");
  
  if (!compareBtn) return;
  
  compareBtn.addEventListener("click", () => {
    const countries = Array.from(countrySelects)
      .map(s => s.value)
      .filter(c => c);
    
    const years = parseInt(yearsInput.value) || 10;
    
    if (countries.length === 0) {
      alert("Select at least one country");
      return;
    }
    
    const results = [];
    countries.forEach(country => {
      const { tuition, rate } = getTuitionAndRate(country);
      if (tuition > 0) {
        const schedule = generatePaymentSchedule(tuition, rate, years);
        const monthly = schedule[0]?.payment || 0;
        const totalInterest = schedule[schedule.length - 1]?.totalInterest || 0;
        const total = tuition + totalInterest;
        results.push({
          country,
          tuition,
          rate,
          monthly,
          total,
          interest: totalInterest
        });
      }
    });
    
    // Sort by total cost
    results.sort((a, b) => a.total - b.total);
    
    // Update table
    const table = document.getElementById("comparisonTable");
    if (table) {
      let rows = "";
      results.forEach((r, idx) => {
        rows += `
          <tr>
            <td><strong>${r.country}</strong></td>
            <td>${formatCurrency(r.tuition)}</td>
            <td>${formatPercent(r.rate)}</td>
            <td>${formatCurrency(r.monthly)}</td>
            <td>${formatCurrency(r.interest)}</td>
            <td><strong>${formatCurrency(r.total)}</strong></td>
          </tr>
        `;
      });
      table.innerHTML = rows;
    }
    
    // Summary
    const summary = document.getElementById("comparisonSummary");
    if (summary && results.length > 0) {
      const cheapest = results[0];
      const expensive = results[results.length - 1];
      const savings = expensive.total - cheapest.total;
      summary.innerHTML = `
        <p><strong>Cheapest:</strong> ${cheapest.country} (${formatCurrency(cheapest.total)})</p>
        <p><strong>Most expensive:</strong> ${expensive.country} (${formatCurrency(expensive.total)})</p>
        <p><strong>Potential savings:</strong> ${formatCurrency(savings)} over ${years} years</p>
      `;
    }
    
    // Chart
    drawComparisonChart(results);
  });
}

function drawComparisonChart(results) {
  const ctx = document.getElementById("comparisonChart");
  if (!ctx) return;
  
  if (currentCharts.comparison) currentCharts.comparison.destroy();
  
  const colors = ["#185FA5", "#2A6B2E", "#8C5A0A", "#6535A8", "#C93A39"];
  
  currentCharts.comparison = new Chart(ctx, {
    type: "bar",
    data: {
      labels: results.map(r => r.country),
      datasets: [
        {
          label: "Monthly Payment",
          data: results.map(r => r.monthly),
          backgroundColor: "#185FA5"
        },
        {
          label: "Total Interest",
          data: results.map(r => r.interest),
          backgroundColor: "#C93A39"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: "y",
      plugins: {
        legend: { position: "bottom" }
      },
      scales: {
        x: {
          ticks: { callback: v => "$" + (v / 1000).toFixed(0) + "k" }
        }
      }
    }
  });
}

// ─── Tab 3: What-If Scenario ──────────────────────────────────────────
function initScenarioTab() {
  const countrySelect = document.getElementById("scenarioCountry");
  const baseRateInput = document.getElementById("scenarioBaseRate");
  const baseYearsInput = document.getElementById("scenarioBaseYears");
  const altRateInput = document.getElementById("scenarioAltRate");
  const altYearsInput = document.getElementById("scenarioAltYears");
  const earlyPayInput = document.getElementById("scenarioEarlyPay");
  const analyzeBtn = document.getElementById("scenarioBtn");
  
  if (!analyzeBtn) return;
  
  analyzeBtn.addEventListener("click", () => {
    const country = countrySelect.value;
    const { tuition } = getTuitionAndRate(country);
    
    if (!tuition) {
      alert("Select a country");
      return;
    }
    
    const baseRate = (parseFloat(baseRateInput.value) || 0) / 100;  // Convert % to decimal
    const baseYears = parseInt(baseYearsInput.value) || 10;
    const altRate = (parseFloat(altRateInput.value) || 0) / 100;  // Convert % to decimal
    const altYears = parseInt(altYearsInput.value) || 15;
    const earlyPay = parseFloat(earlyPayInput.value) || 0;
    
    // Scenario 1: Base
    const baseMonthly = calculateMonthlyPayment(tuition, baseRate, baseYears);
    const baseTotal = baseMonthly * baseYears * 12;
    const baseInterest = baseTotal - tuition;
    
    // Scenario 2: Alternative
    const altMonthly = calculateMonthlyPayment(tuition, altRate, altYears);
    const altTotal = altMonthly * altYears * 12;
    const altInterest = altTotal - tuition;
    
    // Scenario 3: Early payment
    let earlyMonths = 0;
    let earlyInterest = 0;
    let balance = tuition;
    const earlyMonthly = baseMonthly + earlyPay;
    const monthlyRate = baseRate / 12;
    
    while (balance > 0 && earlyMonths < baseYears * 12) {
      const interest = balance * monthlyRate;
      const principal = Math.min(earlyMonthly - interest, balance);
      balance -= principal;
      earlyInterest += interest;
      earlyMonths++;
    }
    
    const earlyYears = earlyMonths / 12;
    const earlyTotal = tuition + earlyInterest;
    
    // Update table
    const table = document.getElementById("scenarioTable");
    if (table) {
      table.innerHTML = `
        <tr>
          <td><strong>Base Case</strong></td>
          <td>${formatCurrency(baseMonthly)}</td>
          <td>${formatPercent(baseRate)}</td>
          <td>${baseYears} yr</td>
          <td>${formatCurrency(baseInterest)}</td>
          <td><strong>${formatCurrency(baseTotal)}</strong></td>
        </tr>
        <tr>
          <td><strong>Alternative Rate/Term</strong></td>
          <td>${formatCurrency(altMonthly)}</td>
          <td>${formatPercent(altRate)}</td>
          <td>${altYears} yr</td>
          <td>${formatCurrency(altInterest)}</td>
          <td><strong>${formatCurrency(altTotal)}</strong></td>
        </tr>
        <tr>
          <td><strong>Early Payment (+${formatCurrency(earlyPay)}/mo)</strong></td>
          <td>${formatCurrency(earlyMonthly)}</td>
          <td>${formatPercent(baseRate)}</td>
          <td>${earlyYears.toFixed(1)} yr</td>
          <td>${formatCurrency(earlyInterest)}</td>
          <td><strong>${formatCurrency(earlyTotal)}</strong></td>
        </tr>
      `;
    }
    
    // Summary
    const summary = document.getElementById("scenarioSummary");
    if (summary) {
      const best = Math.min(baseTotal, altTotal, earlyTotal);
      const scenarios = [
        { name: "Base", total: baseTotal },
        { name: "Alternative", total: altTotal },
        { name: "Early Payment", total: earlyTotal }
      ];
      const winner = scenarios.find(s => s.total === best);
      
      summary.innerHTML = `
        <p><strong>Best strategy:</strong> ${winner.name} (${formatCurrency(best)})</p>
        <p><strong>Savings vs worst:</strong> ${formatCurrency(Math.max(baseTotal, altTotal, earlyTotal) - best)}</p>
        <p><strong>Principal borrowed:</strong> ${formatCurrency(tuition)}</p>
      `;
    }
    
    drawScenarioChart(baseTotal, altTotal, earlyTotal, baseInterest, altInterest, earlyInterest);
  });
}

function drawScenarioChart(base, alt, early, baseInt, altInt, earlyInt) {
  const ctx = document.getElementById("scenarioChart");
  if (!ctx) return;
  
  if (currentCharts.scenario) currentCharts.scenario.destroy();
  
  currentCharts.scenario = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Base", "Alternative", "Early Payment"],
      datasets: [
        {
          label: "Principal",
          data: [base - baseInt, alt - altInt, early - earlyInt],
          backgroundColor: "#185FA5"
        },
        {
          label: "Interest",
          data: [baseInt, altInt, earlyInt],
          backgroundColor: "#C93A39"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: "bottom" } },
      scales: {
        x: { stacked: true },
        y: {
          stacked: true,
          ticks: { callback: v => "$" + (v / 1000).toFixed(0) + "k" }
        }
      }
    }
  });
}

// Initialize on page load
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initLoanCalculator);
} else {
  initLoanCalculator();
}
