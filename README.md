# Halcyon

This is a simple static website builder based on PyYAML, Jinja2, libsass and
Commonmark.

Halcyon originated when I wrote a Python script mainly to learn about
[Jinja2][1] templates. I have a few uses for something like this beyond just
web site maintenance.

A secondary reason was to sharpen my Python skills as it's a couple of years
since I used Python in anger and I wanted to start something from scratch in
Python 3.  I also found this was initially simpler to do than to try to
understand the source code of, say, Sphinx or Mkdocs.  Then I got carried away,
restructured the script, added more features, called it Halcyon and released
the code on GitHub.  Nevertheless, having trodden that path, going back and
looking at those projects it is now much easier to understand what they are
doing and the rationale for their design.

Finally, I wrote it because because Ruby's module infrasructure was annoying
me, despite Jekyll being an otherwise great tool.

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
* [libsass-python][2] Sass/SCSS for Python.
* [PyYAML][3] YAML parser/generator.
* [cmark-gfm][4]. GitHub Flavor Markdown parser with extensions.

## Running

All options are specified in `sitemap.yml`. Create one with suitable options
write some content and run `$ halcyon`. That's it.

[1]: https://jinja.palletsprojects.com/en/2.11.x/
[2]: https://sass.github.io/libsass-python/
[3]: https://pyyaml.org/
[4]: https://github.com/github/cmark-gfm.git
