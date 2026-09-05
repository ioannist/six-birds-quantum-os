# External Citation Bibliography Template

Use this file to collect candidate external references before promoting them to `references.bib`.

- TODO: citation key, source, reason for inclusion, and status.

## Entry templates

Copy the relevant shape into `references.bib` under the matching banner and fill it in.
Citation keys are stable and must not be renamed once drafting starts.

### Sibling paper in the series

```bibtex
@misc{TsiokosYYYYShortKey,
  author = {Tsiokos, Ioannis},
  title  = {Title of the sibling paper},
  year   = {YYYY}
}
```

### Foundations paper this work builds on

```bibtex
@misc{TsiokosYYYYFoundations,
  author = {Tsiokos, Ioannis},
  title  = {Foundations title},
  year   = {YYYY},
  doi    = {TODO},
  url    = {TODO}
}
```

### Preprint with an arXiv identifier

```bibtex
@misc{ShortKey,
  author        = {Tsiokos, Ioannis},
  title         = {{Title} with protected capitalization},
  year          = {YYYY},
  eprint        = {ARXIV.ID},
  archivePrefix = {arXiv},
  primaryClass  = {PRIMARY.CLASS},
  note          = {\href{https://arxiv.org/abs/ARXIV.ID}{arXiv:ARXIV.ID [PRIMARY.CLASS]}}
}
```
