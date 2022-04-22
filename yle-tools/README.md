# Processing of the Yle Finnish News Archive corpora

## Download data

Original files
`ylenews-fi-2011-2018-src.zip`,
`ylenews-fi-2019-2020-src.zip`,
`ylenews-fi-2011-2018-selko-src.zip` and
`ylenews-fi-2019-2020-selko-src.zip`
downloaded from
<http://urn.fi/urn:nbn:fi:lb-2017070501>,
<http://urn.fi/urn:nbn:fi:lb-2021050401>,
<http://urn.fi/urn:nbn:fi:lb-2019050901> and
<http://urn.fi/urn:nbn:fi:lb-2021050701>
(Academic license, registration required)

## Unpack

```
for f in ylenews-fi-*-src.zip; do unzip -d unpacked $f; done
```

## Convert

```
mkdir converted
for d in unpacked/ylenews-fi-*-src; do
    python3 convert_yle.py $d > converted/$(basename $d -src).jsonl;
done
```

## Checksum for converted corpora

```
md5sum converted/ylenews-fi-*.jsonl
```

```
64051b9cd98c968ed667624b38399272  converted/ylenews-fi-2011-2018.jsonl
a50d3151d083ac4e95b89321eb2ebbd9  converted/ylenews-fi-2011-2018-selko.jsonl
4a345032454b362103d3e517ac9370bc  converted/ylenews-fi-2019-2020.jsonl
8e83daaf0625a706a319cb3670e1ff1b  converted/ylenews-fi-2019-2020-selko.jsonl
```

## Statistics for converted corpora

```
for f in converted/ylenews-fi-*.jsonl; do
    echo '###' $f; echo; python3 ../jsonl_stats.py $f; echo;
done
```

### converted/ylenews-fi-2011-2018.jsonl

|docs|words|chars|
|----|-----|-----|
|703673|186450815|1326878066|
|(703.7K)|(186.5M)|(1.3G)|

### converted/ylenews-fi-2011-2018-selko.jsonl

|docs|words|chars|
|----|-----|-----|
|4063|652304|4406271|
|(4.1K)|(652.3K)|(4.4M)|

### converted/ylenews-fi-2019-2020.jsonl

|docs|words|chars|
|----|-----|-----|
|128815|47327439|340165985|
|(128.8K)|(47.3M)|(340.2M)|

### converted/ylenews-fi-2019-2020-selko.jsonl

|docs|words|chars|
|----|-----|-----|
|1916|281185|1897240|
|(1.9K)|(281.2K)|(1.9M)|

## Deduplicate

Clone tools supporting deduplication with `onion`

Reverse for latest-first so that deduplication will remove older versions.

```
for f in converted/ylenews-fi-*.jsonl; do
    tac $f > $(basename $f .jsonl).rev.jsonl;
done
```

Convert to `onion` input format

```
for f in ylenews-fi-*.rev.jsonl; do
    python3 onion-tools/jsonl_to_vert.py $f > ${f%.jsonl}.vert;
done
```

Mark duplicates with `onion` (<http://corpus.tools/wiki/Onion>)

```
for f in ylenews-fi-*.vert; do onion $f > ${f%.vert}.onion; done
```

Filter out duplicates

```
for f in ylenews-fi-*.onion; do
    echo '###' $f; python3 onion-tools/filter_onion.py $f > ${f%.onion}.dedup;
done
```

### ylenews-fi-2011-2018.rev.onion

output 182621087/187690999 (97.3%) lines
output 689573/703673 (98.0%) docs

### ylenews-fi-2011-2018-selko.rev.onion

output 633342/673458 (94.0%) lines
output 2252/4063 (55.4%) docs

### ylenews-fi-2019-2020.rev.onion

output 44776198/48364325 (92.6%) lines
output 124356/128815 (96.5%) docs

### ylenews-fi-2019-2020-selko.rev.onion

output 280807/299583 (93.7%) lines
output 929/1916 (48.5%) docs

Convert back to JSONL

```
for f in ylenews-fi-*.dedup; do
    python3 onion-tools/onion_to_jsonl.py $f > $f.jsonl;
done
```

Reverse back

```
for f in ylenews-fi-*.rev.dedup.jsonl; do tac $f > ${f/.rev}; done
```

## Checksum for deduplicated corpora

```
ls ylenews-fi-*.dedup.jsonl | egrep -v rev | xargs md5sum
```

```
e4e0f8b3685d9514d3b0b5c9eb0491f1  ylenews-fi-2011-2018.dedup.jsonl
3e8d0f7f3db441c07fd06c41a7496cfc  ylenews-fi-2011-2018-selko.dedup.jsonl
7191e49e26615ce56525d4110e364705  ylenews-fi-2019-2020.dedup.jsonl
384bda1bd31949c72f3d42cc54b142a9  ylenews-fi-2019-2020-selko.dedup.jsonl
```

## Statistics for deduplicated corpora

```
ls ylenews-fi-*.dedup.jsonl | egrep -v rev | while read f; do
    echo '###' $f; python3 ~/git_checkout/finngen-tools/jsonl_stats.py $f;
done
```

### ylenews-fi-2011-2018.dedup.jsonl

|docs|words|chars|
|----|-----|-----|
|689573|181351046|1291875515|
|(689.6K)|(181.4M)|(1.3G)|

### ylenews-fi-2011-2018-selko.dedup.jsonl

|docs|words|chars|
|----|-----|-----|
|2252|609038|4148049|
|(2.3K)|(609.0K)|(4.1M)|

### ylenews-fi-2019-2020.dedup.jsonl

|docs|words|chars|
|----|-----|-----|
|124356|43813093|315055509|
|(124.4K)|(43.8M)|(315.1M)|

### ylenews-fi-2019-2020-selko.dedup.jsonl

|docs|words|chars|
|----|-----|-----|
|929|260910|1782357|
|(929.0)|(260.9K)|(1.8M)|

## Filter

Heuristic filter to remove documents that aren't primarily Finnish prose text.

```
ls ylenews-fi-*.dedup.jsonl | egrep -v rev | while read f;
    do echo '###' $f;
    python3 ../filter_jsonl.py \
        --digit-ratio 0.1 \
        --punct-ratio 0.1 \
        --upper-ratio 0.1 \
        --foreign-ratio 0.01 \
        --short-ratio 0.05 \
        --min-words 25 \
        --avg-len 5 \
        --lang-prob 0.999 \
        $f > ${f%.jsonl}.filtered.jsonl
done
```

### ylenews-fi-2011-2018.dedup.jsonl

```
ylenews-fi-2011-2018.dedup.jsonl:	fail-avg-len	1319 (0.2%)
ylenews-fi-2011-2018.dedup.jsonl:	fail-digit-ratio	577 (0.1%)
ylenews-fi-2011-2018.dedup.jsonl:	fail-foreign-ratio	503 (0.1%)
ylenews-fi-2011-2018.dedup.jsonl:	fail-lang-prob	2043 (0.3%)
ylenews-fi-2011-2018.dedup.jsonl:	fail-min-words	4154 (0.6%)
ylenews-fi-2011-2018.dedup.jsonl:	fail-punct-ratio	285 (0.0%)
ylenews-fi-2011-2018.dedup.jsonl:	fail-short-ratio	5288 (0.8%)
ylenews-fi-2011-2018.dedup.jsonl:	fail-upper-ratio	1383 (0.2%)
ylenews-fi-2011-2018.dedup.jsonl:	pass-all	674021 (97.7%)
ylenews-fi-2011-2018.dedup.jsonl: output 674021/689573 documents (97.7%)
```

### ylenews-fi-2011-2018-selko.dedup.jsonl

```
ylenews-fi-2011-2018-selko.dedup.jsonl:	fail-avg-len	7 (0.3%)
ylenews-fi-2011-2018-selko.dedup.jsonl:	fail-foreign-ratio	1 (0.0%)
ylenews-fi-2011-2018-selko.dedup.jsonl:	fail-lang-prob	3 (0.1%)
ylenews-fi-2011-2018-selko.dedup.jsonl:	fail-min-words	251 (11.1%)
ylenews-fi-2011-2018-selko.dedup.jsonl:	pass-all	1990 (88.4%)
ylenews-fi-2011-2018-selko.dedup.jsonl: output 1990/2252 documents (88.4%)
```

### ylenews-fi-2019-2020.dedup.jsonl

```
ylenews-fi-2019-2020.dedup.jsonl:	fail-avg-len	221 (0.2%)
ylenews-fi-2019-2020.dedup.jsonl:	fail-digit-ratio	47 (0.0%)
ylenews-fi-2019-2020.dedup.jsonl:	fail-foreign-ratio	228 (0.2%)
ylenews-fi-2019-2020.dedup.jsonl:	fail-lang-prob	169 (0.1%)
ylenews-fi-2019-2020.dedup.jsonl:	fail-min-words	1271 (1.0%)
ylenews-fi-2019-2020.dedup.jsonl:	fail-punct-ratio	3 (0.0%)
ylenews-fi-2019-2020.dedup.jsonl:	fail-short-ratio	661 (0.5%)
ylenews-fi-2019-2020.dedup.jsonl:	fail-upper-ratio	66 (0.1%)
ylenews-fi-2019-2020.dedup.jsonl:	pass-all	121690 (97.9%)
ylenews-fi-2019-2020.dedup.jsonl: output 121690/124356 documents (97.9%)
```

### ylenews-fi-2019-2020-selko.dedup.jsonl

```
ylenews-fi-2019-2020-selko.dedup.jsonl:	fail-avg-len	1 (0.1%)
ylenews-fi-2019-2020-selko.dedup.jsonl:	fail-min-words	123 (13.2%)
ylenews-fi-2019-2020-selko.dedup.jsonl:	pass-all	805 (86.7%)
ylenews-fi-2019-2020-selko.dedup.jsonl: output 805/929 documents (86.7%)
```

## Checksums for deduplicated and filtered corpora

```
md5sum ylenews-fi-*.dedup.filtered.jsonl
```

```
20deeb8e5617d26d4fc75c0967a48d54  ylenews-fi-2011-2018.dedup.filtered.jsonl
51f950c5df6b8a96a59ecd090784b934  ylenews-fi-2011-2018-selko.dedup.filtered.jsonl
a1f9b843d2479fb7bfeea71a4cb69ccf  ylenews-fi-2019-2020.dedup.filtered.jsonl
f1ad2c06aae40644ecf8d0f07df8821f  ylenews-fi-2019-2020-selko.dedup.filtered.jsonl
```

## Statistics for deduplicated and filtered corpora

```
for f in ylenews-fi-*.dedup.filtered.jsonl; do
    echo '###' $f; python3 ../jsonl_stats.py $f;
done
```

### ylenews-fi-2011-2018.dedup.filtered.jsonl

|docs|words|chars|
|----|-----|-----|
|674021|178238822|1274612172|
|(674.0K)|(178.2M)|(1.3G)|

### ylenews-fi-2011-2018-selko.dedup.filtered.jsonl

|docs|words|chars|
|----|-----|-----|
|1990|599426|4090114|
|(2.0K)|(599.4K)|(4.1M)|

### ylenews-fi-2019-2020.dedup.filtered.jsonl

|docs|words|chars|
|----|-----|-----|
|121690|43212584|311659817|
|(121.7K)|(43.2M)|(311.7M)|

### ylenews-fi-2019-2020-selko.dedup.filtered.jsonl

|docs|words|chars|
|----|-----|-----|
|805|256652|1756920|
|(805.0)|(256.7K)|(1.8M)|
