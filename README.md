# SmartBranch 360

## Secure Branch Office Network

A secure branch-office network project built using **Cisco Packet Tracer and Python**. The project demonstrates VLAN segmentation, inter-VLAN routing, DHCP, NAT, guest Wi-Fi isolation, network security, automated validation, and systematic troubleshooting through fault injection.

---

## 📌 Project Objective

The objective of SmartBranch 360 is to design and build a small but secure branch-office network supporting:

- Wired employee devices
- Guest Wi-Fi
- Internal server access
- Inter-VLAN routing
- Internet access using NAT/PAT
- Guest network isolation.
- Secure wireless connectivity
- Out-of-band management
- Automated network assurance using Python
- Fault injection and troubleshooting with verified evidence

---

## 🏗️ Network Topology

The network consists of:

- **R1** – Router performing Router-on-a-Stick inter-VLAN routing and NAT
- **SW1** – Distribution switch
- **SW2** – Access switch
- **AP1** – Wireless Access Point for guest Wi-Fi
- **SRV1** – Internal server
- **6 Employee PCs**
- **1 Management PC**
- **2 Wireless Guest Devices**

### Architecture

```text
                    Internet
                       |
                    [ R1 ]
                       |
                     Trunk
                       |
                    [ SW1 ]
                  /    |    \
                 /     |     \
              Trunk   SRV1   Mgmt PC
               |
             [ SW2 ]
        / / / / / \
      Employee PCs

AP1 → Guest Wi-Fi Network
