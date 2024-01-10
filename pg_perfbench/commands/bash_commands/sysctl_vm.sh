#/sbin/sysctl vm 2>/dev/null
/sbin/sysctl vm |& grep -v "permission denied"
