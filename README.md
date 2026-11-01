# Wolfram Client Library for Python (wolframpy fork)

> [!NOTE]
> This is an independent fork of Wolfram Research's MIT-licensed
> [WolframClientForPython](https://github.com/WolframResearch/WolframClientForPython),
> forked from version 1.4.1. It is **not affiliated with, endorsed by or supported by
> Wolfram Research**; report problems with this fork here, not to Wolfram. The import and
> distribution name are unchanged (`wolframclient`), so `pip install wolframclient` from
> PyPI still gets the upstream release; install from this repository to get the fork.

The Wolfram Client Library provides Wolfram Language integration in Python:

- evaluate arbitrary code on a local kernel,
- evaluate arbitrary code on the Wolfram Cloud, public or private,
- call deployed `APIFunction`s,
- build Python functions on top of Wolfram Language functions,
- represent arbitrary Wolfram Language code as Python objects,
- serialize Python objects to Wolfram Language `InputForm` strings and to WXF,
- extend serialization to any Python class,
- parse WXF-encoded expressions.

## Requirements

- Python 3.12 or newer
- Wolfram Language 11.3 or newer, for local kernel evaluation

## Installation

Core install (serialization, deserialization, `wl` expressions):

```bash
uv add "wolframclient @ git+https://github.com/edoardob90/wolframpy"
```

Optional features are extras:

| Extra | Enables | Installs |
|---|---|---|
| `kernel` | local kernel sessions, ExternalEvaluate | `pyzmq`, `oauthlib` |
| `cloud` | Wolfram Cloud sessions and API calls | `requests`, `oauthlib` |
| `async` | asynchronous cloud sessions | `aiohttp` |
| `pandas` | pandas and Arrow serialization | `pandas`, `pyarrow` |
| `pillow` | PIL image serialization | `Pillow` |
| `all` | everything above | |

```bash
uv add "wolframclient[kernel,pandas] @ git+https://github.com/edoardob90/wolframpy"
```

With pip: `pip install "wolframclient[kernel] @ git+https://github.com/edoardob90/wolframpy"`.

## Quickstart

```python
from wolframclient.language import wl, wlexpr
from wolframclient.serializers import export

export(wl.Range(3))  # b'Range[3]'
export([1, 2, 3], target_format="wxf")  # WXF bytes
```

With a local kernel (needs the `kernel` extra):

```python
from wolframclient.evaluation import WolframLanguageSession

# Pass the kernel path if it is not found automatically, e.g. on macOS:
# WolframLanguageSession("/Applications/Wolfram.app/Contents/MacOS/WolframKernel")
with WolframLanguageSession() as session:
    session.evaluate(wl.StringReverse("abc"))  # 'cba'
    session.evaluate(wlexpr("Range[5]"))  # packed array, NumPy-backed: [1 2 3 4 5]
```

The upstream [documentation](https://reference.wolfram.com/language/WolframClientForPython)
covers the full API, which this fork keeps.

## Development

```bash
git clone https://github.com/edoardob90/wolframpy && cd wolframpy
uv sync --all-extras          # package, all extras and dev tools
uv run pre-commit install     # ruff, formatting and lockfile hooks
uv run pytest                 # kernel/cloud tests are skipped unless configured
```

To run the kernel and cloud tests, see [`tests/README.md`](tests/README.md). Build the
docs with `docs/build.sh`. See [`CLAUDE.md`](CLAUDE.md) for the workflow and
[`docs/MODERNIZATION_PLAN.md`](docs/MODERNIZATION_PLAN.md) for the roadmap.

## License

MIT, see [LICENSE](LICENSE). Original work copyright 2018 Wolfram Research Inc.;
modifications copyright 2026 Edoardo Baldi.

Wolfram, Wolfram Language, Wolfram Cloud and Mathematica are trademarks of Wolfram
Research, Inc. They are used here only to describe what this library interoperates with.
