# grep MemTotal /proc/meminfo | awk '{print int($2 / 1024) " MB"}'
grep MemTotal /proc/meminfo | awk '{print int($2 / 1048576) " GB"}'
