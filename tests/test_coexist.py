#!/usr/bin/env python3
"""Read-only router evidence plus LAN transparent TCP IPv4 egress tests."""
import argparse, datetime, ipaddress, json, os, re, subprocess, sys, time
from pathlib import Path
from urllib.parse import urlsplit
REMOTE = r"""
set -u
printf 'MODULES='
awk '$1 ~ /^(ecm|qca_nss_drv|qca_nss_dp)$/ {printf "%s ",$1}' /proc/modules
printf '\nENGINE='
uci -q get ecm.global.acceleration_engine || true
printf 'PASSWALL='
uci -q get passwall.@global[0].enabled || true
printf 'FLOW='
uci -q get firewall.@defaults[0].flow_offloading || true
printf 'FLOW_HW='
uci -q get firewall.@defaults[0].flow_offloading_hw || true
for f in /sys/kernel/debug/ecm/ecm_nss_ipv4/accelerated_count /sys/kernel/debug/ecm/ecm_nss_ipv6/accelerated_count; do
 printf 'STAT %s=' "$f"; cat "$f" 2>/dev/null || echo UNAVAILABLE
done
for f in /sys/kernel/debug/qca-nss-drv/stats/ipv4 /sys/kernel/debug/qca-nss-drv/stats/ipv6; do
 printf 'NSS %s\n' "$f"
 if test -r "$f"; then cat "$f"; else echo UNAVAILABLE; fi
done
printf 'NFT_BEGIN\n'
# Only counter totals; no addresses, rules, subscriptions, node names or keys.
if nft list table inet passwall >/dev/null 2>&1; then
 echo TABLE_PRESENT
 nft list table inet passwall | sed -n 's/.*counter packets \([0-9][0-9]*\) bytes \([0-9][0-9]*\).*/\1 \2/p'
else
 echo TABLE_ABSENT
fi
printf 'NFT_END\n'
"""

def command(args, **kw):
    return subprocess.run(args, text=True, capture_output=True, timeout=kw.pop('timeout', 45), **kw)

def snapshot(router):
    result=command(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10',router,'sh -s'],input=REMOTE)
    if result.returncode:
        raise RuntimeError('SSH snapshot failed: '+result.stderr.strip())
    text=result.stdout
    def value(name):
        match=re.search(r'^'+name+r'=(.*)$',text,re.M)
        return match.group(1).strip() if match else ''
    return dict(modules=value('MODULES').split(),engine=value('ENGINE'),passwall=value('PASSWALL'),
                flow=value('FLOW'),flow_hw=value('FLOW_HW'),evidence=text)

def extract_ip(text):
    text=text.strip()
    try:
        data=json.loads(text)
        if isinstance(data,dict):
            text=data.get('ip',data.get('address',''))
        elif isinstance(data,str): text=data
    except ValueError: pass
    return str(ipaddress.ip_address(text.strip()))

def egress(url,expected):
    result=command(['curl','-4','--noproxy','*','--fail','--silent','--show-error',
                    '--connect-timeout','10','--max-time','25','--max-filesize','65536',
                    '-H','Connection: close',url],timeout=30)
    if result.returncode: return dict(status='FAIL',error='curl failed',code=result.returncode)
    try: actual=extract_ip(result.stdout)
    except (ValueError,AttributeError): return dict(status='FAIL',error='Endpoint must return a plain IP or JSON ip/address')
    return dict(status='PASS' if actual==expected else 'FAIL',actual=actual,expected=expected)

def packet_counters(text):
    result={}; section=''
    for line in text.splitlines():
        if line.startswith('NSS '): section=line[4:]
        elif line.startswith('NFT_BEGIN'): section=''
        elif section:
            match=re.search(r'([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([0-9]+)',line)
            if match: result[section+':'+match.group(1)]=int(match.group(2))
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--router',required=True)
    for kind in ['proxy','direct']:
        ap.add_argument('--'+kind+'-url',required=True)
        ap.add_argument('--expected-'+kind+'-ip',required=True)
    ap.add_argument('--direct-download-url')
    ap.add_argument('--seconds',type=int,default=30,choices=range(5,301),metavar='5..300')
    ap.add_argument('--output',default='ax9000-coexist-test.json')
    args=ap.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_.-]+@[A-Za-z0-9_.:-]+',args.router):
        ap.error('router must be user@host')
    for url in [args.proxy_url,args.direct_url,args.direct_download_url]:
        if url:
            u=urlsplit(url)
            if u.scheme not in ['https','http'] or not u.hostname or u.username or u.password:
                ap.error('Use HTTP(S) URLs without embedded credentials')
    if urlsplit(args.proxy_url).hostname==urlsplit(args.direct_url).hostname:
        ap.error('Use different hostnames for forced PROXY and DIRECT rules')
    try:
        proxy=str(ipaddress.IPv4Address(args.expected_proxy_ip))
        direct=str(ipaddress.IPv4Address(args.expected_direct_ip))
    except ValueError: ap.error('This test requires independently known IPv4 egress addresses')
    if proxy==direct: ap.error('Equal expected egress IPs cannot distinguish proxy from bypass')
    report=dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                scope='LAN transparent TCP IPv4; no explicit proxy; router configuration unchanged',
                hardware_flow_attribution='INCONCLUSIVE',udp_ipv6_dns_failover_old_connections='NOT_TESTED',tests=[])
    code=2
    try:
        report['before']=snapshot(args.router)
        b=report['before']
        functional=(set(['ecm','qca_nss_drv','qca_nss_dp'])<=set(b['modules']) and b['engine']=='nss'
                    and b['passwall']=='1' and b['flow']=='0' and b['flow_hw']=='0'
                    and 'TABLE_PRESENT' in b['evidence'])
        report['services_before']='PASS' if functional else 'FAIL'
        for phase in ['before_load','after_load']:
            for repeat in range(3):
                for kind, url, expected in [('proxy',args.proxy_url,proxy),('direct',args.direct_url,direct)]:
                    report['tests'].append(dict(phase=phase,repeat=repeat,kind=kind,**egress(url,expected)))
            if phase=='before_load' and args.direct_download_url:
                load=command(['curl','-4','--noproxy','*','--fail','--silent','--show-error',
                              '--connect-timeout','10','--max-time',str(args.seconds),
                              '--output',os.devnull,'--write-out','%{size_download} %{speed_download}',
                              args.direct_download_url],timeout=args.seconds+15)
                report['load']=dict(code=load.returncode,bytes_and_bytes_per_second=load.stdout.strip())
                # Exit 28 is expected for a duration-limited transfer, provided it transferred data.
                try: load_ok=load.returncode in [0,28] and float(load.stdout.split()[0])>0
                except (ValueError,IndexError): load_ok=False
                functional= functional and load_ok
        report['after']=snapshot(args.router)
        a=report['after']
        functional= functional and set(['ecm','qca_nss_drv','qca_nss_dp'])<=set(a['modules']) and a['engine']=='nss' and a['passwall']=='1' and 'TABLE_PRESENT' in a['evidence']
        functional= functional and all(t['status']=='PASS' for t in report['tests'])
        report['functional_result']='PASS' if functional else 'FAIL'
        before_counts=packet_counters(b['evidence']); after_counts=packet_counters(a['evidence'])
        report['nss_counter_deltas']={k:after_counts[k]-v for k,v in before_counts.items() if k in after_counts}
        report['statistics_available']=all('UNAVAILABLE' not in s['evidence'] for s in [b,a])
        code=0 if functional else 1
        if functional and not report['statistics_available']: code=2
    except (OSError,RuntimeError,subprocess.TimeoutExpired) as error:
        report['error']=str(error)
    report['exit_code']=code
    Path(args.output).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ['before','after','tests']},indent=2))
    print('Report:',str(Path(args.output).resolve()))
    print('PASS is limited functional evidence, not proof of full hardware acceleration or leak freedom.')
    return code

if __name__=='__main__': sys.exit(main())
