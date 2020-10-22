# Halcyon

This is a simple static website builder based on PyYAML, Jinja2 and
MultiMarkdown (MMD).

I wrote it because I could and because Ruby's module infratsructure
was annoying me, despite Jekyll being an otherwise great tool.

See the [halcyon-ssg wiki](https://github.com/iarthair/halcyon-ssg/wiki)
for more information.

# Download

Halcyon source code is available from
[GitHub](https://github.com/iarthair/halcyon).
Clone the repository as follows:

```sh
$ git clone https://github.com/iarthair/halcyon.git
```

Run `setup.py` in the usual way to build and install, dependencies should
pull in automatically.

## Dependencies

Halcyon depends on:

* [Jinja2][1] Template system.
* [PyYAML][2] YAML parser/generator.
* [cmark-gfm][7]. GitHub Flavor Markdown parser with extensions.

## Running

All options are specified in `sitemap.yml`. Create one with suitable options
write some content and run `$ halcyon`. That's it.

[1]: https://jinja.palletsprojects.com/en/2.11.x/
[2]: https://pyyaml.org/
[7]: https://github.com/github/cmark-gfm.git
