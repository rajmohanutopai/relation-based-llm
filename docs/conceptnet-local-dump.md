# ConceptNet Local Dump

Date: 2026-05-01

Downloaded source:

```text
https://s3.amazonaws.com/conceptnet/downloads/2019/edges/conceptnet-assertions-5.7.0.csv.gz
```

Full compressed dump:

```text
497,963,447 bytes
34,074,917 rows
```

Local filtered file:

```text
data/external/conceptnet/conceptnet-assertions-5.7.0-en-en.tsv
```

Filter:

```text
Keep rows where both start and end concept URIs begin with /c/en/
```

Local filtered size:

```text
3,423,004 rows
1,014,357,374 bytes
about 967 MiB
```

SHA-256:

```text
ae5323083011f341a7f78c085447169e71163a4e844cf69a341e7b25cf7de68b
```

The compressed temporary filtered file was:

```text
/tmp/conceptnet-5.7-en-en.tsv.gz
57,454,446 bytes
sha256: 52a388c444eca8f35d9c62e05f28ec9f901b70a429c866190d3846385c369fdb
```

Git policy:

```text
data/external/ is ignored in .gitignore.
Do not commit the raw ConceptNet dump.
```
