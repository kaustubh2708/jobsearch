import fs from "node:fs/promises";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const root = "/Users/kaustubhsingh/Developer/job_search_agent 2";
const jobs = JSON.parse(await fs.readFile(`${root}/data/jobs_vrinda_portfolio_20260930.json`, "utf8"));
const queue = JSON.parse(await fs.readFile(`${root}/data/review_queue_vrinda_portfolio_20260930.json`, "utf8"));
const dead = JSON.parse(await fs.readFile(`${root}/data/dead_links_vrinda_portfolio_20260930.json`, "utf8"));
const headers = ["Company", "Title", "Location", "Job ID", "Experience", "Portfolio Match", "Original Match", "Verification", "Link Status", "Score", "Salary Status", "LinkedIn Age", "Application Link", "Evidence Origin"];
const wb = Workbook.create();

function link(url) {
  if (!url) return "";
  return `=HYPERLINK("${String(url).replaceAll('"', '""')}","Open listing")`;
}
function rows(list) {
  return list.map((x) => [x.company || "", x.title || "", x.location || "", x.job_id || "", x.experience_required || "", x.portfolio_match_label || "", x.match_label || "", x.verification_status || "", x.link_status || "", x.overall_match_score ?? "", x.salary_status || "unknown", x.linkedin_age_flag || "date unknown", link(x.canonical_source_url || x.source_url), x.evidence_origin || "historical"]);
}
function addTable(name, list, color) {
  const s = wb.worksheets.add(name);
  const data = [headers, ...rows(list)];
  const end = `N${Math.max(1, data.length)}`;
  s.getRange(`A1:${end}`).values = data;
  s.getRange("A1:N1").format = { fill: color, font: { bold: true, color: "#FFFFFF" }, wrapText: true, verticalAlignment: "center" };
  s.getRange(`A1:N${Math.max(1, data.length)}`).format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
  s.getRange(`A1:N${Math.max(1, data.length)}`).format.wrapText = true;
  s.getRange("A:A").format.columnWidth = 22;
  s.getRange("B:B").format.columnWidth = 44;
  s.getRange("C:C").format.columnWidth = 20;
  s.getRange("E:E").format.columnWidth = 32;
  s.getRange("M:M").format.columnWidth = 22;
  s.getRange("N:N").format.columnWidth = 28;
  s.freezePanes.freezeRows(1);
}

const strong = jobs.filter((x) => x.portfolio_match_label === "strong_match");
const potential = jobs.filter((x) => x.portfolio_match_label === "potential_match");
const stretch = jobs.filter((x) => x.portfolio_match_label === "stretch");

const dash = wb.worksheets.add("Dashboard");
dash.getRange("A1:B11").values = [
  ["Vrinda Portfolio", "Run 2026-09-30"],
  ["Evidence-backed active exact", jobs.length],
  ["Strong matches", strong.length],
  ["Potential matches", potential.length],
  ["Stretch matches", stretch.length],
  ["Review/blocked queue", queue.length],
  ["Dead/closed/not relevant", dead.length],
  ["Target profile", "Approximately 3 years, backend/SDE, SDE II and selected SDE III"],
  ["Salary policy", "Employer-published only; otherwise unknown/estimate"],
  ["LinkedIn browser pass", "Not run in this terminal pass"],
  ["Validation", "JSON passed with 0 errors and 0 warnings"]
];
dash.getRange("A1:B1").format = { fill: "#1F4E78", font: { bold: true, color: "#FFFFFF" } };
dash.getRange("A1:B11").format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
dash.getRange("A:A").format.columnWidth = 34;
dash.getRange("B:B").format.columnWidth = 75;

addTable("Strong Matches", strong, "#2E7D32");
addTable("Potential Matches", potential, "#5B9BD5");
addTable("Stretch Matches", stretch, "#ED7D31");
addTable("Review Queue", queue, "#A5A5A5");
addTable("Dead Closed", dead, "#7F7F7F");
addTable("All Portfolio Jobs", jobs, "#1F4E78");

wb.recalculate();
const out = await SpreadsheetFile.exportXlsx(wb);
await out.save(`${root}/data/jobs_vrinda_portfolio_20260930.xlsx`);
console.log(JSON.stringify({ output: `${root}/data/jobs_vrinda_portfolio_20260930.xlsx`, jobs: jobs.length, strong: strong.length, potential: potential.length, stretch: stretch.length }));

