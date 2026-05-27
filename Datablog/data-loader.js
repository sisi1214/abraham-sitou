/**
 * data-loader.js  —  University Cost Dashboard live data injector
 *
 * How it works:
 *   1. Fetches ./data.json (updated weekly by GitHub Actions)
 *   2. Finds elements by their data-live="key" attribute
 *   3. Replaces their text content with the formatted live value
 *   4. Stamps a "Last updated" badge in the footer
 *
 * To wire up any element in index.html, add:
 *   data-live="tuition.HK"          → USD tuition for Hong Kong
 *   data-live="tuition.UK"          → USD tuition for UK
 *   data-live="rate.UK_plan2"       → UK Plan 2 loan rate as %
 *   data-live="rate.US"             → US federal loan rate as %
 *   data-live="fx.GBP"              → 1 USD in GBP
 *   data-live="updated"             → human-readable last-updated date
 *
 * Full key reference:
 *   Tuition keys:  HK · UK · US_instate · US_private · SG · AU · CA · DE · FR
 *   Rate keys:     DE · CA · FR · HK · US · SG · UK_plan5 · UK_plan2 · AU_cpi
 *   FX keys:       GBP · AUD · SGD · HKD · CAD · EUR
 */

(async function initDashboard() {
  // ── 1. Fetch data.json ───────────────────────────────────────────────────
  let data;
  try {
    const resp = await fetch("./data.json", { cache: "no-store" });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    data = await resp.json();
  } catch (err) {
    console.warn("[data-loader] Could not load data.json — static values shown.", err);
    return;
  }

  // ── 2. Helpers ───────────────────────────────────────────────────────────
  const fmt = {
    usd: (n) =>
      n != null
        ? "$" + Math.round(n).toLocaleString("en-US")
        : null,
    pct: (r) =>
      r != null
        ? (r * 100).toFixed(1) + "%"
        : null,
    fx: (r) =>
      r != null
        ? r.toFixed(4)
        : null,
    date: (iso) => {
      try {
        return new Date(iso).toLocaleDateString("en-GB", {
          day: "numeric",
          month: "long",
          year: "numeric",
        });
      } catch {
        return iso;
      }
    },
  };

  function resolve(key) {
    if (key === "updated") return fmt.date(data.meta?.last_updated);

    const [type, id] = key.split(".");
    if (!type || !id) return null;

    if (type === "tuition") {
      const t = data.tuitions_usd?.[id];
      return t ? fmt.usd(t.usd) : null;
    }
    if (type === "rate") {
      const r = data.loan_rates?.[id];
      return r != null ? fmt.pct(r) : null;
    }
    if (type === "fx") {
      const f = data.exchange_rates_from_usd?.[id];
      return f != null ? fmt.fx(f) : null;
    }
    if (type === "tuition_local") {
      const t = data.tuitions_usd?.[id];
      return t
        ? t.local_amount.toLocaleString("en-US") + " " + t.local_currency
        : null;
    }
    return null;
  }

  // ── 3. Inject values into data-live elements ─────────────────────────────
  document.querySelectorAll("[data-live]").forEach((el) => {
    const key = el.getAttribute("data-live");
    const value = resolve(key);
    if (value !== null && value !== undefined) {
      el.textContent = value;
      el.classList.add("live-data");          // optional: style injected values
    }
  });

  // ── 4. "Last updated" badge in footer ────────────────────────────────────
  const rateDate = data.exchange_rate_date || "";
  const updatedDate = fmt.date(data.meta?.last_updated);
  const badge = document.createElement("p");
  badge.className = "live-updated-badge";
  badge.innerHTML =
    `<small>📡 Exchange rates: <strong>${rateDate}</strong> · ` +
    `Data refreshed: <strong>${updatedDate}</strong> · ` +
    `Source: ECB via <a href="https://www.frankfurter.app" target="_blank" rel="noopener">frankfurter.app</a></small>`;

  // Insert before the existing footer <p>, or append to footer
  const footer = document.querySelector("footer") || document.body;
  footer.prepend(badge);

  console.log("[data-loader] Dashboard data loaded:", data.meta?.last_updated);
})();
