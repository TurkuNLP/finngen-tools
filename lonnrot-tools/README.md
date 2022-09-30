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

## Combine

```
cat converted/*.jsonl > projekti-lonnrot.jsonl
```

## Filter to Finnish

```
python3 ../filter_jsonl.py -l 0.9 projekti-lonnrot.jsonl \
    > projekti-lonnrot-finnish.jsonl
```

```
projekti-lonnrot.jsonl:	fail-lang-prob	77 (2.9%)
projekti-lonnrot.jsonl:	pass-all	2574 (97.1%)
projekti-lonnrot.jsonl: output 2574/2651 documents (97.1%)
```

## Checksum for converted corpus

Note that the source data is being extended, so checksums and
statistics are likely to differ if the corpus is recreated following
these steps.

```
md5sum projekti-lonnrot-finnish.jsonl
```

```
9443d26c4c6287377fbe44b5732548c7  projekti-lonnrot-finnish.jsonl
```

## Statistics for converted corpus

```
python3 ../jsonl_stats.py projekti-lonnrot-finnish.jsonl
```

|docs|words|chars|
|----|-----|-----|
|2574|125337227|771644154|
|(2.6K)|(125.3M)|(771.6M)|
