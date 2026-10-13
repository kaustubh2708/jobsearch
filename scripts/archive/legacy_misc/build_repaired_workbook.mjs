import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "/Users/kaustubhsingh/Developer/job_search_agent 2";
const rows = JSON.parse(await fs.readFile(`${root}/data/jobs_repaired.json`, "utf8"));

const wb = Workbook.create();
const headers = [
  "Company", "Title", "Location", "Job ID", "Experience Required",
  "Min YOE", "Max YOE", "Verification", "Link Status", "Source Type",
  "Match Label", "Score", "Salary Status", "Posted At", "Age Days",
  "Age Flag", "Open Status", "Application URL"
];

function valuesFor(list) {
  return list.map((r) => [
    r.company, r.title, r.location, r.job_id, r.experience_required,
    r.experience_min_years_detected, r.experience_max_years_detected,
    r.verification_status, r.link_status, r.source_type, r.match_label,
    r.overall_match_score, r.salary_status, r.linkedin_posted_at,
    r.linkedin_age_days, r.linkedin_age_flag, r.linkedin_open_status,
    r.canonical_source_url
  ]);
}

function addTable(name, list, color) {
  const sheet = wb.worksheets.add(name);
  sheet.showGridLines = false;
  sheet.tabColor = color;
  const data = [headers, ...valuesFor(list)];
  const end = `R${data.length}`;
  sheet.getRange(`A1:${end}`).values = data;
  sheet.getRange("A1:R1").format = {
    fill: "#1F4E78", font: { bold: true, color: "#FFFFFF" },
    wrapText: true, verticalAlignment: "center"
  };
  sheet.getRange(`A1:R${data.length}`).format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
  sheet.getRange(`A2:R${data.length}`).format.wrapText = true;
  sheet.getRange(`L2:L${data.length}`).format.numberFormat = "0";
  sheet.getRange(`F2:G${data.length}`).format.numberFormat = "0.0";
  sheet.getRange("A:R").format.columnWidth = 16;
  sheet.getRange("B:B").format.columnWidth = 32;
  sheet.getRange("E:E").format.columnWidth = 24;
  sheet.getRange("R:R").format.columnWidth = 48;
  sheet.freezePanes.freezeRows(1);
  return sheet;
}

const active = rows.filter((r) => r.verification_status === "verified" && r.link_status === "active_exact");
const leads = rows.filter((r) => r.verification_status === "lead");
const older = rows.filter((r) => r.linkedin_age_flag === "older_than_1_month" || r.linkedin_age_flag === "closed_signal");

const dash = wb.worksheets.add("Dashboard");
dash.showGridLines = false;
dash.getRange("A1:B10").values = [
  ["Repaired Job Search Dataset", "Current master repair"],
  ["Generated", new Date().toISOString()],
  ["Total records", rows.length],
  ["Verified active exact", active.length],
  ["Leads awaiting verification", leads.length],
  ["Age/closure flags", older.length],
  ["Strong matches", rows.filter((r) => r.match_label === "strong_match").length],
  ["Potential matches", rows.filter((r) => r.match_label === "potential_match").length],
  ["Unknown salary status", rows.filter((r) => r.salary_status === "unknown").length],
  ["Rule", "Only page-level evidence can produce verified / active_exact"]
];
dash.getRange("A1:B1").format = { fill: "#1F4E78", font: { bold: true, color: "#FFFFFF" } };
dash.getRange("A1:B10").format.borders = { preset: "all", style: "thin", color: "#D9E2F3" };
dash.getRange("A:A").format.columnWidth = 28;
dash.getRange("B:B").format.columnWidth = 60;

addTable("All Records", rows, "#5B9BD5");
addTable("Verified Active", active, "#70AD47");
addTable("Review Queue", leads, "#ED7D31");
addTable("LinkedIn Freshness", older, "#A5A5A5");

wb.recalculate();
const out = await SpreadsheetFile.exportXlsx(wb);
await out.save(`${root}/data/jobs_repaired.xlsx`);
console.log(JSON.stringify({ output: `${root}/data/jobs_repaired.xlsx`, records: rows.length, active: active.length, leads: leads.length }));
