# Quick scripts to redact old blog images

For data protection reasons, the maintainers of a blog needed to
replace images older than some threshold with a placeholder image.
This repo holds the quick and dirty scripts I used to do this.


## Script to run on webhost machine

The hosting machine did not have a very fresh version of Python, and
no `ensurepip`, so the `venv` module would not create a venv.  The
hosting machine did have the `file` and `jhead` utilities, though, so
the script `measure_sizes.py` calls out to those separate programs.

It needs env.vars

* `HOME`
* `SITE_NAME`

to be set.


## Script to run on developer machine

Many images are of the same size, so to cut down on space, only one
image is generated per size.  These files are created and written to a
directory `placeholders-for-removed`.  Then, for every original file
on the webhost, a symlink is created with the same name pointing
(using a relative path) to the generated image of matching size.

Needs env.vars

* `HOSTING_HOME`
* `SITE_NAME`

to be set.

### Image creation

In an attempt to make the placeholders look better, different layouts
of the text are available for the script to choose from, breaking the
short text into different numbers of lines.  The layout whose aspect
ratio most closely matches the image's aspect ratio is used.  By
default, text at 18px is used, but if this would use more than 80% of
either the width or the height, a smaller font is used so bring the
text down to that limit.  We end up with images like this:

![Examples of placeholder images](two-examples.png)

This part is quite slow and could no doubt be parallelised.


## Gathering results into separate tarfiles

Creating a tarfile for the actual images is done directly from the
command line:

``` shell
tar \
    --create \
    --xz \
    --file=placeholder-images.tar.xz \
    --directory=images-out \
    placeholders-for-removed
```

The resulting `placeholder-images.tar.xz` file can then be unpacked in
the `wp-content/uploads/` directory.

The blog is organised based on the European academic year, and it was
helpful to gather the symlinks into such years.  Taking the start of
the academic year to be the first day of August, the script
`gather_into_years.py` generates tarfiles with names of the form

``` text
symlinks-{year}-{year+1}.tar
```

and also writes a list of null-terminated filenames in each of the
tarfiles to files with names of the form

``` text
filenames-{year}-{year+1}.null-terminated
```

The idea is that these `filenames-*.null-terminated` files can be used
for creating year-by-year tarfiles of the original files.  Once this
is done, the original files can be replaced with symlinks, by
unpacking the relevant `symlinks-*.tar.xz` files.

Creating tarfiles of the original images can be done like this:

``` shell
tar \
    --create \
    --file=original-images/original-images-2008-2009.tar \
    --directory=$HOME/$SITE_NAME/wp-content/uploads \
    --null \
    --verbatim-files-from \
    --files-from=replace-images/filenames-2008-2009.null-terminated
```
