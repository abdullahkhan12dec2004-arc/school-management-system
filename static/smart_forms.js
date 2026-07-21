/**
 * smart_forms.js
 * School Management System — Global Enhancements
 *
 * Feature 1 → TABLE ALIGNMENT
 *   Scans every <td> in every table.
 *   If the cell content looks like a number / currency / percentage / date,
 *   adds class "num-cell" (styled right-aligned in smart_forms.css).
 *   Also aligns the matching <th> header right (class "num-header").
 *
 * Feature 2 → FORM AUTO-TAB
 *   On every <form> in the page, pressing Enter in any focusable field
 *   automatically moves focus to the next field.
 *   Works for: input (text, number, email, tel, password, date, etc.),
 *              select, textarea.
 *   Skips: buttons, hidden fields, disabled fields, read-only fields,
 *          fields with data-skip="true".
 *   Pressing Enter on the LAST field submits the form (normal behaviour).
 */

(function () {
  "use strict";

  /* ══════════════════════════════════════════════════════════════
     FEATURE 1 — SMART TABLE ALIGNMENT
     ══════════════════════════════════════════════════════════════ */

  /**
   * Returns true if the trimmed string looks like a pure numeric value.
   * Matches:
   *   integers          →  42
   *   decimals          →  3.14
   *   negatives         →  -7
   *   percentages       →  98.5%
   *   currency (PKR/Rs) →  Rs 1,200  /  1,200.00
   *   plain fractions   →  3/5
   *   marks entry       →  45/100
   *   roll numbers      →  NOT matched (mixed text)
   *
   * Intentionally NOT matched:
   *   pure dates like "2024-01-15" or "Jan 2024" → left-aligned
   *   student codes like "STD-20240101"           → left-aligned
   */
  function looksNumeric(str) {
    var s = str.trim();
    if (s === "" || s === "-" || s === "N/A" || s.toLowerCase() === "null") {
      return false;
    }

    // Remove common currency symbols / thousand separators first
    var cleaned = s.replace(/^(Rs\.?|PKR|₨)\s*/i, "")
                   .replace(/,/g, "");

    // percentage
    if (/^-?\d+(\.\d+)?%$/.test(cleaned)) return true;

    // fraction like 45/100
    if (/^\d+\/\d+$/.test(cleaned)) return true;

    // plain integer or decimal (possibly negative)
    if (/^-?\d+(\.\d+)?$/.test(cleaned)) return true;

    return false;
  }

  function alignTables() {
    var tables = document.querySelectorAll("table");

    tables.forEach(function (table) {
      var rows = table.querySelectorAll("tr");
      if (!rows.length) return;

      // Determine column count from first row
      var firstRow = rows[0];
      var colCount = firstRow.querySelectorAll("th, td").length;

      // For each column index, check if ALL data cells (td) are numeric
      for (var colIdx = 0; colIdx < colCount; colIdx++) {
        var dataCells = [];
        var nonEmpty = 0;
        var numericCount = 0;

        rows.forEach(function (row) {
          var cells = row.querySelectorAll("td");
          if (cells[colIdx]) {
            var text = cells[colIdx].innerText || cells[colIdx].textContent || "";
            text = text.trim();

            // If cell has an input inside, read its value
            var inp = cells[colIdx].querySelector("input");
            if (inp) {
              text = inp.value || inp.placeholder || "";
              // If type="number" or class contains marks — always numeric
              if (inp.type === "number" || inp.classList.contains("marks-input")) {
                numericCount++;
                nonEmpty++;
                dataCells.push(cells[colIdx]);
                return;
              }
            }

            if (text !== "") {
              nonEmpty++;
              if (looksNumeric(text)) numericCount++;
            }
            dataCells.push(cells[colIdx]);
          }
        });

        // If >75% of non-empty cells are numeric → align whole column right
        var isNumericColumn = nonEmpty > 0 && (numericCount / nonEmpty) >= 0.75;

        if (isNumericColumn) {
          // Mark data cells
          dataCells.forEach(function (cell) {
            cell.classList.add("num-cell");
          });

          // Mark the header cell too
          var headerRows = table.querySelectorAll("thead tr, tr:first-child");
          headerRows.forEach(function (hRow) {
            var ths = hRow.querySelectorAll("th");
            if (ths[colIdx]) {
              ths[colIdx].classList.add("num-header");
            }
          });
        }
      }
    });
  }


  /* ══════════════════════════════════════════════════════════════
     FEATURE 2 — FORM AUTO-TAB (Enter → next field)
     ══════════════════════════════════════════════════════════════ */

  /**
   * Collects all focusable, non-skipped fields inside a form.
   */
  function getFocusableFields(form) {
    var selector = [
      'input:not([type="hidden"]):not([type="submit"])',
      'input:not([type="hidden"]):not([type="button"])',
      'input:not([type="hidden"]):not([type="reset"])',
      "select",
      "textarea"
    ].join(", ");

    // Use a Set to deduplicate (the join above can repeat inputs)
    var allInputs = Array.from(form.querySelectorAll(
      'input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="reset"]):not([type="checkbox"]):not([type="radio"]),' +
      'select,' +
      'textarea'
    ));

    return allInputs.filter(function (el) {
      return !el.disabled &&
             !el.readOnly &&
             el.getAttribute("data-skip") !== "true" &&
             el.offsetParent !== null;   // visible check
    });
  }

  function setupAutoTab(form) {
    form.addEventListener("keydown", function (e) {
      // Only intercept Enter key
      if (e.key !== "Enter") return;

      var active = document.activeElement;
      if (!active) return;

      // Don't intercept Enter on textarea (multi-line) or buttons
      if (active.tagName === "TEXTAREA") return;
      if (active.tagName === "BUTTON") return;
      if (active.type === "submit" || active.type === "button") return;

      var fields = getFocusableFields(form);
      var idx = fields.indexOf(active);

      if (idx === -1) return;   // not in our list

      if (idx < fields.length - 1) {
        // Move to next field
        e.preventDefault();
        fields[idx + 1].focus();

        // If it's a text input, select all text so user can overwrite easily
        var next = fields[idx + 1];
        if (next.select && (next.type === "text" || next.type === "number" ||
            next.type === "email" || next.type === "tel" ||
            next.type === "password" || next.type === "date")) {
          next.select();
        }
      }
      // If it's the last field, let default form submit happen
    });
  }

  function setupAllForms() {
    var forms = document.querySelectorAll("form");
    forms.forEach(function (form) {
      setupAutoTab(form);
    });
  }


  /* ══════════════════════════════════════════════════════════════
     INIT — Run after DOM is ready
     ══════════════════════════════════════════════════════════════ */

  function init() {
    alignTables();
    setupAllForms();

    /* ── Watch for dynamically added rows / tables (marks entry, etc.) ── */
    if (window.MutationObserver) {
      var observer = new MutationObserver(function (mutations) {
        var needsAlign = mutations.some(function (m) {
          return m.addedNodes.length > 0;
        });
        if (needsAlign) {
          alignTables();
          // Re-setup forms in case new ones were injected via AJAX
          setupAllForms();
        }
      });

      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
  }

  /* Run when DOM is ready */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();   // already loaded
  }

})();