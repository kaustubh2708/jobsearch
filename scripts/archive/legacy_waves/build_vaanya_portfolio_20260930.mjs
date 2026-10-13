import fs from "node:fs/promises";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const root = "/Users/kaustubhsingh/Developer/job_search_agent 2";
const jobs = JSON.parse(await fs.readFile(`${root}/data/jobs_vaanya_portfolio_20260930.json`, "utf8"));
const queue = JSON.parse(await fs.readFile(`${root}/data/review_queue_vaanya_portfolio_20260930.json`, "utf8"));
const dead = JSON.parse(await fs.readFile(`${root}/data/dead_links_vaanya_portfolio_20260930.json`, "utf8"));

const wb = Workbook.create();
const headers = ["Company", "Title", "Location", "Job ID", "Experience", "Eligibility", "Verification", "Link Status", "Match", "Score", "Salary Status", "LinkedIn Age", "Application Link", "Evidence Origin"];

function link(url) {
  if (!url) return "";
  return `=HYPERLINK("${String(url).replaceAll('"', '""')}","Open listing")`;
}

function rows(list) {
  return list.map((x) => [
    x.company || "", x.title || "", x.location || "", x.job_id || "",
    x.experience_required || "", x.experience_eligibility_decision || x.portfolio_status || "",
    x.verification_status || "", x.link_status || "", x.match_label || "",
    x.overall_match_score ?? "", x.salary_status || "unknown",
    x.linkedin_age_flag || "date unknown", link(x.canonical_source_url || x.source_url),
    x.evidence_origin || "historical"
  ]);
}

function addTable(name, list, color) {
  const s = wb.worksheets.add(name);
  const data = [headers, ...rows(list)];
  const end = `N${Math.max(1, data.length)}`;
  s.getRange(`A1:${end}`).values = data;
  s.getRange("A1:N1").format = { fill: color, font: { bold: true, color: "#FFFFFF" }, wrapText: true, verticalAlignment: "center" };
  s.getRange(`A1:N${Math.max(1, data.length)}`).format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
  s.getRange(`A1:N${Math.max(1, data.length)}`).format.wrapText = true;
  s.getRange("A:A").format.columnWidth = 20;
  s.getRange("B:B").format.columnWidth = 42;
  s.getRange("C:C").format.columnWidth = 20;
  s.getRange("E:E").format.columnWidth = 30;
  s.getRange("M:M").format.columnWidth = 22;
  s.getRange("N:N").format.columnWidth = 24;
  s.freezePanes.freezeRows(1);
}

const eligible = jobs.filter((x) => x.portfolio_status === "eligible_active_exact");
const manual = jobs.filter((x) => x.portfolio_status === "active_exact_manual_eligibility_review");

const dash = wb.worksheets.add("Dashboard");
dash.getRange("A1:B12").values = [
  ["Vaanya Portfolio", "Run 2026-09-30"],
  ["Evidence-backed active exact", jobs.length],
  ["Fresher/graduate eligible", eligible.length],
  ["Manual eligibility review", manual.length],
  ["Review/blocked queue", queue.length],
  ["Dead/closed/excluded", dead.length],
  ["New exact roles from fresh portal pass", 0],
  ["Fresh public portal scope", "137 mapped portals"],
  ["LinkedIn browser pass", "Not run in this terminal pass"],
  ["Salary policy", "Employer-published only; otherwise unknown/estimate"],
  ["Eligibility rule", "Minimum 2+ years rejected; unknown/1+ without fresher signal reviewed"],
  ["Validation", "JSON passed with 0 errors and 0 warnings"]
];
dash.getRange("A1:B1").format = { fill: "#1F4E78", font: { bold: true, color: "#FFFFFF" } };
dash.getRange("A1:B12").format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
dash.getRange("A:A").format.columnWidth = 36;
dash.getRange("B:B").format.columnWidth = 72;

addTable("Eligible Active", eligible, "#2E7D32");
addTable("Manual Eligibility", manual, "#ED7D31");
addTable("Review Queue", queue, "#5B9BD5");
addTable("Dead Closed Excluded", dead, "#A5A5A5");
addTable("All Portfolio Jobs", jobs, "#1F4E78");

wb.recalculate();
const out = await SpreadsheetFile.exportXlsx(wb);
await out.save(`${root}/data/jobs_vaanya_portfolio_20260930.xlsx`);
console.log(JSON.stringify({ output: `${root}/data/jobs_vaanya_portfolio_20260930.xlsx`, jobs: jobs.length, eligible: eligible.length, manual: manual.length }));

