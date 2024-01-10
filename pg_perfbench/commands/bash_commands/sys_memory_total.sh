#!/bin/bash
meminfo_path='/proc/meminfo'
exclude_params='MemFree|MemAvailable|Buffers|Cached|Active|Inactive|Active\(anon\)|Inactive\(anon\)|Active\(file\)|Inactive\(file\)|Unevictable|Dirty|AnonPages|Mapped|Shmem|KReclaimable|Slab|SReclaimable|SUnreclaim|KernelStack|PageTables|Committed_AS|VmallocUsed|Writeback|WritebackTmp'
if [ -f "$meminfo_path" ]; then
	grep -Ev "$exclude_params" "$meminfo_path"
fi