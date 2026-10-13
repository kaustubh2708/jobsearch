#!/usr/bin/env python3
"""Comprehensive Automated Test Suite for Strict Job Validator.

Tests that the validator strictly enforces evidence rules and rejects impossible states:
  - Rejects 403s, 404s, or timeouts marked as active_exact or verified.
  - Rejects active_exact lacking visible application forms or page title evidence.
  - Rejects generic career portal URLs claiming direct/active status.
  - Rejects forced 0–1 experience claims when source JD states 0–2 or 2+ years.
  - Rejects unknown experience marked 'eligible' without review.
  - Rejects confirmed salary statuses without published salary numbers.
  - Allows strong matches that are pending verification (needs_verification=True).
  - Accepts authentic, fully evidenced records.
"""

import copy
import unittest
from pathlib import Path

from scripts.validate_jobs import validate_job_records

BASE_VALID_RECORD = {
    "company": "Cisco",
    "title": "Software Engineer",
    "location": "Bengaluru, Karnataka, India",
    "job_id": "internal:test_swe_001",
    "experience_required": "Bachelor’s degree in CS/IT/ECE; 0–1 year entry-level full-time intake.",
    "experience_min_years_detected": 0,
    "experience_max_years_detected": 1,
    "experience_eligibility_decision": "eligible",
    "experience_eligibility_reason": "Explicit 0–1 year experience matches fresher target.",
    "skills": ["Python", "C++", "Networking", "Linux"],
    "original_source_url": "https://careers.cisco.com/global/en/job/12345/Software-Engineer",
    "canonical_source_url": "https://careers.cisco.com/global/en/job/12345/Software-Engineer",
    "source_url": "https://careers.cisco.com/global/en/job/12345/Software-Engineer",
    "link_status": "active_exact",
    "source_url_is_direct": True,
    "source_type": "official_career_page",
    "verification_status": "verified",
    "needs_verification": False,
    "checked_at": "2026-10-13T10:00:00Z",
    "verification_reason": "Verified Live Exact Requisition with active application route (HTTP 200).",
    "salary_status": "estimated_market",
    "salary_fit": "estimated_above_target",
    "role_fit_score": 25,
    "experience_or_batch_fit_score": 20,
    "skill_fit_score": 18,
    "location_fit_score": 10,
    "source_evidence_score": 5,
    "salary_fit_score": 15,
    "freshness_score": 5,
    "overall_match_score": 98,
    "match_label": "strong_match",
    "status": "new",
    "actual_http_status": 200,
    "application_form_visible": True,
    "page_title_actual": "Software Engineer - Cisco Careers",
    "page_company_actual": "Cisco",
    "page_location_actual": "Bengaluru, Karnataka, India",
}


class TestStrictJobValidator(unittest.TestCase):

    def test_accept_valid_record_with_complete_evidence(self):
        """A properly evidenced record must pass with zero errors."""
        rec = copy.deepcopy(BASE_VALID_RECORD)
        errors, warnings = validate_job_records([rec])
        self.assertEqual(errors, [], f"Expected 0 errors, got: {errors}")

    def test_reject_403_marked_as_active_exact(self):
        """A 403 Forbidden response must NEVER be accepted as active_exact or verified."""
        rec = copy.deepcopy(BASE_VALID_RECORD)
        rec["actual_http_status"] = 403
        rec["link_status"] = "active_exact"
        rec["verification_status"] = "verified"

        errors, _ = validate_job_records([rec])
        self.assertTrue(any("must have actual HTTP 200" in e for e in errors), f"Errors: {errors}")

    def test_reject_404_marked_as_active_exact(self):
        """A 404 Not Found response must NEVER be accepted as active_exact."""
        rec = copy.deepcopy(BASE_VALID_RECORD)
        rec["actual_http_status"] = 404
        rec["link_status"] = "active_exact"

        errors, _ = validate_job_records([rec])
        self.assertTrue(any("must have actual HTTP 200" in e for e in errors), f"Errors: {errors}")

    def test_reject_active_exact_without_visible_application_form(self):
        """active_exact requires observed application_form_visible=True."""
        rec = copy.deepcopy(BASE_VALID_RECORD)
        rec["application_form_visible"] = False

        errors, _ = validate_job_records([rec])
        self.assertTrue(any("visible application form/route" in e for e in errors), f"Errors: {errors}")

    def test_reject_active_exact_without_page_title(self):
        """active_exact requires observed page_title_actual."""
        rec = copy.deepcopy(BASE_VALID_RECORD)
        rec["page_title_actual"] = None

        errors, _ = validate_job_records([rec])
        self.assertTrue(any("page_title_actual" in e for e in errors), f"Errors: {errors}")

    def test_reject_generic_career_url_as_active_exact(self):
        """A generic portal URL (/careers) cannot be active_exact or source_url_is_direct=True."""
        rec = copy.deepcopy(BASE_VALID_RECORD)
        rec["canonical_source_url"] = "https://careers.cisco.com/careers"
        rec["link_status"] = "active_exact"

        errors, _ = validate_job_records([rec])
        self.assertTrue(any("cannot have link_status=active_exact" in e for e in errors), f"Errors: {errors}")

    def test_reject_forced_0_to_1_when_source_says_0_to_2(self):
        """Rejects falsified bounds where source states 0–2 years but max_years is forced to 1."""
        rec = copy.deepcopy(BASE_VALID_RECORD)
        rec["experience_required"] = "Bachelor’s degree in CS; 0–2 years of experience required."
        rec["experience_eligibility_decision"] = "eligible"
        rec["experience_min_years_detected"] = 0
        rec["experience_max_years_detected"] = 1  # Falsified max_years!

        errors, _ = validate_job_records([rec])
        self.assertTrue(any("falsified experience bounds" in e for e in errors), f"Errors: {errors}")

    def test_reject_unknown_experience_marked_eligible(self):
        """Rejects experience_eligibility_decision='eligible' when experience_required is empty/unknown."""
        rec = copy.deepcopy(BASE_VALID_RECORD)
        rec["experience_required"] = ""
        rec["experience_eligibility_decision"] = "eligible"

        errors, _ = validate_job_records([rec])
        self.assertTrue(any("when experience_required is empty/unknown" in e for e in errors), f"Errors: {errors}")

    def test_reject_2_plus_years_marked_eligible_for_fresher(self):
        """Rejects experience_eligibility_decision='eligible' when JD explicitly requires 3+ years."""
        rec = copy.deepcopy(BASE_VALID_RECORD)
        rec["experience_required"] = "Requires 3+ years of professional backend experience."
        rec["experience_eligibility_decision"] = "eligible"

        errors, _ = validate_job_records([rec])
        self.assertTrue(any("role requires 2+ years of experience" in e for e in errors), f"Errors: {errors}")

    def test_reject_confirmed_salary_without_published_numbers(self):
        """salary_status='confirmed_published' requires non-null employer_published_salary object."""
        rec = copy.deepcopy(BASE_VALID_RECORD)
        rec["salary_status"] = "confirmed_published"
        rec["employer_published_salary"] = None

        errors, _ = validate_job_records([rec])
        self.assertTrue(any("requires non-null employer_published_salary" in e for e in errors), f"Errors: {errors}")

    def test_allow_strong_match_with_manual_check_when_needs_verification(self):
        """A role can be a strong potential match while still needing verification (manual_check)."""
        rec = copy.deepcopy(BASE_VALID_RECORD)
        rec["verification_status"] = "manual_check"
        rec["link_status"] = "blocked_403"
        rec["actual_http_status"] = 403
        rec["needs_verification"] = True
        rec["application_form_visible"] = False
        rec["match_label"] = "strong_match"

        errors, warnings = validate_job_records([rec])
        self.assertEqual(errors, [], f"Expected 0 errors for pending manual_check strong_match, got: {errors}")


if __name__ == "__main__":
    unittest.main()
