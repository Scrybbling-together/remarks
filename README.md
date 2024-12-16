# Scrybble remarks

With Remarks, you can export notebooks and PDFs from your ReMarkable.

1. Export your notebooks as PDF
2. Extract highlights as text

## Goals

This is a fork of https://github.com/lucasrla/remarks. This fork has a few goals

- Support ReMarkable v3
- Support Type Folio output
- Retain support for older ReMarkable versions
- Note: This fork **does not** support all original output variants offered by the original remarks. The focus lies only on getting PDFs and text highlights out. You can use other tools such as Pandoc for conversion.

This project assumes familiarity with `git`, `python` and the commandline.

## A visual example

Highlight and annotate PDFs

<img width="300" alt="IMG_0642-low.jpg" src="https://user-images.githubusercontent.com/1920195/88480247-3d776680-cf2b-11ea-9c30-061ec0e5cc60.jpg">

And then use `remarks` to export annotated pages to `Markdown`, `PDF`, `PNG`, or `SVG` on your computer:

<img width="300" alt="demo-remarks-png.png" src="https://user-images.githubusercontent.com/1920195/88480249-410aed80-cf2b-11ea-919b-22fb550ed9d7.png">

> <mark>WHAT IS LIFE?</mark>
> 
> Based on lectures delivered under the auspices of the <mark>Dublin Institute for</mark> <mark>Advanced Studies at Trinity College,</mark> Dublin, in February 1943
> 
> <mark>To</mark>
> <mark>the memory of My</mark> <mark>Parents</mark>

## Installing Remarks

Linux is recommended, Windows should work too.

- Install Python 3.10+ and [Poetry](https://python-poetry.org/docs/)

```bash
## Get remarks on your computer
git clone https://github.com/lucasrla/remarks.git && cd remarks
## Install the dependencies
poetry install
```

## Using Remarks

To get `remarks` up and running on your local machine, follow the instructions below:

## Usage and Demo

Run `remarks` and check out what arguments are available:

```sh
python -m pytest -q remarks/test_initial.py
```

## Credits and Acknowledgements

- [Scrybble](https://scrybble.ink) A paid user-friendly service that helps non-technical ReMarkable users synchronize their notebooks to Obsidian. Financially supports @Azeirah to work on remarks.

- [lucasrla](https://github.com/lucasrla) who wrote the original implementation of remarks

- [@JorjMcKie](https://github.com/JorjMcKie) who wrote and maintains the great [PyMuPDF](https://github.com/pymupdf/PyMuPDF)

- [u/stucule](https://www.reddit.com/user/stucule/) who [posted to r/RemarkableTablet](https://www.reddit.com/r/RemarkableTablet/comments/7c5fh0/work_in_progress_format_of_the_lines_files/) the first account (that I could find online) about reverse engineering `.rm` files

- [@ax3l](https://github.com/ax3l) who wrote [lines-are-rusty](https://github.com/ax3l/lines-are-rusty) / [lines-are-beautiful](https://github.com/ax3l/lines-are-beautiful) and also [contributed to reverse engineering of `.rm` files](https://plasma.ninja/blog/devices/remarkable/binary/format/2017/12/26/reMarkable-lines-file-format.html)

- [@edupont, @Liblor, @florian-wagner, and @jackjackk for their contributions to rM2svg](https://github.com/reHackable/maxio/blob/33cdc1706b29698c15aac647619374e895ed3869/tools/rM2svg)

- [@ericsfraga, @jmiserez](https://github.com/jmiserez/maxio/blob/ee15bcc86e4426acd5fc70e717468862dce29fb8/tmp-rm16-ericsfraga-rm2svg.py), [@peerdavid](https://github.com/peerdavid/rmapi/blob/master/tools/rM2svg), [@phill777](https://github.com/phil777/maxio) and [@lschwetlick](https://github.com/lschwetlick/maxio/blob/master/rm_tools/rM2svg.py) for updating rM2svg to the most recent `.rm` format

- [@lschwetlick](https://github.com/lschwetlick) who wrote [rMsync](https://github.com/lschwetlick/rMsync) and also two blog posts about reMarkable-related software [[1](http://lisaschwetlick.de/blog/2018/03/25/reMarkable/), [2](http://lisaschwetlick.de/blog/2019/06/10/reMarkable-Update/)]

- [@soulisalmed](https://github.com/soulisalmed) who wrote [biff](https://github.com/soulisalmed/biff)

- [@benlongo](https://github.com/benlongo) who wrote [remarkable-highlights](https://github.com/benlongo/remarkable-highlights)

For more reMarkable resources, check out [awesome-reMarkable](https://github.com/reHackable/awesome-reMarkable) and [remarkablewiki.com](https://remarkablewiki.com/).

## License

`remarks` is [Free Software](https://www.gnu.org/philosophy/free-sw.html) distributed under the [GNU General Public License v3.0](https://choosealicense.com/licenses/gpl-3.0/).

## Disclaimers

This is a hobby project of an enthusiastic reMarkable user. There is no warranty whatsoever. Use it at your own risk.

> The author(s) and contributor(s) are not associated with reMarkable AS, Norway. reMarkable is a registered trademark of reMarkable AS in some countries. Please see https://remarkable.com for their products.
