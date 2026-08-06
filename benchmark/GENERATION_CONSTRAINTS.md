# Generation constraints (summary)

The ECNetBench generator enforces:

1. Referential integrity across foreign keys  
2. Temporal integrity of counter series  
3. Causal ordering: onset ≤ detection ≤ recovery  
4. Topological integrity of link endpoints  
5. Leakage-safe label construction for T1–T6  
6. Realism upgrades: addressing, MACs, BGP/VSX/STP state, ARP/MAC/RIB/FIB, syslog bursts, alert FP/FN, telemetry gaps  

See `benchmark/generator/` and `docs/` for full specifications. Frozen instances must not be overwritten; new seeds use new directories.
