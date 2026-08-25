# SmartBranch 360 — Fault Cards

## Fault 1: Wrong default gateway
- **Injection:** On PC2, manually set gateway to 10.10.10.254 (nonexistent) instead of DHCP.
- **Symptom:** PC2 gets an IP but `ping 10.10.30.10` and internet both fail; local VLAN 10 pings work.
- **Root cause:** Incorrect/unreachable default gateway.
- **Fix:** Reconfigure PC2 to obtain gateway via DHCP (or set 10.10.10.1).
- **OSI layer:** Layer 3 (Network).

## Fault 2: Missing VLAN on trunk
- **Injection:** On SW2 Fa0/1 trunk, run `switchport trunk allowed vlan remove 20`.
- **Symptom:** Guest devices associated to AP1 get no DHCP address at all.
- **Root cause:** VLAN 20 not permitted across the SW2↔SW1 trunk, so DHCP discover never reaches R1.
- **Fix:** `switchport trunk allowed vlan add 20` on the SW2 trunk port.
- **OSI layer:** Layer 2 (Data Link).

## Fault 3: DHCP pool exhausted / excluded wrong range
- **Injection:** Change `ip dhcp excluded-address 10.10.10.1 10.10.10.254` (excludes almost the whole pool).
- **Symptom:** New PCs fail to get an IP ("DHCP request timed out"); existing leases still work.
- **Root cause:** Misconfigured excluded-address range starves the DHCP pool.
- **Fix:** Correct the excluded range back to `10.10.10.1 10.10.10.99`.
- **OSI layer:** Layer 3 / Application (DHCP).

## Fault 4: ACL blocking DNS
- **Injection:** Add `deny udp any any eq 53` above the permit line in a guest-facing ACL.
- **Symptom:** Guest devices can ping 8.8.8.8 by IP but websites by name fail to resolve.
- **Root cause:** ACL blocks UDP/53 (DNS) before the permit statement is reached.
- **Fix:** Remove/reorder the deny statement so DNS traffic is permitted.
- **OSI layer:** Layer 4/7 (Transport/Application).

## Fault 5: NAT not applied to a subnet
- **Injode:** Remove the `permit 10.10.20.0 0.0.0.255` line from `NAT_ACL`.
- **Symptom:** Guest VLAN loses internet access entirely; employee VLAN still browses fine.
- **Root cause:** Guest subnet no longer matched by the NAT-eligible ACL, so R1 doesn't translate its traffic.
- **Fix:** Re-add the guest subnet line to `NAT_ACL`.
- **OSI layer:** Layer 3 (NAT/Network).

---
Each fault should be screenshotted before/after and logged with: symptom observed, `show` command evidence gathered, root cause, and the fix applied — this is what the Python checker and NetSage-style workflow expect as evidence.
