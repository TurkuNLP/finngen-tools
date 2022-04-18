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

## Checksum for deduplicated

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
