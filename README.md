# SDN QoS Priority Controller (Project 16)

## Course
UE24CS252B - Computer Networks  
PES University  

---

## 📌 Problem Statement
Implement an SDN-based QoS controller using POX to prioritize different traffic types and demonstrate failure scenarios.

---

## 🎯 Objective
- Classify traffic based on protocol
- Assign priority levels using OpenFlow rules
- Demonstrate performance differences
- Simulate failure condition

---

## 🧠 QoS Policy

| Traffic Type | Priority | Description |
|-------------|---------|------------|
| ICMP        | 300     | Highest priority (low latency) |
| TCP         | 200     | Medium priority |
| UDP         | 100     | Lowest priority |
| DROP (Failure) | 400  | Blocks selected traffic |

---

## ⚙️ Setup Instructions

### Step 1: Run Controller
```bash
cd ~/pox
./pox.py log.level --DEBUG ext.qos_controller

---
📊 Results
ICMP shows lowest latency
TCP shows stable throughput
UDP shows reduced performance under load
Failure scenario blocks traffic to selected host

🧠 Conclusion

The project demonstrates QoS implementation using SDN.
Traffic prioritization is achieved using OpenFlow rules, and failure scenarios are simulated using drop rules.