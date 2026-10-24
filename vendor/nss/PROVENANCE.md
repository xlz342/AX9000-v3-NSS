NSS kernel integration is selectively imported from:
https://github.com/qosmio/openwrt-ipq/tree/d6848fa2ea00193b5b7d3973e3990da7f608027c

Only 0600–0607 NSS/ECM/client patches, 0981 skb recycler, supporting net/include
files, and ipq8074-nss.dtsi are imported. Original copyright/license notices
are retained. The upstream LICENSES directory is included. manifest.json records
the SHA-256 of every imported source file. Kernel recipes, device image recipes,
stock DTS, NAND/MTD/UBI layout and upgrade logic remain from ImmortalWrt v25.12.2.

The parent AX9000 DTS receives one NSS include; this adds hardware nodes only.
The stock child DTS is unchanged. No donor ath11k NSS-wifi patches are imported.
NSS firmware/driver/ECM/clients/crypto packages come from the separately pinned
qosmio/nss-packages feed, not from this vendor directory.

Local rebase: 0600-4 bonding callbacks use the 6.12.103 RCU aggregator context,
read the aggregator through rcu_dereference(), and preserve upstream 802.3AD
neighbor broadcast handling while routing XOR mode through the NSS-aware helper.
The imported patch hash in manifest.json reflects this local rebase.
0603-5 VXLAN context is updated from old_iph to the 6.12.103 ip_hdr(skb) call.
0607-2 IPsec support is excluded: its MTU implementation predates the upstream
6.12.103 bounds checks. This project does not select NSS IPsec clients and does
not replace those upstream checks. NSS crypto itself remains selected.
0981 skb recycler's final release-data context preserves the newer zero-copy
reference increment in pskb_carve_inside_nonlinear().
