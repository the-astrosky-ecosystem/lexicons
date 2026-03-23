# lexicons

Lexicon (record / query) schemas for Astrosky Ecosystem apps, services, or tools.

See [this tutorial](https://nickthesick.com/blog/Publishing+ATProto+Lexicons) for how this works.

## Dependencies

Publishing lexicons requires the [goat CLI tool](https://github.com/bluesky-social/goat). If you have `go` installed, then this is as easy as

```bash
go install github.com/bluesky-social/goat@latest
```

You may need to also make sure that `/home/USERNAME/go/bin` is in your `$PATH`.


## Updating lexicons

The following scripts update certain lexicons in this repository:

- NASA GCN: `uv run update-gcn`

Be sure to run `goat lex lint` after updating to check your results. **These scripts will overwrite existing lexicons** - be careful!
