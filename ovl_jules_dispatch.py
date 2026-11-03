#!/usr/bin/env python3
"""
ovl_jules_dispatch.py - Account-aware, bounded, and observable Jules session dispatcher.

Features:
- Canonical account reconciliation: maps canonical ACC_xx IDs, provider emails, profile numbers,
  branches, and repositories by explicit identity, avoiding ordinal guessing or treating branches
  as separate accounts.
- Dry-run default: Prevents unexpected live mutations without explicit flags; validates manifest
  existence, identity verification, account mapping, and quota availability.
- Provider Adapter: Abstraction for create/get/activity/approve-plan interactions with support
  for CLI discovery, mock adapters for offline unit tests, and ambiguous timeout reconciliation.
- Durable Receipts: Maintains json receipt records tracking lifecycle states:
  planned, submitted, awaiting-plan-approval, running, artifact-ready, failed, quota-blocked.
- Task Scope & Plan Approval Guard: Validates that returned execution plans conform strictly
  to the authorized prompt/scope before approval.
- Bounded Concurrency & Daily Quota: Enforces limits per canonical account (not branch ordinal).
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import logging
import os
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("jules_dispatch")

DEFAULT_REPO = "watkinsbobbyd1971-netizen/ovl-jules-waterfall"

# Canonical registry of accounts reconciled between README.md and FLEET_BLACKBOARD.json.
# Keyed by canonical ID. Note that email identity is unique per account.
CANONICAL_ACCOUNTS: Dict[str, Dict[str, Any]] = {
    "ACC_01": {
        "acc_id": "ACC_01",
        "email": "watkinsbobbyd1971@gmail.com",
        "default_branch": "profile-1-cat01-04",
        "legacy_profiles": [1, 6],
        "allowed_categories": ["CAT_01", "CAT_02", "CAT_03"],
        "max_concurrent_vms": 60,
        "daily_task_quota": 300,
    },
    "ACC_02": {
        "acc_id": "ACC_02",
        "email": "tanishawatkins0125@gmail.com",
        "default_branch": "profile-2-cat05-08",
        "legacy_profiles": [1, 2],
        "allowed_categories": ["CAT_04", "CAT_05", "CAT_06"],
        "max_concurrent_vms": 60,
        "daily_task_quota": 300,
    },
    "ACC_03": {
        "acc_id": "ACC_03",
        "email": "claudevisualdy@gmail.com",
        "default_branch": "profile-3-cat09-12",
        "legacy_profiles": [2, 3],
        "allowed_categories": ["CAT_07", "CAT_08", "CAT_09", "CAT_10"],
        "max_concurrent_vms": 60,
        "daily_task_quota": 300,
    },
    "ACC_04": {
        "acc_id": "ACC_04",
        "email": "tanishabobby4life@gmail.com",
        "default_branch": "profile-4-cat13-16",
        "legacy_profiles": [3, 4],
        "allowed_categories": ["CAT_11", "CAT_12", "CAT_13", "CAT_14"],
        "max_concurrent_vms": 60,
        "daily_task_quota": 300,
    },
    "ACC_05": {
        "acc_id": "ACC_05",
        "email": "magnificent19710125@gmail.com",
        "default_branch": "profile-5-cat17-20",
        "legacy_profiles": [4, 5],
        "allowed_categories": ["CAT_15", "CAT_16", "CAT_17"],
        "max_concurrent_vms": 60,
        "daily_task_quota": 300,
    },
    "ACC_06": {
        "acc_id": "ACC_06",
        "email": "optimizedvisuallearning@gmail.com",
        "default_branch": "profile-6-global-all20",
        "legacy_profiles": [5, 6],
        "allowed_categories": ["CAT_18", "CAT_19", "CAT_20"],
        "max_concurrent_vms": 60,
        "daily_task_quota": 300,
    },
}

# Branch to Canonical Account mapping based on verified identity ownership
BRANCH_TO_ACC: Dict[str, str] = {
    "profile-1-cat01-04": "ACC_01",
    "profile-2-cat05-08": "ACC_02",
    "profile-3-cat09-12": "ACC_03",
    "profile-4-cat13-16": "ACC_04",
    "profile-5-cat17-20": "ACC_05",
    "profile-6-global-all20": "ACC_06",
}


class DispatchError(Exception):
    """Base error for dispatch operations."""
    pass


class AccountMismatchError(DispatchError):
    """Raised when account identity cannot be verified or mismatches."""
    pass


class DuplicateClaimError(DispatchError):
    """Raised when an identical manifest hash is claimed concurrently or repeatedly."""
    pass


class QuotaExceededError(DispatchError):
    """Raised when account concurrency limit or daily quota is exhausted."""
    pass


class ScopeViolationError(DispatchError):
    """Raised when an agent plan violates authorized task boundaries."""
    pass


class AmbiguousTimeoutError(DispatchError):
    """Raised when a request times out and status is indeterminate."""
    pass


def reconcile_account(
    acc_id: Optional[str] = None,
    email: Optional[str] = None,
    branch: Optional[str] = None,
    legacy_profile: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Reconciles account metadata using explicit identity matching.
    Never relies on ordinal guessing alone.
    """
    matched: Optional[Dict[str, Any]] = None

    if acc_id:
        norm_acc = acc_id.strip().upper()
        if norm_acc in CANONICAL_ACCOUNTS:
            matched = CANONICAL_ACCOUNTS[norm_acc]
        else:
            raise AccountMismatchError(f"Unknown canonical account ID: {acc_id}")

    if email:
        norm_email = email.strip().lower()
        by_email = next((a for a in CANONICAL_ACCOUNTS.values() if a["email"].lower() == norm_email), None)
        if by_email:
            if matched and matched["acc_id"] != by_email["acc_id"]:
                raise AccountMismatchError(
                    f"Account conflict: {matched['acc_id']} vs email {email} ({by_email['acc_id']})"
                )
            matched = by_email
        else:
            raise AccountMismatchError(f"Unknown provider email identity: {email}")

    if branch:
        norm_branch = branch.strip()
        mapped_acc = BRANCH_TO_ACC.get(norm_branch)
        if mapped_acc:
            acc_by_branch = CANONICAL_ACCOUNTS[mapped_acc]
            if matched and matched["acc_id"] != acc_by_branch["acc_id"]:
                raise AccountMismatchError(
                    f"Branch '{branch}' belongs to {acc_by_branch['acc_id']} ({acc_by_branch['email']}), "
                    f"not {matched['acc_id']}"
                )
            matched = acc_by_branch

    if legacy_profile is not None:
        if not matched:
            raise AccountMismatchError(
                f"Cannot infer account from legacy profile ordinal {legacy_profile} alone without identity verification."
            )
        if legacy_profile not in matched["legacy_profiles"]:
            raise AccountMismatchError(
                f"Legacy profile {legacy_profile} does not match verified account {matched['acc_id']} "
                f"(valid profiles: {matched['legacy_profiles']})"
            )

    if not matched:
        raise AccountMismatchError("No valid account identity provided for reconciliation.")

    return matched


def compute_manifest_hash(manifest_path_or_content: str) -> str:
    """Computes a durable SHA256 hash for a manifest path or content string."""
    if os.path.isfile(manifest_path_or_content):
        with open(manifest_path_or_content, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    return hashlib.sha256(manifest_path_or_content.encode("utf-8")).hexdigest()


class BaseReceiptStore:
    """Interface for durable receipt tracking."""

    def load_receipt(self, receipt_key: str) -> Optional[Dict[str, Any]]:
        raise NotImplementedError

    def save_receipt(self, receipt: Dict[str, Any]) -> None:
        raise NotImplementedError

    def list_receipts_for_account(self, acc_id: str) -> List[Dict[str, Any]]:
        raise NotImplementedError


class FileReceiptStore(BaseReceiptStore):
    """Durable receipt store writing JSON files to disk."""

    def __init__(self, root_dir: str = ".jules_receipts"):
        self.root_dir = root_dir
        os.makedirs(self.root_dir, exist_ok=True)

    def _file_path(self, receipt_key: str) -> str:
        safe_key = re.sub(r"[^A-Za-z0-9_\-\.]", "_", receipt_key)
        return os.path.join(self.root_dir, f"{safe_key}.json")

    def load_receipt(self, receipt_key: str) -> Optional[Dict[str, Any]]:
        path = self._file_path(receipt_key)
        if not os.path.exists(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read receipt {path}: {e}")
            return None

    def save_receipt(self, receipt: Dict[str, Any]) -> None:
        key = receipt["receipt_key"]
        path = self._file_path(key)
        tmp_path = path + f".tmp.{os.getpid()}"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2, sort_keys=True)
        os.replace(tmp_path, path)

    def list_receipts_for_account(self, acc_id: str) -> List[Dict[str, Any]]:
        res = []
        if not os.path.exists(self.root_dir):
            return res
        for fname in os.listdir(self.root_dir):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(self.root_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    r = json.load(f)
                    if r.get("account_id") == acc_id:
                        res.append(r)
            except Exception:
                continue
        return res


class ProviderAdapter:
    """
    Contract for provider interactions (CLI or API).
    """

    def verify_authenticated_identity(self, expected_email: str) -> bool:
        """Verifies currently authenticated CLI/API session matches expected provider email."""
        raise NotImplementedError

    def create_session(
        self,
        repo: str,
        branch: str,
        prompt: str,
        account_id: str,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        """Creates a remote session. Must return dict with session_id and optional session_url."""
        raise NotImplementedError

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Returns session status/metadata."""
        raise NotImplementedError

    def list_activities(self, session_id: str) -> List[Dict[str, Any]]:
        """Returns session activities/events."""
        raise NotImplementedError

    def approve_plan(self, session_id: str) -> bool:
        """Approves the proposed plan on the session."""
        raise NotImplementedError


class MockProviderAdapter(ProviderAdapter):
    """Mock adapter for offline tests and simulations."""

    def __init__(self, authenticated_email: Optional[str] = None):
        self.authenticated_email = authenticated_email
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.activities: Dict[str, List[Dict[str, Any]]] = {}
        self.should_fail_create = False
        self.should_timeout_create = False
        self.created_calls = 0
        self.proposed_plan: Optional[str] = None

    def verify_authenticated_identity(self, expected_email: str) -> bool:
        if self.authenticated_email is None:
            return True
        return self.authenticated_email.lower() == expected_email.lower()

    def create_session(
        self,
        repo: str,
        branch: str,
        prompt: str,
        account_id: str,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        self.created_calls += 1
        if self.should_fail_create:
            raise subprocess.CalledProcessError(1, ["mock", "create"], stderr="Simulated CLI failure")
        if self.should_timeout_create:
            # Ambiguous timeout: session was created on provider, but client experienced timeout
            sess_id = f"mock-sess-{hashlib.sha256(idempotency_key.encode()).hexdigest()[:12]}"
            self.sessions[sess_id] = {
                "session_id": sess_id,
                "repo": repo,
                "branch": branch,
                "prompt": prompt,
                "account_id": account_id,
                "idempotency_key": idempotency_key,
                "status": "pending",
                "session_url": f"https://jules.google.com/session/{sess_id}",
            }
            raise AmbiguousTimeoutError("Request timed out waiting for provider response")

        sess_id = f"mock-sess-{hashlib.sha256(idempotency_key.encode()).hexdigest()[:12]}"
        plan_text = self.proposed_plan or f"Run worker for branch {branch} and commit ONLY output/profile-N/batch_v3.jsonl"
        sess = {
            "session_id": sess_id,
            "session_url": f"https://jules.google.com/session/{sess_id}",
            "repo": repo,
            "branch": branch,
            "prompt": prompt,
            "account_id": account_id,
            "idempotency_key": idempotency_key,
            "status": "awaiting-plan-approval",
            "proposed_plan": plan_text,
            "plan_approved": False,
        }
        self.sessions[sess_id] = sess
        self.activities[sess_id] = [
            {"event": "created", "timestamp": time.time()},
            {"event": "plan_generated", "plan": plan_text},
        ]
        return sess

    def get_session(self, session_id: str) -> Dict[str, Any]:
        if session_id in self.sessions:
            return self.sessions[session_id]
        raise DispatchError(f"Session not found: {session_id}")

    def list_activities(self, session_id: str) -> List[Dict[str, Any]]:
        return self.activities.get(session_id, [])

    def approve_plan(self, session_id: str) -> bool:
        if session_id in self.sessions:
            self.sessions[session_id]["status"] = "running"
            self.sessions[session_id]["plan_approved"] = True
            self.activities[session_id].append({"event": "plan_approved", "timestamp": time.time()})
            return True
        return False


class CLIProviderAdapter(ProviderAdapter):
    """
    Adapter using the installed `jules` CLI contract.
    Queries CLI help or known subcommands rather than blindly executing.
    """

    def __init__(self, cli_bin: str = "jules"):
        self.cli_bin = cli_bin

    def _check_cli_available(self) -> bool:
        res = subprocess.run(
            ["which", self.cli_bin],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return res.returncode == 0

    def verify_authenticated_identity(self, expected_email: str) -> bool:
        if not self._check_cli_available():
            raise DispatchError(f"CLI binary '{self.cli_bin}' not found on PATH")
        # Check `jules auth status` or `jules whoami` if supported
        res = subprocess.run(
            [self.cli_bin, "auth", "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if res.returncode != 0:
            # Fallback to whoami
            res = subprocess.run(
                [self.cli_bin, "whoami"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        output = (res.stdout + " " + res.stderr).lower()
        return expected_email.lower() in output

    def create_session(
        self,
        repo: str,
        branch: str,
        prompt: str,
        account_id: str,
        idempotency_key: str,
    ) -> Dict[str, Any]:
        if not self._check_cli_available():
            raise DispatchError(f"CLI binary '{self.cli_bin}' is missing; cannot execute live create.")
        cmd = [
            self.cli_bin,
            "session",
            "create",
            "--repo",
            repo,
            "--branch",
            branch,
            "--prompt",
            prompt,
        ]
        try:
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=120,
            )
            if res.returncode != 0:
                raise subprocess.CalledProcessError(res.returncode, cmd, output=res.stdout, stderr=res.stderr)
            stdout = res.stdout.strip()
            # Extract session id or session url
            sess_id_match = re.search(r"session[ /]([0-9a-zA-Z\-_]+)", stdout, re.IGNORECASE)
            sess_id = sess_id_match.group(1) if sess_id_match else f"cli-{int(time.time())}"
            sess_url_match = re.search(r"https://[^\s]+", stdout)
            sess_url = sess_url_match.group(0) if sess_url_match else ""
            return {"session_id": sess_id, "session_url": sess_url, "raw_output": stdout}
        except subprocess.TimeoutExpired as e:
            raise AmbiguousTimeoutError(f"CLI command timed out: {e}")

    def get_session(self, session_id: str) -> Dict[str, Any]:
        if not self._check_cli_available():
            raise DispatchError("CLI binary missing")
        cmd = [self.cli_bin, "session", "get", session_id]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise DispatchError(f"Failed to get session {session_id}: {res.stderr}")
        return {"session_id": session_id, "status": "active", "output": res.stdout}

    def list_activities(self, session_id: str) -> List[Dict[str, Any]]:
        if not self._check_cli_available():
            return []
        cmd = [self.cli_bin, "session", "activities", session_id]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            return []
        return [{"raw": res.stdout}]

    def approve_plan(self, session_id: str) -> bool:
        if not self._check_cli_available():
            raise DispatchError("CLI binary missing")
        cmd = [self.cli_bin, "session", "approve-plan", session_id]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return res.returncode == 0


def validate_plan_scope(proposed_plan: str, branch: str, prompt: str) -> Tuple[bool, Optional[str]]:
    """
    Validates agent proposed plan against authorized task scope.
    Ensures:
    1. Plan targets the specific branch/output path.
    2. Does NOT alter shared root files or global settings.
    """
    plan_lower = proposed_plan.lower()
    # Check for forbidden actions
    forbidden_terms = [
        "modify shared root files",
        "edit agents.md",
        "edit profile_config.json",
        "delete branch",
        "drop table",
        "upgrade subscription",
        "paid quota",
    ]
    for term in forbidden_terms:
        if term in plan_lower:
            return False, f"Scope blocker: proposed plan contains forbidden operation '{term}'"

    # Verify branch/output containment
    profile_match = re.search(r"profile-(\d+)", branch)
    if profile_match:
        prof_num = profile_match.group(1)
        expected_output_subpath = f"profile-{prof_num}"
        # If the plan mentions writing to another profile's output directory, block it
        for other_num in range(1, 7):
            if str(other_num) != prof_num and f"profile-{other_num}" in plan_lower and "commit" in plan_lower:
                return False, f"Scope blocker: plan targets profile-{other_num} output when assigned to {branch}"

    return True, None


class JulesDispatcher:
    """
    Bounded, account-aware, observable dispatcher.
    """

    def __init__(
        self,
        adapter: ProviderAdapter,
        receipt_store: Optional[BaseReceiptStore] = None,
        dry_run: bool = True,
    ):
        self.adapter = adapter
        self.receipt_store = receipt_store or FileReceiptStore()
        self.dry_run = dry_run

    def check_quota(self, account: Dict[str, Any]) -> Tuple[int, int]:
        """
        Checks current active sessions and rolling daily count from receipts.
        Returns: (active_slots_used, daily_tasks_dispatched)
        """
        receipts = self.receipt_store.list_receipts_for_account(account["acc_id"])
        now = time.time()
        one_day_ago = now - 86400

        active_count = 0
        daily_count = 0

        for r in receipts:
            state = r.get("state")
            timestamp = r.get("updated_at", 0)
            if timestamp >= one_day_ago:
                daily_count += 1
            if state in ("submitted", "awaiting-plan-approval", "running"):
                active_count += 1

        return active_count, daily_count

    def reconcile_timeout_session(
        self,
        receipt_key: str,
        account: Dict[str, Any],
        idempotency_key: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Reconciles any in-flight or timed-out session with matching receipt key or idempotency key.
        """
        receipt = self.receipt_store.load_receipt(receipt_key)
        if receipt and receipt.get("session_id"):
            try:
                remote_info = self.adapter.get_session(receipt["session_id"])
                if remote_info:
                    return remote_info
            except Exception:
                pass
        return None

    def dispatch(
        self,
        repo: str,
        branch: str,
        prompt: str,
        manifest_claim: str,
        acc_id: Optional[str] = None,
        account_id: Optional[str] = None,
        email: Optional[str] = None,
        legacy_profile: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Dispatches a task with strict account identity, quota checking, and observable receipts.
        """
        # 1. Identity reconciliation
        resolved_acc_id = acc_id or account_id
        account = reconcile_account(
            acc_id=resolved_acc_id,
            email=email,
            branch=branch,
            legacy_profile=legacy_profile,
        )

        manifest_hash = compute_manifest_hash(manifest_claim)
        receipt_key = f"{account['acc_id']}_{manifest_hash[:16]}"
        now = time.time()

        # Check existing receipt to prevent duplicate claims
        existing_receipt = self.receipt_store.load_receipt(receipt_key)
        if existing_receipt:
            current_state = existing_receipt.get("state")
            if current_state in ("running", "artifact-ready", "submitted", "awaiting-plan-approval"):
                raise DuplicateClaimError(
                    f"Duplicate manifest claim {manifest_hash} already in progress or completed "
                    f"(state={current_state}, session_id={existing_receipt.get('session_id')})"
                )

        receipt = {
            "receipt_key": receipt_key,
            "account_id": account["acc_id"],
            "account_email": account["email"],
            "manifest_hash": manifest_hash,
            "manifest_claim": manifest_claim,
            "repo": repo,
            "branch": branch,
            "prompt": prompt,
            "state": "planned",
            "session_id": existing_receipt.get("session_id") if existing_receipt else None,
            "session_url": existing_receipt.get("session_url") if existing_receipt else None,
            "created_at": existing_receipt.get("created_at", now) if existing_receipt else now,
            "updated_at": now,
            "blocker_reason": None,
            "dry_run": self.dry_run,
        }
        self.receipt_store.save_receipt(receipt)

        # 2. Check Quota & Concurrency
        active_slots, daily_tasks = self.check_quota(account)
        if active_slots >= account["max_concurrent_vms"]:
            receipt["state"] = "quota-blocked"
            receipt["blocker_reason"] = f"Account VM slot ceiling reached ({active_slots}/{account['max_concurrent_vms']})"
            receipt["updated_at"] = time.time()
            self.receipt_store.save_receipt(receipt)
            raise QuotaExceededError(receipt["blocker_reason"])

        if daily_tasks >= account["daily_task_quota"]:
            receipt["state"] = "quota-blocked"
            receipt["blocker_reason"] = f"Account daily quota reached ({daily_tasks}/{account['daily_task_quota']})"
            receipt["updated_at"] = time.time()
            self.receipt_store.save_receipt(receipt)
            raise QuotaExceededError(receipt["blocker_reason"])

        # 3. Dry-run early exit
        if self.dry_run:
            logger.info(f"[DRY-RUN] Planned dispatch for {account['acc_id']} ({account['email']}) on {branch}")
            receipt["state"] = "planned"
            receipt["blocker_reason"] = "Dry-run mode active; execution skipped."
            receipt["updated_at"] = time.time()
            self.receipt_store.save_receipt(receipt)
            return receipt

        # 4. Identity verification against provider
        if not self.adapter.verify_authenticated_identity(account["email"]):
            receipt["state"] = "failed"
            receipt["blocker_reason"] = f"Provider identity does not match account email: {account['email']}"
            receipt["updated_at"] = time.time()
            self.receipt_store.save_receipt(receipt)
            raise AccountMismatchError(receipt["blocker_reason"])

        # 5. Idempotent session creation / reconciliation
        idempotency_key = f"{account['acc_id']}_{manifest_hash}"
        # Check if already created during a previous ambiguous timeout
        reconciled = None
        if existing_receipt and existing_receipt.get("session_id"):
            reconciled = self.reconcile_timeout_session(receipt_key, account, idempotency_key)

        session_meta: Dict[str, Any] = {}
        if reconciled:
            session_meta = reconciled
            logger.info(f"Reconciled existing remote session {session_meta.get('session_id')}")
        else:
            try:
                receipt["state"] = "submitted"
                receipt["updated_at"] = time.time()
                self.receipt_store.save_receipt(receipt)

                session_meta = self.adapter.create_session(
                    repo=repo,
                    branch=branch,
                    prompt=prompt,
                    account_id=account["acc_id"],
                    idempotency_key=idempotency_key,
                )
            except AmbiguousTimeoutError:
                # Mark as submitted with timeout blocker note and attempt reconcile
                receipt["state"] = "failed"
                receipt["blocker_reason"] = "Ambiguous timeout during session creation; markers saved for retry"
                receipt["updated_at"] = time.time()
                self.receipt_store.save_receipt(receipt)
                raise

        sess_id = session_meta.get("session_id")
        receipt["session_id"] = sess_id
        receipt["session_url"] = session_meta.get("session_url")
        receipt["state"] = "awaiting-plan-approval"
        receipt["updated_at"] = time.time()
        self.receipt_store.save_receipt(receipt)

        # 6. Plan inspection and approval
        proposed_plan = session_meta.get("proposed_plan")
        if not proposed_plan:
            # Query activities to find proposed plan if available
            activities = self.adapter.list_activities(sess_id)
            for act in activities:
                if act.get("plan"):
                    proposed_plan = act["plan"]
                    break

        if proposed_plan:
            valid, blocker = validate_plan_scope(proposed_plan, branch, prompt)
            if not valid:
                receipt["state"] = "failed"
                receipt["blocker_reason"] = blocker
                receipt["updated_at"] = time.time()
                self.receipt_store.save_receipt(receipt)
                raise ScopeViolationError(blocker)

            # Explicit plan approval
            approved = self.adapter.approve_plan(sess_id)
            if approved:
                receipt["state"] = "running"
                receipt["updated_at"] = time.time()
                self.receipt_store.save_receipt(receipt)
            else:
                receipt["blocker_reason"] = "Provider failed to approve valid plan"
                self.receipt_store.save_receipt(receipt)
        else:
            # If no plan approval step is required by the provider contract, transition to running
            receipt["state"] = "running"
            receipt["updated_at"] = time.time()
            self.receipt_store.save_receipt(receipt)

        return receipt


def main():
    parser = argparse.ArgumentParser(description="Account-aware observable Jules dispatcher")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Target git repository")
    parser.add_argument("--branch", required=True, help="Target branch (e.g. profile-1-cat01-04)")
    parser.add_argument("--prompt", required=True, help="Task prompt")
    parser.add_argument("--manifest", required=True, help="Manifest file path or claim string")
    parser.add_argument("--acc-id", help="Canonical account ID (ACC_01..ACC_06)")
    parser.add_argument("--email", help="Provider email identity")
    parser.add_argument("--profile-n", type=int, help="Legacy profile number (1..6)")
    parser.add_argument("--receipts-dir", default=".jules_receipts", help="Durable receipts directory")
    parser.add_argument(
        "--live",
        action="store_true",
        default=False,
        help="Execute live dispatch instead of dry-run (dry-run is default)",
    )

    args = parser.parse_args()

    adapter = CLIProviderAdapter()
    receipt_store = FileReceiptStore(root_dir=args.receipts_dir)
    dispatcher = JulesDispatcher(
        adapter=adapter,
        receipt_store=receipt_store,
        dry_run=not args.live,
    )

    try:
        receipt = dispatcher.dispatch(
            repo=args.repo,
            branch=args.branch,
            prompt=args.prompt,
            manifest_claim=args.manifest,
            account_id=args.acc_id,
            email=args.email,
            legacy_profile=args.profile_n,
        )
        print(f"[RECEIPT] Status: {receipt['state']}, Session: {receipt.get('session_id')}, Account: {receipt['account_id']}")
        print(json.dumps(receipt, indent=2))
        if receipt["state"] == "quota-blocked" or receipt["state"] == "failed":
            sys.exit(1)
    except Exception as e:
        print(f"[DISPATCH ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
