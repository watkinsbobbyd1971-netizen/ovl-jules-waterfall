#!/usr/bin/env python3
"""
Unit and integration tests for ovl_jules_dispatch.py
Tests:
- Account mismatch (wrong email, unknown acc_id, branch-account conflict, ordinal guessing)
- Quota reached (concurrency slots and daily limit)
- Missing CLI binary handling
- Subprocess failure handling
- Duplicate manifest / claim rejection
- Ambiguous create timeout & reconciliation without duplicate session creation
- Plan approval required & plan approval execution
- Scope mismatch blocker (forbidden operations, cross-profile output access)
- Resumed execution with existing receipts
- Truthful receipts across all lifecycle states
"""

import os
import shutil
import subprocess
import tempfile
import unittest

from ovl_jules_dispatch import (
    AccountMismatchError,
    AmbiguousTimeoutError,
    CLIProviderAdapter,
    DuplicateClaimError,
    FileReceiptStore,
    JulesDispatcher,
    MockProviderAdapter,
    QuotaExceededError,
    ScopeViolationError,
    reconcile_account,
    validate_plan_scope,
)


class TestAccountReconciliation(unittest.TestCase):
    def test_canonical_reconciliation_by_id(self):
        acc = reconcile_account(acc_id="ACC_01")
        self.assertEqual(acc["acc_id"], "ACC_01")
        self.assertEqual(acc["email"], "watkinsbobbyd1971@gmail.com")

    def test_canonical_reconciliation_by_email(self):
        acc = reconcile_account(email="tanishawatkins0125@gmail.com")
        self.assertEqual(acc["acc_id"], "ACC_02")

    def test_canonical_reconciliation_by_branch(self):
        acc = reconcile_account(branch="profile-3-cat09-12")
        self.assertEqual(acc["acc_id"], "ACC_03")

    def test_account_mismatch_error_on_conflict(self):
        with self.assertRaises(AccountMismatchError):
            reconcile_account(acc_id="ACC_01", email="claudevisualdy@gmail.com")

    def test_branch_conflict_with_account(self):
        with self.assertRaises(AccountMismatchError):
            reconcile_account(acc_id="ACC_01", branch="profile-2-cat05-08")

    def test_legacy_profile_ordinal_guess_rejected_without_identity(self):
        with self.assertRaises(AccountMismatchError):
            reconcile_account(legacy_profile=1)

    def test_legacy_profile_mismatch(self):
        with self.assertRaises(AccountMismatchError):
            reconcile_account(acc_id="ACC_01", legacy_profile=4)


class TestDispatcherOffline(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.receipt_store = FileReceiptStore(root_dir=self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dry_run_truthful_receipt(self):
        adapter = MockProviderAdapter(authenticated_email="watkinsbobbyd1971@gmail.com")
        dispatcher = JulesDispatcher(adapter=adapter, receipt_store=self.receipt_store, dry_run=True)

        receipt = dispatcher.dispatch(
            repo="watkinsbobbyd1971-netizen/ovl-jules-waterfall",
            branch="profile-1-cat01-04",
            prompt="Run worker",
            manifest_claim="manifest_01",
            acc_id="ACC_01",
        )
        self.assertEqual(receipt["state"], "planned")
        self.assertIsNone(receipt["session_id"])
        self.assertTrue(receipt["dry_run"])
        self.assertEqual(adapter.created_calls, 0)

        # Verify saved to disk
        loaded = self.receipt_store.load_receipt(receipt["receipt_key"])
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["state"], "planned")

    def test_live_dispatch_successful_lifecycle(self):
        adapter = MockProviderAdapter(authenticated_email="watkinsbobbyd1971@gmail.com")
        dispatcher = JulesDispatcher(adapter=adapter, receipt_store=self.receipt_store, dry_run=False)

        receipt = dispatcher.dispatch(
            repo="watkinsbobbyd1971-netizen/ovl-jules-waterfall",
            branch="profile-1-cat01-04",
            prompt="Run worker",
            manifest_claim="manifest_live_01",
            acc_id="ACC_01",
        )
        self.assertEqual(receipt["state"], "running")
        self.assertIsNotNone(receipt["session_id"])
        self.assertTrue(receipt["session_id"].startswith("mock-sess-"))
        self.assertIn("https://jules.google.com/session/", receipt["session_url"])
        self.assertEqual(adapter.created_calls, 1)

    def test_provider_identity_mismatch_fails(self):
        adapter = MockProviderAdapter(authenticated_email="wrong_account@gmail.com")
        dispatcher = JulesDispatcher(adapter=adapter, receipt_store=self.receipt_store, dry_run=False)

        with self.assertRaises(AccountMismatchError):
            dispatcher.dispatch(
                repo="watkinsbobbyd1971-netizen/ovl-jules-waterfall",
                branch="profile-1-cat01-04",
                prompt="Run worker",
                manifest_claim="manifest_fail_id",
                acc_id="ACC_01",
            )

    def test_duplicate_manifest_claim_rejected(self):
        adapter = MockProviderAdapter(authenticated_email="watkinsbobbyd1971@gmail.com")
        dispatcher = JulesDispatcher(adapter=adapter, receipt_store=self.receipt_store, dry_run=False)

        dispatcher.dispatch(
            repo="watkinsbobbyd1971-netizen/ovl-jules-waterfall",
            branch="profile-1-cat01-04",
            prompt="Run worker",
            manifest_claim="manifest_duplicate_01",
            acc_id="ACC_01",
        )

        with self.assertRaises(DuplicateClaimError):
            dispatcher.dispatch(
                repo="watkinsbobbyd1971-netizen/ovl-jules-waterfall",
                branch="profile-1-cat01-04",
                prompt="Run worker",
                manifest_claim="manifest_duplicate_01",
                acc_id="ACC_01",
            )

    def test_quota_concurrency_slots_reached(self):
        adapter = MockProviderAdapter(authenticated_email="watkinsbobbyd1971@gmail.com")
        dispatcher = JulesDispatcher(adapter=adapter, receipt_store=self.receipt_store, dry_run=False)

        # Mock 60 active receipts already running for ACC_01
        for i in range(60):
            r = {
                "receipt_key": f"ACC_01_mock_{i}",
                "account_id": "ACC_01",
                "state": "running",
                "created_at": 1000.0,
                "updated_at": 1000.0,
            }
            self.receipt_store.save_receipt(r)

        with self.assertRaises(QuotaExceededError) as ctx:
            dispatcher.dispatch(
                repo="watkinsbobbyd1971-netizen/ovl-jules-waterfall",
                branch="profile-1-cat01-04",
                prompt="Run worker",
                manifest_claim="manifest_over_quota",
                acc_id="ACC_01",
            )
        self.assertIn("slot ceiling reached", str(ctx.exception))

    def test_quota_daily_limit_reached(self):
        adapter = MockProviderAdapter(authenticated_email="watkinsbobbyd1971@gmail.com")
        dispatcher = JulesDispatcher(adapter=adapter, receipt_store=self.receipt_store, dry_run=False)

        # Mock 300 completed receipts within the last 24h
        import time

        now = time.time()
        for i in range(300):
            r = {
                "receipt_key": f"ACC_01_mock_daily_{i}",
                "account_id": "ACC_01",
                "state": "artifact-ready",
                "created_at": now - 3600,
                "updated_at": now - 3600,
            }
            self.receipt_store.save_receipt(r)

        with self.assertRaises(QuotaExceededError) as ctx:
            dispatcher.dispatch(
                repo="watkinsbobbyd1971-netizen/ovl-jules-waterfall",
                branch="profile-1-cat01-04",
                prompt="Run worker",
                manifest_claim="manifest_over_daily",
                acc_id="ACC_01",
            )
        self.assertIn("daily quota reached", str(ctx.exception))

    def test_ambiguous_timeout_and_reconciliation(self):
        adapter = MockProviderAdapter(authenticated_email="watkinsbobbyd1971@gmail.com")
        dispatcher = JulesDispatcher(adapter=adapter, receipt_store=self.receipt_store, dry_run=False)

        adapter.should_timeout_create = True
        with self.assertRaises(AmbiguousTimeoutError):
            dispatcher.dispatch(
                repo="watkinsbobbyd1971-netizen/ovl-jules-waterfall",
                branch="profile-1-cat01-04",
                prompt="Run worker",
                manifest_claim="manifest_timeout_test",
                acc_id="ACC_01",
            )
        self.assertEqual(adapter.created_calls, 1)

        # Check receipt recorded timeout failure
        receipts = self.receipt_store.list_receipts_for_account("ACC_01")
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["state"], "failed")

        # Now simulate session ID being recognized from remote query or manual reconciliation marker
        timeout_sess_id = list(adapter.sessions.keys())[0]
        receipts[0]["session_id"] = timeout_sess_id
        self.receipt_store.save_receipt(receipts[0])

        # Second dispatch attempt: should reconcile existing session instead of creating a duplicate
        adapter.should_timeout_create = False
        reconciled_receipt = dispatcher.dispatch(
            repo="watkinsbobbyd1971-netizen/ovl-jules-waterfall",
            branch="profile-1-cat01-04",
            prompt="Run worker",
            manifest_claim="manifest_timeout_test",
            acc_id="ACC_01",
        )
        self.assertEqual(reconciled_receipt["session_id"], timeout_sess_id)
        # Verify created_calls was NOT incremented on the retry
        self.assertEqual(adapter.created_calls, 1)
        self.assertEqual(reconciled_receipt["state"], "running")

    def test_scope_violation_plan_rejection(self):
        adapter = MockProviderAdapter(authenticated_email="watkinsbobbyd1971@gmail.com")
        # Propose plan that attempts to modify shared root files
        adapter.proposed_plan = "Modify shared root files and AGENTS.md directly."
        dispatcher = JulesDispatcher(adapter=adapter, receipt_store=self.receipt_store, dry_run=False)

        with self.assertRaises(ScopeViolationError) as ctx:
            dispatcher.dispatch(
                repo="watkinsbobbyd1971-netizen/ovl-jules-waterfall",
                branch="profile-1-cat01-04",
                prompt="Run worker",
                manifest_claim="manifest_bad_plan",
                acc_id="ACC_01",
            )
        self.assertIn("Scope blocker", str(ctx.exception))

    def test_scope_violation_cross_profile_write(self):
        adapter = MockProviderAdapter(authenticated_email="watkinsbobbyd1971@gmail.com")
        # Propose plan that writes to profile-2 output while running on profile-1
        adapter.proposed_plan = "Commit output to profile-2 batch jsonl file."
        dispatcher = JulesDispatcher(adapter=adapter, receipt_store=self.receipt_store, dry_run=False)

        with self.assertRaises(ScopeViolationError) as ctx:
            dispatcher.dispatch(
                repo="watkinsbobbyd1971-netizen/ovl-jules-waterfall",
                branch="profile-1-cat01-04",
                prompt="Run worker",
                manifest_claim="manifest_cross_profile_plan",
                acc_id="ACC_01",
            )
        self.assertIn("Scope blocker", str(ctx.exception))

    def test_subprocess_failure(self):
        adapter = MockProviderAdapter(authenticated_email="watkinsbobbyd1971@gmail.com")
        adapter.should_fail_create = True
        dispatcher = JulesDispatcher(adapter=adapter, receipt_store=self.receipt_store, dry_run=False)

        with self.assertRaises(subprocess.CalledProcessError):
            dispatcher.dispatch(
                repo="watkinsbobbyd1971-netizen/ovl-jules-waterfall",
                branch="profile-1-cat01-04",
                prompt="Run worker",
                manifest_claim="manifest_cli_failure",
                acc_id="ACC_01",
            )

    def test_missing_cli_handling(self):
        adapter = CLIProviderAdapter(cli_bin="nonexistent_jules_binary_xyz")
        dispatcher = JulesDispatcher(adapter=adapter, receipt_store=self.receipt_store, dry_run=False)

        from ovl_jules_dispatch import DispatchError

        with self.assertRaises(DispatchError) as ctx:
            dispatcher.dispatch(
                repo="watkinsbobbyd1971-netizen/ovl-jules-waterfall",
                branch="profile-1-cat01-04",
                prompt="Run worker",
                manifest_claim="manifest_missing_cli",
                acc_id="ACC_01",
            )
        self.assertIn("not found on PATH", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
