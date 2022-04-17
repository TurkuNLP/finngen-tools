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
<http://urn.fi/urn:nbn:fi:lb-2019050901>,
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

(TODO)
