import importlib.util, sys, tempfile, contextlib, io, subprocess, json
from pathlib import Path
root=Path(sys.argv[1]);spec=importlib.util.spec_from_file_location('coexist',root/'tests/test_coexist.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
subprocess.run(['sh','-n'],input=m.REMOTE,text=True,check=True)
with tempfile.TemporaryDirectory() as tmp:
 for scenario,expected in [('ok',0),('bypass',1),('missing_module',1),('missing_stats',2)]:
  report=Path(tmp)/'report.json'
  sys.argv=['test','--router','root@192.168.1.1','--proxy-url','https://proxy.example/ip','--expected-proxy-ip','203.0.113.1','--direct-url','https://direct.example/ip','--expected-direct-ip','198.51.100.1','--output',str(report)]
  m.snapshot=lambda router: dict(modules=['ecm','qca_nss_drv','qca_nss_dp'] if scenario!='missing_module' else [],engine='nss',passwall='1',flow='0',flow_hw='0',evidence='TABLE_PRESENT'+(' UNAVAILABLE' if scenario=='missing_stats' else ''))
  m.egress=lambda url,ip: dict(status='FAIL' if scenario=='bypass' and 'proxy' in url else 'PASS')
  with contextlib.redirect_stdout(io.StringIO()): code=m.main()
  assert code==expected,(scenario,code)
  r=json.loads(report.read_text());assert r['hardware_flow_attribution']=='INCONCLUSIVE'
print('PASS offline cases: expected egress, proxy bypass, missing ECM, unavailable statistics; shell syntax. No hardware test performed.')
