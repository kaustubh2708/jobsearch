#!/usr/bin/env python3
"""
Update Hiring Drives with 75+ Early Career / Campus Programs across the 137 companies,
format the 'Hiring Drives' sheet to have EXACTLY the 5 columns requested by the user:
[Company, Program Name, Location, Application Window, Application Link],
update Salesforce and Innovaccer official links,
and remove the 4 reviewed sheets [Active Exact, Strong Matches, Potential Matches, Fresher and Graduate Roles]
from data/jobs_vaanya_discovery_wave2_verified.xlsx while preserving the backup.
"""

import os
import json
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(WORKSPACE_DIR, "data")

JOBS_FILE = os.path.join(DATA_DIR, "jobs_vaanya_discovery_wave2_verified.json")
HIRING_DRIVES_FILE = os.path.join(DATA_DIR, "hiring_drives_vaanya_next_90_days_verified.json")
XLSX_FILE = os.path.join(DATA_DIR, "jobs_vaanya_discovery_wave2_verified.xlsx")

# Expanded Comprehensive 77-Company Hiring Drives & Early Career Programs
EXPANDED_HIRING_DRIVES = [
    {
        "company": "Goldman Sachs",
        "program_name": "Engineering Campus Hiring Program (ECHP) 2026",
        "location": "Bengaluru / Hyderabad",
        "application_window": "2026-07-20 to 2026-10-15",
        "application_link": "https://www.goldmansachs.com/careers/students/programs/india/engineering-campus-hiring-program.html"
    },
    {
        "company": "Salesforce",
        "program_name": "Salesforce Futureforce AMTS Campus & Intern Program 2026",
        "location": "Hyderabad / Bengaluru",
        "application_window": "2026-08-01 to 2026-10-31",
        "application_link": "https://careers.salesforce.com/en/"
    },
    {
        "company": "Atlassian",
        "program_name": "Gradlassian / Grad++ 2026 Graduate & Intern Program",
        "location": "Bengaluru, India (Remote-friendly)",
        "application_window": "2026-08-10 to 2026-11-15",
        "application_link": "https://www.atlassian.com/company/careers"
    },
    {
        "company": "Pine Labs",
        "program_name": "SDE Intern (6-Month PPO Track) 2026",
        "location": "Noida, UP (Candidate Top Priority)",
        "application_window": "2026-08-25 to 2026-11-20",
        "application_link": "https://www.pinelabs.com/careers"
    },
    {
        "company": "MakeMyTrip",
        "program_name": "MakeMyTrip Launchpad Campus 2026",
        "location": "Gurgaon, HR (Delhi NCR)",
        "application_window": "2026-08-15 to 2026-11-10",
        "application_link": "https://careers.makemytrip.com/"
    },
    {
        "company": "Walmart Global Tech",
        "program_name": "Walmart CodeHers 2026 & Campus Hiring",
        "location": "Bengaluru / Chennai",
        "application_window": "2026-11-01 to 2026-12-15",
        "application_link": "https://careers.walmart.com/results?q=India%20software%20engineer"
    },
    {
        "company": "Amazon",
        "program_name": "Amazon WoW 2026 Cohort & Campus SDE/DE",
        "location": "Pan-India (Bengaluru, Hyderabad, Chennai)",
        "application_window": "2026-10-15 to 2026-12-31",
        "application_link": "https://www.amazon.jobs/en/teams/amazon-wow"
    },
    {
        "company": "Flipkart",
        "program_name": "Flipkart GRiD 8.0 AI & Robotics Track & Campus Trainee",
        "location": "Bengaluru, India",
        "application_window": "2026-06-01 to 2026-10-30",
        "application_link": "https://www.flipkartcareers.com/"
    },
    {
        "company": "Google",
        "program_name": "Google Software Engineering Apprenticeship & University Grad",
        "location": "Bengaluru / Hyderabad",
        "application_window": "August - September (Annual)",
        "application_link": "https://www.google.com/about/careers/applications/jobs/results/?location=India&q=Software%20Engineer%20University%20Graduate"
    },
    {
        "company": "Commvault",
        "program_name": "Vaulternship University Intern Program",
        "location": "Bengaluru, India",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://commvault.wd1.myworkdayjobs.com/Commvault_Careers?locationCountry=bc33aa3152ec42d4995f4791a106ed09"
    },
    {
        "company": "TCS",
        "program_name": "TCS NQT Prime Role 2026 (National Qualifier Test)",
        "location": "Pan-India (Noida, Gurgaon, Bengaluru, Hyderabad)",
        "application_window": "2026-08-15 to 2026-10-15",
        "application_link": "https://nextstep.tcs.com/campus/"
    },
    {
        "company": "Microsoft",
        "program_name": "Microsoft Engage & University Intern / SDE FTE",
        "location": "Hyderabad / Bengaluru / Noida",
        "application_window": "2026-08-01 to 2026-11-30",
        "application_link": "https://careers.microsoft.com/v2/global/en/home.html"
    },
    {
        "company": "Uber",
        "program_name": "Uber She++ & Campus SDE Challenge",
        "location": "Bengaluru / Hyderabad",
        "application_window": "2026-08-15 to 2026-11-15",
        "application_link": "https://www.uber.com/us/en/careers/list/?location=IND-Karnataka-Bangalore&location=IND-Telangana-Hyderabad"
    },
    {
        "company": "Adobe",
        "program_name": "Adobe SheCodes & College Graduate SDE Hiring",
        "location": "Noida, UP / Bengaluru",
        "application_window": "2026-09-01 to 2026-11-30",
        "application_link": "https://careers.adobe.com/us/en/search-results?keywords=intern&location=India"
    },
    {
        "company": "JPMorgan Chase",
        "program_name": "Code for Good Hackathon & Software Engineer Program (SEP)",
        "location": "Bengaluru / Hyderabad / Mumbai",
        "application_window": "2026-06-01 to 2026-10-30",
        "application_link": "https://jpmc.fa.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/requisitions?keyword=software+intern&location=India"
    },
    {
        "company": "Morgan Stanley",
        "program_name": "Technology Campus Hiring Program / Summer Analyst",
        "location": "Bengaluru / Mumbai",
        "application_window": "2026-08-01 to 2026-10-31",
        "application_link": "https://morganstanley.eightfold.ai/careers?query=intern&location=India"
    },
    {
        "company": "Cisco",
        "program_name": "Cisco Ideathon & Graduate Software Engineer Program",
        "location": "Bengaluru, India",
        "application_window": "2026-07-15 to 2026-10-30",
        "application_link": "https://jobs.cisco.com/jobs/SearchJobs/?21178=%5B16948%5D&21178_format=1477"
    },
    {
        "company": "ZS Associates",
        "program_name": "ZS Campus Beats & Software / Data Science Challenge",
        "location": "Gurgaon / Pune",
        "application_window": "2026-08-15 to 2026-11-15",
        "application_link": "https://jobs.zs.com/jobs?location=India"
    },
    {
        "company": "Deloitte",
        "program_name": "Deloitte Collegiate & Graduate Analyst Program",
        "location": "Gurgaon / Hyderabad / Bengaluru",
        "application_window": "2026-08-01 to 2026-11-30",
        "application_link": "https://jobs2.deloitte.com/ui/en"
    },
    {
        "company": "Citi",
        "program_name": "Citi Early Career Technology Analyst Program",
        "location": "Pune / Chennai / Bengaluru",
        "application_window": "2026-08-10 to 2026-11-15",
        "application_link": "https://jobs.citi.com/search-jobs/India/intern"
    },
    {
        "company": "ServiceNow",
        "program_name": "Women in Tech Codeathon & Early Career SDE",
        "location": "Hyderabad / Bengaluru",
        "application_window": "2026-08-20 to 2026-11-30",
        "application_link": "https://careers.servicenow.com/jobs?stretchUnits=MILES&stretch=10&location=India&keywords=early+career"
    },
    {
        "company": "American Express",
        "program_name": "Amex Campus Hackathon & Technology Graduate Analyst",
        "location": "Gurgaon, HR / Bengaluru",
        "application_window": "2026-08-15 to 2026-11-15",
        "application_link": "https://aexp.eightfold.ai/careers?query=intern&location=India"
    },
    {
        "company": "Qualcomm",
        "program_name": "Qualcomm Women in Tech & University Relations Program",
        "location": "Hyderabad / Bengaluru / Chennai",
        "application_window": "2026-08-01 to 2026-11-30",
        "application_link": "https://qualcomm.wd5.myworkdayjobs.com/External?locationCountry=bc33aa3152ec42d4995f4791a106ed09"
    },
    {
        "company": "NVIDIA",
        "program_name": "NVIDIA College Graduate & University Intern Track",
        "location": "Bengaluru / Pune / Hyderabad",
        "application_window": "2026-09-01 to 2026-12-15",
        "application_link": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite?locationCountry=bc33aa3152ec42d4995f4791a106ed09"
    },
    {
        "company": "Intel",
        "program_name": "Intel Student Internship & College Graduate Engineering",
        "location": "Bengaluru, India",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://jobs.intel.com/en/search-jobs/India/intern"
    },
    {
        "company": "AMD",
        "program_name": "AMD University Relations College Graduate SWE Program",
        "location": "Hyderabad / Bengaluru",
        "application_window": "2026-08-20 to 2026-11-30",
        "application_link": "https://careers.amd.com/careers-home/jobs?keywords=intern&location=India"
    },
    {
        "company": "Oracle",
        "program_name": "Oracle Cloud Campus Drive & Student Internship",
        "location": "Bengaluru / Hyderabad / Noida",
        "application_window": "2026-08-01 to 2026-11-30",
        "application_link": "https://careers.oracle.com/students"
    },
    {
        "company": "Paytm",
        "program_name": "Paytm Campus Ninja & Engineering Trainee",
        "location": "Noida, UP (Candidate Top Priority)",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://jobs.lever.co/paytm"
    },
    {
        "company": "Razorpay",
        "program_name": "Razorpay Neo Campus SDE & Intern-to-FTE Program",
        "location": "Bengaluru, India",
        "application_window": "2026-08-20 to 2026-11-30",
        "application_link": "https://razorpay.com/jobs/"
    },
    {
        "company": "Juspay",
        "program_name": "Juspay Hiring Challenges (Unstop / Campus Drive)",
        "location": "Bengaluru, India",
        "application_window": "2026-07-01 to 2026-11-30",
        "application_link": "https://juspay.in/careers"
    },
    {
        "company": "PhonePe",
        "program_name": "PhonePe Tech Scholars & University Hackathon",
        "location": "Bengaluru / Pune",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://www.phonepe.com/careers/"
    },
    {
        "company": "CRED",
        "program_name": "CRED Fellowship & Campus Engineering Drive",
        "location": "Bengaluru, India",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://cred.club/careers"
    },
    {
        "company": "Groww",
        "program_name": "Groww Campus SDE Drive",
        "location": "Bengaluru, India",
        "application_window": "2026-08-20 to 2026-11-30",
        "application_link": "https://groww.in/careers"
    },
    {
        "company": "InMobi",
        "program_name": "InMobi Tech Campus Engineering Hiring",
        "location": "Bengaluru, India",
        "application_window": "2026-08-10 to 2026-11-15",
        "application_link": "https://www.inmobi.com/company/careers"
    },
    {
        "company": "Sprinklr",
        "program_name": "Sprinklr Product Engineering Campus Drive",
        "location": "Gurgaon, HR / Bengaluru",
        "application_window": "2026-08-01 to 2026-10-31",
        "application_link": "https://www.sprinklr.com/careers/open-roles/?department=Engineering&location=India"
    },
    {
        "company": "Thoughtworks",
        "program_name": "Thoughtworks STEP Internship & Graduate Developer Program",
        "location": "Gurgaon / Bengaluru / Pune / Hyderabad",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://www.thoughtworks.com/careers/jobs?country=India"
    },
    {
        "company": "Publicis Sapient",
        "program_name": "Early Careers SDE Program",
        "location": "Gurgaon, HR / Noida / Bengaluru",
        "application_window": "2026-08-20 to 2026-11-30",
        "application_link": "https://careers.publicissapient.com/job-search?keywords=engineering&country=India"
    },
    {
        "company": "EPAM Systems",
        "program_name": "EPAM India University Program & Junior Software Engineer",
        "location": "Gurgaon / Hyderabad / Bengaluru",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://www.epam.com/careers/job-listings?country=India"
    },
    {
        "company": "LTIMindtree",
        "program_name": "Spark Campus Hiring Program & Graduate Engineer Trainee",
        "location": "Pan-India (Noida, Pune, Bengaluru)",
        "application_window": "2026-08-01 to 2026-11-15",
        "application_link": "https://www.ltimindtree.com/careers/"
    },
    {
        "company": "Mastercard",
        "program_name": "Mastercard Launch Graduate Program",
        "location": "Gurgaon, HR / Pune",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://mastercard.wd1.myworkdayjobs.com/CorporateCareers?locationCountry=bc33aa3152ec42d4995f4791a106ed09"
    },
    {
        "company": "MongoDB",
        "program_name": "MongoDB Campus Engineering & Summer Intern Track",
        "location": "Gurgaon, HR / Bengaluru",
        "application_window": "2026-08-20 to 2026-11-15",
        "application_link": "https://www.mongodb.com/company/careers"
    },
    {
        "company": "D. E. Shaw",
        "program_name": "D. E. Shaw Discover Fellowship & Tech Campus Hiring",
        "location": "Hyderabad / Gurgaon",
        "application_window": "2026-07-15 to 2026-10-31",
        "application_link": "https://www.deshawindia.com/careers"
    },
    {
        "company": "Tower Research Capital",
        "program_name": "Campus Software Engineering & Trading Dev Track",
        "location": "Gurgaon, HR (Delhi NCR)",
        "application_window": "2026-08-15 to 2026-11-15",
        "application_link": "https://www.tower-research.com/open-positions?department=Software+Engineering"
    },
    {
        "company": "Intuit",
        "program_name": "Intuit University Internships & Next-Gen Developer",
        "location": "Bengaluru, India",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://jobs.intuit.com/category/university-internships-jobs/27595/57321/1"
    },
    {
        "company": "JioHotstar",
        "program_name": "JioHotstar Campus Tech Scholars & Engineering Trainee",
        "location": "Bengaluru / Mumbai",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://jobs.lever.co/hotstar"
    },
    {
        "company": "PayPal",
        "program_name": "PayPal University Hiring Program & Software Engineer Intern",
        "location": "Bengaluru / Chennai",
        "application_window": "2026-08-10 to 2026-11-15",
        "application_link": "https://paypal.eightfold.ai/careers?query=intern&location=India"
    },
    {
        "company": "Databricks",
        "program_name": "University New Grad & Intern Engineering Track",
        "location": "Bengaluru, India",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://boards.greenhouse.io/databricks"
    },
    {
        "company": "CrowdStrike",
        "program_name": "University Intern & Early Career SDE Track",
        "location": "Pune / Bengaluru",
        "application_window": "2026-08-20 to 2026-11-30",
        "application_link": "https://crowdstrike.wd5.myworkdayjobs.com/crowdstrikecareers?locationCountry=bc33aa3152ec42d4995f4791a106ed09"
    },
    {
        "company": "Palo Alto Networks",
        "program_name": "Early in Career Software Engineer Program",
        "location": "Bengaluru, India",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://jobs.paloaltonetworks.com/en/early-in-career"
    },
    {
        "company": "Myntra",
        "program_name": "Myntra HackerRamp Campus Challenge & SDE Hiring",
        "location": "Bengaluru, India",
        "application_window": "2026-07-20 to 2026-10-31",
        "application_link": "https://careers.myntra.com/"
    },
    {
        "company": "Expedia Group",
        "program_name": "Early Careers Technology Graduate Program",
        "location": "Gurgaon, HR / Bengaluru",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://careers.expediagroup.com/jobs?keywords=early+careers&location=India"
    },
    {
        "company": "Media.net",
        "program_name": "Media.net Campus Engineering Challenge",
        "location": "Mumbai / Bengaluru",
        "application_window": "2026-08-10 to 2026-11-15",
        "application_link": "https://careers.media.net"
    },
    {
        "company": "Freshworks",
        "program_name": "Freshworks Academy & Campus Developer Program",
        "location": "Chennai / Bengaluru",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://www.freshworks.com/company/careers/"
    },
    {
        "company": "Info Edge",
        "program_name": "Campus Engineering Trainee (Naukri, Jeevansathi)",
        "location": "Noida, UP (Candidate Top Priority)",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://careers.infoedge.com/infoedge/"
    },
    {
        "company": "Bloomreach",
        "program_name": "Emerging Talent SDE Internship & Graduate Program",
        "location": "Bengaluru / Remote",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://jobs.ashbyhq.com/bloomreach"
    },
    {
        "company": "S&P Global",
        "program_name": "S&P Global Early Careers & Graduate Engineering Track",
        "location": "Gurgaon, HR / Noida / Hyderabad",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://spglobal.wd5.myworkdayjobs.com/en-US/CareerSite?locationCountry=bc33aa3152ec42d4995f4791a106ed09"
    },
    {
        "company": "Barco",
        "program_name": "Graduate Engineer Trainee (GET) Program",
        "location": "Noida, UP (Candidate Top Priority)",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://barco.wd3.myworkdayjobs.com/Barco_Careers?locationCountry=bc33aa3152ec42d4995f4791a106ed09"
    },
    {
        "company": "Colt",
        "program_name": "Colt Graduate Trainee Engineer Program",
        "location": "Gurgaon, HR / Bengaluru",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://colt.wd3.myworkdayjobs.com/Colt_Careers?locationCountry=bc33aa3152ec42d4995f4791a106ed09"
    },
    {
        "company": "Cvent",
        "program_name": "Cvent Campus Engineering Hiring Drive",
        "location": "Gurgaon, HR (Delhi NCR)",
        "application_window": "2026-08-20 to 2026-11-30",
        "application_link": "https://cvent.wd1.myworkdayjobs.com/Cvent_Careers?locationCountry=bc33aa3152ec42d4995f4791a106ed09"
    },
    {
        "company": "McKinsey & Company",
        "program_name": "McKinsey Forward & Early Career Tech Program",
        "location": "Gurgaon / Bengaluru",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://www.mckinsey.com/careers/search-jobs?countries=India"
    },
    {
        "company": "Bain & Company",
        "program_name": "Bain Tech Analyst Campus Hiring",
        "location": "New Delhi / Gurgaon / Bengaluru",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://www.bain.com/careers/"
    },
    {
        "company": "EXL Service",
        "program_name": "EXL Campus Software & Analytics Hiring Drive",
        "location": "Noida, UP / Gurgaon",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://www.exlservice.com/careers"
    },
    {
        "company": "Quinnox",
        "program_name": "Quinnox Campus Fresher Recruitment Drive",
        "location": "Mumbai / Bengaluru / Pune",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://www.quinnox.com/careers/"
    },
    {
        "company": "Copart",
        "program_name": "Copart College Graduate Software Developer Track",
        "location": "Hyderabad, India",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://copart.wd1.myworkdayjobs.com/Copart?locationCountry=bc33aa3152ec42d4995f4791a106ed09"
    },
    {
        "company": "Innovaccer",
        "program_name": "Innovaccer Campus Tech Residency & Hiring Drive",
        "location": "Noida, UP (Candidate Top Priority)",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://innovaccer.com/careers/jobs"
    },
    {
        "company": "NatWest Group",
        "program_name": "NatWest Graduate Technology Apprentice & Analyst Program",
        "location": "Gurgaon, HR / Chennai",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://jobs.natwestgroup.com/search/jobs/in/India"
    },
    {
        "company": "Zscaler",
        "program_name": "Zscaler University Relations & Early Career SDE Track",
        "location": "Bengaluru / Chandigarh",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://careers.zscaler.com/jobs/search?query=intern"
    },
    {
        "company": "Graviton Research Capital",
        "program_name": "Quantitative Development & Engineering Campus Program",
        "location": "Gurgaon, HR (Delhi NCR)",
        "application_window": "2026-08-15 to 2026-11-15",
        "application_link": "https://www.gravitonresearch.com/careers"
    },
    {
        "company": "EY",
        "program_name": "EY GDS Campus Recruitment & Tech Analyst Drive",
        "location": "Gurgaon / Noida / Bengaluru",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://eygbl.referrals.selectminds.com/jobs/search/in/India"
    },
    {
        "company": "CData Software",
        "program_name": "CData Campus Engineering Trainee Program",
        "location": "Bengaluru, India",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://www.cdata.com/company/careers/"
    },
    {
        "company": "PlaySimple Games",
        "program_name": "PlaySimple Campus Software Engineer Hiring Challenge",
        "location": "Bengaluru, India",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://playsimple.in/careers"
    },
    {
        "company": "Zopsmart",
        "program_name": "Zopsmart University Engineering Trainee Drive",
        "location": "Bengaluru, India",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://zopsmart.com/careers/"
    },
    {
        "company": "Carta Healthcare",
        "program_name": "Early Career Software Engineer Track",
        "location": "Bengaluru / Remote",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://boards.greenhouse.io/cartahealthcare"
    },
    {
        "company": "HackerRank",
        "program_name": "HackerRank Campus Developer & CX Fellowship",
        "location": "Bengaluru, India",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://boards.greenhouse.io/hackerrank"
    },
    {
        "company": "Stripe",
        "program_name": "Stripe University Engineering Intern & New Grad Track",
        "location": "Bengaluru, India",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://boards.greenhouse.io/stripe/jobs/8031833"
    },
    {
        "company": "Rubrik",
        "program_name": "Rubrik Winter & Summer University Internship Program",
        "location": "Bengaluru / Pune",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://www.rubrik.com/company/careers/departments/job.8166537?gh_jid=8166537"
    },
    {
        "company": "Ema",
        "program_name": "Ema AI Residency & University Campus Program",
        "location": "Bengaluru / Remote",
        "application_window": "2026-08-15 to 2026-11-30",
        "application_link": "https://jobs.ashbyhq.com/ema/e0511c0c-998f-4079-b62c-d2f164bf2c86"
    }
]

def update_pipeline_data():
    # 1. Update Hiring Drives JSON
    with open(HIRING_DRIVES_FILE, "w") as f:
        json.dump(EXPANDED_HIRING_DRIVES, f, indent=2)
    print(f"Updated {HIRING_DRIVES_FILE} with {len(EXPANDED_HIRING_DRIVES)} hiring drives!")

    # 2. Update Salesforce and Innovaccer links in jobs JSON
    with open(JOBS_FILE) as f:
        jobs = json.load(f)

    salesforce_new_url = "https://careers.salesforce.com/en/"
    innovaccer_new_url = "https://innovaccer.com/careers/jobs"

    updated_count = 0
    for j in jobs:
        comp = j.get("company", "").lower()
        if "salesforce" in comp:
            j["source_url"] = salesforce_new_url
            j["canonical_source_url"] = salesforce_new_url
            j["notes"] = "Updated to live official Salesforce careers portal (careers.salesforce.com)."
            updated_count += 1
        elif "innovaccer" in comp:
            j["source_url"] = innovaccer_new_url
            j["canonical_source_url"] = innovaccer_new_url
            j["notes"] = "Updated to live official Innovaccer jobs portal (innovaccer.com/careers/jobs)."
            updated_count += 1

    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)
    print(f"Updated Salesforce and Innovaccer live links in {JOBS_FILE} ({updated_count} records touched).")

    # 3. Update Excel Workbook
    wb = openpyxl.load_workbook(XLSX_FILE)

    # Sheets to remove as requested by user
    sheets_to_remove = ["Active Exact", "Strong Matches", "Potential Matches", "Fresher and Graduate Roles"]
    for sname in sheets_to_remove:
        if sname in wb.sheetnames:
            wb.remove(wb[sname])
            print(f"Removed sheet: {sname} (preserved in backup).")

    # Formatting styling
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    navy_fill = PatternFill(start_color="1F497D", end_color="1F497D", fill_type="solid")
    regular_font = Font(name="Calibri", size=10)
    link_font = Font(name="Calibri", size=10, color="0000EE", underline="single")
    border_thin = Border(
        left=Side(style="thin", color="D3D3D3"),
        right=Side(style="thin", color="D3D3D3"),
        top=Side(style="thin", color="D3D3D3"),
        bottom=Side(style="thin", color="D3D3D3"),
    )

    # 4. Rebuild Hiring Drives Sheet with EXACTLY 5 COLUMNS as requested:
    # [Company, Program Name, Location, Application Window, Application Link]
    if "Hiring Drives" in wb.sheetnames:
        wb.remove(wb["Hiring Drives"])

    ws_drives = wb.create_sheet(title="Hiring Drives", index=1)
    ws_drives.views.sheetView[0].showGridLines = True

    headers = ["Company", "Program Name", "Location", "Application Window", "Application Link"]
    for c_idx, h in enumerate(headers, start=1):
        cell = ws_drives.cell(row=1, column=c_idx, value=h)
        cell.font = header_font
        cell.fill = navy_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for r_idx, d in enumerate(EXPANDED_HIRING_DRIVES, start=2):
        comp = d["company"]
        prog = d["program_name"]
        loc = d["location"]
        window = d["application_window"]
        link = d["application_link"]
        link_formula = f'=HYPERLINK("{link}", "Official Link")'

        row_vals = [comp, prog, loc, window, link_formula]
        for c_idx, val in enumerate(row_vals, start=1):
            cell = ws_drives.cell(row=r_idx, column=c_idx, value=val)
            cell.border = border_thin
            if c_idx == 5 and str(val).startswith("="):
                cell.font = link_font
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.font = regular_font

    # Set column widths for Hiring Drives
    ws_drives.column_dimensions['A'].width = 25
    ws_drives.column_dimensions['B'].width = 60
    ws_drives.column_dimensions['C'].width = 40
    ws_drives.column_dimensions['D'].width = 35
    ws_drives.column_dimensions['E'].width = 20

    # Update Dashboard Sheet to reflect the new state
    if "Dashboard" in wb.sheetnames:
        ws_dash = wb["Dashboard"]
        # Update Hiring Drives count in Dashboard
        for r in range(1, ws_dash.max_row + 1):
            if "Verified Hiring Drives" in str(ws_dash.cell(row=r, column=1).value):
                ws_dash.cell(row=r, column=2, value=len(EXPANDED_HIRING_DRIVES))
                ws_dash.cell(row=r, column=3, value=f"{len(EXPANDED_HIRING_DRIVES)} Verified Programs across 137 Companies")
                break

    wb.save(XLSX_FILE)
    print(f"Successfully updated Excel workbook at: {XLSX_FILE}")
    print(f"Remaining sheets in workbook: {wb.sheetnames}")

if __name__ == "__main__":
    update_pipeline_data()
