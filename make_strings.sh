#!/bin/sh -x


for source in `find . -type f -name "*.po"`; do
    destination=`echo $source | sed -e "s/.po$/.mo/g"`

    msgfmt $source -o $destination
done
