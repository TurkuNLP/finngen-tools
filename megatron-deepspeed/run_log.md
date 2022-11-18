## LOG

| setting                         | precision | fused kernels    | model | result    | SLURM_JOBID |
|---------------------------------|-----------|------------------|-------|-----------|-------------|
| old torch, no-pipeline-parallel | fp32      | torch layer norm | MS-DS | explosion | 2042168     |


* Currently fp16 from apex doesn't seem to work but 


