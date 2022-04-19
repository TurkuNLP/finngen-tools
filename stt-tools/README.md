# Processing of the Finnish News Agency Archive 1992-2018 corpus

## Download data

Original file `stt-fi-1992-2018-src.zip` downloaded from
<http://urn.fi/urn:nbn:fi:lb-2019041501> (Academic license,
registration required)

## Unpack

```
unzip -d unpacked stt-fi-1992-2018-src.zip
for f in unpacked/stt-fi-1992-2018-src/data/arkistosiirto*.zip; do
    unzip -d unpacked $f;
done
```

## Convert

```
mkdir converted
for d in unpacked/arkistosiirto*; do
    python3 convert_stt.py $d > converted/$(basename $d).jsonl;
done
```

## Combine

```
cat converted/*.jsonl > combined.jsonl
```

## Rename

```
cp combined.jsonl stt-fi-1992-2018.jsonl
```

## Checksum for converted corpus

```
md5sum stt-fi-1992-2018.jsonl
```

```
fecc6b2a65ca001c72351036b780f819  stt-fi-1992-2018.jsonl
```

## Statistics for converted corpus

```
python3 ../jsonl_stats.py stt-fi-1992-2018.jsonl
```

|docs|words|chars|
|----|-----|-----|
|2848322|693722035|4145355415|
|(2.8M)|(693.7M)|(4.1G)|

## Deduplicate

Clone tools supporting deduplication with `onion`

```
git clone https://github.com/spyysalo/onion-tools.git
```

Reverse for latest-first so that deduplication will remove older versions.

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
output 406111268/628429632 (64.6%) lines
output 2125674/2848322 (74.6%) docs
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
mv combined.dedup.jsonl stt-fi-1992-2018.dedup.jsonl
```

## Checksum for deduplicated corpus

```
md5sum stt-fi-1992-2018.dedup.jsonl
```

```
1ef7a5b48c95e71a3cde90118a2ddbe7  stt-fi-1992-2018.dedup.jsonl
```

## Statistics for deduplicated corpus

```
python3 ../jsonl_stats.py stt-fi-1992-2018.dedup.jsonl
```

|docs|words|chars|
|----|-----|-----|
|2125674|442463215|2734890377|
|(2.1M)|(442.5M)|(2.7G)|

## Filter

Heuristic filter to remove documents that aren't primarily Finnish prose text.

```
python3 ../filter_jsonl.py \
    --digit-ratio 0.1 \
    --punct-ratio 0.1 \
    --upper-ratio 0.1 \
    --foreign-ratio 0.01 \
    --short-ratio 0.05 \
    --min-words 25 \
    --avg-len 5 \
    --lang-prob 0.999 \
    stt-fi-1992-2018.dedup.jsonl > stt-fi-1992-2018.dedup.filtered.jsonl
```

```
stt-fi-1992-2018.dedup.jsonl:	fail-avg-len	209425 (9.9%)
stt-fi-1992-2018.dedup.jsonl:	fail-digit-ratio	34744 (1.6%)
stt-fi-1992-2018.dedup.jsonl:	fail-foreign-ratio	318 (0.0%)
stt-fi-1992-2018.dedup.jsonl:	fail-lang-prob	56103 (2.6%)
stt-fi-1992-2018.dedup.jsonl:	fail-min-words	45531 (2.1%)
stt-fi-1992-2018.dedup.jsonl:	fail-punct-ratio	76320 (3.6%)
stt-fi-1992-2018.dedup.jsonl:	fail-short-ratio	33413 (1.6%)
stt-fi-1992-2018.dedup.jsonl:	fail-upper-ratio	45119 (2.1%)
stt-fi-1992-2018.dedup.jsonl:	pass-all	1624701 (76.4%)
stt-fi-1992-2018.dedup.jsonl: output 1624701/2125674 documents (76.4%)
```

## Checksum for deduplicated and filtered corpus

```
md5sum stt-fi-1992-2018.dedup.filtered.jsonl
```

```
51a5646c23960441d5411cbc912f4f50  stt-fi-1992-2018.dedup.filtered.jsonl
```

## Statistics for deduplicated and filtered corpus

```
python3 ../jsonl_stats.py stt-fi-1992-2018.dedup.filtered.jsonl
```

|docs|words|chars|
|----|-----|-----|
|1624701|307547134|2242231250|
|(1.6M)|(307.5M)|(2.2G)|
