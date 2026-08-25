# SmartBranch 360 — Packet Tracer Build Guide & Configs

> Packet Tracer `.pkt` files are a proprietary binary format that can't be generated outside the
> Packet Tracer application itself. Build the topology in Packet Tracer using the plan below, then
> paste these configs into each device's CLI. This gets you a working `SmartBranch360.pkt` in about
> 20–30 minutes.

## 1. Topology to draw
```
                     [Internet Cloud]
                            |
                          R1 (Gi0/0 -> SW1 trunk, Gi0/1 -> Cloud, NAT outside)
                            |
                          SW1 (Distribution - trunk to R1, SW2, AP1)
                       /    |    \
                    SW2    AP1   SRV1 (VLAN30, static 10.10.30.10)
                   /  \      \
              PC1-3  PC4-6  Guest laptop/phone (wireless, VLAN20)
             (VLAN10)      MgmtPC (VLAN99, wired to SW1)
```
Minimum device count: 1 router, 2 switches, 1 AP, 1 server, 8+ endpoints, 1 cloud object — matches the brief.

## 2. R1 (Router) config
```
enable
configure terminal
hostname R1

interface GigabitEthernet0/0
 no shutdown
!
interface GigabitEthernet0/0.10
 encapsulation dot1Q 10
 ip address 10.10.10.1 255.255.255.0
 ip helper-address 10.10.10.1
!
interface GigabitEthernet0/0.20
 encapsulation dot1Q 20
 ip address 10.10.20.1 255.255.255.0
!
interface GigabitEthernet0/0.30
 encapsulation dot1Q 30
 ip address 10.10.30.1 255.255.255.0
!
interface GigabitEthernet0/0.99
 encapsulation dot1Q 99
 ip address 10.10.99.1 255.255.255.0
!
interface GigabitEthernet0/1
 ip address dhcp
 ip nat outside
 no shutdown
!
ip nat inside source list NAT_ACL interface GigabitEthernet0/1 overload
ip access-list standard NAT_ACL
 permit 10.10.10.0 0.0.0.255
 permit 10.10.20.0 0.0.0.255
!
ip dhcp excluded-address 10.10.10.1 10.10.10.99
ip dhcp excluded-address 10.10.20.1 10.10.20.49
ip dhcp pool EMPLOYEE
 network 10.10.10.0 255.255.255.0
 default-router 10.10.10.1
 dns-server 8.8.8.8
ip dhcp pool GUEST
 network 10.10.20.0 255.255.255.0
 default-router 10.10.20.1
 dns-server 8.8.8.8
!
ip access-list extended GUEST_ISOLATION
 deny ip 10.10.20.0 0.0.0.255 10.10.30.0 0.0.0.255
 deny ip 10.10.20.0 0.0.0.255 10.10.99.0 0.0.0.255
 permit ip any any
interface GigabitEthernet0/0.20
 ip access-group GUEST_ISOLATION in
!
username admin privilege 15 secret Cisco123!
line vty 0 4
 login local
 transport input ssh
 access-class MGMT_ONLY in
ip access-list standard MGMT_ONLY
 permit 10.10.99.0 0.0.0.255
 deny any
!
ip domain-name smartbranch.local
crypto key generate rsa modulus 1024
end
write memory
```

## 3. SW1 (Distribution switch) config
```
enable
configure terminal
hostname SW1
vlan 10
 name EMPLOYEE
vlan 20
 name GUEST
vlan 30
 name SERVER
vlan 99
 name MANAGEMENT
!
interface range FastEthernet0/1 - 2
 switchport mode trunk
 switchport trunk allowed vlan 10,20,30,99
!
interface FastEthernet0/3
 switchport mode access
 switchport access vlan 30
 switchport port-security
 switchport port-security maximum 2
 switchport port-security violation restrict
!
interface FastEthernet0/4
 switchport mode access
 switchport access vlan 99
 switchport port-security
!
interface vlan 99
 ip address 10.10.99.11 255.255.255.0
ip default-gateway 10.10.99.1
username admin privilege 15 secret Cisco123!
line vty 0 4
 login local
 transport input ssh
end
write memory
```

## 4. SW2 (Access switch) config
```
enable
configure terminal
hostname SW2
vlan 10
 name EMPLOYEE
vlan 20
 name GUEST
vlan 99
 name MANAGEMENT
!
interface FastEthernet0/1
 switchport mode trunk
 switchport trunk allowed vlan 10,20,99
!
interface range FastEthernet0/2 - 7
 switchport mode access
 switchport access vlan 10
 switchport port-security
 switchport port-security maximum 2
 switchport port-security violation restrict
!
interface vlan 99
 ip address 10.10.99.12 255.255.255.0
ip default-gateway 10.10.99.1
end
write memory
```

## 5. AP1 (Access Point, guest wireless)
- SSID: `SmartBranch-Guest`, WPA2-PSK, VLAN 20 (connect AP's wired uplink to a VLAN20 access port on SW1).

## 6. Endpoint IP settings
| Device | VLAN | Method |
|---|---|---|
| PC1–PC6 | 10 | DHCP |
| Guest laptop/phone | 20 | DHCP (over Wi-Fi) |
| SRV1 | 30 | Static 10.10.30.10 /24, GW 10.10.30.1 |
| MgmtPC | 99 | Static 10.10.99.2 /24, GW 10.10.99.1 |

## 7. Verification checklist
1. `ipconfig` on PC1 → gets 10.10.10.x, pings 10.10.30.10 (server) and 8.8.8.8 (internet).
2. Guest device → gets 10.10.20.x, pings 8.8.8.8, **fails** to ping 10.10.30.10 and 10.10.99.x.
3. From MgmtPC → `ssh admin@10.10.99.11` succeeds; from PC1, SSH to switches is refused.
4. `show ip nat translations` on R1 shows PAT entries when PCs browse.

## 8. Fault injection (do these one at a time, screenshot, then run the Python checker)
See `fault_cards.md` for the 5 required fault scenarios and expected diagnosis.
