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
d=submissions-data; ls $d | head -n 1; ls $d | tail -n 1; ls $d | wc -l
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

## Checksum

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

## Statistics

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

```
|docs|words|chars|
|----|-----|-----|
|154080|4084150|26717647|
|(154.1K)|(4.1M)|(26.7M)|
```

