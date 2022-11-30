# Processing of Wikipedia corpus

## Download data

```
wget https://mirror.accum.se/mirror/wikimedia.org/dumps/fiwiki/20221120/fiwiki-20221120-pages-articles.xml.bz2
```

## Clone WikiExtractor

Use WikiExtractor (<https://github.com/attardi/wikiextractor>) for
initial extraction.

```
git clone https://github.com/attardi/wikiextractor.git
```

Check out v3.0.6 to avoid <https://github.com/attardi/wikiextractor/issues/283>

```
cd wikiextractor
git checkout tags/v3.0.6
cd ..
```

## Extract text

```
PYTHONPATH=wikiextractor python3 -m wikiextractor.WikiExtractor \
    fiwiki-20221120-pages-articles.xml.bz2 \
    --processes 16 \
    --output fiwiki
```

## Convert to JSONL

```
python3 convert_wikiextractor.py fiwiki > fiwiki-20221120-pages.jsonl
```

## Checksum for converted corpus

```
md5sum fiwiki-20221120-pages.jsonl
```

```
6737c2b4dd71141cc684da0832bea3bc  fiwiki-20221120-pages.jsonl
```

## Statistics for converted corpus

```
python3 ../jsonl_stats.py fiwiki-20221120-pages.jsonl
```

|docs|words|chars|
|----|-----|-----|
|837069|119704503|823498268|
|(837.1K)|(119.7M)|(823.5M)|

## Deduplicate

```
git clone https://github.com/spyysalo/onion-tools.git
```

Convert to `onion` input format

```
python3 onion-tools/jsonl_to_vert.py fiwiki-20221120-pages.jsonl \
    > fiwiki-20221120-pages.vert
```

Mark duplicates with `onion` (<http://corpus.tools/wiki/Onion>)

```
onion fiwiki-20221120-pages.vert > fiwiki-20221120-pages.onion
```

Filter out duplicates

```
python3 onion-tools/filter_onion.py fiwiki-20221120-pages.onion \
    > fiwiki-20221120-pages.dedup.onion
```

```
output 99180896/105471310 (94.0%) lines
output 470171/837069 (56.2%) docs
```

Convert back to JSONL

```
python3 onion-tools/onion_to_jsonl.py fiwiki-20221120-pages.dedup.onion \
    > fiwiki-20221120-pages.dedup.jsonl
```

## Checksum for deduplicated corpus

```
md5sum fiwiki-20221120-pages.dedup.jsonl
```

```
ef52f3d130495ef5328ac49fe3f24d1d  fiwiki-20221120-pages.dedup.jsonl
```

## Statistics for deduplicated corpus

```
python3 ../jsonl_stats.py fiwiki-20221120-pages.dedup.jsonl
```

|docs|words|chars|
|----|-----|-----|
|470171|114382592|788865437|
|(470.2K)|(114.4M)|(788.9M)|

## Filter

Heuristic filter to remove documents that aren't primarily Finnish prose text.

```
python3 ../filter_jsonl.py \
    --digit-ratio 0.1 \
    --punct-ratio 0.1 \
    --upper-ratio 0.1 \
    --foreign-ratio 0.05 \
    --short-ratio 0.1 \
    --min-words 15 \
    --avg-len 5 \
    --lang-prob 0.99 \
    fiwiki-20221120-pages.dedup.jsonl \
    > fiwiki-20221120-pages.dedup.filtered.jsonl
```

```
fiwiki-20221120-pages.dedup.jsonl:	fail-avg-len	2 (0.0%)
fiwiki-20221120-pages.dedup.jsonl:	fail-digit-ratio	4851 (1.0%)
fiwiki-20221120-pages.dedup.jsonl:	fail-foreign-ratio	1552 (0.3%)
fiwiki-20221120-pages.dedup.jsonl:	fail-lang-prob	6021 (1.3%)
fiwiki-20221120-pages.dedup.jsonl:	fail-min-words	132 (0.0%)
fiwiki-20221120-pages.dedup.jsonl:	fail-punct-ratio	541 (0.1%)
fiwiki-20221120-pages.dedup.jsonl:	fail-short-ratio	3072 (0.7%)
fiwiki-20221120-pages.dedup.jsonl:	fail-upper-ratio	983 (0.2%)
fiwiki-20221120-pages.dedup.jsonl:	pass-all	453017 (96.4%)
fiwiki-20221120-pages.dedup.jsonl: output 453017/470171 documents (96.4%)
```

## Checksum for deduplicated and filtered corpus

```
md5sum fiwiki-20221120-pages.dedup.filtered.jsonl
```

```
182f2ebde3efd4cf74ff0f7dfcd116b0  fiwiki-20221120-pages.dedup.filtered.jsonl
```

## Statistics for deduplicated and filtered corpus

```
python3 ../jsonl_stats.py fiwiki-20221120-pages.dedup.filtered.jsonl
```

|docs|words|chars|
|----|-----|-----|
|453017|112559323|778917493|
|(453.0K)|(112.6M)|(778.9M)|
