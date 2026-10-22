#!/bin/sh
# Read-only, explicitly selected diagnostic fields. No full UCI/Nikki dumps.
uname -a
echo '=== NSS modules ==='
lsmod | grep -E 'qca_nss|qca_ssdk|^ecm'
echo '=== NSS firmware/core boot ==='
dmesg | grep -Ei 'NSS.*(FW|firmware|core|boot)|NSS.FW' | tail -30
echo '=== ath11k parameters ==='
modinfo ath11k 2>/dev/null | grep '^parm:'
ax9000-wifi-nss status
echo '=== ECM accelerated connections ==='
for family in ipv4 ipv6; do
    node="/sys/kernel/debug/ecm/ecm_nss_$family/accelerated_count"
    printf '%s: ' "$family"
    if [ -r "$node" ]; then cat "$node"; else echo unavailable; fi
done
echo '=== NSS IPv4 statistics ==='
node=/sys/kernel/debug/qca-nss-drv/stats/ipv4
if [ -r "$node" ]; then
    grep -E 'create_requests|hash_hits|rx_packets|tx_packets|rx_bytes|tx_bytes' "$node"
fi
echo '=== forwarding and Nikki state ==='
for key in 'firewall.@defaults[0].flow_offloading' 'firewall.@defaults[0].flow_offloading_hw' 'network.globals.packet_steering' 'ecm.global.acceleration_engine' 'nikki.config.enabled'; do
    printf '%s=' "$key"; uci -q get "$key"
done
echo '=== Nikki counters (rule bodies omitted) ==='
for chain in lan_redirect lan_tun; do
    printf '%s\n' "$chain"
    nft list chain inet nikki "$chain" 2>/dev/null | grep -oE 'counter packets [0-9]+ bytes [0-9]+'
done
exit 0
