# TRAI DLT SMS Headers & Domains Verification Checklist (TODO_VERIFY.md)

This document tracks SMS sender headers, brand domains, and DLT principal entity IDs that require manual telecom/DLT verification.
Do not guess or assume headers. All headers included in the default `headers.json` are verified against active Indian commercial DLT registries (Vilpower, Smartping, PingConnect, Jionet DLT).

---

## 1. Candidate Headers Pending Operator Verification

| Entity Name | Sector | Proposed Headers | Target Domain | Reason for Manual Review |
| :--- | :--- | :--- | :--- | :--- |
| **State Bank of India** | Banking | `SBGINT`, `SBINPS` | `sbi.co.in` | Verify whether `SBGINT` is currently allocated for global remittance or superseded by `SBIRTN`. |
| **Indian Railway / IRCTC**| Transport | `IRCTCi`, `CRISIN`, `IRCTCS` | `irctc.co.in` | IRCTC frequently uses numeric shortcodes (139) in addition to alphanumeric headers. |
| **Ration Card / PDS CG** | State Govt | `CGKHAD`, `CGPDSN` | `khadya.cg.nic.in` | Chhattisgarh state food & civil supplies department DLT registration confirmation needed. |
| **Mahtari Vandan Yojana**| State Scheme | `CGMVYN`, `WCDCG` | `mahtarivandan.cg.gov.in` | Bulk SMS sent via state NIC gateway; confirm primary registered 6-char header. |
| **Zomato / Swiggy** | Food Delivery | `ZOMATO`, `SWIGGY`, `SWGIND` | `zomato.com`, `swiggy.com` | High OTP frequency; verify promotional vs transactional suffix mapping. |
| **Tata Power / BESCOM** | State Electricity | `BESCOM`, `TATAPW` | `bescom.karnataka.gov.in` | Regional electricity discom headers across non-CG states. |

---

## 2. Brand Domain Whitelist Rules to Validate

1. **Shortened Brand Redirects**:
   - SBI uses `sbi.co.in` and `onlinesbi.sbi` (TLD `.sbi`).
   - HDFC Bank uses `hdfcbank.com` and shortlinks `hdfcbk.io` (Verify if `hdfcbk.io` is strictly whitelisted for marketing or transactional).
   - Amazon uses `amazon.in` and official shortener `amzn.to` / `amzn.in`.
2. **Third-Party Payment Gateways**:
   - BillDesk (`billdesk.com`), Razorpay (`razorpay.com`), and Cashfree (`cashfree.com`) send transaction receipts on behalf of banks.
   - Clarify whether generic gateway receipts should trigger cross-domain mismatch alerts when the sender header is the gateway itself (e.g. `RAZORP`).

---

## 3. How to Verify on TRAI DLT Portals
To verify any new sender header before adding to `headers.json`:
1. Check TRAI's official DLT verification tools on telecom operators:
   - Airtel DLT Portal: `https://www.airtel.in/business/commercial-communication`
   - Jio DLT (Trueconnect): `https://trueconnect.jio.com`
   - Vodafone Idea (Vilpower): `https://www.vilpower.in`
   - BSNL DLT: `https://www.ucc-bsnl.co.in`
2. Check Header Registration:
   - Ensure the header is exactly **6 alphanumeric characters**.
   - Check Header Type: **Transactional (T)**, **Service Implicit (SI)**, **Service Explicit (SE)**, or **Promotional (P)**.
3. Update `backend/models/headers.json`, `android/app/src/main/assets/headers.json`, and run unit tests.
