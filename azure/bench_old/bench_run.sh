IP=20.237.72.234

# Common flags:
# -t 15s: prevent client-side timeouts under load
# --disable-keepalive false (default): keep connections warm
# --latency-correction: compensate client send jitter a bit

# C=6 (60s)
oha -z 60s -c 6  -m POST \
  -t 15s --latency-correction \
  -H 'Content-Type: application/json' \
  -D body_nostream.json \
  http://$IP/v1/chat/completions

# C=12 (60s)
oha -z 60s -c 12 -m POST \
  -t 15s --latency-correction \
  -H 'Content-Type: application/json' \
  -D body_nostream.json \
  http://$IP/v1/chat/completions

# C=24 (60s)
oha -z 60s -c 24 -m POST \
  -t 15s --latency-correction \
  -H 'Content-Type: application/json' \
  -D body_nostream.json \
  http://$IP/v1/chat/completions

# C=32 (5 min sustained; autoscale trigger)
oha -z 300s -c 32 -m POST \
  -t 20s --latency-correction \
  -H 'Content-Type: application/json' \
  -D body_nostream.json \
  http://$IP/v1/chat/completions
