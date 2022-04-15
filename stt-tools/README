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
1911f26ea5ddfab77011929b33f7caff  stt-fi-1992-2018.jsonl
```

## Statistics for converted corpus

```
python3 finngen-tools/jsonl_stats.py stt-fi-1992-2018.jsonl
```

|docs|words|chars|
|----|-----|-----|
|2848322|693718677|4145360051|
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
    > combined.rev.filtered.onion
```

```
output 406112341/628430118 (64.6%) lines
output 2125676/2848322 (74.6%) docs
```

Convert back to JSONL

```
python3 onion-tools/onion_to_jsonl.py combined.rev.filtered.onion \
    > combined.rev.filtered.jsonl
```

Reverse back

```
tac combined.rev.filtered.jsonl > combined.filtered.jsonl
```

## Rename

```
mv combined.filtered.jsonl stt-fi-1992-2018.dedup.jsonl
```

## Checksum for deduplicated

```
md5sum stt-fi-1992-2018.dedup.jsonl
```

```
b5ab84ad93fa284ec2ae94bb5dacc91d  stt-fi-1992-2018.dedup.jsonl
```

## Statistics for deduplicated corpus

```
python3 finngen-tools/jsonl_stats.py stt-fi-1992-2018.dedup.jsonl
```

|docs|words|chars|
|----|-----|-----|
|2125676|442462974|2734899491|
|(2.1M)|(442.5M)|(2.7G)|
