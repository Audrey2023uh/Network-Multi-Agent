# External Network-Engineer Review Checklist

For independent SME review of frozen ECNetBench v1.1.0-INST. Check each item Pass/Fail/NA.

## Inventory & addressing

- [ ] VLAN SVI addressing is plausible for campus/branch
- [ ] WAN /BGP peer addresses consistent
- [ ] Access dual-homing and VSX ISL present and sensible
- [ ] Interface speeds match on link endpoints

## Control plane

- [ ] STP has blocking/alternate on redundant edge
- [ ] BGP states during routing incidents look operationally familiar
- [ ] VSX split/sync_progress/sync trajectory believable
- [ ] BFD associated with WAN BGP

## Failures & ops

- [ ] Onset → detect → recover ordering always holds
- [ ] Syslog content roughly matches category (link/BGP/STP/VSX/AAA)
- [ ] Not every incident has a perfect alert (FN exist)
- [ ] Recovery actions map to category

## Telemetry

- [ ] Counters do not go backwards
- [ ] CPU/traffic show weekday business-hour structure
- [ ] Gaps/delays exist (collector not perfect)

## Labels / ML hygiene

- [ ] Would refuse to train on `description` for RCA
- [ ] Would refuse `incident_id` / `y_*_gt` as features
- [ ] Temporal holdout is the default evaluation story

## Scope honesty

- [ ] Comfortable calling this synthetic
- [ ] 14 days / 19 devices acknowledged as small estate
- [ ] EVPN emptiness accepted for campus profile

## Sign-off

| Reviewer | Date | Overall | Notes |
|---|---|---|---|
| _pending external SME_ |  |  |  |
