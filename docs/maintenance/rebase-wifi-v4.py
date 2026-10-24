from pathlib import Path
import re
root=Path(__file__).resolve().parents[1]/'outputs/AX9000-v4-NSS/vendor/wifi/patches/ath11k'
p=root/'999-900-bss-transition-handling.patch'
s=p.read_text()
old=' \tif (rxcb->peer_id)\n-\t\tpeer = ath11k_peer_find_by_id(ab, rxcb->peer_id);\n+\t\tpeer = ath11k_peer_find_by_id(ar, rxcb->peer_id);'
new='-\tpeer = ath11k_peer_find_by_id(ab, rxcb->peer_id);\n+\tpeer = ath11k_peer_find_by_id(ar, rxcb->peer_id);'
assert s.count(old)==1
s=s.replace(old,new)
old=' \t\tu16 peer_id;\n \n-\t\tpeer_id = ath11k_hal_rx_mpduinfo_get_peerid(ab, mpdu_info);\n+\t\tpeer_id = ath11k_hal_rx_mpduinfo_get_peerid(ar->ab, mpdu_info);\n \t\tif (peer_id)\n \t\t\tppdu_info->peer_id = peer_id;'
new=' \n-\t\tppdu_info->peer_id = ath11k_hal_rx_mpduinfo_get_peerid(ab, mpdu_info);\n+\t\tppdu_info->peer_id = ath11k_hal_rx_mpduinfo_get_peerid(ar->ab, mpdu_info);'
assert s.count(old)==1
s=s.replace(old,new)
lines=s.splitlines(keepends=True)
for i,line in enumerate(lines):
    m=re.match(r'@@ -(\d+),\d+ \+(\d+),\d+ @@(.*)',line)
    if not m:continue
    old=new=0
    for body in lines[i+1:]:
        if body.startswith(('@@','--- ','diff ','-- \n')):break
        if body.startswith((' ','-')):old+=1
        if body.startswith((' ','+')):new+=1
    lines[i]=f'@@ -{m[1]},{old} +{m[2]},{new} @@{m[3]}\n'
p.write_text(''.join(lines))
