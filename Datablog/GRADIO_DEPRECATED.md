# Standalone Gradio Loan Analysis Tool (OPTIONAL)

This is a **standalone alternative** to the main loan calculator integrated in the Datablog dashboard.

## ⚠️ Status: Deprecated in favor of integrated web version

The primary loan analysis tool is now **integrated directly into the dashboard**:
- **Location**: [Datablog/index.html](./index.html) — "💰 Loan Calculator" tab
- **No external dependencies** — runs entirely in the browser
- **Always available** — works alongside other dashboard tabs
- **Real-time data** — uses live tuition and rate data from `data.json`

## What was this?

This was a **Gradio-based Python web app** that provided:
- Interactive loan calculators
- Payment schedule visualization
- Scenario comparison

## Why the change?

The **integrated JavaScript version is better because:**
1. ✅ No Python environment needed
2. ✅ No external server required
3. ✅ Works offline after page load
4. ✅ Seamlessly integrates with existing dashboard
5. ✅ Consistent design and theming
6. ✅ No deployment/port management issues

## If you want to use the Gradio version anyway:

```bash
# Install dependencies
pip install gradio pandas matplotlib numpy

# Run the server
cd Datablog
python loan_analysis_tool.py

# Open browser to: http://127.0.0.1:7861
```

**⚠️ Note**: The Gradio tool is no longer maintained. Use the dashboard calculator instead.

---

**→ [Go to Loan Calculator](./index.html)**
