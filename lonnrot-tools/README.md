# Processing of the Project Lönnrot corpus

## Download data from http://www.lonnrot.net

```
mkdir original-data
curl -s http://www.lonnrot.net/valmiit.html \
    | iconv -f ISO-8859-1 -t UTF-8 \
    | egrep '<a href' | perl -pe 's/.*?<a href="(.*?)".*/$1/' \
    | while read u; do
    wget -P original-data $u
done
```

## Unpack

```
mkdir unpacked
for f in original-data/*.zip; do unzip -d unpacked $f; done
```

## Convert

```
mkdir converted
for f in unpacked/*.txt; do
    python3 convert_lonnrot.py $f > converted/$(basename $f .txt).jsonl
done
```
