#!/usr/bin/env python3
"""
SmartBranch 360 - Python Assurance Tool
========================================
Validates a YAML IP/VLAN plan (requirements.yaml) and/or a folder of
`show`-command text output captured from Packet Tracer devices, then
prints a readable findings report.

Usage:
    python network_checker.py --plan requirements.yaml
    python network_checker.py --plan requirements.yaml --show-dir show_outputs/

`show_outputs/` should contain plain-text files named like:
    R1_show_ip_interface_brief.txt
    R1_show_ip_nat_translations.txt
    SW1_show_vlan_brief.txt
    SW1_show_interfaces_trunk.txt
    SW2_show_interfaces_trunk.txt
(paste `show` command output from Packet Tracer's CLI into these files)
"""

import argparse
import ipaddress
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("This script needs PyYAML: pip install pyyaml --break-system-packages")
    sys.exit(1)


class Finding:
    def __init__(self, severity, area, message, fix=""):
        self.severity = severity  # ERROR, WARN, INFO
        self.area = area
        self.message = message
        self.fix = fix

    def __str__(self):
        base = f"[{self.severity:5}] ({self.area}) {self.message}"
        if self.fix:
            base += f"\n         -> Suggested fix: {self.fix}"
        return base


def load_plan(path):
    with open(path) as f:
        return yaml.safe_load(f)


def check_plan(plan):
    findings = []
    vlans = plan.get("vlans", [])
    seen_ids, seen_subnets = set(), []

    for v in vlans:
        vid, name, subnet = v.get("id"), v.get("name"), v.get("subnet")

        # Duplicate VLAN ID
        if vid in seen_ids:
            findings.append(Finding("ERROR", "VLAN", f"Duplicate VLAN ID {vid} ({name})",
                                     "Assign a unique VLAN ID."))
        seen_ids.add(vid)

        # Subnet validity + overlap check
        try:
            net = ipaddress.ip_network(subnet, strict=False)
        except ValueError:
            findings.append(Finding("ERROR", "IP-PLAN", f"VLAN {vid} ({name}) has invalid subnet '{subnet}'"))
            continue

        for other_id, other_net in seen_subnets:
            if net.overlaps(other_net):
                findings.append(Finding("ERROR", "IP-PLAN",
                                         f"VLAN {vid} subnet {net} overlaps VLAN {other_id} subnet {other_net}",
                                         "Re-address one of the VLANs to a non-overlapping /24."))
        seen_subnets.append((vid, net))

        # Gateway must be inside subnet
        gw = v.get("gateway")
        if gw and ipaddress.ip_address(gw) not in net:
            findings.append(Finding("ERROR", "IP-PLAN",
                                     f"VLAN {vid} gateway {gw} is not inside subnet {net}",
                                     f"Use an address within {net} for the gateway."))

    # Guest isolation policy sanity check
    guest = next((v for v in vlans if v.get("name", "").upper() == "GUEST"), None)
    if guest and (guest.get("server_access") or guest.get("management_access")):
        findings.append(Finding("ERROR", "SECURITY",
                                 "GUEST VLAN has server or management access enabled in the plan",
                                 "Guest must be isolated from SERVER and MANAGEMENT VLANs."))

    # SSH-only-from-management check
    mgmt = next((v for v in vlans if v.get("name", "").upper() == "MANAGEMENT"), None)
    if mgmt and not mgmt.get("ssh_source_only"):
        findings.append(Finding("WARN", "SECURITY",
                                 "MANAGEMENT VLAN does not mark itself as the sole SSH source",
                                 "Add an access-class ACL restricting vty lines to the management subnet."))

    if not findings:
        findings.append(Finding("INFO", "IP-PLAN", "Plan passed all static checks: no duplicate VLANs, "
                                                     "no overlapping subnets, gateways valid, guest isolated."))
    return findings


def check_show_outputs(show_dir):
    findings = []
    files = {f: open(os.path.join(show_dir, f)).read() for f in os.listdir(show_dir) if f.endswith(".txt")}

    for fname, text in files.items():
        # Missing VLAN on a trunk
        if "trunk" in fname.lower():
            allowed = re.search(r"Vlans allowed on trunk\s*\n?(.*)", text)
            if allowed and "20" not in allowed.group(1) and "GUEST" not in text.upper():
                findings.append(Finding("ERROR", "TRUNK", f"{fname}: VLAN 20 (GUEST) missing from trunk-allowed list",
                                         "switchport trunk allowed vlan add 20"))

        # Interface down
        for m in re.finditer(r"(\S+)\s+\S+\s+YES\s+\S+\s+(administratively down|down)\s+down", text):
            findings.append(Finding("ERROR", "INTERFACE", f"{fname}: interface {m.group(1)} is {m.group(2)}",
                                     "no shutdown on the affected interface"))

        # Duplicate IP warning text from Packet Tracer/IOS log
        if "duplicate" in text.lower() and "ip" in text.lower():
            findings.append(Finding("ERROR", "IP-CONFLICT", f"{fname}: duplicate IP address detected in log",
                                     "Re-IP one of the conflicting hosts / check DHCP excluded-address range."))

        # NAT translations empty but should exist
        if "nat_translations" in fname.lower() and len(text.strip().splitlines()) <= 1:
            findings.append(Finding("WARN", "NAT", f"{fname}: no active NAT translations found",
                                     "Check NAT_ACL includes the source subnet and outside interface has ip nat outside."))

    if not findings:
        findings.append(Finding("INFO", "SHOW-OUTPUT", "No issues detected in provided show-command output."))
    return findings


def main():
    ap = argparse.ArgumentParser(description="SmartBranch 360 network assurance checker")
    ap.add_argument("--plan", help="Path to requirements.yaml")
    ap.add_argument("--show-dir", help="Directory of pasted show-command .txt files")
    args = ap.parse_args()

    if not args.plan and not args.show_dir:
        ap.error("Provide at least --plan or --show-dir")

    print("=" * 60)
    print("SmartBranch 360 - Validation Report")
    print("=" * 60)

    if args.plan:
        plan = load_plan(args.plan)
        print(f"\n--- Plan checks: {args.plan} ---")
        for f in check_plan(plan):
            print(f)

    if args.show_dir:
        print(f"\n--- Show-output checks: {args.show_dir} ---")
        for f in check_show_outputs(args.show_dir):
            print(f)

    print("\nDone.")


if __name__ == "__main__":
    main()
