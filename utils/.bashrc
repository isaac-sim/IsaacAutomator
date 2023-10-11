# create credentials store when starting from prebuilt image

for d in "/app/state/.azure" "/app/state/.gcp"; do
  if [ ! -d $d ]; then
    mkdir -p $d
    touch $d/empty
  fi
done

