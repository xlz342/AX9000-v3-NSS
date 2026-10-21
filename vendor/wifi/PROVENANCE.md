# Wi-Fi NSS provenance and rebase

Upstream: https://github.com/qosmio/openwrt-ipq/tree/92a2d104145c8d265851c4b388a41bd8e9c21cd9/package/kernel/mac80211/patches/nss

Reviewed main-nss HEAD on 2026-10-08 (Asia/Hong_Kong). Import only subsys (27 patches) and ath11k (69 patches). Preserve source copyright/license headers; license texts are retained in ../nss/LICENSES. No source firmware, partition, bootloader or calibration path replacement.

Donor backports 6.18.26 -> ImmortalWrt 6.18.39. Linux remains 6.12.103; upstream already includes the kernel-6.12 compatibility patches. These are different version axes.

Manual rebase changes:

* 068-ath11k-add-rx-histogram-stats.patch: apply MPDU byte accumulation after the new unconditional peer-id assignment. Do not resurrect the old `if (peer_id)` that excluded valid ID zero.
* 335-0002-ath11k-use-DECLARE_BITMAP-for-idr-operations.patch: retain the new `dp->tx_ring[i].tx_status = NULL` after kfree while changing TX pending cleanup to bitmap operations.
* 999-900-bss-transition-handling.patch: port ab->ar peer lookup changes around unconditional peer-ID lookup and monitor status assignment; preserve the new valid-ID-zero logic.

All official release mac80211 patches followed by these 96 patches applied with GNU patch --batch --forward --fuzz=0 locally. No failed hunk skipped. Application success is not a runtime correctness guarantee. The Actions build separately applies the same series and compiles the actual target modules.

recipe.patch adds minimal Kconfig/include paths/patch ordering/default module parameters. It keeps ImmortalWrt's separately packaged qcom-qmi-helpers rather than copying the donor's entire ath.mk. NSS mesh and mac80211 automatic redirect are not enabled. Firmware/NSS packages remain pinned to the proven v3 revision.

Apple issue https://github.com/qosmio/openwrt-ipq/issues/95 remained open with no confirmed fix during review. Recent donor change 819196f2 addresses AP_VLAN ext-vdev cleanup/open error paths; it is not evidence of an Apple EAPOL fix. Keep fallback nss_offload=0 frame_mode=1 and hardware acceptance mandatory.
