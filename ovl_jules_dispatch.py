#!/usr/bin/env python3
"""Fail-closed offline dispatcher engine. Default CLI is deliberately blocked.

Live activation requires an independently verified provider adapter, fresh account
identity/capacity, and a single shared locking receipt store for all launchers.
This module does not establish distributed capacity reservations across external
launchers: the provider must atomically enforce capacity at create time as well.
JSON manifest schema is documented in read_manifest. Local claims retain exact
canonical subject/property keys across accounts. No implicit claim release.
"""

from __future__ import annotations

import argparse
import contextlib
import fcntl
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

# Non-secret expected identities; these are not authentication evidence.
# Every live attempt requires an exact, fresh authenticated provider match.
CANONICAL_ACCOUNTS: Dict[str, Dict[str, Any]] = {
    "ACC_01": {
        "acc_id": "ACC_01",
        "email": "watkinsbobbyd1971@gmail.com",
        "legacy_profiles": [1, 6],
        "allowed_categories": ["CAT_01", "CAT_02", "CAT_03"],
    },
    "ACC_02": {
        "acc_id": "ACC_02",
        "email": "tanishawatkins0125@gmail.com",
        "legacy_profiles": [1, 2],
        "allowed_categories": ["CAT_04", "CAT_05", "CAT_06"],
    },
    "ACC_03": {
        "acc_id": "ACC_03",
        "email": "claudevisualdy@gmail.com",
        "legacy_profiles": [2, 3],
        "allowed_categories": ["CAT_07", "CAT_08", "CAT_09", "CAT_10"],
    },
    "ACC_04": {
        "acc_id": "ACC_04",
        "email": "tanishabobby4life@gmail.com",
        "legacy_profiles": [3, 4],
        "allowed_categories": ["CAT_11", "CAT_12", "CAT_13", "CAT_14"],
    },
    "ACC_05": {
        "acc_id": "ACC_05",
        "email": "magnificent19710125@gmail.com",
        "legacy_profiles": [4, 5],
        "allowed_categories": ["CAT_15", "CAT_16", "CAT_17"],
    },
    "ACC_06": {
        "acc_id": "ACC_06",
        "email": "optimizedvisuallearning@gmail.com",
        "legacy_profiles": [5, 6],
        "allowed_categories": ["CAT_18", "CAT_19", "CAT_20"],
    },
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


def read_manifest(path):
    """Only caller-owned JSON manifests; keys identify subject/property globally.

    Schema: {work_keys: [str], account_id: str, repo: str, branch: str,
             scope: {files: [relative path], actions: ["write"]}}
    All dispatchers must share this receipt directory on a filesystem with flock.
    Separate hosts/stores are NOT a distributed claim mechanism.
    """
    with open(path, encoding="utf-8") as handle:
        manifest = json.load(handle)
    keys = manifest.get("work_keys")
    if not isinstance(keys, list) or not keys or any(not isinstance(k, str) or not k or k != k.strip() for k in keys):
        raise DispatchError("Manifest requires nonempty canonical work_keys")
    if len(set(keys)) != len(keys):
        raise DuplicateClaimError("Repeated work key in manifest")
    manifest["work_keys"] = sorted(keys)
    if not isinstance(manifest.get("scope"), dict):
        raise ScopeViolationError("Structured authorized scope required")
    return manifest


def compute_manifest_hash(path):
    manifest = read_manifest(path)
    return hashlib.sha256(json.dumps(manifest["work_keys"], separators=(",", ":")).encode()).hexdigest()


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

    @contextlib.contextmanager
    def exclusive(self):
        # Serializes claim checking, durable submission marker and reconciliation.
        # Provider adapters must use bounded network deadlines.
        with open(os.path.join(self.root_dir, ".dispatch.lock"), "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def release_unsubmitted(self, receipt_key):
        """Explicit operator/runner action only; attempted submissions never released."""
        with self.exclusive():
            receipt = self.load_receipt(receipt_key)
            if not receipt or receipt.get("create_attempted"):
                raise DispatchError("Only verified unsubmitted claims can be released")
            receipt.update(state="released", updated_at=time.time())
            self.save_receipt(receipt)

    def all_receipts(self):
        for name in os.listdir(self.root_dir):
            if name.endswith(".json"):
                with open(os.path.join(self.root_dir, name), encoding="utf-8") as handle:
                    yield json.load(handle)  # Corrupt state fails closed.

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
            raise DispatchError("Unreadable existing receipt") from e

    def save_receipt(self, receipt: Dict[str, Any]) -> None:
        key = receipt["receipt_key"]
        path = self._file_path(key)
        tmp_path = path + f".tmp.{os.getpid()}"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2, sort_keys=True)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        directory = os.open(self.root_dir, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)

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


class CLIProviderAdapter(ProviderAdapter):
    """Live CLI contract is not verified. Never guess commands or simulate success.

    Install an explicitly verified ProviderAdapter in the calling runner instead.
    snapshot(account_id) must return authenticated email, observed_at, inventory
    completeness, active_count, max_concurrent and remaining_tasks. find_sessions
    must search durable idempotency_key markers; absence never licenses re-create.
    Session reads require account_id, repo, branch, idempotency_key, session_id,
    observed_at and explicit status. Plan approval is bound to plan_id.
    """
    def __init__(self, cli_bin="jules"):
        self.cli_bin = cli_bin

    def snapshot(self, account_id):
        raise DispatchError("Live adapter blocked: supported identity/capacity/session contract not verified")

    def create_session(self, **kwargs):
        raise DispatchError("Live adapter blocked; no CLI commands executed")


def validate_plan_scope(plan, branch, scope):
    if not isinstance(plan, dict) or not isinstance(scope, dict):
        return False, "Structured plan and authorized scope required"
    if plan.get("branch") != branch or not plan.get("plan_id"):
        return False, "Plan branch or immutable plan identifier missing/mismatched"
    files, actions = plan.get("files"), plan.get("actions")
    if not isinstance(files, list) or not files or not isinstance(actions, list) or not actions:
        return False, "Plan files/actions missing"
    if set(actions) != {"write"} or set(scope.get("actions", [])) != {"write"}:
        return False, "Only explicitly authorized file writes supported"
    for path in files:
        if not isinstance(path, str) or path.startswith("/") or "\\" in path or any(x in ("", ".", "..") for x in path.split("/")):
            return False, "Noncanonical file path"
        if any(x.startswith(".") or x.lower() in ("agents.md", "profile_config.json") for x in path.split("/")):
            return False, "Protected file"
        if path not in scope.get("files", []):
            return False, "File outside authorized scope: " + path
    return True, None


class JulesDispatcher:
    def __init__(self, adapter, receipt_store=None, dry_run=True):
        self.adapter = adapter
        self.receipt_store = receipt_store or FileReceiptStore()
        self.dry_run = dry_run

    def _save(self, receipt, state, reason=None):
        receipt.update(state=state, blocker_reason=reason, updated_at=time.time())
        self.receipt_store.save_receipt(receipt)
        return receipt

    @staticmethod
    def _fresh(observed_at):
        return type(observed_at) in (int, float) and 0 <= time.time() - observed_at <= 60

    def _observe(self, receipt, session, scope):
        expected = {k: receipt[k] for k in ("account_id", "repo", "branch", "idempotency_key")}
        if not isinstance(session, dict) or any(session.get(k) != v for k, v in expected.items()):
            return self._save(receipt, "ambiguous", "Session ownership/correlation unverified")
        sid = session.get("session_id")
        if not isinstance(sid, str) or not sid.strip() or (receipt.get("session_id") and receipt["session_id"] != sid):
            return self._save(receipt, "ambiguous", "Provider session identifier missing/mismatched")
        receipt.update(session_id=sid, session_url=session.get("session_url"))
        if not self._fresh(session.get("observed_at")):
            return self._save(receipt, "unknown", "Stale/missing session observation")
        status = session.get("status")
        if status == "awaiting-plan-approval":
            valid, reason = validate_plan_scope(session.get("proposed_plan"), receipt["branch"], scope)
            if not valid:
                return self._save(receipt, "awaiting-plan-approval", reason)
            plan_id = session["proposed_plan"]["plan_id"]
            if receipt.get("approval_attempted") == plan_id:
                return self._save(receipt, "awaiting-plan-approval", "Approval already attempted; awaiting provider observation")
            receipt["approval_attempted"] = plan_id
            self._save(receipt, "awaiting-plan-approval")
            self.adapter.approve_plan(sid, plan_id=plan_id)
            return self._observe(receipt, self.adapter.get_session(sid), scope)
        if status == "artifact-ready" and not session.get("artifact_url"):
            return self._save(receipt, "unknown", "Artifact evidence missing")
        if status in ("running", "artifact-ready") and (
                not receipt.get("approval_attempted") or session.get("approved_plan_id") != receipt["approval_attempted"]):
            return self._save(receipt, "blocked", "Execution observed without this assignment's verified plan approval")
        if status in ("running", "artifact-ready", "failed", "cancelled"):
            if session.get("artifact_url"):
                receipt["artifact_url"] = session["artifact_url"]
            return self._save(receipt, status)
        return self._save(receipt, "submitted" if status in ("pending", "queued") else "unknown", "Execution not observed")

    def dispatch(self, repo, branch, prompt, manifest_claim, acc_id=None, account_id=None, email=None, legacy_profile=None):
        account = reconcile_account(acc_id=acc_id or account_id, email=email, legacy_profile=legacy_profile)
        manifest = read_manifest(manifest_claim)
        for k, v in {"account_id": account["acc_id"], "repo": repo, "branch": branch}.items():
            if manifest.get(k) != v:
                raise DispatchError("Manifest ownership mismatch: " + k)
        valid, reason = validate_plan_scope(dict(manifest["scope"], branch=branch, plan_id="scope-validation"), branch, manifest["scope"])
        if not valid:
            raise ScopeViolationError(reason)
        key = hashlib.sha256(json.dumps(manifest["work_keys"], separators=(",", ":")).encode()).hexdigest()
        receipt = dict(receipt_key=key, manifest_hash=key, work_keys=manifest["work_keys"], account_id=account["acc_id"],
                       repo=repo, branch=branch, prompt=prompt, scope=manifest["scope"], idempotency_key=key,
                       session_id=None, created_at=time.time(), dry_run=self.dry_run, state="planned")
        if self.dry_run:
            # Preview does not reserve work or overwrite a live receipt.
            return receipt
        with self.receipt_store.exclusive():
            existing = self.receipt_store.load_receipt(key)
            if existing and existing.get("state") == "released":
                existing = None
            if existing:
                if any(existing.get(k) != receipt[k] for k in ("account_id", "repo", "branch", "prompt", "scope")):
                    raise DuplicateClaimError("Existing claim belongs to a different assignment")
                receipt = existing
            for other in self.receipt_store.all_receipts():
                if other.get("state") != "released" and other["receipt_key"] != key and set(other["work_keys"]) & set(receipt["work_keys"]):
                    raise DuplicateClaimError("Overlapping work keys already reserved")
            try:
                snapshot = self.adapter.snapshot(account["acc_id"])
                if (snapshot.get("email") != account["email"] or snapshot.get("account_id") != account["acc_id"]
                        or snapshot.get("identity_verified") is not True or not self._fresh(snapshot.get("observed_at"))):
                    return self._save(receipt, "blocked", "Fresh authenticated account identity required")
                if existing and existing.get("create_attempted"):
                    if receipt.get("session_id"):
                        return self._observe(receipt, self.adapter.get_session(receipt["session_id"]), manifest["scope"])
                    matches = self.adapter.find_sessions(idempotency_key=key, account_id=account["acc_id"])
                    if not isinstance(matches, list) or len(matches) != 1:
                        return self._save(receipt, "ambiguous", "Submission unresolved; creation will not be repeated")
                    return self._observe(receipt, matches[0], manifest["scope"])
                if snapshot.get("inventory_complete") is not True or any(type(snapshot.get(k)) is not int or snapshot[k] < 0 for k in ("active_count", "max_concurrent", "remaining_tasks")):
                    return self._save(receipt, "blocked", "Observed provider capacity unknown")
                known_ids = snapshot.get("session_ids")
                if not isinstance(known_ids, list) or any(not isinstance(x, str) for x in known_ids):
                    return self._save(receipt, "blocked", "Provider session inventory required")
                unobserved = sum(1 for other in self.receipt_store.all_receipts()
                    if other.get("account_id") == account["acc_id"] and other.get("create_attempted")
                    and other.get("session_id") not in known_ids)
                if snapshot["active_count"] + unobserved >= snapshot["max_concurrent"] or snapshot["remaining_tasks"] <= unobserved:
                    return self._save(receipt, "quota-blocked", "Observed provider capacity exhausted")
                receipt["create_attempted"] = True
                self._save(receipt, "submitted")  # Durable before any remote mutation.
                session = self.adapter.create_session(repo=repo, branch=branch, prompt=prompt, account_id=account["acc_id"], idempotency_key=key, require_plan_approval=True)
                return self._observe(receipt, session, manifest["scope"])
            except Exception as error:
                # A create/approval exception cannot establish that no side effect occurred.
                state = "ambiguous" if receipt.get("create_attempted") else "blocked"
                return self._save(receipt, state, type(error).__name__ + ": adapter operation unresolved")


def main():
    parser = argparse.ArgumentParser(description="Account-aware observable Jules dispatcher")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Target git repository")
    parser.add_argument("--branch", required=True, help="Target branch (e.g. profile-1-cat01-04)")
    parser.add_argument("--prompt", required=True, help="Task prompt")
    parser.add_argument("--manifest", required=True, help="Existing JSON manifest file path")
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
        if receipt["state"] not in ("planned", "running", "artifact-ready"):
            sys.exit(1)
    except Exception as e:
        print(f"[DISPATCH ERROR] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

