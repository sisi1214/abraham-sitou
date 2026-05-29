# 💰 Global Student Loan Analysis Tool

An interactive loan calculator integrated into your Datablog dashboard. Model repayment schedules, compare loans across countries, and analyze what-if scenarios—all with live tuition and interest rate data.

## Features

### 1. **Payment Schedule Visualization** 📈
- Generate detailed amortization schedules for any country
- Visualize remaining balance over time
- See the breakdown of principal vs interest paid
- Interactive charts powered by Chart.js

### 2. **Loan Comparison** 🌍
- Compare repayment costs across multiple countries
- Up to 3 countries at a time
- Instant cost analysis showing potential savings
- Bar charts comparing monthly payments and total interest

### 3. **What-If Scenario Analysis** 🔮
- Model base case vs alternative rates/terms
- Analyze the impact of extra monthly payments
- See how early repayment strategy affects total cost
- Stacked bar charts showing principal vs interest breakdown

## Data Integration

The calculator reads from **`data.json`** which contains:

```json
{
  "tuitions_usd": {
    "HK": { "usd": 5373, ... },
    "UK": { "usd": 12459, ... },
    // ... other countries
  },
  "loan_rates": {
    "HK": 0.03,
    "US": 0.0639,
    "UK_plan2": 0.062,
    // ... other schemes
  }
}
```

**Auto-updated weekly** by `fetch_data.py` via GitHub Actions with:
- Current exchange rates (frankfurter.app)
- UK RPI for income-contingent loan calculations
- Australia CPI for HECS-HELP indexation
- Latest tuition fees from government sources

## Architecture

```
Datablog/
├── index.html              # Main dashboard with all 6 tabs
├── loan-calculator.js      # Interactive calculator logic (NEW)
├── data-loader.js          # Live data injector
├── data.json              # Source data (auto-updated)
└── fetch_data.py          # GitHub Actions data updater
```

### No External Dependencies
- Pure JavaScript (no Node.js, npm, or build step)
- Uses Chart.js CDN for visualizations
- Fully client-side calculations
- Works offline once page loads

## How to Use

### 1. **Payment Schedule Tab**
1. Select a country
2. Enter interest rate (or use default)
3. Set repayment period in years
4. Click "Generate Schedule"
5. View charts and detailed month-by-month breakdown

### 2. **Compare Countries Tab**
1. Select 1-3 countries from the dropdowns
2. Set repayment period
3. Click "Compare"
4. See side-by-side analysis with savings potential

### 3. **What-If Analysis Tab**
1. Choose a country
2. Set base scenario (rate + years)
3. Set alternative scenario (different rate/term)
4. Optionally add extra monthly payment
5. Click "Analyze"
6. Compare which strategy saves the most

## Files Overview

### `loan-calculator.js`
- Main calculator module (460+ lines)
- Calculation functions:
  - `calculateMonthlyPayment()` - Fixed monthly payment using amortization formula
  - `generatePaymentSchedule()` - Full month-by-month schedule
  - `getTuitionAndRate()` - Retrieves live data for each country
- UI functions:
  - Tab management and switching
  - Chart rendering (balance, comparison, scenarios)
  - Summary display
- No external dependencies beyond Chart.js

### `index.html` (updated)
- New "💰 Loan Calculator" tab button
- HTML structure for 3 sub-tabs (schedule, comparison, scenario)
- Forms with country selectors, rate inputs, year inputs
- Chart containers and table structures
- Styling integrated into existing dashboard CSS

### `data.json` (existing)
- Tuition fees in USD (converted from local currency at current rates)
- Loan rates for each country/scheme
- Exchange rates
- Metadata and data sources

## Calculations

### Monthly Payment (Amortization Formula)
```
M = P × [r(1+r)^n] / [(1+r)^n - 1]

Where:
  M = Monthly payment
  P = Principal (loan amount)
  r = Monthly interest rate (annual ÷ 12)
  n = Total number of payments (years × 12)
```

### Amortization Schedule
For each month:
1. Interest payment = Remaining balance × monthly rate
2. Principal payment = Monthly payment - Interest payment
3. New balance = Previous balance - Principal payment
4. Cumulative interest tracked

### Early Payment Impact
When paying extra monthly:
1. Increase total monthly payment by extra amount
2. Recalculate month-by-month with higher payment
3. Loan pays off faster with lower total interest
4. Savings = Interest saved + Time saved

## Browser Compatibility

- Modern browsers with ES6+ support (Chrome, Firefox, Safari, Edge)
- Requires Chart.js library (loaded from CDN)
- JavaScript must be enabled

## Future Enhancements

- [ ] Export payment schedule as PDF/CSV
- [ ] Income-contingent repayment modeling (UK, Australia)
- [ ] Multiple loan comparison (undergrad + grad loans)
- [ ] Inflation adjustment for longer-term scenarios
- [ ] Mobile optimization for landscape charts

## Troubleshooting

**"Could not load data.json"**
- Check that `data.json` exists in the Datablog folder
- Ensure it's valid JSON (use `json-validate` or similar)
- Check browser console for CORS errors

**Charts not displaying**
- Verify Chart.js CDN is accessible
- Check browser console for JavaScript errors
- Ensure canvas elements have IDs matching the code

**Calculations seem wrong**
- Double-check the interest rate format (entered as %, calculated as decimal)
- Verify the country and tuition amount loaded correctly
- Check that monthly rate = annual rate ÷ 12

## Related Files

- **fetch_data.py** - Updates data.json weekly via GitHub Actions
- **data-loader.js** - Injects live values into HTML elements
- **index.html** - Datablog dashboard (main page)
- **posts.json** - Blog posts (separate from loan tool)

## License

This calculator is part of the abraham-sitou datablog project.
