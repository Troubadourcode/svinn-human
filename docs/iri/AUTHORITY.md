# Authority (Y1 freeze)

- Unit of work = **action request**
- No Y1 auto-execute of MFA reset
- Challenge OOB to IdP/HR recovery owner or manager (≠ initiator ≠ beneficiary)
- Session revoke optional; not coupled to every reset
- Two-person for high-impact; break-glass TTL’d dual-control accounts
- Case `AUTHORIZED_*` / JSM `authorized` → still need **Case release + ledger** before Action execute
