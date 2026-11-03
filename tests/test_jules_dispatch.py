import json,tempfile,time,unittest
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from ovl_jules_dispatch import *
class Fake(ProviderAdapter):
 def __init__(self):self.n=0;self.sessions=[];self.fail=False;self.findable=True;self.quota=2;self.identity=True;self.status='pending';self.plan=None;self.approvals=0
 def snapshot(self,a):return dict(account_id=a,email=CANONICAL_ACCOUNTS[a]['email'],identity_verified=self.identity,observed_at=time.time(),inventory_complete=True,active_count=len(self.sessions),max_concurrent=2,remaining_tasks=self.quota,session_ids=[x['session_id'] for x in self.sessions])
 def create_session(self,**kw):
  self.n+=1;s=dict(kw,session_id='real-id',status=self.status,observed_at=time.time(),proposed_plan=self.plan);self.sessions.append(s)
  if self.fail:raise TimeoutError()
  return s
 def find_sessions(self,**kw):return self.sessions if self.findable else []
 def get_session(self,sid):return dict(self.sessions[0],observed_at=time.time())
 def approve_plan(self,sid,plan_id):self.approvals+=1;self.sessions[0]['status']='running';self.sessions[0]['approved_plan_id']=plan_id
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.store=FileReceiptStore(str(self.root/'r'));self.f=Fake();self.m=dict(work_keys=['a'],account_id='ACC_01',repo='r',branch='b',scope=dict(files=['output/a'],actions=['write']));self.p=self.root/'m';self.write()
 def tearDown(self):self.tmp.cleanup()
 def write(self):self.p.write_text(json.dumps(self.m))
 def call(self,dry=False,adapter=None):return JulesDispatcher(adapter or self.f,self.store,dry).dispatch('r','b','task',str(self.p),acc_id='ACC_01')
 def test_pending(self):self.assertEqual(self.call()['state'],'submitted')
 def test_timeout_reconcile(self):
  self.f.fail=True;self.assertEqual(self.call()['state'],'ambiguous');self.assertEqual(self.call()['session_id'],'real-id');self.assertEqual(self.f.n,1)
 def test_timeout_missing_never_recreate(self):
  self.f.fail=True;self.f.findable=False;self.call();self.call();self.assertEqual(self.f.n,1)
 def test_quota(self):self.f.quota=0;self.assertEqual(self.call()['state'],'quota-blocked');self.assertEqual(self.f.n,0)
 def test_identity(self):self.f.identity=False;self.assertEqual(self.call()['state'],'blocked');self.assertEqual(self.f.n,0)
 def test_branch_identity(self):
  with self.assertRaises(AccountMismatchError):reconcile_account(branch='profile-1-cat01-04')
 def test_synthetic_manifest(self):
  with self.assertRaises(FileNotFoundError):compute_manifest_hash('synthetic')
 def test_hash_order(self):
  self.m['work_keys']=['a','b'];self.write();a=compute_manifest_hash(str(self.p));self.m['work_keys']=['b','a'];self.write();self.assertEqual(a,compute_manifest_hash(str(self.p)))
 def test_concurrent_claim(self):
  with ThreadPoolExecutor(4) as p:list(p.map(lambda _:self.call(),range(8)))
  self.assertEqual(self.f.n,1)
 def test_cross_account_overlap(self):
  self.call();self.m.update(account_id='ACC_02',work_keys=['a','b']);self.write()
  with self.assertRaises(DuplicateClaimError):JulesDispatcher(self.f,self.store,False).dispatch('r','b','task',str(self.p),acc_id='ACC_02')
 def test_dryrun(self):self.call(True);self.assertEqual(list(self.store.all_receipts()),[])
 def test_poll_running(self):
  self.f.status='awaiting-plan-approval';self.f.plan=dict(branch='b',plan_id='p',files=['output/a'],actions=['write']);self.call();self.assertEqual(self.call()['state'],'running');self.assertEqual(self.f.n,1)
 def test_scope_approval(self):
  self.f.status='awaiting-plan-approval';self.f.plan=dict(branch='b',plan_id='p',files=['output/a'],actions=['write']);self.assertEqual(self.call()['state'],'running');self.assertEqual(self.f.approvals,1)
 def test_text_plan(self):self.f.status='awaiting-plan-approval';self.f.plan='edit README.md';self.assertEqual(self.call()['state'],'awaiting-plan-approval');self.assertEqual(self.f.approvals,0)
 def test_scope_escape(self):
  for path in ['README.md','output/../AGENTS.md','/output/a','AGENTS.md']:
   self.assertFalse(validate_plan_scope(dict(branch='b',plan_id='p',files=[path],actions=['write']),'b',self.m['scope'])[0])
 def test_live_cli_no_subprocess(self):
  from unittest.mock import patch
  with patch('subprocess.run',side_effect=AssertionError()):self.assertEqual(self.call(adapter=CLIProviderAdapter())['state'],'blocked')
 def test_corrupt_state(self):
  self.call();next((self.root/'r').glob('*.json')).write_text('bad')
  with self.assertRaises(DispatchError):self.call()
 def test_running_without_approved_plan_blocked(self):
  self.f.status='running';self.assertEqual(self.call()['state'],'blocked')
 def test_invalid_scope_precreate(self):
  self.m['scope']['files']=['../AGENTS.md'];self.write()
  with self.assertRaises(ScopeViolationError):self.call()
  self.assertEqual(self.f.n,0)
 def test_unobserved_reservation_reduces_capacity(self):
  original=self.f.snapshot
  def stale_inventory(a):
   r=original(a);r.update(active_count=0,session_ids=[],max_concurrent=1);return r
  self.f.snapshot=stale_inventory;self.call();self.m['work_keys']=['b'];self.write()
  self.assertEqual(self.call()['state'],'quota-blocked');self.assertEqual(self.f.n,1)
 def test_release_only_unsubmitted(self):
  self.f.quota=0;r=self.call();self.store.release_unsubmitted(r['receipt_key']);self.f.quota=2;self.call()
  with self.assertRaises(DispatchError):self.store.release_unsubmitted(r['receipt_key'])
 def test_manifest_read_once(self):
  from unittest.mock import patch
  original=read_manifest
  with patch('ovl_jules_dispatch.read_manifest', wraps=original) as reader:
   self.call();self.assertEqual(reader.call_count,1)
 def test_fsync_receipt_and_directory(self):
  from unittest.mock import patch
  import os
  with patch('ovl_jules_dispatch.os.fsync', wraps=os.fsync) as sync:
   self.call();self.assertGreaterEqual(sync.call_count,4)
 def test_unknown_plan_command_rejected(self):
  p=dict(branch='b',plan_id='p',files=['output/a'],actions=['write'],command='rm -rf other')
  self.assertFalse(validate_plan_scope(p,'b',self.m['scope'])[0])
if __name__=='__main__':unittest.main()
