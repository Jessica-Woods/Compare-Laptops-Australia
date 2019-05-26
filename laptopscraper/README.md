# How to use

To scrape website data run:

```
scrapy crawl scorptec -o laptops.json -t jsonlines
```

Make sure to delete `laptops.json` before re-running as scrapy appends to the existing file

To turn the json lines into a valid json add `[` to the top of the file, `]` to the bottom of the file
and append a `,` to each existing line.
