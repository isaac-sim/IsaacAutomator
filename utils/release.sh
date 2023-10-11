git fetch -pvtf origin

echo "Enter the tag to release: "
read TAG 

git pull origin master
git checkout $TAG

docker build --no-cache -t ovca:$TAG .

# iterate through destinations
for DST in "nvcr.io/nv-drive-internal/driveconst-qa/ov-cloud-automation" "nvcr.io/brhwxzfhxkr4/ovca"; do
  docker tag ovca:$TAG $DST:$TAG
  docker tag ovca:$TAG $DST:latest
  docker push $DST:latest
  docker push $DST:$TAG
done
