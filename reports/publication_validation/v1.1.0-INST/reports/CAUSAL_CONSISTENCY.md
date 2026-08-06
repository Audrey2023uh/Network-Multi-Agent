# Cross-table / Causal Consistency

Pass rate: 100.00%

- [PASS] `incident_order`: violations=0
- [PASS] `recovery_fk`: orphan_recovery=0
- [PASS] `incident_entities`: missing=0
- [PASS] `rca_category_match`: label_rca vs failure_incident
- [PASS] `if_failure_oper_down`: 3/3 interface_failures show oper=down
- [PASS] `routing_bgp_state`: 3/3 routing incidents co-occur with non-established BGP
- [PASS] `vsx_split_state`: 2/2 vsx incidents show split state
- [PASS] `syslog_burst_near_onset`: 30/37 incidents have >=2 syslog near onset
- [PASS] `service_impact_coverage`: 36/37 incidents have service_impact
- [PASS] `alerts_not_perfect`: false_negative_incidents_without_alert=2 (imperfect monitoring is realistic)
