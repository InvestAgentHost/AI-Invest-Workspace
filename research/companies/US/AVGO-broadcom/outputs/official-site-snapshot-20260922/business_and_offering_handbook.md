---
schema_version: research_foundry_official_site_deliverable.v1
document_type: business_and_offering_handbook
target_name: "AVGO-broadcom"
as_of: 2026-09-22
snapshot_id: oss_manual_avgo_20260922a1
run_id: run_manual_avgo_20260922b2
quality_status: partial
---

# Business and Offering Handbook

**Methodology note:** Broadcom's official website (www.broadcom.com) and investor-relations site (investors.broadcom.com) could not be crawled by this research package's automated official-site capability or by any other tool available in this environment — www.broadcom.com is a client-side-rendered React single-page application with no server-rendered text, and investors.broadcom.com is blocked by bot-management/WAF protection (both independently confirmed multiple times; see `data/acquisition-attempt-log.md` A004-A012). Per the user's explicit instruction, this deliverable substitutes the company's own SEC-filed disclosures (a higher tier in this skill's documented source hierarchy than official-site pages) for the unreachable website content, gathered via the skill's sanctioned "manual and web intake" method (`references/source-acquisition.md` §4). All content below is COMPANY_CLAIM (self-reported by Broadcom in a regulatory filing), not independently verified fact, unless otherwise noted.

## Company overview

Broadcom Inc. describes itself as "a global technology leader that designs, develops and supplies a broad range of semiconductor and infrastructure software solutions." The company traces its roots through more than 60 years of history and innovation, dating back to its origins within AT&T and Bell Labs, and eventually Lucent and Hewlett-Packard/Agilent, and has grown both organically and through a number of significant acquisitions, including LSI Corporation, Broadcom Corporation, Brocade Communications' storage networking business, CA, Inc., the Symantec enterprise security business, and VMware [S010].

## Business segments

Broadcom organizes its business into two reportable segments [S010]:

### Semiconductor Solutions
Products and services span five end markets: **Networking Connectivity**, **Wireless Device Connectivity**, **Servers and Storage Systems**, **Broadband**, and **Industrial**. This segment includes custom AI accelerator (ASIC) design and Ethernet-based AI networking silicon — the category underlying the AI-infrastructure partnerships described in `strategy_and_developments.md` [S010].

### Infrastructure Software
Five portfolios: **Private Cloud / VMware Cloud Foundation**, **Mainframe Software**, **Cybersecurity**, **Enterprise Software**, and **Fibre Channel SAN Management** [S010].

## Product catalog

The 10-K's "Products and Markets" disclosure (Item 1) names specific product families within each end market/portfolio, below the segment level. This is the most granular product-level detail available from a company-authored source in this research pass; it is regulatory-disclosure language, not the marketing-style product/datasheet catalog that would normally live on www.broadcom.com/products (unreachable — see Scope note) [S010] [E011].

### Semiconductor Solutions — by end market

**Networking Connectivity** — solutions for data center, service-provider and enterprise network data movement, including AI data center connectivity:
- *Custom Silicon Solutions* — ASIC design platforms (embedded logic, high-bandwidth memory, SerDes, IP/processor cores) for customer-specific accelerators/XPUs used by hyperscalers, AI-frontier-model companies and system integrators.
- *Ethernet Switching & Routing* — high-capacity, low-latency switching silicon for AI/enterprise data centers, service-provider carrier networks, and secure/encrypted enterprise switch product families.
- *Ethernet NIC Controllers* — controllers for high-performance virtualization, intelligent flow processing, secure data-center connectivity and machine learning.
- *Physical Layer Devices (PHYs)* — Ethernet transceivers (proprietary DSP architecture) plus an automotive Ethernet PHY/switch/camera-microcontroller line for in-vehicle connectivity.
- *Fiber Optic Components* — optical components for Ethernet networking, storage, and access/metro/long-haul telecom.

**Wireless Device Connectivity** — connectivity solutions for smartphones, tablets and wearables:
- *RF Semiconductor Devices* — front-end modules and filters using proprietary FBAR (film bulk acoustic resonator) technology.
- *Connectivity Solutions* — Wi-Fi chipsets, Bluetooth silicon/software, and combination Wi-Fi/Bluetooth chips.
- *Custom Touch Controllers* — touch-screen signal processing.
- *Inductive Charging ASICs* — wireless-charging ICs for mobile/wearable devices.

**Servers and Storage Systems** — data movement between hosts (servers, PCs) and storage devices (HDD/SSD):
- *PCIe Switches* — interconnect semiconductors for AI and non-AI computing systems.
- *SAS & RAID Products* — controller/adapter products for host-to-storage data transmission and HDD-failure protection.
- *Fibre Channel Products* — host bus adapters connecting servers to FC SAN storage.
- *HDD & SSD Solutions* — read-channel SoCs, preamplifiers, and flash controllers for hard-disk and solid-state drives.

**Broadband** — set-top box and broadband access platforms:
- *Set-Top Box* — SoC platforms for cable, satellite, IPTV, OTT and terrestrial STBs (transcoding, DVR, HD video processing).
- *Broadband Access* — SoC platforms for DSL, cable, PON and WLAN, covering both CPE (modems, gateways, Wi-Fi routers) and central-office equipment.

**Industrial** — factory automation, renewable energy and automotive electronics: optocouplers, industrial fiber optics, industrial/medical sensors, motion encoders, LED devices, and Ethernet ICs, used in industrial automation, power generation/distribution, medical equipment, defense/aerospace, and EV powertrain/infotainment/ADAS subsystems.

### Infrastructure Software — by portfolio

**Private Cloud Software Portfolio:**
- *VMware Cloud Foundation (VCF)* — integrated compute, networking, storage, management and security, with native Kubernetes for VMs and containers. Per Broadcom's own techdocs, VCF 9 is built from 6 named components: **VCF Installer**, **vSphere**, **vSAN**, **NSX**, **VCF Operations**, and **VCF Automation** [S032] [E012]. Optional advanced services: **VMware vDefend**, **VMware Avi Load Balancer**, **VMware Tanzu Platform**, **VMware Private AI**, **VMware Live Recovery** (detailed below) [S010].
- *VMware Cloud Foundation Edge* — edge-site app/infrastructure management for distributed, resource-limited sites [S010].
- *VMware vSphere Foundation* — software-defined compute/storage/networking/operations for existing infrastructure; positioned as the foundational layer underlying full VCF. Provides a unified VM+container workload platform (native Kubernetes runtime), intelligent operations management, hyperconverged infrastructure (integrated compute/storage virtualization), and simplified deployment/scalability. It explicitly **excludes** the cloud-management and integrated-automation capabilities that come with full VCF — that is the documented product-tier boundary between the two [S033] [E012].
- *Telco Cloud Platform* — VCF-based platform for telecom/communications-service-provider network modernization and 5G/cloud service monetization [S010].
- *VMware Private AI* — generative-AI enablement add-on for VCF. Two distinct layers per techdocs: **VMware Private AI Foundation with NVIDIA** (the infrastructure layer — preconfigured Deep Learning VM images validated by NVIDIA and VMware for GPU acceleration, intended for VI administrators, data scientists, MLOps/DevOps engineers) and the separately-installed **Private AI Services** (the application layer — 4 modules: Model Gallery built on the Harbor container registry, Model Runtime running completion/embedding models via vLLM and Infinity inference engines, Data Indexing and Retrieval, and Agent Builder) [S036] [E015].
- *VMware Live Recovery* — disaster- and ransomware-recovery service for VCF customers, spanning two delivery models per techdocs: **on-premises Live Site Recovery** (combines what were previously separate Live Site Recovery, vSAN Data Protection, and vSphere Replication appliances into one; supports Planned Migration between two live sites and Disaster Recovery when the protected site is down) and **Live Recovery Cloud (SaaS)**, including **Live Cyber Recovery**, which provides an isolated recovery environment (IRE) to inspect, clean, and restore ransomware-infected VMs before returning them to production [S035] [E014].
- *Application Networking and Security Portfolio* — zero-trust lateral security and load balancing (VMware vDefend, VMware Avi Load Balancer) [S010].
- *Application Development and Data Services Portfolio* — Tanzu AI application-development platform and low-latency data access for on-prem/cloud AI applications [S010].

**Pricing/licensing disclosure boundary:** Broadcom does not publish a public price list for VCF/vSphere Foundation. Since version 9.0, licensing is subscription- and capacity-based: customers purchase a term subscription for a specified capacity, and a license object (issued via the VCF Operations console / vcf.broadcom.com Business Services console) entitles use; this replaced the older 25-character-license-key model. Connected components (e.g. vCenter) are auto-licensed once tied to a licensed VCF/vSphere Foundation instance, with a 90-day evaluation grace period if unlicensed [S034] [E013]. This is functionally the same "undisclosed/RFQ-equivalent" pricing pattern documented for most B2B network-infrastructure vendors (e.g. the NOK-nokia product handbook's pricing convention) — actual dollar figures require a direct sales quote, not a published source.

**Mainframe Software Portfolio:** AIOps & Automation; Databases & Data Management; DevX & DevOps; Cybersecurity & Compliance Management; Beyond Code Programs (customer education/upskilling); Foundational & Open Mainframe Solutions (core mission-critical capabilities plus API-driven/cloud-integrated open-mainframe tooling).

**Cybersecurity Portfolio:**
- *Endpoint Security* — Symantec and Carbon Black endpoint protection across laptops, desktops, wireless devices, servers and cloud workloads.
- *Network Security* — inbound/outbound threat protection for end users, information and infrastructure.
- *Information Security* — single-policy-framework data protection across endpoints, on-prem networks, cloud services and private applications.
- *Application Security* — Carbon Black-based positive-security-model protection for critical/legacy/air-gapped systems.
- *Identity & Access Management* — access-control and access-governance solutions.

**Enterprise Software Portfolio:** organized around AIOps, Automation and Network Observability, DevOps, and Value Stream Management — end-to-end visibility across the software delivery lifecycle.

**FC SAN Management:** mission-critical Fibre Channel storage-area-network modules, switches and subsystems, plus software-based management tools for storage-network visibility and uptime.

## Scale and workforce

As of November 2, 2025 (fiscal year-end 2025), Broadcom reported approximately 33,000 employees worldwide, with approximately 57% in research and development roles. Geographic distribution was approximately 49% North America, 36% Asia, and 15% EMEA; voluntary attrition for FY2025 was approximately 4.1% [S010] [E002].

## Intellectual property

As of November 2, 2025, the company reported holding approximately 19,000 U.S. and other patents, with 2,170 U.S. and other pending patent applications [S010] [E003].

## Headquarters and facilities

Broadcom is headquartered in Palo Alto, California; its primary warehouse is located in Malaysia. As of fiscal year-end 2025, total facilities spanned 6,465,985 square feet (3,655,412 sq ft in the United States and 2,810,573 sq ft in other countries). The company holds long-term land leases in Malaysia (through 2051/2077) and near Stanford, California for its Palo Alto headquarters (through 2046) [S010] [E004].

## Leadership (executive officers, as of the FY2025 10-K's filing date)

Per the FY2025 10-K's executive-officer table (dated December 18, 2025) [S010] [E005]:

- **Hock E. Tan** (74) — President, Chief Executive Officer and Director
- **Kirsten M. Spears** (61) — Chief Financial Officer and Chief Accounting Officer *(superseded — see note below)*
- **Mark D. Brazeal** (57) — Chief Legal and Corporate Affairs Officer
- **Charlie B. Kawwas, PhD** (55) — President, Semiconductor Solutions Group

**Note on leadership change:** subsequent to the 10-K, Broadcom disclosed (SEC Form 8-K, filed 2026-04-02) that Kirsten M. Spears retired as CFO/CAO effective June 12, 2026, and was succeeded by **Amie Thuener**, effective the same date. This is detailed with full sourcing in `strategy_and_developments.md` and `important_information.md` [S026] [S018] [E006].

## Official web presence (as confirmed, not crawled)

The FY2025 10-K's "Available Information" section confirms www.broadcom.com as the company's official website, stating that its Investor Center hosts SEC filings and related materials "free of charge." This corroborates that www.broadcom.com / investors.broadcom.com is the correct, sole official channel — the acquisition failure documented in this snapshot is a technical access limitation (SPA rendering / WAF blocking), not a wrong-URL or targeting error [S010].

## Scope note

This handbook is a **manually-synthesized substitute** for a true official-website crawl, which was technically infeasible in this environment (see methodology note above and `data/acquisition-attempt-log.md` A004-A012 for the full diagnostic record, independently re-confirmed in this session). Content here is drawn from Broadcom's FY2025 Form 10-K (Item 1 "Business" and Item 2 "Properties"), a company-authored SEC filing rather than website copy — factually authoritative but written in regulatory-disclosure style rather than marketing/positioning language, and current as of the filing's respective "as of" dates (primarily November 2, 2025, with one December 18, 2025 update for the executive-officer table) rather than the 2026-09-22 as-of date of this snapshot.

**Product catalog coverage (updated 2026-09-22, per user feedback):** the "Product catalog" section above lists every named product family/line disclosed in the 10-K's Item 1 "Products and Markets" narrative — this is the most specific product-level breakdown available from a company-authored source without a working crawl of www.broadcom.com/products. It closes the gap previously noted here. What is **still not covered**: individual product/part numbers and datasheet-level technical specifications (e.g., specific chip model numbers, throughput/latency figures per switch generation), brand-level marketing copy and positioning language, product images, and pricing/packaging/licensing-tier detail (e.g., specific VCF or vSphere Foundation edition names and their feature/SKU differences) — all of which would normally come from www.broadcom.com/products, individual product datasheets, or VMware/Symantec product-specific microsites, none of which were reachable in this environment. A future pass with working browser access to those pages, or targeted fetches of individual product datasheets/press releases, could close this remaining layer.

**Depth-alignment probe against the NOK-nokia product handbook (2026-09-22):** at the user's request, this pass benchmarked AVGO's catalog depth against `research/companies/US/NOK-nokia`'s per-product, per-URL handbook (built from a genuine 547-page crawl of a server-rendered nokia.com). Probing found the two AVGO business segments have genuinely asymmetric official-site reachability, not a uniform gap:
- **Infrastructure Software (VMware) side — deepened to near-NOK depth this pass.** `techdocs.broadcom.com` was discovered to be a reachable, server-rendered official Broadcom subdomain (distinct from the blocked `www.broadcom.com` SPA and the WAF-blocked `investors.broadcom.com`). It supplied genuine per-product detail with individual source URLs for VCF's six components, the vSphere Foundation/VCF product-tier boundary, the licensing/pricing-disclosure model, VMware Live Recovery's on-prem/SaaS sub-products, and VMware Private AI's infrastructure/application layers — see the Private Cloud Software Portfolio entries above [S032]-[S036] [E012]-[E015].
- **Semiconductor Solutions (chip) side — deliberately NOT deepened; remains at the 10-K product-family level (E011).** No Broadcom-owned domain tested this pass could supply chip-level detail (model numbers, throughput/process-node specs): `www.broadcom.com/products/...` deep chip pages remain empty SPA shells even at the individual-product-page level (confirmed for `bcm78910-series`); `docs.broadcom.com` is reachable but serves graphic-heavy PDFs with no extractable text layer in this environment (buyers'-guide and optical-interconnect briefs both failed to yield text); `investors.broadcom.com`'s PDF-serving press-release endpoints timed out, consistent with its known WAF block [S037] [S038] [E016]. The only source of chip-model-level specifics found (e.g. Tomahawk 6/BCM78910 at 102.4 Tbps on TSMC 3nm) was third-party technical press (NextPlatform, IPInfusion, aichiplink) — a lower source-hierarchy tier than every other citation in this handbook. Per the user's explicit decision after being shown this asymmetry, that third-party layer was **not** incorporated, to keep the catalog's evidence tier consistent; the Semiconductor Solutions subsection above should be read as coarser (product-family, not product-model) than the Infrastructure Software subsection, as a genuine and disclosed source-availability limitation rather than an oversight.
