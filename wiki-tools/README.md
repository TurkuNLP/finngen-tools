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
python3 convert_wikiextractor.py fiwiki > fiwiki.jsonl
```

## Checksum for converted corpus

```
md5sum fiwiki.jsonl
```

```
82472bbe4bd12a0948cbdba3d5808a1c  fiwiki.jsonl
```

## Statistics for converted corpus

```
python3 ../jsonl_stats.py fiwiki.jsonl
```

|docs|words|chars|
|----|-----|-----|
|837069|119704503|824738045|
|(837.1K)|(119.7M)|(824.7M)|
