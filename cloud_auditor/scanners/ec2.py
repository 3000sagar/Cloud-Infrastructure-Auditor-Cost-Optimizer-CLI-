"""EC2 low-utilization scanner. Not yet implemented (Week 2).

Will use CloudWatch GetMetricData to find instances with sustained
CPU < 5% over a 14-day window (see config/config.yaml for the
threshold and period, both configurable).
"""