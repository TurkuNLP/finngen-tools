# Processing of the Reddit corpus

## Download data

Download comments data from http://files.pushshift.io/reddit/comments/

```
mkdir comments-data
curl -s http://files.pushshift.io/reddit/comments/ \
    | egrep '<td><a href=.*>RC_[0-9]{4}-[0-9]+' \
    | perl -pe 's/.*<a href='\''\.\/(.*?)'\''.*/$1/' \
    | while read f; do
    wget -P comments-data http://files.pushshift.io/reddit/comments/$f
done
```

Download submissions data from https://files.pushshift.io/reddit/submissions/

```
mkdir submissions-data
curl -s https://files.pushshift.io/reddit/submissions/ \
    | egrep '<td><a href=.*>RS_[0-9]{4}-[0-9]+' \
    | perl -pe 's/.*<a href='\''\.\/(.*?)'\''.*/$1/' \
    | while read f; do
    wget -P submissions-data http://files.pushshift.io/reddit/submissions/$f
done
```

Date ranges and total counts for comments and submissions data

```
d=comments-data; ls $d | head -n 1; ls $d | tail -n 1; ls $d | wc -l
```

```
RC_2005-12.zst
RC_2022-08.zst
201
```

```
d=submissions-data; ls $d | head -n 1; ls $d | tail -n 1; ls $d | wc -l
```

```
RS_2005-06.zst
RS_2022-08.zst
207
```

## Filter by subreddit

Filter to comments in the `r/Suomi` subreddit.

```
mkdir reddit-Suomi-comments
for f in comments-data/*.zst; do
    python3 get_subreddit.py Suomi $f \
        > reddit-Suomi-comments/$(basename $f .zst).jsonl
done
```

Filter to submissions in the `r/Suomi` subreddit.

```
mkdir reddit-Suomi-submissions
for f in submissions-data/*.zst; do
    python3 get_subreddit.py Suomi $f \
        > reddit-Suomi-submissions/$(basename $f .zst).jsonl
done
```

## Convert

Convert comments

```
python3 convert_reddit.py reddit-Suomi-comments/*.jsonl \
    > reddit-Suomi-comments.jsonl
```

Convert submissions

```
python3 convert_reddit.py reddit-Suomi-submissions/*.jsonl \
    > reddit-Suomi-submissions.jsonl
```

## Checksums for converted corpus

```
md5sum reddit-Suomi-comments.jsonl
```

```
c8c66ccdc6d5a6a23bd89cb47a7c4378  reddit-Suomi-comments.jsonl
```

```
md5sum reddit-Suomi-submissions.jsonl
```

```
7e55876d329f48cc4222bbff1cfd26fe  reddit-Suomi-submissions.jsonl
```

## Statistics for converted corpus

```
python3 ../jsonl_stats.py reddit-Suomi-comments.jsonl
```

|docs|words|chars|
|----|-----|-----|
|3840780|150894052|971875232|
|(3.8M)|(150.9M)|(971.9M)|

```
python3 ../jsonl_stats.py reddit-Suomi-submissions.jsonl
```

|docs|words|chars|
|----|-----|-----|
|154080|4084150|26717647|
|(154.1K)|(4.1M)|(26.7M)|

## Deduplicate

Clone tools supporting deduplication with `onion`

```
git clone https://github.com/spyysalo/onion-tools.git
```

Reverse for latest-first so that deduplication will remove older texts.

```
tac reddit-Suomi-comments.jsonl > reddit-Suomi-comments.rev.jsonl
```

```
tac reddit-Suomi-submissions.jsonl > reddit-Suomi-submissions.rev.jsonl 
```

Convert to `onion` input format

```
python3 onion-tools/jsonl_to_vert.py reddit-Suomi-comments.rev.jsonl \
    > reddit-Suomi-comments.rev.vert
```

```
python3 onion-tools/jsonl_to_vert.py reddit-Suomi-submissions.rev.jsonl \
    > reddit-Suomi-submissions.rev.vert
```

Mark duplicates with `onion` (<http://corpus.tools/wiki/Onion>)

```
onion reddit-Suomi-comments.rev.vert > reddit-Suomi-comments.rev.onion
```

```
onion reddit-Suomi-submissions.rev.vert > reddit-Suomi-submissions.rev.onion
```

Filter out duplicates

```
python3 onion-tools/filter_onion.py reddit-Suomi-comments.rev.onion \
    > reddit-Suomi-comments.rev.dedup.onion
```

```
output 113915520/148546040 (76.7%) lines
output 1701445/3840780 (44.3%) docs
```

```
python3 onion-tools/filter_onion.py reddit-Suomi-submissions.rev.onion \
    > reddit-Suomi-submissions.rev.dedup.onion
```

```
output 2436043/4205782 (57.9%) lines
output 23752/154080 (15.4%) docs
```

Convert back to JSONL

```
python3 onion-tools/onion_to_jsonl.py reddit-Suomi-comments.rev.dedup.onion \
    > reddit-Suomi-comments.rev.dedup.jsonl
```

```
python3 onion-tools/onion_to_jsonl.py reddit-Suomi-submissions.rev.dedup.onion \
    > reddit-Suomi-submissions.rev.dedup.jsonl
```

Reverse back

```
tac reddit-Suomi-comments.rev.dedup.jsonl > reddit-Suomi-comments.dedup.jsonl
```

```
tac reddit-Suomi-submissions.rev.dedup.jsonl > reddit-Suomi-submissions.dedup.jsonl
```

## Checksums for deduplicated corpus

```
md5sum reddit-Suomi-comments.dedup.jsonl
```

```
52bc5a48bba9bac81ef985c37b154f87  reddit-Suomi-comments.dedup.jsonl
```

```
md5sum reddit-Suomi-submissions.dedup.jsonl
```

```
3af458b29d0994b9fac453b7de6cccc1  reddit-Suomi-submissions.dedup.jsonl
```

## Statistics for deduplicated corpus

```
python3 ../jsonl_stats.py reddit-Suomi-comments.dedup.jsonl
```

|docs|words|chars|
|----|-----|-----|
|1701445|119280943|779170848|
|(1.7M)|(119.3M)|(779.2M)|

```
python3 ../jsonl_stats.py reddit-Suomi-submissions.dedup.jsonl
```

|docs|words|chars|
|----|-----|-----|
|23752|2567322|16304085|
|(23.8K)|(2.6M)|(16.3M)|

## Filter

Heuristic filter to remove documents that aren't primarily Finnish prose text.

```
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
    reddit-Suomi-comments.dedup.jsonl \
    > reddit-Suomi-comments.dedup.filtered.jsonl
```

```
reddit-Suomi-comments.dedup.jsonl:	fail-avg-len	3220 (0.2%)
reddit-Suomi-comments.dedup.jsonl:	fail-digit-ratio	1756 (0.1%)
reddit-Suomi-comments.dedup.jsonl:	fail-foreign-ratio	964 (0.1%)
reddit-Suomi-comments.dedup.jsonl:	fail-lang-prob	11543 (0.7%)
reddit-Suomi-comments.dedup.jsonl:	fail-max-repeat	956 (0.1%)
reddit-Suomi-comments.dedup.jsonl:	fail-punct-ratio	2587 (0.2%)
reddit-Suomi-comments.dedup.jsonl:	fail-short-ratio	31439 (1.8%)
reddit-Suomi-comments.dedup.jsonl:	fail-type-token-ratio	2919 (0.2%)
reddit-Suomi-comments.dedup.jsonl:	fail-upper-ratio	3138 (0.2%)
reddit-Suomi-comments.dedup.jsonl:	pass-all	1642923 (96.6%)
reddit-Suomi-comments.dedup.jsonl: output 1642923/1701445 documents (96.6%)
```

```
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
    reddit-Suomi-submissions.dedup.jsonl \
    > reddit-Suomi-submissions.dedup.filtered.jsonl
```

```
reddit-Suomi-submissions.dedup.jsonl:	fail-avg-len	112 (0.5%)
reddit-Suomi-submissions.dedup.jsonl:	fail-digit-ratio	54 (0.2%)
reddit-Suomi-submissions.dedup.jsonl:	fail-foreign-ratio	17 (0.1%)
reddit-Suomi-submissions.dedup.jsonl:	fail-lang-prob	191 (0.8%)
reddit-Suomi-submissions.dedup.jsonl:	fail-max-repeat	31 (0.1%)
reddit-Suomi-submissions.dedup.jsonl:	fail-punct-ratio	82 (0.3%)
reddit-Suomi-submissions.dedup.jsonl:	fail-short-ratio	1062 (4.5%)
reddit-Suomi-submissions.dedup.jsonl:	fail-type-token-ratio	157 (0.7%)
reddit-Suomi-submissions.dedup.jsonl:	fail-upper-ratio	136 (0.6%)
reddit-Suomi-submissions.dedup.jsonl:	pass-all	21910 (92.2%)
reddit-Suomi-submissions.dedup.jsonl: output 21910/23752 documents (92.2%)
```

## Checksum for filtered corpus

```
md5sum reddit-Suomi-comments.dedup.filtered.jsonl
```

```
a95368dda0ad6e3651777156dac09a29  reddit-Suomi-comments.dedup.filtered.jsonl
```

```
md5sum reddit-Suomi-submissions.dedup.filtered.jsonl
```

```
e92eacd8ba9767aad0c555f350ce2e11  reddit-Suomi-submissions.dedup.filtered.jsonl
```

## Statistics for filtered corpus

```
python3 ../jsonl_stats.py reddit-Suomi-comments.dedup.filtered.jsonl
```

|docs|words|chars|
|----|-----|-----|
|1642923|113893888|751506305|
|(1.6M)|(113.9M)|(751.5M)|

```
python3 ../jsonl_stats.py reddit-Suomi-submissions.dedup.filtered.jsonl
```

|docs|words|chars|
|----|-----|-----|
|21910|2240451|14612776|
|(21.9K)|(2.2M)|(14.6M)|
