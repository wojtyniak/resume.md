build-examples:
    #! /bin/bash
    for file in examples/*.md; do
        python3 main.py $file examples/$(basename $file .md).html
        python3 main.py -s style-classic.css $file examples/$(basename $file .md)-classic.html
    done