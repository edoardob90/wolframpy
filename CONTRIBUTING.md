# Contributing to Wolfram<sup>&reg;</sup>

> [!NOTE]
> This repository is the `wolframpy` fork. Report bugs and send pull requests for the
> fork to [edoardob90/wolframpy](https://github.com/edoardob90/wolframpy/issues); the
> development workflow is at the end of this file. The sections below are inherited
> from upstream Wolfram Research.

Thank you for taking the time to contribute to the [Wolfram Research](https://github.com/wolframresearch) repos on GitHub.

## Licensing of Contributions

By contributing to Wolfram, you agree and affirm that:

> Wolfram may release your contribution under the terms of the [MIT license](https://opensource.org/licenses/MIT); and

> You have read and agreed to the [Developer Certificate of Origin](http://developercertificate.org/), version 1.1 or later.

Please see [LICENSE](LICENSE) for licensing conditions pertaining
to individual repositories.


## Bug reports

### Security Bugs

Please **DO NOT** file a public issue regarding a security issue.
Rather, send your report privately to security@wolfram.com.  Security
reports are appreciated and we will credit you for it.  We do not offer
a security bounty, but the forecast in your neighborhood will be cloudy
with a chance of Wolfram schwag!

### General Bugs

Please use the repository issues page to submit general bug issues.

Please do not duplicate issues.

Please do send a complete and well-written report to us.  Note:  **the
thoroughness of your report will positively correlate to our willingness
and ability to address it**.

When reporting issues, always include:

* Your version of *Mathematica*<sup>&reg;</sup> or the Wolfram Language<sup>&trade;</sup>.
* Your operating system.

## Development workflow

This fork is developed with [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-extras          # install the package, all extras and the dev group
uv run pre-commit install     # ruff check + format, uv.lock check, whitespace
uv run pytest                 # tests; kernel/cloud tests auto-skip without config
uv run ruff check && uv run ruff format --check
docs/build.sh                 # HTML docs into docs/_build/html
```

- Add or change dependencies only through uv (`uv add`, `uv add --optional <extra>`,
  `uv add --group <group>`, `uv remove`); never edit `uv.lock` by hand.
- Tests live in `tests/` and are named `test_*.py`. Mark tests that need a local kernel
  with `pytest.mark.kernel` and those that need Wolfram Cloud credentials with
  `pytest.mark.cloud`; see `tests/README.md` to run them.
- Every bug fix starts with a test that fails without the fix.
- Larger changes follow the plan → tracking issue → PR workflow described in
  [`CLAUDE.md`](CLAUDE.md).
