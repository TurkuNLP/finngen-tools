# Processing of the Finnish News Agency Archive 1992-2018 corpus

## Download data

Original files `suomi24-2001-2017-vrt-v1-2.zip` and
`suomi24-2018-2020-vrt-beta.zip` downloaded from
<http://urn.fi/urn:nbn:fi:lb-2021101527> (Academic license,
registration required)

## Unpack

```
unzip -d unpacked suomi24-2001-2017-vrt-v1-2.zip
unzip -d unpacked suomi24-2018-2020-vrt-beta.zip 
```

## Convert

```
mkdir converted
find unpacked -name '*.vrt' | while read f; do
    python3 convert_suomi24.py --jsonl $f > converted/$(basename $f .vrt).jsonl;
done
```

## Combine

```
cat converted/*.jsonl > combined.jsonl
```

## Rename

```
cp combined.jsonl suomi24-2001-2020.jsonl
```

## Checksum for converted corpus

```
md5sum suomi24-2001-2020.jsonl
```

```
1a4b59abedae3e9a4dd0f38b5c541932  suomi24-2001-2020.jsonl
```

 ## Statistics for converted corpus

```
python3 ../jsonl_stats.py suomi24-2001-2020.jsonl
```

|docs|words|chars|
|----|-----|-----|
|94758071|4962707983|30091043294|
|(94.8M)|(5.0G)|(30.1G)|

## Deduplicate

Clone tools supporting deduplication with `onion`

```
git clone https://github.com/spyysalo/onion-tools.git
```

Reverse for latest-first so that deduplication will remove older texts.

```
tac combined.jsonl > combined.rev.jsonl
```

Convert to `onion` input format

```
python3 onion-tools/jsonl_to_vert.py combined.rev.jsonl > combined.rev.vert
```

Mark duplicates with `onion` (<http://corpus.tools/wiki/Onion>)

```
onion combined.rev.vert > combined.rev.onion
```

Filter out duplicates

```
python3 onion-tools/filter_onion.py combined.rev.onion \
    > combined.rev.dedup.onion
```

```
output 3518536961/4573140448 (76.9%) lines
output 47720193/94758071 (50.4%) docs
```

Convert back to JSONL

```
python3 onion-tools/onion_to_jsonl.py combined.rev.dedup.onion \
    > combined.rev.dedup.jsonl
```

Reverse back

```
tac combined.rev.dedup.jsonl > combined.dedup.jsonl
```

## Rename

```
mv combined.dedup.jsonl suomi24-2001-2020.dedup.jsonl
```

## Checksum for deduplicated corpus

```
md5sum suomi24-2001-2020.dedup.jsonl
```

```
ea29358593b6c43b2c53b4e02ad04f9b  suomi24-2001-2020.dedup.jsonl
```

## Statistics for deduplicated corpus

```
python3 ../jsonl_stats.py suomi24-2001-2020.dedup.jsonl
```

|docs|words|chars|
|----|-----|-----|
|47720193|3853821768|23854201177|
|(47.7M)|(3.9G)|(23.9G)|

## Filter

Heuristic filter to remove documents that aren't primarily Finnish prose text.

python3 ../filter_jsonl.py \
    --digit-ratio 0.1 \
    --punct-ratio 0.1 \
    --upper-ratio 0.1 \
    --type-token-ratio 0.5 \
    --foreign-ratio 0.01 \
    --short-ratio 0.05 \
    --min-words 5 \
    --avg-len 5 \
    --max-repeat 5 \
    --lang-prob 0.9 \
    suomi24-2001-2020.dedup.jsonl > suomi24-2001-2020.dedup.filtered.jsonl
```

```
suomi24-2001-2020.dedup.jsonl:	fail-avg-len	227914 (0.5%)
suomi24-2001-2020.dedup.jsonl:	fail-digit-ratio	80598 (0.2%)
suomi24-2001-2020.dedup.jsonl:	fail-foreign-ratio	18439 (0.0%)
suomi24-2001-2020.dedup.jsonl:	fail-lang-prob	129552 (0.3%)
suomi24-2001-2020.dedup.jsonl:	fail-max-repeat	422435 (0.9%)
suomi24-2001-2020.dedup.jsonl:	fail-punct-ratio	284129 (0.6%)
suomi24-2001-2020.dedup.jsonl:	fail-short-ratio	912511 (1.9%)
suomi24-2001-2020.dedup.jsonl:	fail-type-token-ratio	141325 (0.3%)
suomi24-2001-2020.dedup.jsonl:	fail-upper-ratio	631772 (1.3%)
suomi24-2001-2020.dedup.jsonl:	pass-all	44871518 (94.0%)
suomi24-2001-2020.dedup.jsonl: output 44871518/47720193 documents (94.0%)
```

## Checksum for deduplicated and filtered corpus

```
md5sum suomi24-2001-2020.dedup.filtered.jsonl
```

```
f144cba9391e98fcc2d28c6959b68b29  suomi24-2001-2020.dedup.filtered.jsonl
```

## Statistics for deduplicated and filtered corpus

```
python3 ../jsonl_stats.py suomi24-2001-2020.dedup.filtered.jsonl
```

|docs|words|chars|
|----|-----|-----|
|44871518|3536752031|22193001509|
|(44.9M)|(3.5G)|(22.2G)|

