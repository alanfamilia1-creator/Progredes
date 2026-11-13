#!/bin/bash
echo "Data     :$(date '+%F %T')"
echo "Host     :$(hostname)"
echo "Usuario  :$(whoami)"
echo "Disco /  :$(df --output=pcent / | tail -1 | tr -d ' ')"
